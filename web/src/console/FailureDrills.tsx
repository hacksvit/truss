import { useEffect, useRef } from "react";
import type { ConsoleSnapshot, DrillKind, DrillReport } from "./types";
import { DRILLS, runDrill } from "./drills";
import { Heading } from "./panels";
import { download } from "./model";
export default function FailureDrills({
  s,
  busy,
  blocked,
  setBusy,
  report,
  setReport,
}: {
  s: ConsoleSnapshot;
  busy: boolean;
  blocked: boolean;
  setBusy: (v: boolean) => void;
  report: DrillReport | null;
  setReport: (v: DrillReport) => void;
}) {
  const controller = useRef<AbortController | null>(null);
  const alive = useRef(true);
  const running = !!report && report.phase !== "Complete";
  useEffect(() => {
    alive.current = true;
    return () => {
      alive.current = false;
      controller.current?.abort();
    };
  }, []);
  useEffect(() => {
    if (!running) return;
    const warn = (e: BeforeUnloadEvent) => {
      e.preventDefault();
      e.returnValue = "";
    };
    window.addEventListener("beforeunload", warn);
    return () => window.removeEventListener("beforeunload", warn);
  }, [running]);
  async function start(kind: DrillKind) {
    if (busy || blocked || controller.current) return;
    const c = new AbortController();
    controller.current = c;
    setBusy(true);
    try {
      await runDrill(
        kind,
        s,
        (r) => {
          if (alive.current) setReport(r);
        },
        c.signal,
      );
    } finally {
      controller.current = null;
      if (alive.current) setBusy(false);
    }
  }
  return (
    <section id="drills" className="panel">
      <Heading
        number="03 / FAILURE DRILLS"
        title="Let the protocol answer."
        detail="Real process actions. Recorded observations. Explicit recovery."
      />
      <p className="cx-note">
        A drill temporarily changes this virtual site, then attempts to restore
        its starting setup. Keep this page open until recovery completes.
        Delivery faults expire automatically.
      </p>
      {s.source === "live" &&
        (s.site.state !== "leased" || s.site.observed_quality !== "fresh") && (
          <p className="cx-alert">
            Drills need a healthy starting state with fresh enforcer readings.{" "}
            {s.members.some((m) => m.status === "fault")
              ? "An enforcer has a persistent fault. A new backend run is required; restarting only the coordinator will not clear it."
              : "Wait for recovery and current readings before starting."}
          </p>
        )}
      {s.source !== "live" && (
        <p className="cx-alert">
          Mock preview cannot run real failure drills. Select Live runtime
          above.
        </p>
      )}
      <div className="cx-drills">
        {DRILLS.map((d) => (
          <button
            key={d.id}
            className="cx-drill"
            disabled={
              busy ||
              blocked ||
              s.source !== "live" ||
              !s.capabilities.chaos ||
              s.site.state !== "leased" ||
              s.site.coordinator_status !== "online" ||
              s.site.observed_quality !== "fresh"
            }
            onClick={() => start(d.id)}
          >
            <span>{d.seconds}s observation</span>
            <h3>{d.name}</h3>
            <p>{d.description}</p>
            <b>Run drill ↗</b>
          </button>
        ))}
      </div>
      {report && (
        <div className="cx-drill-result" aria-live="polite">
          <div className="cx-inline-heading">
            <div>
              <h3>{DRILLS.find((d) => d.id === report.kind)?.name}</h3>
              <p>
                {report.phase} · {report.samples.length} snapshots captured
              </p>
            </div>
            <span
              className={`cx-status ${report.status === "failed" ? "cx-warn" : ""}`}
            >
              {report.status.replaceAll("_", " ")}
            </span>
          </div>
          {report.status === "running" && (
            <button onClick={() => controller.current?.abort()}>
              Stop and restore
            </button>
          )}
          {report.error && <p className="cx-alert">{report.error}</p>}
          <ul className="cx-checks">
            {report.checks.map((c) => (
              <li key={c.label}>
                <span
                  className={
                    c.status === "observed"
                      ? "cx-check-observed"
                      : "cx-check-unknown"
                  }
                >
                  {c.status === "observed" ? "✓" : "?"}
                </span>
                <div>
                  <b>{c.label}</b>
                  <p>{c.detail}</p>
                </div>
                <small>{c.status.replaceAll("_", " ")}</small>
              </li>
            ))}
          </ul>
          {report.phase === "Complete" && (
            <p className="cx-note">{report.recovery}</p>
          )}
          <details>
            <summary>Operation trail</summary>
            <ol className="cx-events">
              {report.operations.map((o) => (
                <li key={o.operation_id}>
                  <time>
                    {o.finished_at
                      ? new Date(o.finished_at).toLocaleTimeString()
                      : "pending"}
                  </time>
                  <span>{o.message ?? o.kind}</span>
                  <code>{o.status}</code>
                </li>
              ))}
            </ol>
          </details>
          {report.status !== "running" && (
            <button
              onClick={() => download("truss-failure-drill.json", report)}
            >
              Download this drill
            </button>
          )}
          <p className="cx-note">
            “Observed” means this finite, sampled check found the expected
            result. “Inconclusive” means the evidence is incomplete. Neither is
            a proof over arbitrary failures.
          </p>
        </div>
      )}
    </section>
  );
}
