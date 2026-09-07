import { useEffect, useState } from "react";
import { useConsole } from "../console/useConsole";
import {
  Baselines,
  FairnessPanel,
  Homes,
  Inspector,
  Processes,
  Safety,
} from "../console/panels";
import FailureDrills from "../console/FailureDrills";
import Evidence from "../console/Evidence";
import { watts } from "../console/model";
import type { DrillReport } from "../console/types";
import "../console/console.css";
export default function Console() {
  const c = useConsole();
  const [selected, setSelected] = useState<string | null>(null),
    [cap, setCap] = useState(5000),
    [report, setReport] = useState<DrillReport | null>(null);
  const s = c.snapshot?.source === c.source ? c.snapshot : null;
  const stale = c.connection === "stale" || c.connection === "connecting";
  const blocked = stale || !!c.unresolved;
  const member = s?.members.find((m) => m.id === selected);
  useEffect(() => {
    if (s) {
      setCap(s.site.cap_w);
      setSelected(null);
      setReport(null);
    }
  }, [s?.run_id, c.source]);
  return (
    <main className="console cx-console">
      <div className="page-heading">
        <div>
          <div className="section-label">OPERATOR CONSOLE</div>
          <h1>One limit. Five households.</h1>
          <p className="cx-subtitle">
            See the allocation. Test the failure. Keep the evidence.
          </p>
        </div>
        <div className="cx-source">
          <div role="group" aria-label="Console data source">
            <button
              aria-pressed={c.source === "live"}
              disabled={c.busy || !!c.unresolved}
              onClick={() => c.setSource("live")}
            >
              Live runtime
            </button>
            <button
              aria-pressed={c.source === "mock"}
              disabled={c.busy || !!c.unresolved}
              onClick={() => c.setSource("mock")}
            >
              Mock preview
            </button>
          </div>
          <span className={`cx-connection ${stale ? "cx-warn" : ""}`}>
            <i className={`cx-dot ${stale ? "cx-dot-off" : ""}`} />
            {c.connection === "connected"
              ? "Streaming"
              : c.connection === "polling"
                ? "Polling fallback"
                : c.connection}
          </span>
        </div>
      </div>
      <div className="cx-boundary">
        <strong>
          {c.source === "live" ? "LIVE SOFTWARE DEMO" : "MOCK PREVIEW"}
        </strong>
        <span>
          {c.source === "live"
            ? "Actual local processes and MQTT. All appliance readings are virtual."
            : "Synthetic state only. Process failure drills and live policy controls are unavailable."}
        </span>
      </div>
      <nav className="cx-sections" aria-label="Console sections">
        {[
          ["overview", "Overview"],
          ["drills", "Failure drills"],
          ["fairness", "Fairness"],
          ["baselines", "Minimums"],
          ["evidence", "Evidence"],
        ].map(([id, label]) => (
          <a key={id} href={`#${id}`}>
            {label}
          </a>
        ))}
      </nav>
      {!s ? (
        <section className="panel cx-waiting">
          <span className="cx-dot cx-dot-off" />
          <h2>
            Waiting for the{" "}
            {c.source === "live" ? "live runtime" : "mock server"}
          </h2>
          <p>
            No readings or permissions are assumed while disconnected. The
            console will reconnect automatically.
          </p>
          <p className="cx-note">
            {c.source === "live"
              ? "The live backend is expected on local port 8001."
              : "The mock backend is expected on local port 8000."}
          </p>
        </section>
      ) : (
        <>
          {stale && (
            <p className="cx-alert" role="alert">
              Connection is stale. Readings and countdowns are unverified, and
              controls are disabled.
            </p>
          )}
          <Safety s={s} history={c.history} stale={stale} />
          <div className="cx-live-controls panel">
            <div className="cx-control-cap">
              <label htmlFor="cx-cap">
                Site capacity <b>{watts(cap)}</b>
              </label>
              <div>
                <input
                  id="cx-cap"
                  type="range"
                  min="0"
                  max="6000"
                  step="100"
                  value={cap}
                  disabled={c.busy || blocked}
                  onChange={(e) => setCap(Number(e.target.value))}
                />
                <input
                  aria-label="Site capacity in watts"
                  type="number"
                  min="0"
                  max="1000000"
                  step="1"
                  value={Number.isNaN(cap) ? "" : cap}
                  disabled={c.busy || blocked}
                  onChange={(e) =>
                    setCap(e.target.value === "" ? NaN : Number(e.target.value))
                  }
                />
                <button
                  disabled={
                    c.busy ||
                    blocked ||
                    !Number.isInteger(cap) ||
                    cap < 0 ||
                    cap > 1000000
                  }
                  onClick={() => c.act("cap", { watts: cap })}
                >
                  Apply capacity
                </button>
              </div>
            </div>
            <div className="cx-control-process">
              <span>Coordinator</span>
              <div className="cx-button-row">
                <button
                  disabled={c.busy || blocked || !s.capabilities.chaos}
                  onClick={() =>
                    c.act("chaos", {
                      action:
                        s.site.coordinator_status === "offline"
                          ? "restart_coordinator"
                          : "kill_coordinator",
                      member_id: null,
                    })
                  }
                >
                  {s.site.coordinator_status === "offline"
                    ? "Restart coordinator"
                    : "Stop coordinator"}
                </button>
                {c.source === "live" && (
                  <button
                    disabled={c.busy || blocked}
                    onClick={() =>
                      c.act("chaos", {
                        action: "restart_coordinator",
                        member_id: null,
                      })
                    }
                  >
                    Restart with recovery hold
                  </button>
                )}
              </div>
            </div>
            <p className="cx-control-status" role="status">
              {c.busy
                ? report?.status === "running"
                  ? `${report.phase}…`
                  : c.message || "Waiting for confirmation…"
                : c.message ||
                  "Capacity and policy changes keep earlier permissions reserved until expiry."}
              {c.operation && (
                <span>
                  Operation {c.operation.operation_id.slice(0, 8)} ·{" "}
                  {c.operation.status}
                </span>
              )}
            </p>
            {c.unresolved && !c.busy && (
              <div className="cx-alert">
                The last action is not fully confirmed. New actions are blocked.
                <button onClick={c.retry}>
                  Check / retry the same operation
                </button>
              </div>
            )}
          </div>
          <Homes s={s} stale={stale} onSelect={setSelected} />
          <FailureDrills
            s={s}
            busy={c.busy}
            blocked={blocked}
            setBusy={c.setBusy}
            report={report}
            setReport={setReport}
          />
          <FairnessPanel
            s={s}
            fairness={c.fairness}
            disabled={c.busy || blocked}
            onRule={(rule) => c.act("rule", { rule })}
          />
          <Baselines key={`baselines:${s.run_id}:${c.source}`} s={s} />
          <Evidence
            key={`evidence:${s.run_id}:${c.source}`}
            s={s}
            stale={stale}
            source={c.source}
            history={c.history}
            report={report}
          />
          {c.source === "live" && <Processes runtime={c.runtime} />}
          <p className="cx-note">{c.auxError}</p>
          <footer className="cx-footer">
            <span>
              Run {s.run_id.slice(0, 8)} · {s.source.toUpperCase()}
            </span>
            <span>
              No mains switching. No medical-device control or certification.
            </span>
          </footer>
          {member && (
            <Inspector
              key={member.id}
              m={member}
              s={s}
              stale={stale}
              onClose={() => setSelected(null)}
            />
          )}
        </>
      )}
    </main>
  );
}
