# 18 — The protocol needs a reservation ledger

Proposed amendment to 05–08. Owner: **M1**, with M3 implementing the member side and M2 the independent emulated plant. Status: design reasoning, not a tested system. Evidence and confidence are in [the research review](../research/2026-09-06-review.md).

## Break the present design before repairing it

All times below are elapsed seconds on an ideal reference clock unless stated otherwise. Camber is zero in the simplest examples. These are counterexamples, not simulated test results.

| Attack | Trace | Why existing rules do not save it |
|---|---|---|
| Delayed grant | Cap 1,000 W. A's 1,000 W grant is sent at 0, received at 5, expires locally at 11. Coordinator releases its reservation at 6 and grants B 1,000 W. | Valid versions, no duplicates, but A and B overlap for 5 s. Broker expiry before delivery does not subtract the delay from the payload TTL. |
| Renewal / redistribution | Old budgets A=800, B=200. New budgets A=200, B=800. B receives its increase; A's decrease is lost. | Both plans pass a 1,000 W sum check; possible draw is 1,600 W. A transport PUBACK is not proof of applied reduction. |
| Floors disappear from accounting | A's 400 W lease expires to a 200 W floor. Coordinator removes A from the lease sum and gives B the full 1,000 W. | Real entitlement becomes 1,200 W. Floors continue consuming capacity when no lease exists. |
| Cap falls | Existing commitments 1,000 W; physical/model cap becomes 600 W now. | I3 against the new cap is immediately false. No lost-message-tolerant protocol can revoke authority instantaneously. |
| Camber rises | Commitments 800 W, cap 1,000 W, fixed reserve 100 W. A goes stale; dynamic camber rises to 400 W. | The right-hand side shrinks below previously admitted commitments without any new issue. The same member may also be counted twice. |
| Last draw is too low | Stale A last reported 100 W but holds authority for 600 W and can start a permitted load. Coordinator reserves only 100 W. | A measurement is not an upper bound on future entitlement. |
| Clock drift | Member clock rate 0.99; coordinator rate 1.01. Both count 6 local seconds from the same real instant. | Coordinator releases at 5.941 real s; member expires at 6.061 s. Monotonicity did not prevent overlap. |
| Member freezes | Member is stopped at 5.9 s; separate devices keep running. | A blocked event loop does not execute expiry. A dead process does not lower a physical or emulated device by intent alone. |
| Refused shutdown | Washer has 60 s minimum run remaining; member lease expires in 6 s. | “May refuse” and “must floor immediately” conflict. A deadline forcing entry can violate the ceiling too. |
| Coordinator restarts twice | Old delayed grant from t=0 arrives at t=8. Restarts at t=1 and t=2, final wait ends t=8. | Receipt-started old grant can now run to t=14 while new grants start. Repeated waiting helps only if it bounds old authority, not just send time. |
| Partition heals during renewal | A lower version is applied; a duplicate renewal arrives after its first expiry. | A duplicate must not restart a timer. “Same watts twice” is insufficient idempotence. A process reboot can also erase the high-water mark. |
| Wrong recipient/session | New member instance resets its version counter; old lease arrives, or a payload for another member is accepted. | Numeric ordering alone does not authenticate recipient, bind a boot or distinguish issuer epochs. |
| Two issuers | A second coordinator starts while the first still runs. Each allocates 1,000 W. | UUID epochs distinguish messages but do not exclude simultaneous authorities. A shared MQTT client ID alone does not prevent queued old publishes. |
| Faulty receiver | Member applies an expired or unauthorised 2,000 W grant. | Sender-side proofs cannot constrain an arbitrary receiver. Include receiver/enforcer correctness in the trusted computing base. |

## Assumptions — explicit and load-bearing

