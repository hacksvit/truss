# Current implementation status

6 September 2026. **The core backend now runs through real local MQTT with independent virtual plant processes.** Claude is now working on the frontend; this backend update does not edit or re-audit its files. The build started after the user authorised implementation during the hackathon; Codex made no commit or history rewrite. The user subsequently committed the basic backend. This status supersedes the earlier scaffold-only handoff.

## Implemented backend

| Area | What exists | Owner |
|---|---|---|
| Contract | All 17 repaired MQTT variants, strict Pydantic validation, generated JSON Schema/OpenAPI, valid/invalid fixtures | M1 |
| Allocation | Sorted weighted-surplus water-filling, exact rational target, downward watt rounding, independent validator; default equal weights; optional persisted service-deficit weighting | M1 |
| Authority | Fixed registered baselines; request-anchored 6000 ms lease; conservative max-per-member reservation; immutable grant retries; no ack-based reclaim | M1/M3 |
| Coordinator | Separate MQTT process; fresh offers; durable singleton/epoch; serialized admission against committed cap; 6400 ms recovery on every boot | M1 |
| Member | Separate household process; private profiles, aggregate offers, boot/binding checks, anchored requests, bounded ceilings and device commands | M3 |
| Plant | Separate enforcer process; complete command identity/ref validation, aggregate gate, protected maxima, independent meter/telemetry/ack, tick-driven expiry | M2 |
| Broker | Local authenticated Mosquitto 2.1.2; role ACLs; no anonymous access; tested denial of private coordinator reads and member grant writes | M3 |
| Runtime | Own-child supervisor, manifests/logs, five members/five plants, real kill/restart actions, bounded application partition/delay faults | M2 |
| Operator API | Live/mock source isolation; REST/WS snapshots; durable cap/chaos idempotency and revisions; real owned-process controls | M5 |
| Evidence | Actual MQTT JSONL; stale/future/wrong-domain observation rejection for compliance; independent plant state files during broker outage | M5 |
| Frontend support | Mock server, checked example states, three existing route shells, eight frontend tests; source-switch handoff documented | M4/M5 |

The full file map, public interfaces, dependencies and owners are in [architecture](architecture.md). Pure cores stayed separate from new process adapters. This adds small lifecycle modules to plan 19; it avoids coupling allocation/unit tests to broker setup.

## Verified versus still limited

The real-process suite exercises normal allocation, coordinator kill, two restarts inside TTL, cap reduction, infeasible baselines, member kill/restart, broker death/reconnect, member partition/healing and grants delayed beyond their request lifetime. Broker negative tests run with real credentials. Final command/counts are in [evidence](evidence.md); a finite test run is not a proof over arbitrary operating-system schedules.

The plant still trusts member software to forward a genuine accepted grant with its original request deadline. It validates wire identity/binding/ref/amount and rejects obviously overlong future ceilings, but it does not cryptographically verify the coordinator grant itself. A malicious member that invents authority is outside the trust model. Strengthening this would require an explicit new plant-verifiable authority design, not an AI classifier.

A healthy plant loop checks deadlines every 20 ms and marks a persistent fault if a loop gap exceeds 250 ms. A whole-PC suspend or crashed/frozen plant is outside the timing theorem. Local state files report observed expiry lateness where available; the bound is an assumption with empirical checks, not a certified scheduler guarantee. No mains or medical equipment is connected.

Live cap acceptance means **desired cap committed**. Existing authority can remain above a newly lowered cap until it expires. Infeasible protected baselines remain visible; the system never fabricates enough capacity. During recovery the conservative maximum reservation may itself exceed cap, but no new grant is issued in that wait.

## Deliberate remaining cuts

- Live defaults to equal surplus. Authoritative time-integrated service-deficit weighting is now selectable with a cap of 2. Credits are checkpointed authorization history, not measured sacrifice; no guaranteed repayment claim. See [backend extensions](backend-extensions.md).
- Binary devices are handled by skipping an unaffordable whole step and reporting the stranded watts; the allocator itself stays continuous. Giving stranded capacity back to another household within the same round is **not** implemented — it needs either a second allocation pass or richer offers, and richer offers would publish appliance step sizes and weaken the household privacy boundary. That trade-off is deliberate and unresolved.
- Protected/unclassified policy is fixed for the full run. Private profiles are copied into the run directory at startup, so editing source config cannot change protection during a member/plant restart. New policy requires a new reviewed run. No runtime downgrade or criticality classifier.
- Replay now provides separately recorded operator snapshots with immutable sessions, seek and 1× play/pause. Values and ages are historical at each recorded frame. Existing raw-event reconstruction remains separate; gaps are not filled and old runs without snapshots have no invented UI recording.
- Lab runs in a bounded lower-priority subprocess on live/mock, with uniform/saturated/skewed scenarios and separate allocation/validation samples. Live planner stage durations are measured. Neither is end-to-end latency, and sharing the same PC is not a real-time resource guarantee.
- AI/SGLang were removed at the user’s request. No model runtime, feature flag, endpoint or future integration branch is required.
- CP-SAT, binary/non-interruptible appliance scheduling, deadline guarantees, hardware appliance control and cloud paths remain cut. An optional read-only ESP32 screen now displays aggregate virtual status over USB; it is outside the authority path. See [display evidence and setup](esp32-display.md).
- The last backend handoff left the UI wired to mock. Claude owns subsequent UI changes; current UI source wiring is not re-asserted here. [Frontend handoff](frontend-handoff.md) and [backend extensions](backend-extensions.md) define the available backend behavior.
- The current backend has one local operator and trusted processes. No multi-host control clocks, production authentication/TLS deployment, multi-worker API, automatic orphan takeover or rolling registry changes are claimed.
- Queued chaos operations survive in SQLite; if the API crashes between queuing and performing an action, retries return that queued record rather than silently performing it twice. Manual reconciliation is required. Cap transactions are atomic and durable.
- JSONL evidence failures stop assurances and stale out the view; they do not grant authority. Telemetry gaps caused by a broker outage are unknown observations, not proof of zero draw.

## Assumptions and missing information

A1: M1–M5 remain proposed roles; real names were not supplied. Codex is carrying backend work now; user owns frontend after 9. A2: 9 means 21:00 local time; this is not a scheduled automation. A3: the inspected Linux PC is the intended host. A4: event rules permit the public dependencies/AI assistance being used; organiser approval was not independently verified. A5: fictional registered maxima are correct, one trusted coordinator/member/plant stack and a stable run/registry define the model. A6: clock drift ≤0.001 and enforcement allowance ≤250 ms are assumptions, not hardware certification. A7: a cap below baselines plus reserve is infeasible. A8: the official elapsed hackathon hour and review schedule were not provided.

## Next build order

Use [BUILD_PLAN](../BUILD_PLAN.md). Core fault evidence comes before optional features. The user can build frontend against mock immediately or consume the live API after completing the source-aware handoff. Both paths are ordinary deterministic software. Do not trade reservation, expiry or protected-baseline checks for demo polish.
