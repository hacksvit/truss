# 17 — Change list, in build order

This is a review amendment, not a wholesale rewrite. Existing 00–16 remain intact. The proposed implementation baseline is specified in 18–21. User's chosen Python / React + Vite + TypeScript / MQTT 5 / Mosquitto / Pydantic / Hypothesis stack takes precedence over older Streamlit decisions.

Confidence: protocol and arithmetic counterexamples are high-confidence design reasoning; source-backed corrections refer to [the research review](../research/2026-09-06-review.md); estimates are explicitly estimates.

## Wrong — change before implementation

| Priority | Location / claim | Specific change | Reason / cost |
|---|---|---|---|
| P0 | 00, 05, 06, 08: receipt-started TTL and one-TTL restart prove safety | Adopt request-anchored authority, conservative reservation and 6.4 s illustrative recovery bound from 18 | Delayed grants break the old proof. Adds a request, session binding and ledger; not four lines. |
| P0 | 08 I3: sum of outstanding leases ≤ current cap−dynamic camber at every instant | Count effective possible ceilings per member plus persistent baselines; state stable-cap and cap-transition cases separately | Renewals overlap, floors do not expire, caps/reserves can shrink. Changes visible accounting. |
| P0 | 06 minimum runs may refuse shutdown; deadlines force entry | Interruptible-load MVP; never force start above ceiling. Non-interruptible work requires pre-reserved commitment | Old device autonomy contradicts expiry safety. Costs realism; preserve rejection demonstration within safe ceiling. |
| P0 | 05/08 member planner itself enforces expiry | Add independent plant gate; five plants own 20 emulated devices | Dead/frozen planner cannot execute expiry. Costs a small process and aggregate ceiling contract per house. |
| P0 | 08 camber = last-known stale draw | Reserve authority upper bounds; hatch uncertainty inside reservations; fixed/external reserve separate | Last draw may be lower than permitted next draw. Do not double count. |
| P0 | 00/03/07/13 provably max-min fair budgets | Say weighted leximin **normalised surplus**, continuous target, fixed weights/snapshot; state rounding | Existing total-watt theorem is false. No coding cost beyond correct algorithm. |
| P0 | 07 algorithm O(n log n); microseconds at 5,000 | Sort saturation breakpoints and fill once; measure latency before quoting | Existing repeated scanning can be O(n²). |
| P0 | 02/07/13 nobody loses twice; debt repays sacrifice | Drop guarantee; use optional service-deficit weighting, explicitly not measured sacrifice | Scarcity and saturated weights can persist forever. Defines ledger semantics. |
| P0 | 03 nearest art is like-device PEM | Add EEBus, operating envelopes, FlexOffers, household privacy optimisation | Direct counter-evidence; retire “layer nobody owns.” |
| P0 | 03/05/06 nothing private leaves home | State coordinator data minimisation, demo observer exception and aggregate leakage | Device inspector and logger contradict strict privacy. Add ACLs, remove device count from coordinator offer. |
| P0 | 04 cap recovery in 5 s with 6 s TTL, arbitrary loss | Model acceptance ≤7 s under declared bounds; plan computation still targeted ≤1 s | Lost reductions must wait for old authority. No instantaneous overload prevention claim. |
| P1 | 05 Pydantic fallback = hand validation | Remove fallback; malformed grants fail closed | Safety contract cannot be weaker in the backup path. |
| P1 | 05/08 Will means immediate/millisecond death detection | Say connection-loss hint; heartbeat freshness and lease expiry are separate | MQTT Keep Alive/Will timing is not instant. |
| P1 | 06 “six schemas”; discovery unspecified | Freeze the complete message matrix in 20, including status, requests, lease ack, capacity, plan, plant ceiling/meter and discovery | Old timeline undercounts the contract. Initial subset by hour 1; full contract by hour 2. |
| P1 | 06 offer deadline example | Remove wall-time scheduling; use monotonic relative remaining duration for local deadline hints | Sample deadline is already in the past relative to sample timestamp. It also contradicts “no timestamp decisions.” |
| P1 | 06 exactly one ack | Allow repeated cached result replies, exactly-once effects | Lost ack must be recoverable without reapplying. |
| P1 | 06 retained plan makes joining console immediately correct | Retained plan is historical intent; query fresh API snapshot with age/quality | Retained does not mean current or applied. |
| P1 | 07 CP-SAT device-level model at coordinator | Cut implementation; if revisited, place local device schedule inside member or define an aggregate horizon contract | Current privacy boundary supplies neither device constraints nor enough deadline buckets. A single energy/deadline pair cannot encode multiple jobs. |
| P1 | 05/10 Streamlit; 11 forbids React; 16 mandates React | Canonical front end is React/Vite/TS now; remove implicit mid-event stack switch | Existing plans directly conflict. One React owner, thin routes. |
| P1 | 04/10/11 same seed → byte-identical live trace | Fixed recorded input order → deterministic reducer and allocator output; raw live traces need not match | OS schedules, MQTT ordering, boot IDs and timestamps differ. |
| P1 | 16 mock is the demo if backend late | Persistent MOCK / REPLAY labels; do not narrate mocked failures as live distributed proof | A backup presentation is useful but cannot substitute for the implementation claim. |
| P1 | 11/15 kill-point conflicts (6/8, 12/14, 36/40) | Use 21's gates at 6, 12, 18, 24, 36 only | Ambiguous deadlines undermine stop rules. |
| P1 | 07 solver cut at 18; 11 begins at 30 | Cut solver this event | Original schedule is internally impossible and strong builder is already the bottleneck. |
| P1 | 12/13 mock household story as universal fact | Label wattages, timing, appliance flexibility and operator behaviour as scenario assumptions | No field demand study. Remove “exactly three options” and invented universal lack of control. |
| P1 | 13 strongest opening: nothing enforces feeder limit | Cut | Protection devices exist; the prototype must not imply it replaces them. |
| P1 | 14 retyping resolves advance-spec prohibition | Replace with “follow organiser ruling on use of prepared specifications” | Retyping does not resolve a rule forbidding preparation itself. No legal/eligibility assurance offered here. |
| P2 | 16 stress-50 cap 30 kW outside 20 kW slider | Separate lab cap range 0–100 kW, no live fleet mutation | Internal UI mismatch and unnecessary live safety coupling. |
| P2 | 09/16 colour exclusively red for observed overload | Keep red for known overload; add text/icon for lost assurance and errors without manufacturing red load | Unknown must not look verified or be confused with a measured violation. |
| P2 | 01/README redundant load paths analogy | Do not imply a lost household's full share is immediately reusable | Reservations survive failure until safe release. Metaphor must follow arithmetic. |

