import type { ConsoleSnapshot, DrillKind, DrillReport } from "./types";
import { delay, intent, sendIntent, state } from "./transport";
import { evaluateDrill } from "./model";
export const DRILLS: {
  id: DrillKind;
  name: string;
  seconds: number;
  description: string;
}[] = [
  {
    id: "coordinator",
    name: "Coordinator stops",
    seconds: 9,
    description:
      "Stop the actual coordinator. Watch independent enforcers return to their minimums.",
  },
  {
    id: "delayed_grant",
    name: "A reply arrives too late",
    seconds: 17,
    description:
      "Delay Home C’s grants by 7 seconds, beyond the 6-second request lifetime.",
  },
  {
    id: "partition",
    name: "A home loses contact",
    seconds: 13,
    description:
      "Partition Home C’s agent for 10 seconds. Its enforcer keeps its own clock.",
  },
  {
    id: "double_restart",
    name: "Two quick restarts",
    seconds: 9,
    description: "Restart the coordinator twice and observe the recovery hold.",
  },
  {
    id: "infeasible",
    name: "Minimums do not fit",
    seconds: 4,
    description:
      "Temporarily lower usable capacity below the approved minimums. Expect an explicit shortage.",
  },
];
export async function runDrill(
  kind: DrillKind,
  initial: ConsoleSnapshot,
  onUpdate: (r: DrillReport) => void,
  signal: AbortSignal,
): Promise<DrillReport> {
  const definition = DRILLS.find((d) => d.id === kind)!;
  const target =
    initial.members.find((m) => m.id === "member-c") ?? initial.members[0];
  const report: DrillReport = {
    schema: "truss.console_drill.v1",
    id: crypto.randomUUID(),
    kind,
    run_id: initial.run_id,
    source: "live",
    initial_snapshot: initial,
    started_at: new Date().toISOString(),
    finished_at: null,
    phase: "Preparing",
    status: "running",
    checks: [],
    operations: [],
    samples: [],
    events: [],
    missing_samples: 0,
    recovery: "Pending",
    scope:
      "Sampled browser observations of virtual enforcers and actual process actions. Not a complete message trace, timing proof, or physical electrical measurement.",
  };
  const emit = () =>
    onUpdate({
      ...report,
      operations: [...report.operations],
      samples: [...report.samples],
      events: [...report.events],
      checks: [...report.checks],
    });
  let changed = false;
  let started = performance.now();
  let uncertain = false;
  const fresh = async (abort?: AbortSignal) => {
    const s = await state("live", abort);
    if (s.run_id !== initial.run_id)
      throw new Error(
        "Backend run changed. Automatic actions stop to avoid controlling another run.",
      );
    return s;
  };
  const action = async (
    path: string,
    fields: Record<string, unknown>,
    abort?: AbortSignal,
  ) => {
    const s = await fresh(abort);
    const i = intent("live", s, path, fields);
    changed = true;
    try {
      return await sendIntent(
        i,
        (o) => {
          const at = report.operations.findIndex(
            (v) => v.operation_id === o.operation_id,
          );
          if (at < 0) report.operations.push(o);
          else report.operations[at] = o;
          emit();
        },
        abort,
      );
    } catch (e) {
      uncertain =
        !i.operation || ["queued", "running"].includes(i.operation.status);
      throw e;
    }
  };
  const capture = (s: ConsoleSnapshot) => {
    report.samples.push({
      elapsed_ms: Math.round(performance.now() - started),
      snapshot: s,
    });
    const seen = new Set(report.events.map((e) => e.seq));
    for (const e of s.events)
      if (e.seq > initial.event_cursor && !seen.has(e.seq)) {
        report.events.push(e);
        seen.add(e.seq);
      }
    emit();
  };
  try {
    if (initial.source !== "live" || !initial.capabilities.chaos)
      throw new Error("Failure drills require the live runtime.");
    if (
      initial.site.coordinator_status !== "online" ||
      initial.site.state !== "leased" ||
      initial.site.observed_quality !== "fresh"
    )
      throw new Error(
        "Start from a healthy live run with fresh observations and the coordinator online.",
      );
    if (
      initial.site.observed_w === null ||
      initial.site.observed_w <= initial.site.baseline_sum_w
    )
      throw new Error(
        "There is no flexible draw to withdraw. Restore a usable capacity before running this drill.",
      );
    const before = await fresh(signal);
    if (
      before.site.coordinator_status !== "online" ||
      before.site.state !== "leased" ||
      before.site.observed_quality !== "fresh" ||
      before.site.observed_w === null ||
      before.site.observed_w <= before.site.baseline_sum_w
    )
      throw new Error(
        "The starting state changed. Wait for a healthy run before trying again.",
      );
    report.initial_snapshot = before;
    capture(before);
    report.phase = definition.name;
    emit();
    if (kind === "coordinator")
      await action(
        "chaos",
        { action: "kill_coordinator", member_id: null },
        signal,
      );
    if (kind === "double_restart") {
      await action(
        "chaos",
        { action: "restart_coordinator", member_id: null },
        signal,
      );
      capture(await fresh(signal));
      await action(
        "chaos",
        { action: "restart_coordinator", member_id: null },
        signal,
      );
    }
    if (kind === "delayed_grant")
      await action(
        "faults",
        {
          target: `member:${target.id}`,
          action: "delay_grants",
          duration_ms: 10000,
          delay_ms: 7000,
          rate: 1,
        },
        signal,
      );
    if (kind === "partition")
      await action(
        "faults",
        {
          target: `member:${target.id}`,
          action: "partition",
          duration_ms: 10000,
          delay_ms: 0,
          rate: 1,
        },
        signal,
      );
    if (kind === "infeasible")
      await action(
        "cap",
        {
          watts: Math.max(
            0,
            initial.site.baseline_sum_w +
              initial.site.measurement_reserve_w +
              initial.site.external_bound_w -
              100,
          ),
        },
        signal,
      );
    // Window starts after the confirmed action, so request/queue latency cannot satisfy expiry checks.
    started = performance.now();
    report.samples = [];
    while (performance.now() - started < definition.seconds * 1000) {
      signal.throwIfAborted();
      try {
        capture(await fresh(signal));
      } catch (e) {
        if (signal.aborted || String(e).includes("run changed")) throw e;
        report.missing_samples++;
        emit();
      }
      await delay(450, signal);
    }
    report.checks = evaluateDrill(report);
    report.status = report.checks.some((c) => c.status === "not_observed")
      ? "failed"
      : report.checks.some((c) => c.status === "inconclusive")
        ? "inconclusive"
        : "observed";
  } catch (e) {
    report.status = "inconclusive";
    report.error = signal.aborted
      ? "Drill cancelled. Recovery is still attempted."
      : e instanceof Error
        ? e.message
        : "Drill interrupted";
  } finally {
    report.phase = "Restoring the starting setup";
    emit();
    if (changed) {
      try {
        if (uncertain)
          throw new Error(
            "An action was not confirmed. Inspect operation/process status before another action.",
          );
        if (kind === "coordinator" || kind === "double_restart")
          await action("chaos", {
            action: "restart_coordinator",
            member_id: null,
          });
        if (kind === "infeasible")
          await action("cap", { watts: initial.site.cap_w });
        report.recovery =
          kind === "partition" || kind === "delayed_grant"
            ? "The delivery fault expires automatically after 10 seconds; delayed messages still face normal validation."
            : "Starting configuration restored. Existing leases and recovery holds still apply.";
      } catch (e) {
        report.recovery = `Manual recovery required: ${e instanceof Error ? e.message : "Unable to confirm recovery"}`;
        report.status = "inconclusive";
      }
    } else report.recovery = "No scenario action was applied.";
    report.finished_at = new Date().toISOString();
    report.phase = "Complete";
    emit();
  }
  return report;
}