| ID | Assumption / chosen demo value | What happens if absent |
|---|---|---|
| A1 | Single import-only scalar watt cap; all relevant emulated draw belongs to registered members, plus a declared bounded external reserve. | No claims about phase imbalance, voltage/frequency, reactive power, inverter surge, export or real feeder protection. |
| A2 | Registry is fixed during a judged run: member identities, approved baseline `f_i`, maximum `p_i`, local device baselines. Sum of baselines plus reserve fits the starting cap. | Refuse new flexible operation; report policy/configuration conflict. No live anonymous join or topology reset. |
| A3 | One issuing coordinator on the primary host, enforced by an exclusive process lock held through shutdown. Only its broker credential may publish grants. Epoch increment is durably committed before issuing. | Fail closed on lock/epoch uncertainty. No automatic failover to a second host. |
| A4 | Member and plant share one OS clock domain per house. Relative clock rates of coordinator and member lie in `[1−ρ, 1+ρ]`, illustrative `ρ=0.001`. | Value is an engineering assumption, not measured hardware certification. Outside it the timing proof does not apply. Disable suspend for demo; clock health failure stops grants. |
| A5 | A separate plant process enforces the aggregate ceiling and fallback independently of the member planner. Expiry-to-enforcement delay at most `δ=250 ms` in the demo model. | An arbitrary stalled/broken enforcer is outside the theorem. Report an enforcement fault, never continued verified safety. |
| A6 | Plant observes its own emulated output; this is not an independent electrical meter. Plant reset starts all flexible output off. | No claim that a hardware actuator was independently verified. |
| A7 | Broker/clients can drop, duplicate, delay and reorder messages but do not forge authorised grants. Basic topic ACLs and per-role demo credentials enforce read/write separation. | A malicious broker, stolen issuer key or arbitrary member software is outside the proof. |
| A8 | API/evidence service and browser survive a coordinator kill because they are separate processes. | If killed too, show disconnected state or a recording; no fabricated live expiry evidence. |
| A9 | Python 3.12+ runtime is available; member and plant on the same host have system-wide monotonic time. The user's own PC is the primary profile; any additional hosts must be checked individually. | Keep the single-host process profile if other hosts differ. Local deadlines must never be interpreted by another host. |

A4/A5 are not guarantees obtained by choosing Python. Measure lateness under CPU load, and show the chosen bound. No hard real-time electrical claim is made by this software prototype.

## The smallest defensible authority protocol

Replace unsolicited receipt-started leases with **request-anchored leases**. This costs one request topic, pending-request state, issuer deduplication, a reservation ledger and a longer conservative recovery wait. It removes the need to bound network delay for safety; delay may destroy usefulness.

1. Member opens request `q` at its own monotonic time `s`, with a unique request ID, boot ID and current offer sequence. Its deadline is fixed at **`s + T`**, `T=6,000 ms`. One pending request at a time; request every 2,000 ms, superseding unanswered older requests without revoking the current applied lease.
2. Coordinator receives it at local time `r`. It never uses an absolute member timestamp. It reserves the candidate amount **before publishing**. It issues at most one immutable grant per `(member_id, member_boot_id, request_id)`; repeats return the same grant while its reservation is live, and are ignored after retirement. Request sequence high-water marks prevent old request reissuance in that coordinator epoch.
3. Member accepts only a grant for its current pending request, current boot, matching site/member/registry, trusted issuer, acceptable epoch/version, and `budget ∈ [f_i,p_i]`. Grant TTL must equal requested TTL and the fixed run limit. If local time is already at the fixed deadline, reject. Receipt does not create a new six seconds.
4. Member atomically updates the accepted lease and high-water mark. It forwards an aggregate plant ceiling carrying the same **local clock-domain deadline**, grant identity and baseline version. Plant rejects expired or mismatched-domain updates. Reductions and device commands cannot bypass its aggregate gate.
5. Expiry applies locally. The plant allows no flexible output after its deadline plus the explicitly bounded enforcement delay. The local baseline remains. New requests and duplicate acks never extend an old grant.
6. Missing grant/ack merely wastes reservation. In the MVP, **acks never release watts early**. Keep older reservations until their conservative expiry even after a reported reduction. This sacrifices up to one hold interval of utilisation and makes the race proof much shorter.

Let every possible old grant for member i remain in set `L_i`. Define:

