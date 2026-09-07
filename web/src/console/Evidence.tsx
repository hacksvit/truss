import { useEffect, useRef, useState } from "react";
import type {
  ConsoleSnapshot,
  ConsoleSource,
  DrillReport,
  HistoryPoint,
  Recording,
  Replay,
} from "./types";
import { api } from "./transport";
import { download, home, watts } from "./model";
import { Heading } from "./panels";
export default function Evidence({
  s,
  source,
  history,
  report,
  stale,
}: {
  s: ConsoleSnapshot;
  stale: boolean;
  source: ConsoleSource;
  history: HistoryPoint[];
  report: DrillReport | null;
}) {
  const [catalog, setCatalog] = useState<Recording[]>([]),
    [chosen, setChosen] = useState(""),
    [replay, setReplay] = useState<Replay | null>(null),
    [seq, setSeq] = useState(0),
    [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  const alive = useRef(true),
    version = useRef(0),
    pending = useRef(false);
  const close = (id: string) =>
    api("live", `replays/${id}`, undefined, { method: "DELETE" }).catch(
      () => {},
    );
  useEffect(() => {
    alive.current = true;
    return () => {
      alive.current = false;
      version.current++;
    };
  }, []);
  useEffect(() => {
    let disposed = false;
    if (source === "live" && s.capabilities.replay)
      api<{ items: Recording[] }>("live", "recordings")
        .then((c) => {
          if (!disposed) {
            setCatalog(c.items);
            setChosen(c.items.find((i) => i.replayable)?.recorded_run_id ?? "");
          }
        })
        .catch((e) => {
          if (!disposed) setError(String(e.message));
        });
    return () => {
      disposed = true;
    };
  }, [source, s.run_id, s.capabilities.replay]);
  useEffect(() => {
    if (!replay?.playing) return;
    let disposed = false,
      inFlight = false;
    const id = setInterval(async () => {
      if (inFlight || pending.current) return;
      inFlight = true;
      const requestVersion = version.current;
      try {
        const r = await api<Replay>("live", `replays/${replay.replay_id}`);
        if (!disposed && requestVersion === version.current) {
          setReplay(r);
          setSeq(r.frame_seq);
        }
      } catch (e) {
        if (!disposed && requestVersion === version.current) {
          setError(e instanceof Error ? e.message : "Replay unavailable");
          setReplay((r) => (r ? { ...r, playing: false } : r));
        }
      } finally {
        inFlight = false;
      }
    }, 500);
    return () => {
      disposed = true;
      clearInterval(id);
    };
  }, [replay?.replay_id, replay?.playing]);
  useEffect(() => {
    const id = replay?.replay_id;
    return () => {
      if (id) void close(id);
    };
  }, [replay?.replay_id]);
  async function load() {
    if (pending.current || source !== "live" || !chosen) return;
    pending.current = true;
    version.current++;
    setBusy(true);
    setError("");
    setReplay(null);
    try {
      const r = await api<Replay>("live", "replays", {
        recorded_run_id: chosen,
        from_seq: 0,
        speed: 1,
      });
      if (alive.current) {
        setReplay(r);
        setSeq(r.frame_seq);
      } else await close(r.replay_id);
    } catch (e) {
      if (alive.current)
        setError(
          e instanceof Error ? e.message : "Recording could not be opened",
        );
    } finally {
      pending.current = false;
      if (alive.current) setBusy(false);
    }
  }
  async function move(path: string, body: unknown) {
    if (!replay || pending.current) return;
    pending.current = true;
    version.current++;
    setBusy(true);
    setError("");
    try {
      const r = await api<Replay>(
        "live",
        `replays/${replay.replay_id}/${path}`,
        body,
      );
      if (alive.current) {
        setReplay(r);
        setSeq(r.frame_seq);
      }
    } catch (e) {
      if (alive.current)
        setError(e instanceof Error ? e.message : "Replay action failed");
    } finally {
      pending.current = false;
      if (alive.current) setBusy(false);
    }
  }
  return (
    <section id="evidence" className="panel">
      <Heading
        number="06 / EVIDENCE"
        title="Show what actually happened."
        detail="Download the observations, inspect the event trail or open a saved recording."
      />
      {stale && (
        <p className="cx-alert">
          The connection is stale. Exports are marked as last-known state.
        </p>
      )}
      <div className="cx-button-row">
        <button
          onClick={() =>
            download("truss-console-evidence.json", {
              schema: "truss.console_evidence.v1",
              created_at: new Date().toISOString(),
              source,
              run_id: s.run_id,
              connection_stale: stale,
              snapshot: s,
              history,
              drill: report?.run_id === s.run_id ? report : null,
              scope:
                "Sampled operator snapshots from virtual devices, not physical measurements or a complete message trace. History covers the current console visit. When connection_stale is true the snapshot is last-known state, not current evidence.",
            })
          }
        >
          Download current evidence
        </button>
        {report && (
          <button onClick={() => download("truss-failure-drill.json", report)}>
            Download last drill report
          </button>
        )}
      </div>
      <details className="cx-event-details">
        <summary>
          Recent events <span>{Math.min(30, s.events.length)} shown of {s.events.length} received</span>
        </summary>
        <ol className="cx-events">
          {[...s.events]
            .reverse()
            .slice(0, 30)
            .map((e) => (
              <li key={e.seq}>
                <time>{new Date(e.at).toLocaleTimeString()}</time>
                <span>{e.text}</span>
                <code>{e.code}</code>
              </li>
            ))}
        </ol>
        <p className="cx-note">
          The event tail is bounded. A missing event does not establish that it
          never happened.
        </p>
      </details>
      <div className="cx-replay">
        <h3>Recorded run</h3>
        <p className="cx-note">
          Replay is read-only and separate from the live controls above. Values
          and ages belong to the recorded frame.
        </p>
        {source !== "live" ? (
          <p className="cx-note">
            Select Live runtime to open backend recordings.
          </p>
        ) : !s.capabilities.replay ? (
          <p className="cx-note">This backend does not advertise replay.</p>
        ) : (
          <>
            <div className="cx-button-row">
              <label className="cx-sr-only" htmlFor="cx-recording">
                Recorded run
              </label>
              <select
                id="cx-recording"
                value={chosen}
                onChange={(e) => setChosen(e.target.value)}
                disabled={busy || !catalog.length}
              >
                <option value="">Select a recording</option>
                {catalog.map((c) => (
                  <option
                    key={c.recorded_run_id}
                    value={c.recorded_run_id}
                    disabled={!c.replayable}
                  >
                    {c.recorded_run_id.slice(0, 8)} ·{" "}
                    {(c.bytes / 1024 / 1024).toFixed(1)} MB
                    {c.recorded_run_id === s.run_id ? " · this run" : ""}
                  </option>
                ))}
              </select>
              <button disabled={!chosen || busy} onClick={load}>
                {busy ? "Loading…" : "Open recording"}
              </button>
            </div>
            {!catalog.length && (
              <p className="cx-note">No recordings are available yet.</p>
            )}
          </>
        )}
        {error && (
          <p role="alert" className="cx-alert">
            {error}
          </p>
        )}
        {replay && (
          <div className="cx-replay-frame">
            <div className="cx-inline-heading">
              <span className="cx-status">
                REPLAY · {replay.recorded_run_id.slice(0, 8)}
              </span>
              <span>
                {(replay.position_ms / 1000).toFixed(1)} /{" "}
                {(replay.duration_ms / 1000).toFixed(1)} s
              </span>
            </div>
            {replay.gap && (
              <p className="cx-alert">
                This recording contains a gap. No missing values have been
                invented.
              </p>
            )}
            <div className="cx-button-row">
              <button
                disabled={busy}
                onClick={() =>
                  move("playback", {
                    action: replay.playing ? "pause" : "play",
                  })
                }
              >
                {replay.playing ? "Pause replay" : "Play replay"}
              </button>
              <label>
                Frame{" "}
                <input
                  aria-label="Replay frame"
                  type="number"
                  min={replay.first_seq}
                  max={replay.last_seq}
                  step="1"
                  value={seq}
                  onChange={(e) => setSeq(Number(e.target.value))}
                />
              </label>
              <button
                disabled={
                  busy ||
                  !Number.isInteger(seq) ||
                  seq < replay.first_seq ||
                  seq > replay.last_seq
                }
                onClick={() => move("seek", { from_seq: seq })}
              >
                Seek frame
              </button>
            </div>
            <p className="cx-note">
              Recorded at{" "}
              {new Date(replay.snapshot.generated_at).toLocaleString()}. Frames{" "}
              {replay.first_seq}–{replay.last_seq}. The saved prefix may end
              before the live run ends.
            </p>
            <div className="cx-replay-facts">
              <span>
                Recorded cap <b>{watts(replay.snapshot.site.cap_w)}</b>
              </span>
              <span>
                Recorded draw{" "}
                <b>
                  {watts(
                    replay.snapshot.site.observed_quality === "fresh"
                      ? replay.snapshot.site.observed_w
                      : null,
                  )}
                </b>
              </span>
              <span>
                Recorded state{" "}
                <b>{replay.snapshot.site.state.replaceAll("_", " ")}</b>
              </span>
            </div>
            <div className="cx-table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Household</th>
                    <th>Recorded draw</th>
                    <th>Reserved</th>
                    <th>Quality</th>
                  </tr>
                </thead>
                <tbody>
                  {replay.snapshot.members.map((m) => (
                    <tr key={m.id}>
                      <th>{home(m.id)}</th>
                      <td>
                        {watts(
                          m.observed_quality === "fresh" ? m.observed_w : null,
                        )}
                      </td>
                      <td>{watts(m.reserved_w)}</td>
                      <td>{m.observed_quality}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </section>
  );
}
