# 21 — Dependency graph, tests and the 3 a.m. plan

This replaces the sequencing decisions in 11 and resolves its conflicts with 07/15/16. It is an estimate for **one strong builder M1 and four learners**, not five interchangeable experts. Start hour is relative to the organiser's confirmed official start. No advance competition code or commits are assumed.

## Achievability verdict

**Original scope: no credible commitment. Revised scope: plausible, still high risk.** First break: hour 0–2 freezes an underspecified contract, while M1 is expected to design the twin, allocator and safety gate and M3 must independently interpret lease semantics. Second break: hour 6–12 introduces correctness after the vertical slice rather than making it part of the slice. Third break: one learner owns a complete animated React site, mock integration and controls while another owns broker, member enforcement, storage and replay. “Fixtures first” removes runtime waiting; it does not remove missing semantics or review work.

Budget planning assumption: M1 has roughly 28–32 focused hours; each other builder roughly 24–30, with sleep, meals, venue rounds and integration consuming the rest. Do not budget five people ×48 productive hours. These are estimates, not a promised schedule. Review times/required deliverables are unknown; M5 shifts rehearsal windows to actual organiser slots without adding features.

Core: five members/five independent plants, twenty virtual devices, equal-surplus allocator, request-anchored grants, reservation gate, console, JSONL evidence, meaningful failure tests. Optional weighted service deficit by hour 18, basic replay by 24, measured lab by 30. SGLang is a separate gated branch in 22; not allowed to consume the safety review slot.

## Dependency graph

`★` marks the expected critical path. An arrow is a real integration dependency. Side-by-side nodes are independent work, not permission to skip handoff verification.

```text
★ G0 h0–1: rules + empty event repo + core contract examples
   │
   ├── B h1–3: broker/ACL + transport loopback (M3)
   ├── P h1–4: plant clock/gate + two device types (M2)
   ├── U h1–6: Console against snapshot; source/stale states (M4)
   ├── F h1–3: mock API/WS + independent race oracle sketch (M5)
   └── ★ A h1–4: allocator + independent validator + reservation gate (M1)
            │
       ★ L h3–6: one member anchored request → gate → plant (M1/M3/M2)
            │ requires B, P; F checks wire acceptance
       ★ G6 h6: one full safe slice; kill coordinator and observe plant floor
            │
       ★ R h6–10: delayed/reordered renewal, epoch, double restart (M1/M3)
            ├── D h6–10: five-house launch + independent plant meters (M2)
            ├── E h3–10: events + reducer + API (M3 event writer; M5 API)
            └── U2 h6–10: inspector + async controls + null quality (M4)
            │
       ★ G12 h10–12: live Console + arbitrary-loss model + process expiry
            │ requires R, D, E, U2
       ★ H h12–18: cap transition/infeasible/unknown + receiver/ACL tests
            ├── W h12–18: optional service deficit, only after core H pass
            ├── Q h12–18: fault orchestration + runbook (M2/M5)
            └── V h12–18: static Showcase, compact layout (M4)
            │
       ★ G18 h18: safety/claims gate; weighted mode cut if unfinished
            │
       ★ G24 h18–24: integrated review demo + recorded evidence
            ├── RP h18–24: read-only replay (M3/M5)
            ├── LAB h24–30: isolated benchmark + /lab (M5/M4)
            └── AI h24–26: optional SGLang branch ONLY if gates in 22 pass
            │
       ★ C h24–34: offline install + adversarial rehearsal + alternate host
            │
       ★ G36 h34–36: three cold starts; freeze; no outstanding safety failure
            │
       ★ RELEASE h36–42: backup recording, contribution record, judge rehearsal
            │
       ★ FINAL h42–48: rollback-only fixes, rest rotation, final handoff
```

The graph has slack for optional branches, not hidden slack in R/H. M1 reviews the lease receiver and gate at h4–6 and h10–12; reserve those blocks. If the paper assumptions prove unimplementable, cut scope rather than postponing tests to h24.

## Five parallel streams with explicit handoffs