`R_i = max(f_i, max(budget(g) for g in L_i))`, with an empty maximum omitted.

The same member cannot consume two alternative aggregate budgets simultaneously, so use its **maximum possible active ceiling**, not the sum of its renewals. Reserve `f_i` exactly once forever during the run. A candidate grant changes `R_i` to `max(R_i, candidate_w)`. Atomically admit only if:

`Σ R_i_after + measurement_reserve_w + external_bound_w ≤ cap_w`.

The allocator may propose anything. The gate ignores its claim of feasibility and validates membership, amount, cap revision and the complete reservation exposure. Issuing threads must not race through separate check-then-publish operations. Use one serial coordinator event loop with no await between checking and reserving. A publish failure keeps the reservation.

### Timing bound and restart

For request-anchored term T, real usable lifetime ends no later than `s_real + T/(1−ρ) + δ`. Since receipt is after request creation, a coordinator hold of

`H = (1+ρ) × [T/(1−ρ) + δ]`

in its own monotonic milliseconds is conservative from receipt. With the illustrative values above H≈6,262.3 ms; use **6,400 ms**, rounded upward, not “one six-second TTL”. A queued old request received later receives a later reservation even if its resulting grant will be rejected; this costs liveness only.

On every coordinator process start: acquire exclusive lock; increment and commit epoch; enter RECOVERING; reserve each member at its registered maximum `p_i` for H; publish no grants; reject queued request work during recovery; then clear unknown old exposure and use baseline reservations. The provisional maximum sum may exceed the current cap, so show `recovering / unverified`, not an admitted safe allocation. No new promise is made during this uncertainty.

Every second restart begins a **new full H wait**. Do not resume a countdown from a previous process's in-memory timer. Any grant issued before the latest crash originated from a request before that crash, so all such grants end within H of the latest restart. Epochs prevent regression; the lock and ACLs establish single-issuer authority. Neither substitutes for the other.

A member restart changes boot ID, discards pending requests and begins at baseline. Existing plant ceiling may live until its deadline; the coordinator retains reservations by stable **member ID**, never by boot ID. Before the restarted member issues a new ceiling, it must obtain the plant's accepted member boot binding. Plant accepts boot rebinding only at baseline after its old ceiling expires. This prevents version reset from reviving old authority. A plant restart similarly starts at baseline, has a fresh plant boot, and requires fresh binding.

### Proof outline — conditional, not a verification badge

Base case: registry baselines plus reserves fit the initial cap. Inductive issue step: the serial admission gate adds a possible entitlement only after its full exposure fits. Delivery step: a correct member/plant can use only an admitted grant, bound to its request deadline. Duplicate, reorder and loss steps introduce no new authority. Expiry/release step: the hold interval ends no earlier than the latest possible use plus actuation delay. Therefore actual compliant emulated member draw is bounded by the reservation exposure. Recovery adds no authority until all old grants must have ended. This argument requires A1–A9 and a fixed cap during an admitted epoch.

### Cap changes and impossible requests

A sudden reduction below current exposure is **CAP_TRANSITION**, not an instantaneous invariant success. Store `requested_cap_w` and current `cap_revision` immediately. Stop all grants that would keep exposure above the new cap, including renewals that would prolong it. Send lower proposals where possible but do not assume delivery. Await reservation expiry; then admit a plan under the new cap. A same-budget renewal is allowed only when the complete resulting exposure already fits that cap.

Under the model assumptions, old flexible authority clears within H real-equivalent time from the last pre-drop request/issue bound, plus processing allowances specified by the test harness. Use a **7 s demo acceptance window**, not the present 5 s target under arbitrary loss. Measure the actual bound from the event at the gate, not from browser click time. Successful reduction messages usually improve response; they are not the proof.

If `Σ f_i + reserves > cap`, report **INFEASIBLE**, deficit watts and *all affected member IDs*. Do not pretend a computed list of “unserved” households has actually been disconnected. Baselines remain; overload may persist indefinitely. A protocol cannot preserve incompatible floors and cap. The red overload indication remains honest. No automatic medical-load decision, floor shedding or mains intervention is implemented.

