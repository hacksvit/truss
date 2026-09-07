import { useEffect, useRef, useState } from "react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend,
} from "recharts";
import type {
  ConsoleSnapshot,
  ConsoleMember,
  HistoryPoint,
  Fairness,
  Rule,
  Runtime,
} from "./types";
import {
  baselineReview,
  download,
  explain,
  home,
  sumKnown,
  watts,
} from "./model";
import { compare } from "./comparison";
export function Heading({
  number,
  title,
  detail,
}: {
  number: string;
  title: string;
  detail?: string;
}) {
  return (
    <div className="cx-heading">
      <div>
        <div className="section-label">{number}</div>
        <h2>{title}</h2>
      </div>
      {detail && <p>{detail}</p>}
    </div>
  );
}
export function Safety({
  s,
  history,
  stale,
}: {
  s: ConsoleSnapshot;
  history: HistoryPoint[];
  stale: boolean;
}) {
  const facts = [
    {
      name: "Proposed",
      value: sumKnown(s.members.map((m) => m.target_w)),
      detail: "What the planner suggests.",
    },
    {
      name: "Issued",
      value: sumKnown(s.members.map((m) => m.issued_w)),
      detail: "Latest visible permissions.",
    },
    {
      name: "Reserved",
      value: s.site.reserved_member_w,
      detail: "Power that may still be in use.",
    },
    {
      name: "Observed",
      value:
        !stale && s.site.observed_quality === "fresh"
          ? s.site.observed_w
          : null,
      detail: stale
        ? "Connection lost. Last values are unverified."
        : s.site.observed_quality === "fresh"
          ? "Fresh readings from virtual enforcers."
          : "Awaiting fresh enforcer readings.",
    },
  ];
  return (
    <section id="overview" className="cx-safety panel">
      <div className="cx-limit">
        <div>
          <div className="section-label">01 / CAPACITY & AUTHORITY</div>
          <h2>
            {watts(s.site.cap_w)} <span>site limit</span>
          </h2>
        </div>
        <span
          className={`cx-status ${s.site.state === "infeasible" ? "cx-warn" : ""}`}
        >
          {stale ? "Unverified connection" : s.site.state.replaceAll("_", " ")}
        </span>
      </div>
      <div className="cx-facts">
        {facts.map((f) => (
          <div key={f.name}>
            <span>{f.name}</span>
            <strong>{watts(f.value)}</strong>
            <small>{f.detail}</small>
          </div>
        ))}
      </div>
      <div className="cx-reserve-line">
        <span>
          Approved minimums <b>{watts(s.site.baseline_sum_w)}</b>
        </span>
        <span>
          Site reserve{" "}
          <b>{watts(s.site.measurement_reserve_w + s.site.external_bound_w)}</b>
        </span>
        <span>
          Exposure including reserve <b>{watts(s.site.exposure_w)}</b>
        </span>
        <span>
          Grant headroom <b>{watts(s.site.available_for_new_grants_w)}</b>
        </span>
      </div>
      {s.site.deficit_w > 0 && (
        <p className="cx-alert" role="alert">
          Minimums do not fit. The shortfall is {watts(s.site.deficit_w)}. No
          protected load is selected for curtailment.
        </p>
      )}
      {s.site.state === "cap_transition" && (
        <p className="cx-alert">
          The new limit is committed. Earlier permissions remain reserved until
          they expire.
        </p>
      )}
      {s.site.unverified_member_reservation_w > 0 && (
        <p className="cx-alert">
          {watts(s.site.unverified_member_reservation_w)} remains reserved for
          homes with unverified authority. It is already included above.
        </p>
      )}
      <div
        className="cx-chart"
        aria-label="Recent capacity, reserved exposure and observed draw"
      >
        <ResponsiveContainer width="100%" height={185} minWidth={0}>
          <LineChart data={history}>
            <CartesianGrid stroke="var(--border-default)" vertical={false} />
            <XAxis
              dataKey="label"
              minTickGap={100}
              tick={{ fill: "var(--text-muted)", fontSize: 10 }}
            />
            <YAxis
              width={55}
              tick={{ fill: "var(--text-muted)", fontSize: 10 }}
            />
            <Tooltip
              contentStyle={{
                background: "var(--bg-bar)",
                borderColor: "var(--border-default)",
                color: "var(--text-primary)",
              }}
            />
            <Legend wrapperStyle={{ fontSize: 11 }} />
            <Line
              name="Site limit (W)"
              dataKey="cap"
              stroke="var(--app-amber)"
              dot={false}
              isAnimationActive={false}
              strokeDasharray="5 4"
            />
            <Line
              name="Reserved exposure (W)"
              dataKey="exposure"
              stroke="var(--text-muted)"
              dot={false}
              isAnimationActive={false}
            />
            <Line
              name="Observed draw (W)"
              dataKey="observed"
              stroke="var(--accent)"
              strokeWidth={2}
              dot={false}
              connectNulls={false}
              isAnimationActive={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
      <p className="cx-note">
        Recent browser samples. Gaps mean missing observations. Reservations can
        exceed a newly reduced limit during a transition.
      </p>
    </section>
  );
}
function Countdown({ m, stale }: { m: ConsoleMember; stale: boolean }) {
  const [elapsed, setElapsed] = useState(0);
  useEffect(() => {
    const t = performance.now();
    setElapsed(0);
    const timer = setInterval(() => setElapsed(performance.now() - t), 100);
    return () => clearInterval(timer);
  }, [m.lease]);
  const known =
    !stale && m.lease.quality === "fresh" && m.lease.remaining_ms !== null;
  const left = known ? Math.max(0, m.lease.remaining_ms! - elapsed) : null;
  return (
    <div className="cx-lease">
      <div>
        <span>Lease estimate</span>
        <b>{left === null ? "Unknown" : `~${(left / 1000).toFixed(1)} s`}</b>
      </div>
      <div className="cx-track">
        <i
          style={{
            width: left === null ? "0%" : `${Math.min(100, left / 60)}%`,
          }}
        />
      </div>
      <small>
        {left === 0
          ? "Await enforcer confirmation."
          : known
            ? "Based on the latest enforcer report."
            : "No fresh countdown is available."}
      </small>
    </div>
  );
}
export function Homes({
  s,
  stale,
  onSelect,
}: {
  s: ConsoleSnapshot;
  stale: boolean;
  onSelect: (id: string) => void;
}) {
  return (
    <section>
      <Heading
        number="02 / HOUSEHOLDS"
        title="Every allocation has a reason."
      />
      <div className="cx-homes">
        {s.members.map((m) => (
          <button
            className="cx-home panel"
            key={m.id}
            onClick={() => onSelect(m.id)}
          >
            <div className="cx-home-top">
              <h3>{home(m.id)}</h3>
              <span className="cx-status">
                {stale ? "unverified" : m.status.replaceAll("_", " ")}
              </span>
            </div>
            <strong className="cx-home-watts">
              {watts(
                !stale && m.observed_quality === "fresh" ? m.observed_w : null,
              )}
            </strong>
            <small>
              {s.source === "mock" ? "Synthetic draw" : "Observed virtual draw"}
            </small>
            <Countdown m={m} stale={stale} />
            <dl>
              {[
                ["Minimum", m.floor_w],
                ["Proposed", m.target_w],
                ["Issued", m.issued_w],
                ["Reserved", m.reserved_w],
              ].map(([k, v]) => (
                <div key={String(k)}>
                  <dt>{k}</dt>
                  <dd>{watts(v as number | null)}</dd>
                </div>
              ))}
            </dl>
            <p>{explain(m, s, stale)}</p>
            <span className="cx-inspect">Why this allocation? ↗</span>
          </button>
        ))}
      </div>
    </section>
  );
}
export function Inspector({
  m,
  s,
  stale,
  onClose,
}: {
  m: ConsoleMember;
  s: ConsoleSnapshot;
  stale: boolean;
  onClose: () => void;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    ref.current?.showModal();
    return () => ref.current?.close();
  }, []);
  return (
    <dialog className="cx-inspector" ref={ref} onCancel={onClose}>
      <button
        className="cx-close"
        onClick={onClose}
        aria-label="Close household inspector"
      >
        ×
      </button>
      <div className="section-label">HOUSEHOLD DECISION</div>
      <h2>{home(m.id)}</h2>
      <p className="cx-lead">{explain(m, s, stale)}</p>
      <div className="cx-inspector-facts">
        <span>
          Approved minimum <b>{watts(m.floor_w)}</b>
        </span>
        <span>
          Useful demand <b>{watts(m.useful_w)}</b>
        </span>
        <span>
          Reserved authority <b>{watts(m.reserved_w)}</b>
        </span>
        <span>
          Plan weight <b>{m.weight.toFixed(3)}×</b>
        </span>
        <span>
          Service deficit <b>{m.debt_wh.toFixed(3)} Wh</b>
        </span>
        <span>
          Unusable within share <b>{watts(m.unusable_w)}</b>
        </span>
      </div>
      {m.basis ? (
        <p className="cx-note">
          The accepted permission includes its allocation basis. The rule for
          this permission is{" "}
          {m.basis.rule === "debt_weighted_surplus"
            ? "debt weighted surplus"
            : "equal surplus"}
          . Its plan proposed {watts(m.basis.proposed_budget_w as number)} and
          issued {watts(m.basis.issued_budget_w as number)}.
        </p>
      ) : (
        <p className="cx-alert">
          No matching accepted-permission basis is available for this reading. A
          specific grant explanation is unverified.
        </p>
      )}
      <h3>Inside this fictional home</h3>
      <p className="cx-note">
        Only the privileged demo observer sees these device details. The
        coordinator receives aggregate offers.
      </p>
      <div className="cx-devices">
        {m.devices.map((d) => (
          <div key={d.id}>
            <div>
              <strong>{d.label}</strong>
              <small>
                {d.control_policy === "flexible"
                  ? "Eligible to wait"
                  : "Reserved for the whole run"}
              </small>
            </div>
            <div>
              <b>{watts(!stale && d.quality === "fresh" ? d.w : null)}</b>
              <small>{d.state.replaceAll("_", " ")}</small>
            </div>
            <p>
              {d.control_policy !== "flexible"
                ? "This load belongs to the approved minimum and is excluded from flexible curtailment."
                : d.state === "deferred"
                  ? `The available household budget cannot serve this step after higher-priority assignments. Requested ${watts(d.requested_w)}.`
                  : `The local scheduler assigned this load within the household permission. Requested ${watts(d.requested_w)}.`}
            </p>
          </div>
        ))}
      </div>
      <p className="cx-note">
        The enforcer still trusts member software to forward genuine authority.
        No physical or medical equipment is controlled.
      </p>
    </dialog>
  );
}
export function FairnessPanel({
  s,
  fairness,
  disabled,
  onRule,
}: {
  s: ConsoleSnapshot;
  fairness: Fairness | null;
  disabled: boolean;
  onRule: (r: Rule) => void;
}) {
  const [preset, setPreset] = useState<"captured" | "earlier_wait">(
    "earlier_wait",
  );
  const [result, setResult] = useState<ReturnType<typeof compare> | null>(null);
  useEffect(() => setResult(null), [s.run_id, s.source]);
  return (
    <section id="fairness" className="panel">
      <Heading
        number="04 / FAIRNESS"
        title="Make the trade-off visible."
        detail="Earlier service deficit can increase a home’s weight, up to 2×."
      />
      <div className="cx-rule-controls">
        <div>
          <label htmlFor="cx-rule">Desired live rule</label>
          <select
            id="cx-rule"
            disabled={
              disabled || s.source !== "live" || !s.capabilities.debt_weighting
            }
            value={fairness?.desired_rule ?? s.site.rule}
            onChange={(e) => onRule(e.target.value as Rule)}
          >
            <option value="equal_surplus">Equal surplus</option>
            <option
              value="debt_weighted_surplus"
              disabled={!fairness?.available}
            >
              Debt weighted surplus
            </option>
          </select>
        </div>
        <p>
          Effective plan:{" "}
          <b>
            {s.site.rule === "debt_weighted_surplus"
              ? "Debt weighted surplus"
              : "Equal surplus"}
          </b>
          <br />
          <small>
            Existing permissions remain reserved when the rule changes.
          </small>
        </p>
      </div>
      {fairness?.error && (
        <p className="cx-alert">Weighting unavailable: {fairness.error}</p>
      )}
      <div className="cx-table-wrap">
        <table>
          <caption className="cx-sr-only">
            Current service deficit and plan weights
          </caption>
          <thead>
            <tr>
              <th>Household</th>
              <th>Service deficit</th>
              <th>Plan weight</th>
              <th>Unusable share</th>
            </tr>
          </thead>
          <tbody>
            {s.members.map((m) => (
              <tr key={m.id}>
                <th>{home(m.id)}</th>
                <td>{m.debt_wh.toFixed(3)} Wh</td>
                <td>{m.weight.toFixed(3)}×</td>
                <td>{watts(m.unusable_w)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="cx-note">
        Credits describe withheld authorization against an equal-surplus
        reference. They are not measured sacrifice, savings or guaranteed
        repayment.
        {fairness && fairness.frozen_gap_ms > 0
          ? ` Accounting froze over ${(fairness.frozen_gap_ms / 1000).toFixed(1)} seconds of long scheduling gaps.`
          : ""}
      </p>
      <div className="cx-comparison">
        <div className="cx-inline-heading">
          <div>
            <h3>Same demand. Two policies.</h3>
            <p>Read-only simulation. It does not change the live site.</p>
          </div>
          <div className="cx-button-row">
            <label className="cx-sr-only" htmlFor="cx-trace">
              Comparison trace
            </label>
            <select
              id="cx-trace"
              value={preset}
              onChange={(e) => {
                setPreset(e.target.value as typeof preset);
                setResult(null);
              }}
            >
              <option value="earlier_wait">Earlier wait for Home A</option>
              <option value="captured">Current offers + credits</option>
            </select>
            <button
              onClick={() => setResult(compare(s, preset))}
              disabled={disabled}
            >
              Compare policies
            </button>
          </div>
        </div>
        {result ? (
          <>
            <p className="cx-note">
              36 identical 10-second steps for each rule. Site limit{" "}
              {watts(result.cap)}.{" "}
              {result.preset === "earlier_wait"
                ? "Home A starts with an illustrative 10 Wh of service deficit; other homes start at zero."
                : "Starting offers and credits are captured from the displayed snapshot."}{" "}
              Home B’s demand drops during the middle third.
            </p>
            {result.results.every((r) => r.feasible) ? (
              <>
                <div className="cx-table-wrap">
                  <table>
                    <caption>Six-minute policy illustration</caption>
                    <thead>
                      <tr>
                        <th>Household</th>
                        <th>Served, equal</th>
                        <th>Served, weighted</th>
                        <th>End deficit, equal</th>
                        <th>End deficit, weighted</th>
                      </tr>
                    </thead>
                    <tbody>
                      {s.members.map((m) => (
                        <tr key={m.id}>
                          <th>{home(m.id)}</th>
                          <td>
                            {result.results[0].served[m.id]?.toFixed(2)} Wh
                          </td>
                          <td>
                            {result.results[1].served[m.id]?.toFixed(2)} Wh
                          </td>
                          <td>{result.results[0].debt[m.id]?.toFixed(2)} Wh</td>
                          <td>{result.results[1].debt[m.id]?.toFixed(2)} Wh</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <div className="cx-comparison-totals">
                  {result.results.map((r) => (
                    <div key={r.rule}>
                      <b>
                        {r.rule === "equal_surplus"
                          ? "Equal surplus"
                          : "Debt weighted surplus"}
                      </b>
                      <span>
                        Unmet demand{" "}
                        {Object.values(r.unmet)
                          .reduce((a, b) => a + b, 0)
                          .toFixed(2)}{" "}
                        Wh
                      </span>
                      <span>
                        Unused available capacity {r.unused.toFixed(2)} Wh
                      </span>
                    </div>
                  ))}
                </div>
              </>
            ) : (
              <p className="cx-alert">
                The captured minimums and reserve do not fit. This comparison is
                infeasible.
              </p>
            )}
            <p className="cx-note">
              This idealised model applies allocations immediately. It excludes
              leases, device steps and communication delays. Live debt uses
              conservative outstanding authority. Neither policy is declared the
              universal winner.
            </p>
            <button
              onClick={() => download("truss-policy-comparison.json", result)}
            >
              Download comparison inputs + results
            </button>
          </>
        ) : (
          <div className="cx-comparison-empty">
            Run a comparison to see who receives more, who waits and how the
            service deficit changes.
          </div>
        )}
      </div>
    </section>
  );
}
export function Baselines({ s }: { s: ConsoleSnapshot }) {
  const [member, setMember] = useState(s.members[0]?.id ?? "");
  const selected = s.members.find((m) => m.id === member) ?? s.members[0];
  const [value, setValue] = useState(selected?.floor_w ?? 0);
  const [reason, setReason] = useState("");
  const review = baselineReview(s, selected?.id ?? "", value);
  return (
    <section id="baselines" className="panel">
      <Heading
        number="05 / BASELINE ADMISSION"
        title="Minimums require a decision."
        detail="Offers cannot raise a registered baseline. Approved values stay fixed for the run."
      />
      <details>
        <summary>Review a proposed increase</summary>
        <p className="cx-note">
          This drafts a proposal for an operator to review. It cannot update
          protected loads or apply a new registry. Decreases and medical
          classifications are outside this tool.
        </p>
        <div className="cx-baseline-form">
          <label>
            Household
            <select
              value={selected?.id}
              onChange={(e) => {
                setMember(e.target.value);
                setValue(
                  s.members.find((m) => m.id === e.target.value)!.floor_w,
                );
              }}
            >
              {s.members.map((m) => (
                <option value={m.id} key={m.id}>
                  {home(m.id)}
                </option>
              ))}
            </select>
          </label>
          <label>
            Proposed minimum (W)
            <input
              type="number"
              min={selected?.floor_w}
              max={selected?.max_w}
              step="1"
              value={Number.isNaN(value) ? "" : value}
              onChange={(e) =>
                setValue(e.target.value === "" ? NaN : Number(e.target.value))
              }
            />
          </label>
          <label className="cx-reason">
            Reason for operator review
            <input
              value={reason}
              maxLength={300}
              onChange={(e) => setReason(e.target.value)}
              placeholder="Explain the additional fixed requirement"
            />
          </label>
        </div>
        <p className={review.fits ? "cx-note" : "cx-alert"}>
          {!review.valid
            ? `Enter a whole-watt minimum between ${selected?.floor_w} and ${selected?.max_w}.`
            : review.fits
              ? `Minimums plus reserve would need ${watts(review.required)}. This fits the configured limit; verification and approval are still required.`
              : `The proposal exceeds the site limit by ${watts(review.shortfall)}. More capacity or a different agreement is needed.`}
        </p>
        <button
          disabled={!review.valid || !reason.trim()}
          onClick={() =>
            download("truss-baseline-review.json", {
              schema: "truss.baseline_review.v1",
              run_id: s.run_id,
              source: s.source,
              member_id: selected.id,
              current_floor_w: selected.floor_w,
              requested_floor_w: value,
              reason,
              review,
              approval_status: "unreviewed",
              applied: false,
              created_at: new Date().toISOString(),
              next_step:
                "Verify need and registered maxima, obtain operator approval, then start a new reviewed run.",
            })
          }
        >
          Download unreviewed proposal
        </button>
      </details>
    </section>
  );
}
export function Processes({ runtime }: { runtime: Runtime | null }) {
  return (
    <details className="cx-processes">
      <summary>Process status and operating assumptions</summary>
      {runtime ? (
        <>
          <div className="cx-process-grid">
            {runtime.processes.map((p) => (
              <div key={p.name}>
                <span className={`cx-dot ${p.running ? "" : "cx-dot-off"}`} />
                <b>{p.name}</b>
                <span>
                  {p.running
                    ? "running"
                    : `stopped (${p.exit_code ?? "unknown"})`}
                </span>
              </div>
            ))}
          </div>
          {runtime.evidence_error && (
            <p className="cx-alert">
              Evidence unavailable: {runtime.evidence_error}
            </p>
          )}
          {runtime.recording_full && (
            <p className="cx-note">
              The backend snapshot recording reached its limit. Live observation
              continues; the saved replay covers an earlier prefix only.
            </p>
          )}
        </>
      ) : (
        <p>Current process status is unavailable.</p>
      )}
      <p className="cx-note">
        Local PC and real MQTT processes. Virtual appliances only. Lease
        lifetime: 6 seconds from request start. Recovery hold: 6.4 seconds on
        each coordinator boot. Healthy local enforcers and bounded clocks are
        assumptions; whole-PC suspension and a frozen enforcer are outside the
        timing guarantee. The plant still trusts the member’s forwarded
        authority.
      </p>
    </details>
  );
}