| Hours | M1 — authority and maths | M2 — plant and operations | M3 — member/transport/evidence | M4 — frontend | M5 — API, oracle and evidence QA |
|---|---|---|---|---|---|
| 0–1 | Walk counterexamples; core schemas + immutable run registry | Empty event repo, process plan, two device profiles; reviews command semantics | Broker connection/clock-domain check; reviews request/expiry semantics | React shell + hand-written typed snapshot; Console first | Record organiser answers, define snapshot/error cases and test oracle independently |
| 1–2 | Freeze all authority fields and rejection cases with receivers | Device transition table and plant baseline gate against fake clock | MQTT validated envelope loopback, own-topic ACL | Capacity bar/member cards, no live service dependency | Mock health/state first, then WS; check types with M4 |
| 2–4 | Pure allocator, independent validator, max-exposure admission | Plant ceiling expiry and idempotence; send valid telemetry/ack fixtures to M3 | Request anchoring, one pending request, binding, private twin; in-memory transport first | Lease estimate + stale/unknown, pending controls against mock | Stateful trace oracle; implement reducer and API models against events fixture |
| 4–6 | Wire sole publisher; review M3 acceptance and M2 gate | One real plant process, kill/stop member test; small supervisor | One live member loop and local policy; broker expiry/Will checks | Complete one-screen mock Console and source banner | Record G6 slice and failures; contract mismatch fixes owned by producer |
| 6–8 | Durable epoch, lock, recovery and cap revision | Expand to five houses, own-PC profile, stable ID registry | Reconnect, boot binding, late grant rejection | Live adapter can connect when API ready; inspector from fixtures meantime | API reads live events, control store integration with M1 interface |
| 8–10 | Renewal/drop/reorder tests; atomic admission review | Managed chaos/drop/delay flags; independently published meters | Append-only writer and gap handling | Drawer/LoadPath exact refs; REST revisions/errors | WS/polling and metrics; same conformance tests against mock/live |
| 10–12 | G12 safety integration, fix protocol only | Run killed/frozen-member and coordinator cases | Double restart/partition heal; review unknown accounting | Live console handoff; countdown proves nothing without plant report | Run stateful model and evidence checks; reject false green |
| 12–16 | Cap transition/infeasible; then optional deficit ledger | Rejected command, overload and policy conflict fixtures; runbook | ACL regression; offer/deadline freshness; replay reader if ahead | Compact 1366×768 layout, static `/` | APIs complete operations, metrics settling window, trace regression |
| 16–18 | Review receiver+gate+oracle, decide equal vs weighted | Full fault rehearsal and stop decisions | Read-only replay contract; protect/policy ack fixes | Showcase and Console contract smoke | G18 claims audit; save test counts/seeds and runnable tag |
| 18–24 | Integrate/fix; prepare technical defence; no solver | Rehearse own-PC and recovery; preserve run manifests | Replay only after safety passes; otherwise help tests | Freeze major Console hierarchy; replay view | Review 1 timing, backup recording; no lab until G24 green |
| 24–30 | Bounded review/bug fixes; optional AI ≤2 h only if no critical work | Offline packs + alternate-PC start; real broker restart | Rehearse/inspect logs; assist boundary tests | Thin `/lab`, or keep unavailable page if no results | Isolated benchmark or core QA; API+mock remain canonical |
| 30–36 | Diagnose only blockers; final proof wording | Three cold starts; G36 evidence with M5 | Replay/restore checks; audit no stale authority resurrection | Responsive and accessibility pass; freeze | Test report, cold-start records, feature capability truth |
| 36–42 | Judge maths/protocol rehearsal | Backups and fallback operator practice | Member/broker explanation rehearsal | Capture final screens; freeze all assets | Record 90 s backup + under-3-minute script; contribution record |
| 42–48 | Rest and rollback-only review | Rest and startup custody | Rest and fallback custody | Rest and presentation custody | Submission links, final run hash, recorded fallback |

M1 is not an on-call rewrite service. For a broken teammate module, use its agreed interface and pair for one bounded session; owner writes the fix. If that fails, remove an optional feature. Do not move every unfinished task into M1's column.

## Blockers and how to remove each one

