import { describe, it, expect } from "vitest";
import fixtures from "../../fixtures/snapshots.json";
import cases from "../../fixtures/allocator-cases.json";
import {
  baselineReview,
  evaluateDrill,
  explain,
  historyPoint,
  sumKnown,
} from "../src/console/model";
import { compare, fill } from "../src/console/comparison";
import type { ConsoleSnapshot, DrillReport } from "../src/console/types";
const snapshot = fixtures[0].data as unknown as ConsoleSnapshot;
const live = () => ({ ...structuredClone(snapshot), source: "live" as const });
function report(): DrillReport {
  return {
    schema: "truss.console_drill.v1",
    id: "test",
    kind: "coordinator",
    run_id: snapshot.run_id,
    source: "live",
    initial_snapshot: live(),
    started_at: "2026-09-07T00:00:00Z",
    finished_at: null,
    phase: "Complete",
    status: "running",
    checks: [],
    operations: [],
    samples: [],
    missing_samples: 0,
    events: [],
    recovery: "",
    scope: "",
  };
}
describe("console evidence boundaries", () => {
  it("does not total partially unknown permissions or graph stale draw", () => {
    expect(sumKnown([100, null, 200])).toBeNull();
    const s = live();
    s.site.observed_quality = "stale";
    s.site.observed_w = 2500;
    expect(historyPoint(s).observed).toBeNull();
  });
  it("never interprets a displayed zero countdown as proof of fallback", () => {
    const r = report(),
      s = live();
    s.site.observed_quality = "unknown";
    s.site.observed_w = null;
    s.members.forEach((m) => (m.lease.remaining_ms = 0));
    r.samples = [{ elapsed_ms: 6500, snapshot: s }];
    expect(
      evaluateDrill(r).find((c) => c.label === "Local fallback observed")
        ?.status,
    ).toBe("inconclusive");
  });
  it("requires a fresh enforcer reading after the lease window", () => {
    const r = report(),
      s = live();
    s.site.observed_quality = "fresh";
    s.site.observed_w = s.site.baseline_sum_w;
    r.samples = [{ elapsed_ms: 6100, snapshot: s }];
    expect(evaluateDrill(r)[0].status).toBe("observed");
    r.samples[0].elapsed_ms = 100;
    expect(evaluateDrill(r)[0].status).toBe("inconclusive");
  });
  it("does not confuse a rejected device command with a rejected lease reply", () => {
    const r = report(),
      s = live();
    r.kind = "delayed_grant";
    r.samples = [{ elapsed_ms: 8000, snapshot: s }];
    r.events = [
      {
        seq: 1,
        at: "now",
        kind: "truss.ack.v1",
        member_id: "member-c",
        text: "rejected",
        code: "rejected",
      },
    ];
    expect(
      evaluateDrill(r).find((c) => c.label === "Expired reply rejected")
        ?.status,
    ).toBe("inconclusive");
  });
  it("checks restart timing instead of merely counting two operations", () => {
    const r = report(),
      s = live();
    r.kind = "double_restart";
    s.site.state = "recovering";
    r.samples = [{ elapsed_ms: 100, snapshot: s }];
    r.operations = [0, 1].map((i) => ({
      operation_id: String(i),
      run_id: s.run_id,
      kind: "chaos",
      status: "applied",
      control_revision: i,
      message: "restart_coordinator",
      created_at: `2026-09-07T00:00:0${i * 7}Z`,
      finished_at: `2026-09-07T00:00:0${i * 7}Z`,
    }));
    expect(evaluateDrill(r)[0].status).toBe("inconclusive");
    r.operations[1].finished_at = "2026-09-07T00:00:01Z";
    expect(evaluateDrill(r)[0].status).toBe("observed");
  });
  it("rejects baseline decreases, fractional watts and infeasible admission", () => {
    const s = live(),
      m = s.members[0];
    expect(baselineReview(s, m.id, m.floor_w - 1).valid).toBe(false);
    expect(baselineReview(s, m.id, m.floor_w + 0.1).valid).toBe(false);
    s.site.cap_w = s.site.baseline_sum_w + s.site.measurement_reserve_w;
    expect(baselineReview(s, m.id, m.floor_w + 1).fits).toBe(false);
  });
  it("compares minimums against the pre-drill registry", () => {
    const r = report(),
      s = live();
    r.kind = "infeasible";
    s.members.forEach((m) => (m.floor_w = 0));
    r.samples = [
      { elapsed_ms: 100, snapshot: s },
      { elapsed_ms: 500, snapshot: s },
    ];
    expect(
      evaluateDrill(r).find((c) => c.label === "Minimums unchanged")?.status,
    ).toBe("not_observed");
  });
  it("prioritizes missing telemetry over optimistic explanations", () => {
    const s = live(),
      m = s.members[0];
    m.observed_quality = "unknown";
    m.weight = 2;
    expect(explain(m, s)).toContain("unverified");
  });
});
describe("read-only policy comparison", () => {
  for (const c of cases)
    it(`matches backend allocator fixture: ${c.name}`, () => {
      const r = fill(
        c.floors.map((f, i) => ({
          id: String(i),
          floor: f,
          useful: c.useful[i],
          weight: c.weights[i],
        })),
        c.cap,
        0,
      );
      expect(
        r ? Object.values(r).map((v) => Math.floor(v + 1e-9)) : null,
      ).toEqual(c.expected);
    });
  it("preserves floors, useful bounds and site capacity across varied inputs", () => {
    for (let seed = 1; seed <= 150; seed++) {
      const d = Array.from({ length: 5 }, (_, i) => ({
        id: String(i),
        floor: 100 + i * 10,
        useful: 200 + ((seed * (i + 1) * 47) % 1800),
        weight: 1 + (seed % 11) / 10,
      }));
      const cap = 700 + seed * 13;
      const result = fill(d, cap, 100)!;
      expect(
        Object.values(result).reduce((a, b) => a + b, 0) + 100,
      ).toBeLessThanOrEqual(cap + 1e-7);
      for (const m of d) {
        expect(result[m.id]).toBeGreaterThanOrEqual(m.floor - 1e-7);
        expect(result[m.id]).toBeLessThanOrEqual(m.useful + 1e-7);
      }
    }
  });
  it("shares one immutable trace and discloses the idealised scope", () => {
    const s = live(),
      before = JSON.stringify(s);
    const r = compare(s, "earlier_wait");
    expect(r.trace).toHaveLength(36);
    expect(r.results.every((x) => x.series.length === 36)).toBe(true);
    expect(r.initial_debt_wh[s.members[0].id]).toBe(10);
    expect(r.results[1].served[s.members[0].id]).toBeGreaterThan(
      r.results[0].served[s.members[0].id],
    );
    expect(JSON.stringify(s)).toBe(before);
    expect(r.scope).toContain("No leases");
  });
});