## Missing — required for a buildable contract

| Addition | Replaces / cost |
|---|---|
| Registered baselines, envelopes and stable member identities | Replaces self-certified floor authority; a fixed run manifest and review process. No medical-data collection. |
| Issuer epoch, member/plant boot IDs, one pending request, immutable grant identity | Replaces bare version numbers; explicit negative fixtures and persistence rules. |
| Separate proposal, admission and applied state | Replaces one `budget_w` being treated as all three; three labelled quantities on inspector. |
| API/evidence process independent of coordinator | Replaces a likely single-process “kill brain and UI dies” failure; one additional service. |
| Complete REST/WS shape, errors, revisions, idempotency, stale/replay semantics | Replaces sketches; M4 and M5 can implement against paper from hour one. |
| Bound on enforcer scheduling/actuation and explicit exclusions | Replaces “monotonic means clock issues cannot occur”; measured model assumptions. |
| Stateful protocol tests before integration | Replaces afternoon allocation fuzzing being presented as distributed proof; M5 starts oracle at hour 2, M1 reviews it. |
| Missing data as null with quality and age | Replaces zero-valued unknown load and false 100% compliance; changes reducers and UI. |
| Offline dependency pack and alternate-host rehearsal | Replaces “fresh clone works offline” with an actual install/run path; public dependencies only, prepared as rules allow. |
| Incidents and 3 a.m. fallbacks | Replaces ad hoc debugging; bounded stop decisions in 21. |

## Cuts, in order

The original MUST list plus full 16 is not an achievable commitment for one strong builder and four learners. **Strong inference, medium confidence:** M1/M3 review and integration dominate; adding four people does not create four independent protocol experts.

