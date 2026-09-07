import type {
  ConsoleMember,
  ConsoleSnapshot,
  HistoryPoint,
  Check,
  DrillReport,
} from "./types";
export const home = (id: string) =>
  `Home ${id.split("-").at(-1)?.toUpperCase()}`;
export const watts = (n: number | null | undefined) =>
  n == null ? "Unknown" : `${Math.round(n).toLocaleString()} W`;
export const sumKnown = (values: (number | null | undefined)[]) =>
  values.some((v) => v == null)
    ? null
    : values.reduce<number>((a, v) => a + (v ?? 0), 0);
export function historyPoint(
  s: ConsoleSnapshot,
  at = Date.now(),
): HistoryPoint {
  return {
    at,
    label: new Date(at).toLocaleTimeString(),
    cap: s.site.cap_w,
    exposure: s.site.exposure_w,
    observed: s.site.observed_quality === "fresh" ? s.site.observed_w : null,
    proposed: sumKnown(s.members.map((m) => m.target_w)),
    issued: sumKnown(s.members.map((m) => m.issued_w)),
  };
}
export function explain(
  m: ConsoleMember,
  s: ConsoleSnapshot,
  stale = false,
): string {
  if (stale || m.observed_quality !== "fresh")
    return "The latest draw is unverified. Silence does not release this home’s reserved capacity.";
  if (s.site.state === "infeasible")
    return "The approved minimums exceed the site limit. Flexible grants cannot resolve this shortage.";
  if (s.site.state === "recovering")
    return "The coordinator is waiting for earlier permissions to expire before issuing new ones.";
  if (m.unusable_w && m.unusable_w > 0)
    return `${watts(m.unusable_w)} cannot fit the next whole appliance step. It remains inside this home’s allocation.`;
  if (m.target_w != null && m.reserved_w > m.target_w)
    return "An earlier, larger permission may still be active. Its capacity remains reserved until expiry.";
  if (
    m.lease.quality === "fresh" &&
    m.lease.remaining_ms === 0 &&
    m.observed_w != null &&
    m.observed_w <= m.floor_w
  )
    return "The local enforcer reports this home at its approved minimum.";
  if (m.target_w != null && m.issued_w != null && m.target_w > m.issued_w)
    return "The proposal exceeds the latest issued permission. The reservation gate must allow any increase.";
  if (m.weight > 1)
    return `Earlier service deficit gives this plan a ${m.weight.toFixed(2)}× weight, capped at 2×.`;
  return "The plan shares flexible capacity equally above approved minimums, up to each home’s useful demand.";
}
export function baselineReview(s: ConsoleSnapshot, id: string, value: number) {
  const m = s.members.find((m) => m.id === id);
  const valid =
    !!m && Number.isInteger(value) && value >= m.floor_w && value <= m.max_w;
  const total = s.site.baseline_sum_w - (m?.floor_w ?? 0) + value;
  const required =
    total + s.site.measurement_reserve_w + s.site.external_bound_w;
  return {
    valid,
    total,
    required,
    shortfall: Math.max(0, required - s.site.cap_w),
    fits: valid && required <= s.site.cap_w,
  };
}
export function evaluateDrill(report: DrillReport): Check[] {
  const samples = report.samples.filter((x) => x.elapsed_ms >= 0);
  const first = samples[0]?.snapshot;
  const last = samples.at(-1)?.snapshot;
  if (!first || !last)
    return [
      {
        label: "Observation available",
        status: "inconclusive",
        detail: "No complete observation window.",
      },
    ];
  const fresh = samples.filter(
    (x) =>
      x.snapshot.site.observed_quality === "fresh" &&
      x.snapshot.site.observed_w !== null,
  );
  const scope: Check = {
    label: "Observation coverage",
    status:
      report.missing_samples || fresh.length !== samples.length
        ? "inconclusive"
        : "observed",
    detail: `${fresh.length}/${samples.length} snapshots have fresh site observations. This is a sampled UI record, not a complete wire trace.`,
  };
  const target =
    first.members.find((m) => m.id === "member-c") ?? first.members[0];
  if (report.kind === "infeasible")
    return [
      {
        label: "Shortage reported",
        status: samples.some(
          (x) =>
            x.snapshot.site.state === "infeasible" &&
            x.snapshot.site.deficit_w > 0,
        )
          ? "observed"
          : "inconclusive",
        detail:
          "The site must report an infeasible capacity rather than reducing registered minimums.",
      },
      {
        label: "Minimums unchanged",
        status: samples.every(
          (x) =>
            x.snapshot.members.length ===
              report.initial_snapshot.members.length &&
            x.snapshot.members.every(
              (m) =>
                m.floor_w ===
                report.initial_snapshot.members.find((v) => v.id === m.id)
                  ?.floor_w,
            ),
        )
          ? "observed"
          : "not_observed",
        detail:
          "Compares registered floors, not medical or electrical continuity.",
      },
      scope,
    ];
  const atFloor = samples.some(
    (x) =>
      x.elapsed_ms >= 6000 &&
      (report.kind === "coordinator"
        ? x.snapshot.site.observed_quality === "fresh" &&
          x.snapshot.site.observed_w !== null &&
          x.snapshot.site.observed_w <= x.snapshot.site.baseline_sum_w
        : x.snapshot.members.some(
            (m) =>
              m.id === target.id &&
              m.observed_quality === "fresh" &&
              m.observed_w !== null &&
              m.observed_w <= m.floor_w,
          )),
  );
  const checks: Check[] = [
    {
      label:
        report.kind === "coordinator"
          ? "Local fallback observed"
          : `${home(target.id)} fallback observed`,
      status: atFloor ? "observed" : "inconclusive",
      detail:
        "Requires a fresh enforcer reading at or below the registered baseline after the lease window. A countdown alone cannot satisfy this check.",
    },
  ];
  if (report.kind === "double_restart") {
    const restarts = report.operations
      .filter((o) => o.message?.includes("restart_coordinator"))
      .slice(0, 2);
    const gap =
      restarts.length === 2
        ? Date.parse(restarts[1].finished_at ?? "") -
          Date.parse(restarts[0].created_at ?? "")
        : NaN;
    return [
      {
        label: "Two restarts within one lease window",
        status:
          Number.isFinite(gap) &&
          gap >= 0 &&
          gap < 6000 &&
          report.samples.some((x) => x.snapshot.site.state === "recovering")
            ? "observed"
            : "inconclusive",
        detail: `Scenario restart interval: ${Number.isFinite(gap) ? gap + " ms" : "unknown"}. Requires an interval below 6,000 ms and an observed recovery hold. This is not a proof of every grant race.`,
      },
      scope,
    ];
  }
  if (report.kind === "delayed_grant")
    checks.push({
      label: "Expired reply rejected",
      status: report.events.some(
        (e) =>
          e.kind === "truss.lease_ack.v1" &&
          e.member_id === target.id &&
          /expired|late|reject/.test(e.code + " " + e.text),
      )
        ? "observed"
        : "inconclusive",
      detail:
        "The snapshot event tail does not currently expose lease acknowledgements. Individual expired-reply rejection requires the backend wire evidence and remains unverified here.",
    });
  return [...checks, scope];
}
export function download(name: string, value: unknown) {
  const url = URL.createObjectURL(
    new Blob([JSON.stringify(value, null, 2)], { type: "application/json" }),
  );
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