### Camber: change the arithmetic

Replace “sum last-known stale draw” with fixed measurement reserve plus declared bounded external draw. Show uncertain **member exposure** as a hatched portion of existing reservations, not a second subtraction. Stale telemetry cannot increase or decrease authority. Fresh telemetry alone cannot release reservations. After safe expiry the reserved member amount becomes its baseline, never zero.

Retain the visible camber vocabulary but label its breakdown: fixed reserve; external bound; unverified portion of member commitments (already counted). This changes 08 and the inspector arithmetic. It costs clearer labels and a reservation view; it removes both undercounting and double counting.

## Local enforcement and the refusal conflict

Chosen scope: five member processes, **five independent plant processes**, twenty emulated devices as state machines inside those plants. This replaces twenty separate device processes and removes ESP32 from the initial build. Devices still use versioned MQTT telemetry/command/ack contracts, handled by the plant that owns them.

Each plant has a fixed baseline per virtual device whose sum is ≤ its registered household baseline. The plant gates aggregate output before every simulated actuation step. It ignores any command that would exceed its active ceiling; absence of a valid ceiling restricts total draw to baseline. It publishes a ceiling acknowledgement and household meter frame independent of member health. Commands may influence distribution within the permitted ceiling, never increase that ceiling.

For protected or unclassified devices, the mandatory amendment in
[22](22-sglang-and-protected-loads.md) applies: full admitted maximum is covered
by a reviewed baseline, or the configuration cannot start. They are never
automatically deferred. “Safety expiry takes precedence” below applies to
eligible flexible output only; it does not switch off protected baseline loads.

The MVP uses interruptible flexible loads. Minimum-run refusal is tested as a **rejected start or a rejected ordinary command within the existing ceiling**; safety expiry takes precedence. A real non-interruptible job can only be supported by reserving enough non-expiring baseline or a commitment covering its whole run before start. Do not promise that enhancement in this event. Deadlines are local demand hints and missed-job reports; they never force a start above budget.

## Revised invariants and obligations

| ID | Exact scope | Verification |
|---|---|---|
| I1 | In an admitted stable-cap state, compliant plant draw plus bounded external draw ≤ cap, allowing stated measurement error. During cap transition, report draw and settle within the declared bound if feasible. | Stateful model, real-process fault tests; distinguish observed samples from continuous proof. |
| I2 | Feasible allocations and every expiry preserve the **registered** baseline; ordinary offers cannot alter it. | Allocator properties, schema/admission units, plant units. |
| I3 | No issue transition makes `Σ R_i + reserves > cap` and no reservation releases before possible use ends. Stable-cap admitted runs therefore preserve the bound under arbitrary message loss. | Stateful model with independent oracle; request/expiry/restart race regressions. |
| I4 | Compliance is `unknown` without fresh complete observations; INFEASIBLE and cap-transition states never display verified compliance by absence of data. | Reducer/API/UI tests and fault scenarios. |
| I5 | Reprocessing an authority message cannot change amount, expiry, accepted version, physical transition count or debt a second time. Duplicate replies may occur. | Unit plus stateful duplicates before/after expiry. |
| I6 | Accepted `(epoch, version)` never decreases within an admitted member boot; previous-boot/foreign-request grants are rejected. | Unit plus restart/reorder state machine. |
| I7 — Authority | Every applied ceiling belongs to the registered site/member, issuer, member boot, plant binding and registry revision; no two issuers run concurrently. | Negative contract tests, lock contention, ACL smoke tests. |
| I8 — Local fallback | With no accepted renewal, the independent plant reaches baseline by request deadline plus δ despite member/coordinator loss. | Plant-clock properties; kill and stop member; coordinator kill; broker loss. |
| I9 — Conservation | Baselines, old grants and external bounds are counted exactly once; telemetry, rejects and missing acks cannot free watts. | Reservation unit/stateful tests. |
| I10 — Isolation | Replay, mock and lab never publish live authority or alter live registry; coordinator receives no device topic. | ACL tests, integration subscription audit, API context tests. |
| I11 — Evidence | State publication is ordered within a run; plan basis references exact input snapshot/config; late evidence never rewrites history. | Reducer/replay unit tests. |