1. **Cut CP-SAT and its comparison chart.** Removes incompatible device visibility/horizon design, solver tuning, timeout plumbing and benchmark claims. Keep the allocator interface; no empty solver module or false “it lost” story.
2. **Cut live `/lab` fleet respawning, TTL/tick sliders, custom mix and chaos.** Replace with an isolated, bounded allocator benchmark and fixtures. This preserves the route and the honest scaling question without resetting live safety state.
3. **Cut six animated Showcase screens and bespoke icon production.** One static page, a compact data-minimisation diagram, one manually started illustrative lease animation if ahead. `/console` gets the time.
4. **Cut ESP32 and standards-adapter stubs from committed scope.** No value in an unimplemented adapter that leaks device contracts. The optional second allocator and hardware remain post-event directions.
5. **Cut exact raw trace replay and ZIP bundle.** Keep ordered JSONL, deterministic read-only state playback and direct event export. Recorded input replay is evidence enough.
6. **Cut non-interruptible scheduling, multi-deadline guarantees and 30 devices.** Five houses × four simple virtual loads, ten member/plant processes. If gate 6 fails: three houses × two loads. Distinct processes, not dozens of OS processes, prove independent failure.
7. **Cut weighted debt from control if not correct by hour 18.** Keep equal-surplus allocation and honest deficit display. Do not cut the reservation gate, request anchoring, baseline accounting or fault tests.
8. **Cut live protect mutation if floor/envelope consequences are still disputed.** Keep a fixed protected baseline and a disabled control explaining why. Never increase it on a click.
9. **Cut full device grid on Console.** Member cards plus a drawer for one household are enough. Reuse that drawer for load-path inspection.
10. **Cut `/lab` execution before cutting a proven failure demonstration.** A static route saying “not measured” is better than invented flat points.

No change here swaps out the requested stack. JSONL replaces SQLite for event evidence to reduce replay/transaction work; a small separate SQLite authority store remains justified for durable epoch, controls and debt. Both are standard Python facilities. Recharts and plain React context are the frontend defaults; no visx/Zustand decision remains for hour one.

## `/lab`: replace the flat-latency claim with two experiments

**Mathematical verdict, high confidence:** work grows with members. Reading n offers is Ω(n); the selected implementation is O(n log n), not O(1). Holding members fixed while device count grows can keep *allocator input and measured call time* roughly unchanged. It does not keep broker, logger, plant, member aggregation, API serialisation or browser work unchanged. Shared CPU contention can affect even the pure call's wall time.

Experiment A: fixed per-household demand distribution, vary n over 5, 10, 25, 50, 100, 500, 1,000 and 5,000 **synthetic offers**. Show actual algorithm/version, machine/CPU/OS/Python, seed, total offered watts, cap/floor ratio and weight distribution. Include all-saturated, no-saturated and staggered-saturation inputs. Fifty points alone cannot establish asymptotic complexity.

Experiment B: hold ten members fixed, vary two to twenty virtual devices per member. Generate device profiles and aggregate outside the allocation timer. Separately measure aggregate formation time, offer size and coordinator allocation time. Equivalent aggregate offers must be held equal for the strict isolation comparison; otherwise label the changed demand distribution as a confounder. This is an offline synthetic experiment, not 200 real nodes.

Measure input validation, sorting/allocation, independent validation, reservation admission, MQTT request→grant, grant→plant acknowledgement, cap-event→verified-settled, and UI snapshot serialisation as separate stages. Each cross-host duration is either measured on one process around a round trip or carries a clock-uncertainty label; never subtract unrelated monotonic clocks. A slow transport path cannot be disguised by a fast allocator number.

Benchmark procedure: 20 warmups then 200 measured calls per point; repeat in three separate batches, rotate size order using a fixed seed, keep snapshots outside the timer. Use a monotonic high-resolution timer, record baseline timer overhead, raw samples, median and p95 per batch, plus maxima and invalid sample count. No network or file write inside the pure-call timer. Do not subtract noisy overhead until numbers become negative. Show units honestly: if below reliable resolution, show “below reliable resolution”, not 0 µs.

No CI confidence interval is required for the MVP; do not add one without a method. Three batches give a basic repeatability view, not a population guarantee. A live run shows progress and raw measured points only, with a 10 s bound and one active job. Run isolated from the judged control demo; CPU load still exists on one laptop, so disable benchmark starts during fault rehearsal. Store environment and results for export. Do not draw a CP-SAT curve without a compatible implemented comparator.

Judge sentence: **“Device detail is aggregated locally. Coordinator allocation scales with household count; here are the measured times and exactly what the timer includes.”**
