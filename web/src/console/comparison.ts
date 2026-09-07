// Read-only policy illustration. This does not issue leases or implement the backend authority gate.
import type { ConsoleSnapshot, Rule } from "./types";
export interface Demand {
  id: string;
  floor: number;
  useful: number;
  weight: number;
}
export function fill(demands: Demand[], cap: number, reserve: number) {
  if (
    !Number.isFinite(cap) ||
    !Number.isFinite(reserve) ||
    cap < 0 ||
    reserve < 0 ||
    new Set(demands.map((d) => d.id)).size !== demands.length ||
    demands.some(
      (d) =>
        ![d.floor, d.useful, d.weight].every(Number.isFinite) ||
        d.floor < 0 ||
        d.useful < d.floor ||
        d.weight < 1 ||
        d.weight > 2,
    )
  )
    throw new Error("Invalid comparison inputs");
  let pool = cap - reserve - demands.reduce((s, d) => s + d.floor, 0);
  if (pool < 0) return null;
  const active = demands
    .filter((d) => d.useful > d.floor)
    .map((d) => ({ ...d, threshold: (d.useful - d.floor) / d.weight }))
    .sort((a, b) => a.threshold - b.threshold || a.id.localeCompare(b.id));
  let level = 0,
    total = active.reduce((s, d) => s + d.weight, 0);
  for (const d of active) {
    const cost = (d.threshold - level) * total;
    if (cost > pool) {
      level += pool / total;
      pool = 0;
      break;
    }
    pool -= cost;
    level = d.threshold;
    total -= d.weight;
  }
  return Object.fromEntries(
    demands.map((d) => [
      d.id,
      d.floor + Math.min(d.useful - d.floor, d.weight * level),
    ]),
  );
}
export function compare(
  s: ConsoleSnapshot,
  preset: "captured" | "earlier_wait",
) {
  const members = s.members.map((m) => ({
    id: m.id,
    floor: m.floor_w,
    useful: m.useful_w ?? m.max_w,
    weight: 1,
  }));
  const initial = Object.fromEntries(
    s.members.map((m, i) => [
      m.id,
      preset === "captured"
        ? Math.min(20, Math.max(0, m.debt_wh))
        : i === 0
          ? 10
          : 0,
    ]),
  );
  const reserve = s.site.measurement_reserve_w + s.site.external_bound_w;
  const floors = members.reduce((n, m) => n + m.floor, 0);
  const useful = members.reduce((n, m) => n + m.useful, 0);
  const cap =
    preset === "captured"
      ? s.site.cap_w
      : Math.floor(floors + reserve + (useful - floors) * 0.5);
  const trace = Array.from({ length: 36 }, (_, tick) => ({
    seconds: tick * 10,
    cap,
    members: members.map((m, i) => ({
      ...m,
      useful:
        tick >= 12 && tick < 24 && i === 1
          ? m.floor + Math.round((m.useful - m.floor) * 0.25)
          : m.useful,
    })),
  }));
  const results = (["equal_surplus", "debt_weighted_surplus"] as Rule[]).map(
    (rule) => {
      const debt = { ...initial },
        served = Object.fromEntries(members.map((m) => [m.id, 0])),
        unmet = { ...served };
      let unused = 0;
      const series: { seconds: number; maxDebt: number; unmetWh: number }[] =
        [];
      for (const step of trace) {
        const reference = fill(step.members, step.cap, reserve);
        const allocations = fill(
          step.members.map((m) => ({
            ...m,
            weight:
              rule === "equal_surplus" ? 1 : 1 + Math.min(1, debt[m.id] / 10),
          })),
          step.cap,
          reserve,
        );
        if (!reference || !allocations)
          return { rule, feasible: false, debt, served, unmet, unused, series };
        for (const m of step.members) {
          served[m.id] += (allocations[m.id] * 10) / 3600;
          unmet[m.id] +=
            (Math.max(0, m.useful - allocations[m.id]) * 10) / 3600;
          debt[m.id] = Math.min(
            20,
            Math.max(
              0,
              debt[m.id] + ((reference[m.id] - allocations[m.id]) * 10) / 3600,
            ),
          );
        }
        unused +=
          (Math.max(
            0,
            step.cap -
              reserve -
              Object.values(allocations).reduce((a, b) => a + b, 0),
          ) *
            10) /
          3600;
        series.push({
          seconds: step.seconds + 10,
          maxDebt: Math.max(...Object.values(debt)),
          unmetWh: Object.values(unmet).reduce((a, b) => a + b, 0),
        });
      }
      return { rule, feasible: true, debt, served, unmet, unused, series };
    },
  );
  return {
    schema: "truss.policy_comparison.v1",
    run_id: s.run_id,
    preset,
    scope:
      "Browser-only continuous policy illustration, 36 identical 10-second steps per rule. No leases, MQTT, rounding, device steps, or observed electricity. Credits use equal-reference minus immediately assigned authority; the live backend accounts conservative outstanding authority instead.",
    initial_debt_wh: initial,
    cap,
    reserve,
    trace,
    results,
  };
}
