# Software design and contracts

Current implementation | 7 September 2026

This is a description of the executable prototype, not a future build specification. Exact payload fields live in the generated [MQTT schema](../fixtures/mqtt.schema.json), [Snapshot schema](../fixtures/snapshot.schema.json) and [OpenAPI contract](../fixtures/openapi.json). Regenerate them with `scripts/build_fixtures.py` after a contract change.

## Boundaries and process ownership

The live supervisor owns one Mosquitto broker, one coordinator, five members and five virtual plants. The observer and HTTP service survive a coordinator kill. Each plant survives its member's termination. All control processes currently share one Linux host and clock domain.

```text
Home profiles -> member agents -> aggregate offers -> MQTT -> coordinator
                                                        allocator
                                                        validator
                                                        reservation gate
Home plants  <- bounded ceilings <- members <- admitted leases
     |+     +-> virtual readings -> privileged observer -> API -> console
```

The coordinator does not read private appliance configuration or device topics. The observer deliberately does, to support the demo inspector. This is data minimisation enforced through roles and topic ACLs, not confidentiality against the broker or host administrator. The operator API can change desired caps/rules and manage owned processes; it is not another grant issuer.

## Allocation: one rule with a narrow fairness claim

For household i, f_i is its registered floor, u_i its useful total demand and w_i its fixed positive weight. After site reserves and floors, the available surplus is shared as:

`extra_i = min(u_i - f_i, w_i * level)`

The largest feasible common level is found by sorting saturation breakpoints `(u_i - f_i) / w_i`. [allocator.py](../src/truss/allocator.py) computes exact rational continuous targets, then rounds each total down to integer watts. Sorting gives O(n log n) work. Quantisation loses less than one watt per member whose target is fractional; it never creates additional authority.

This is weighted max-min fairness of normalised surplus for fixed inputs and weights. It is not equality of total watts, an exact integer leximin solution, appliance-completion fairness or a promise that every job eventually runs. The [independent validator](../src/truss/validator.py) checks the proposal without importing the allocator.

In the three-house Example at 1,800 W with a 100 W reserve, floors 160/170/180 W and sufficient demand, each receives 386.666... W of continuous surplus. Rounded proposals are A 556 W, B 566 W and C 576 W, with 2 W of rounding headroom. This is arithmetic for the illustration, not a live lease record. The former B=350 W behaviour came from the illustration excluding its heater from useful demand; the supplied profiles now drive all three offers.

## Permission admission and recovery

[reservations.py](../src/truss/reservations.py) retains potentially usable grants. For each stable member identity:

`reservation_i = max(registered_floor_i, all still-possible grant amounts_i)`

Renewals for one home are alternative aggregate ceilings, so their maximum is counted rather than their sum. Floors remain counted when all grants expire. Before adding a new grant, the gate requires:

`sum(resulting reservations) + measurement reserve + external bound <= current cap`

The coordinator rereads the committed cap inside a SQLite `BEGIN IMMEDIATE` transaction before proposing/admitting the grant. Admission precedes network publication. Publication failure and acknowledgements do not release the reservation early. Each request's retry returns its original immutable grant during the retained lifetime.

The detailed live grant ledger is in memory. SQLite persists the issuer epoch, controls, operations and fairness checkpoint. On every coordinator boot, the lock excludes another local issuer, the epoch is advanced durably, and all members are conservatively reserved at registered maxima for 6,400 ms with no new grants. This full wait replaces reliance on recovering a detailed old-grant log. Another crash begins a fresh full wait.

Changing the cap does not revoke earlier grants instantaneously. When current exposure exceeds the new cap, incompatible renewals and increases are withheld. A cap below floors plus reserves is infeasible; floors remain and no claim of meeting both constraints is possible. In the supplied registry the feasibility threshold is 1,000 W.

## Request time, identities and independent expiry

[member.py](../src/truss/member.py) fixes the deadline before sending a request: member monotonic time plus 6,000 ms. One pending request is current at a time. Lease receipt cannot reset its deadline. Duplicate replies are idempotent; stale versions, foreign identities, wrong boots, wrong registries and mismatched requests are rejected.

Accepted ceilings include the original deadline, member and plant boot identifiers, binding, registry and lease reference. [plant.py](../src/truss/plant.py) validates those boundaries and limits device commands to the active aggregate ceiling. Member rebinding waits until the old authority has expired and the plant is at its baseline. A restart cannot clear stable-member reservations at the coordinator.

The member and plant interpret deadlines in their shared local clock domain. UTC timestamps are for records and display. Sending this absolute monotonic deadline to an unrelated physical board would be incorrect without another timing protocol.

The conservative hold uses model assumptions of clock-rate deviation rho=0.001 and maximum expiry enforcement allowance delta=250 ms. With T=6,000 ms:

`H >= (1 + rho) * (T / (1 - rho) + delta)`, approximately 6,262.3 ms.

The implementation uses 6,400 ms. This is a conditional engineering bound, not a measured universal clock or scheduler guarantee. The plant loop sleeps 20 ms between iterations and latches an enforcement fault after a loop gap over 250 ms. A healthy independent plant can expire authority when its member or coordinator dies. A frozen plant or suspended whole host is outside that result.

## Local appliances and protected policy