Fairness is a separate algorithm property. Liveness is conditional on eventual communication, stable feasible demand/cap and healthy enforcers. Arbitrary permanent message loss cannot provide renewal progress.

## Fairness rule: an implementable, honest choice

Baseline policy: `0 ≤ f_i ≤ firm_i ≤ useful_i ≤ p_i`. All are **total watts**, not additive tiers. `firm` is a preference/reporting quantity in this allocator, not a second guaranteed floor. Protect selects a local priority within the admitted baseline/ceiling; it cannot manufacture a higher floor.

Default at hour 6: equal-surplus water-filling, all weights 1. Debt data remains observable. Optional by hour 18: bounded weight `w_i = 1 + clamp(D_i / S, 0, 1)`, `S=10 Wh` for the accelerated demonstration, marked as a scenario policy parameter. This illustrative scale is not empirically tuned household policy.

Replace member-authoritative accumulated unmet-demand debt with coordinator-authoritative **service deficit**. At each completed interval of duration Δ hours, calculate equal-surplus reference allocation `e_i` from that interval's validated snapshot. Let `a_i = R_i − f_i` be the coordinator's conservative possible flexible authority during the interval; split intervals whenever exposure changes. Old grants remain counted until their conservative release. This can overstate usable authorisation when messages are lost; it intentionally does not award extra debt for unverifiable delivery failures. In the ledger, use surplus rates, not total watts:

`D_i(next) = clamp(D_i + ((e_i−f_i) − a_i) × Δ, 0, Dmax)`; choose `Dmax=2S` for the scenario.

This is credit for withheld **authorisation**, not actual curtailed energy. Do not call it measured sacrifice. The member's reported unmet demand is a separate diagnostic `reported_curtailment_wh`. No credit accrues during stale/offline offers, cap-infeasible/recovering intervals or registry conflict; freeze D then. Compute each interval once from ordered events, persist D across coordinator restarts, and restore it before planning. If debt state is corrupt, disable weighting for all members and report that reset; do not reward the first reconnecting identity.

Reservations can delay a newly fair plan. Display proposed share, issued authority and retained exposure separately. A pure allocator theorem only applies to the proposal. This credit does not guarantee eventual job completion or eliminate dishonest useful-demand declarations. Useful demand is bounded by a registered envelope; repeated unexplained unused grants trigger review, not automatic baseline punishment. In the MVP no dynamic enforcement sanction is added.

**PSEUDOCODE — specification only, not implementation**

```text
Take a validated, immutable snapshot and fixed positive weights.
If registered baselines plus reserves exceed capacity, return INFEASIBLE.
Let each member's demand be useful minus baseline.
Sort its saturation level (demand divided by weight), with stable ID ties.
Raise the common normalised surplus level to the next saturation level
  if the remaining pool can pay for that rise across all active weights.
Remove saturated weights; otherwise spend the remaining pool and stop.
Materialise each baseline plus min(demand, weight times final level).
Round DOWN to integer watts and retain the fractional remainder as headroom.
Return budgets and the arithmetic basis; never publish from the allocator.
```

Rounding down loses less than one watt per active member and preserves symmetry of identical offers. The implementation claims exact weighted leximin for the continuous target, with <1 W per-member downward quantisation error. Do not assert exact integer leximin or exact work conservation. Compare normalized values with the corresponding `1/w_i` quantisation tolerance. This replaces an unstable EPSILON loop and arbitrary ID-based leftover-watt preference.

Alternative with an equally short explanation: total-watt max-min filling starts by raising the lowest *total* entitlement, respecting lower bounds, instead of equalising surplus. It replaces the current fairness objective and advantages low-baseline members until totals equalise. We recommend surplus fairness because the team explicitly treats floors as prior entitlements; choose publicly, not by borrowing the wrong theorem.
