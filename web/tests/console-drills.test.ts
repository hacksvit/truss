import { afterEach, beforeEach, expect, it, vi } from "vitest";
import fixtures from "../../fixtures/snapshots.json";
import type { ConsoleSnapshot, DrillReport } from "../src/console/types";
import { runDrill } from "../src/console/drills";
import { state, sendIntent } from "../src/console/transport";
vi.mock("../src/console/transport", async (original) => ({
  ...(await original<typeof import("../src/console/transport")>()),
  state: vi.fn(),
  sendIntent: vi.fn(),
}));
const initial = () => {
  const s = structuredClone(fixtures[0].data) as unknown as ConsoleSnapshot;
  s.source = "live";
  s.site.state = "leased";
  s.site.coordinator_status = "online";
  s.site.observed_quality = "fresh";
  s.site.observed_w = s.site.baseline_sum_w + 1000;
  s.capabilities.chaos = true;
  return s;
};
let latest: ConsoleSnapshot;
beforeEach(() => {
  vi.useFakeTimers();
  latest = initial();
  vi.mocked(state).mockImplementation(async () => structuredClone(latest));
  vi.mocked(sendIntent).mockImplementation(async (i, onOperation) => {
    const o = {
      operation_id: crypto.randomUUID(),
      run_id: latest.run_id,
      kind: i.path,
      status: "applied" as const,
      control_revision: 1,
      message: String(i.body.action ?? i.path),
    };
    i.operation = o;
    onOperation?.(o);
    return o;
  });
});
afterEach(() => {
  vi.useRealTimers();
  vi.resetAllMocks();
});
it("restores capacity after cancellation without reusing the aborted signal", async () => {
  const c = new AbortController();
  let report: DrillReport | undefined;
  vi.mocked(sendIntent).mockImplementation(async (i) => {
    if (i.path === "cap") latest.site.cap_w = i.body.watts as number;
    return {
      operation_id: crypto.randomUUID(),
      run_id: latest.run_id,
      kind: i.path,
      status: "applied" as const,
      message: "applied",
      control_revision: 1,
    };
  });
  const before = initial();
  const done = runDrill("infeasible", before, (r) => (report = r), c.signal);
  await vi.advanceTimersByTimeAsync(100);
  expect(latest.site.cap_w).toBeLessThan(
    before.site.baseline_sum_w +
      before.site.measurement_reserve_w +
      before.site.external_bound_w,
  );
  c.abort();
  await done;
  expect(latest.site.cap_w).toBe(before.site.cap_w);
  expect(report?.phase).toBe("Complete");
  expect(report?.recovery).toContain("restored");
  expect(vi.mocked(sendIntent).mock.calls.at(-1)?.[2]).toBeUndefined();
});
it("does not apply a scenario when its preflight health has changed", async () => {
  latest.site.observed_quality = "unknown";
  const r = await runDrill(
    "coordinator",
    initial(),
    () => {},
    new AbortController().signal,
  );
  expect(sendIntent).not.toHaveBeenCalled();
  expect(r.error).toContain("starting state changed");
});
it("does not send cleanup commands into a different run", async () => {
  const c = new AbortController();
  const done = runDrill("coordinator", initial(), () => {}, c.signal);
  await vi.advanceTimersByTimeAsync(100);
  latest.run_id = "another-run";
  c.abort();
  const r = await done;
  expect(sendIntent).toHaveBeenCalledTimes(1);
  expect(r.recovery).toContain("Manual recovery required");
});
it("leaves an uncertain action explicit instead of inventing a new recovery command", async () => {
  vi.mocked(sendIntent).mockRejectedValueOnce(new TypeError("Network lost"));
  const r = await runDrill(
    "coordinator",
    initial(),
    () => {},
    new AbortController().signal,
  );
  expect(sendIntent).toHaveBeenCalledTimes(1);
  expect(r.status).toBe("inconclusive");
  expect(r.recovery).toContain("not confirmed");
});