[local_policy.py](../src/truss/local_policy.py) starts each appliance at its configured baseline and assigns remaining watts to flexible devices in descending priority, with stable ID ties. Modulating devices accept partial steps. Binary devices receive their entire baseline-to-maximum step or none; an unaffordable binary step is skipped so a smaller lower-priority device may still fit.

Protected and unclassified devices reserve their full configured maximum before startup. Private profiles are copied into each run, so editing source profiles cannot change protection during a member restart. Changing this policy requires reviewing configuration and beginning a new run.

`unusable_w` reports permission left after local assignment. It is not proof of saved energy, and it is not automatically returned to other members within the same round. Deadline-related wire fields do not imply a delivered deadline scheduler: current virtual telemetry has no active energy/deadline job model.

## Optional fairness history

[fairness.py](../src/truss/fairness.py) records withheld authorisation against an equal-surplus reference. Over each eligible interval in hours:

`credit_next = clamp(credit + (reference_total_w - reserved_member_w) * hours, 0, 20 Wh)`

The optional weight is `1 + min(credit / 10 Wh, 1)`, bounded from 1 to 2. Equal-surplus remains the startup rule. This is not a meter-based energy debt or a guarantee of repayment.

Intervals split when exposure or eligible inputs change. Missing/stale inputs, recovery, infeasibility and excessive loop gaps freeze relevant accounting. Fractions are stored as numerator/denominator pairs. Checkpointing occurs before grant publication and in the periodic plan cycle; a crash can lose an uncheckpointed accounting tail. Corrupt persisted credit disables weighting for all members and exposes an error. Self-reported useful demand within the approved envelope remains gameable.

## Observation, replay and uncertainty

[observer.py](../src/truss/observer.py) projects actual MQTT records. Plant sample time, clock domain, boot and enforcement state determine freshness. Readings older than 1,500 ms cannot verify compliance. Site observed watts are null unless all required member observations are fresh; older per-member values may remain explicitly labelled stale.

Proposed, issued, reserved and observed values are four different facts. Fresh acknowledged draw need not equal allowance, especially with binary loads. Causal device explanations require matching references. The browser's animated lease countdown is an estimate, not a control clock.

Raw MQTT events are recorded separately from optional operator snapshots. Snapshot recording runs at 2 Hz and stops at 32 MiB or 10,000 frames. Replay sessions freeze the available recorded bytes, disclose gaps, allow seek and 1x play/pause, and cannot control live processes. A capped prefix says nothing about what happened after its final frame. Up to four replay sessions are held at once.

## Operator interfaces

For standalone live/mock services the following paths begin `/api/v1`. In the combined hosted app, live paths begin `/console-api/v1`; mock paths retain `/api/v1`.

| Interface | Purpose |
| --- | --- |
| GET `/health`, `/state?source=live` or `mock` | Health and complete source-specific Snapshot. A mismatched source is rejected. |
| POST `/cap`, `/rule` | Desired cap/rule control. Rule change is live-only. |
| POST `/chaos`, `/faults` | Owned child-process actions and bounded application-message faults. Available actions depend on source. |
| GET `/runtime`, `/fairness` | Live process health and current persisted fairness view. |
| GET `/operations/{id}`, `/events` | A control's recorded status and an event tail with gap information. |
| GET `/recordings`; POST `/replays` | Recording catalog and immutable replay creation. |
| GET/DELETE `/replays/{id}`; POST `/seek`, `/playback` under that session | Read, release, seek, play or pause a replay. |
| POST `/lab/runs`; GET `/lab/runs/{id}` | Submit and poll an isolated synthetic benchmark. |
| POST `/lab/benchmark` | Compatibility endpoint awaiting the same bounded benchmark worker. |

Cap/rule/chaos/fault mutations carry run ID, source, expected control revision and a UUID `Idempotency-Key`. Same key and same parsed input returns the recorded operation; changed input conflicts. A stale revision also conflicts. Live keys persist for the run; mock keys are in memory. Accepted cap control means desired cap committed, not immediate compliance. Queued process actions after an API crash need reconciliation; they are not blindly repeated.

Requests are limited to 16 KiB including streamed bodies. Wire parsing rejects duplicate keys, nonfinite values, extra fields and invalid identities. These checks do not provide production login, TLS or hostile-device protection.

WebSocket state is served at `/ws/v1/state?source=...` with subprotocol `truss.ui.v1`, rewritten to `/console-ws/v1/state` for hosted live state. It sends full snapshots up to 4 Hz, hello and ping frames; the client answers pong. Stream/source/revision checks prevent old updates replacing newer state. Polling is a degraded read path, not a source switch.

## Benchmark and hosting boundaries

Lab accepts 1-5,000 synthetic members, up to 200 samples and uniform/saturated/skewed scenarios. It separates allocation, validation and total sample arrays. Each API permits one active bounded worker and retains 32 recent jobs. Job idempotency is in-memory, unlike durable operator controls. Worker isolation does not make the shared host a real-time system.

[hosted.py](../src/truss/hosted.py) mounts the static site, live backend and separate mock backend on one HTTP origin. One web process owns the broker and virtual fleet. More Uvicorn workers or Heroku dynos would create competing independent runtimes, not scale this system correctly. Detailed operating instructions are in [operations](operations.md).

The [next steps](next-steps.md) identify what must change for multiple hosts, real actuation, stronger security and larger deployments.