| Edge / handoff | Potential wait | Removal and acceptance moment |
|---|---|---|
| Schema → all, h1/h2 | Everybody waits for all models | H1 freeze envelope, offer/request/lease/ceiling and complete Snapshot example. H2 add remaining variants. M4 uses fixture-only types, M2 uses handwritten transition table. No implementation reuses pre-event code. |
| Broker → members/plants, h3 | M3 config/debug blocks device work | Fake transport and fake clock are injected interfaces; h3 loopback is separate acceptance, no network code inside pure devices. |
| Plant → member, h4 | M3 has no telemetry | M2 delivers valid discovery/telemetry/ack examples at h2 and fake plant response at h4. |
| Gate → request consumer, h4 | M3 cannot predict granted amounts | Canned grant/deny trace with the same ref/basis shape; h4 real gate swaps in. |
| M1 review → expiry, h4–6 | Critical semantics wait behind allocator polish | Review is explicitly scheduled; simple equal allocation may be temporarily used but must pass admission. Never stub away safety gate. |
| Epoch/controls → API, h8 | M5 blocked on database schema | Store interface returns Operation and revision from h2; fake store first. M1's real transaction adapter replaces it by h8. |
| Evidence → frontend, h8–12 | M4 waits for logger/API | Mock is a runnable service by h2; exact same conformance suite. H10 live payload comparison; h12 connection switch. |
| Local decision → inspector, h8 | Basis cannot explain a device | Frozen LocalDecision fixture plus exact LeaseRef. Inspector shows missing evidence rather than inventing it. |
| Remote chaos → laptops | M2 cannot control remote OS | Own-PC profile is canonical. No SSH/five-laptop orchestration required. Optional laptop deployment uses manual local restart, explicitly rehearsed. |
| Safety model → integration, h10–12 | Oracle mirrors implementation or arrives late | M5 writes traces before reading gate logic; M1 reviews assumptions, not oracle code shape. Compare against independent interval oracle. |
| Replay → recorded logs, h18 | Real run too late | Fixture event replay first; real recorded input only after G12. Mark mock source all the way through export. |
| Lab → scaling claim, h24 | Waiting for synthetic fleet respawn | No fleet respawn. Pure isolated benchmark input, raw samples, measured labels. |
| AI → GPU/model setup | Kernel, model download or RAM troubleshooting | Optional two-hour branch, disabled on any core delay. No dependent core work. |
| Assets → UI | M4 waits for logo/icons | Existing typography/tokens, text device labels and simple local favicon. No commissioned asset on critical path. |
| Dependencies → offline start | Internet needed for install | Event-created lockfiles and allowed public dependency cache on local media; rehearse with WAN blocked while LAN remains up. No reused project code. |

Nobody waits for an optional feature. The safety integration edges are real shared work; claiming that absolutely nobody can ever be blocked would be dishonest. Scheduled handoffs, fixtures and scope cuts bound those waits.

## Test plan — meaningful proof obligations

### Allocator properties (M1)

Generate registered `0≤floor≤firm≤useful≤maximum`, fixed weights in [1,2], varying cap/reserves, zero members, exact-floor cap and impossible cap. Test:

- feasible rounded budgets respect floors/useful/cap; infeasible results do not fabricate budgets;
- deterministic output and permutation invariance keyed by member ID;
- identical complete offers/weights get identical rounded budgets;
- increasing capacity never decreases a budget **with membership, offers, reserves and weights fixed**;
- target weighted max-min condition: no unsaturated member can receive a transfer improving its normalised surplus from a larger-normalised donor without harming an equal-or-smaller allocation; saturated members are handled correctly;
- continuous target exhausts available useful surplus; downward rounding loss < one W per active member; exact integer leximin is not asserted;
- metamorphic scaling of continuous units and the two counterexamples in the research review.

Independent oracle: for tiny integer/rational cases, enumerate feasible surplus allocations at an appropriately fine test quantum and compare sorted normalised vectors, acknowledging quantisation. For larger cases use the pairwise-transfer condition and an independently calculated λ/root oracle. A hand-built alternative is a regression example, not proof over all alternatives. Keep validator independent; agreement between two copies of one algorithm proves little.

### Stateful protocol properties (M5, reviewed M1/M3/M2)

Use Hypothesis RuleBasedStateMachine with a fake reference clock plus independent coordinator/member clock rates. Generate actions: request, grant admission, deliver/drop/duplicate/reorder, tick, supersede request, change feasible/infeasible cap, change observation freshness, member restart, coordinator crash/restart/restart again, plant binding change, broker reconnect, delayed pre-crash message, wrong IDs/epoch/TTL, and rejected shutdown.

Maintain an independent oracle of **possible grant-use intervals** per member and persistent baselines. It does not use reservations.py to calculate the expected answer. Check I2–I9 after every action; I1 only under its admitted stable-cap preconditions. At cap drops, assert transition/honesty and bounded eventual fallback under healthy clocks/enforcers; do not call the unavoidable initial over-cap state a bug in the proof. Recovery can have unknown conservative exposure above cap without any new grant.

Required shrunk regression traces: all 13 attacks in 18. Critical extra interleavings: duplicate at deadline−1 ns/deadline/deadline+1 ns; lost ack after applied decrease; new request before old request's response; old boot lease after member reset; cap update between plan and admission; crash between reservation and publish; publish failure after reservation; epoch write failure; two simultaneous issuer starts; receipt just before recovery ends; partition heals while old/new requests coexist. A low last-meter reading must never reduce exposure.

Out-of-model faults are tests of **honesty**, not claimed tolerance: deliberately incorrect member bridging of deadline, a stopped/broken plant, clock drift beyond configured bound, or a forged issuer credential. Expected result is recorded loss of assurance/fault; no theorem is asserted for an arbitrary receiver. Add a mutant receiver that resets TTL on duplicate and confirm the oracle catches its violation, so the test suite demonstrates sensitivity.

### Unit tests by invariant

| Invariant | Unit focus | Property/fault companion |
|---|---|---|
| I1 | meter completeness and response-window arithmetic | stateful exposure bound; cap drop real-process scenario |
| I2 | approved floor equality, fixed baseline, priority cannot raise floor | generated allocator; expiry of every household |
| I3 | max overlapping grant, reserve before publish, conservative hold | interval oracle + delayed grants and double restart |
| I4 | null unknown totals, impossible deficit, no invented unserved action | stale-all snapshot, UI tests, observed overload |
| I5 | duplicate deadline/amount/effect/debt unchanged | generated duplicates before and after expiry |
| I6/I7 | epoch/version order, boot/request/topic/domain binding | restarts, wrong-ID traces, broker ACL and lock smoke |
| I8 | plant local-clock expiry with no incoming messages | kill/stop member; kill coordinator; disconnect broker |
| I9 | baseline counted once, stale is not zero, no ack early release | arbitrary loss and underreported meter sequences |
| I10 | replay/lab cannot obtain live publisher; source cannot mutate live | mock/live route and ACL isolation tests |
| I11 | reducer canonical digest, ordered events, stale ack linkage | replay with duplicates, gaps, truncated last log line |

### Real-process verification (M2/M3/M5)

One controlled run with independent plant meter and observer surviving the coordinator. Exercise coordinator kill; repeated restart inside one TTL; stop member (process remains connected or loses heartbeat); member kill; application-message partition and healing; ack drop; telemetry delay; broker restart; sudden cap drop; impossible floors. Record start/stop monotonic times on the owning host, every authority decision and plant output. Run the enforcer under a bounded CPU-load test and report maximum observed lateness. This is empirical evidence for the assumed δ, not a proof over all OS schedules.

Do not use an API button that merely toggles a UI boolean and call it chaos. Supervisor logs the actual managed process action or transport rule. UI reads outcomes from telemetry/events. A plant crash causing its synthetic output to disappear is not evidence that a real appliance powers off when its gateway dies.

### API / frontend tests (M4/M5)

Same fixture-contract tests against mock and live API. Duplicate POST same key causes one effect; same key/different body 409; wrong revision 409; invalid watts 422; unknown entity 404; unavailable capability rejected. Two tabs never silently overwrite a cap revision. Pending operation timeout is reconciled by GET before retry. Policy receipt/rejection completes the correct operation ID.

WS tests: full replacement, duplicates/lower revisions, new stream, new run, source swap, lost ping/pong, slow consumer, REST fallback and recovery. Unknown aggregate stays null; countdown zero with stale telemetry does not become at-floor. Replay source disables controls; seeks cannot publish. Test 1366×768 and 1920×1080, keyboard activation, reduced motion and no external network requests. Do not test every trivial style rule.

In the own-PC profile, delay telemetry while continuing increasing sequences:
sample-time age, not receipt age, must make it stale. Cross-host/future clock
domain samples cannot verify compliance. A fresh command ack paired with old
telemetry cannot become a verified device state. These tests protect against
the deceptively healthy stream of delayed packets.

Mock coverage is exactly 20's 90 s sequence plus named edge fixtures. If M4 cannot render a case, fix the fixture/contract before debugging live transport. Core smoke targets hour 12; full source/reconnect tests by hour 24.

### What we can say about tests

Record actual generated examples, state-machine steps, seeds, shrinking output, test command, duration, software revision and failures. No prewritten “10,000 scenarios passed” sentence. Separate pure allocation tests, stateful model tests and real-process tests in evidence. A finite test campaign increases confidence; the conditional invariant argument remains the proof claim and its assumptions stay visible.

## Gate decisions

| Gate | Pass condition | If it fails |
|---|---|---|
| h6 | One member request→grant→plant loop with local expiry and independent observed fallback | Three houses/two loads; stop expansion. M1/M3/M2 pair on safety slice. M4/M5 continue mock+tests. |
| h12 | Correct old/new grants under loss/reorder; repeated restart; live Console with real plant evidence | Stop all optional work. Do not claim safe leases yet. No CP-SAT, hardware, AI or lab. |
| h18 | Cap transitions, floors, unknown reporting and core property model green | Equal weights only; static Showcase; replay optional. Safety unresolved means presentation must honestly describe incomplete prototype. |
| h24 | Three-minute core review path reproducible; one evidence log; no false live/mock label | Cut lab/replay enhancements and SGLang. Focus cold-start/failure path. |
| h30 | Optional features have actual measured outputs and no effect on safety timing | Disable their capabilities; retain labelled unavailable routes. |
| h36 | Three consecutive offline cold starts, cap drop, coordinator kill, restart and impossible-cap beats | Freeze and shorten script. Choose last known safe checkpoint; do not weaken invariant to force a green demo. |

## 3 a.m. runbook — decide, do not improvise

| Symptom | First evidence to inspect | Action / stop condition |
|---|---|---|
| New allocations stay low | Old reservation expiries and requested/issued/reserved distinction | Wait the conservative hold. Expected underutilisation is not a reason to release on a missing ack. |
| Nothing renews | Coordinator recovering/lock; request ID, offer seq and member boot | Check fixed registry + fresh offer; replay the exact exchange. Never disable version/expiry validation. |
| Reconnect revives old authority | Binding, request anchor and duplicate timer | Stop live feature work, save trace, rollback gate/receiver change. This is P0. |
| Member dead but load remains above floor past bound | Independent plant heartbeat, domain/deadline and enforcement lateness | Mark enforcement fault. Do not fake a floor in UI. Restore verified checkpoint or use labelled recording. |
| Console freezes when coordinator dies | Process tree/API health | Separate API/evidence process; use existing mock only with visible MOCK banner while repairing. |
| Infeasible state remains red | Sum registered floors + reserves versus requested cap | Correct behaviour. Restore a feasible cap to continue; do not arbitrarily cut a protected member. |
| Device declines ordinary command | Ack reason and active aggregate ceiling | Keep uncertainty/reservation; allow safe local policy response. Remove non-interruptible profile if it violates the admitted scope. |
| UI says 100% with no meters | eligible/unknown sample counts | Fix null/quality projection. Hide metric until corrected, never insert zero draw. |
| Port/process collision | Supervisor manifest, child IDs and singleton lock | Stop only owned stale processes; start one run. No broad kill commands. |
| Authority database unavailable | Commit error, epoch and desired cap revision | No grants until reliable store returns; plants expire. Do not hand-reset epoch or assume old cap. |
| Event log disk/error | gap marker, last complete event line | Preserve prefix; declare evidence gap. Local safety continues; replay cannot claim complete reconstruction. |
| Dependency install requires internet | Event-time lockfile/cache and offline pack | Use rehearsed own-PC environment or alternate media. No library upgrades during freeze. |
| SGLang uses too much RAM/GPU or stalls | model process resources and missed enforcer deadlines | Stop optional model service; deterministic inspector remains. No swap/driver/kernel debugging during safety rehearsal. |
| No time for a feature | Capability flag and last safe checkpoint | Disable it; update pitch/evidence truth. Never leave a fake successful control. |

Revised judged path: ordinary feasible run → cap drop with visible transition → coordinator kill and **fresh plant-confirmed** fallback → restart wait → impossible-cap refusal. Show one causal drawer if time. The optional protection/AI story uses fictional profiles and cannot claim actual medical-device safety.
