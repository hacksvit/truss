# 20 — Wire and UI contracts, as specifications

Owner of MQTT/schema authority: **M1**; member/plant review: **M3/M2**. Owner of API projections and mock conformance: **M5**; frontend consumer: **M4**. These are paper specifications. No executable Pydantic classes, generated schemas, server, mock or configuration is created before the event.

This document replaces the incomplete wire examples in 06 and the sketches in 16. Because nothing has shipped, retain `v1` and freeze this corrected v1 at event hour 2. If an old implementation exists elsewhere, it must not be mixed into this build or silently treated as compatible.

## Pydantic modelling rules

Use Pydantic v2 models with forbidden extra fields, strict scalar validation and a discriminated union on JSON key `schema` (internally name it `schema_id` with an alias). Enums are literal strings. Reject non-finite numbers, numeric strings, booleans in number fields, duplicate JSON keys, and unknown variants. Pydantic does not check freshness, topic authority or reservations: handlers do those separately. Strict JSON handling has type-specific rules; test JSON input, not just Python objects. [Pydantic strict mode](https://docs.pydantic.dev/latest/concepts/strict_mode/), [discriminated unions](https://docs.pydantic.dev/latest/concepts/unions/#discriminated-unions).

All fields listed are **required**, including nullable fields; omitted ≠ null. No silent defaults on the wire. Lists are ordered by stable ID unless an explicit time/sequence order is stated. Units are in field names. All object definitions below forbid unspecified fields.

| Type shorthand | Exact wire restriction |
|---|---|
| ID | String, 1–64 ASCII lowercase letters, digits, hyphen or underscore; starts with letter/digit; no slash or MQTT wildcard |
| UUID | Canonical lowercase UUID string; used for boot/run/request/connection/operation IDs |
| Nat | JSON integer, 0 through 9,007,199,254,740,991; counters must stop safely rather than wrap |
| Pos | Nat ≥1 |
| W | Integer watts, 0–100,000; use wider Nat for sums in lab results only |
| Wh | Finite JSON number, 0–1,000,000; no floating-point watt authority |
| Ms | Nat milliseconds; specific fields narrow this range |
| Mono | Decimal-digit string encoding nonnegative monotonic nanoseconds, at most 20 digits; local clock domain only; never converted through a JS number |
| UTC | RFC3339 UTC string with `Z`, for human/evidence time only |
| Text | UTF-8 string, 1–500 characters; untrusted, plain text in UI |
| Hash | 64 lowercase hexadecimal characters, SHA-256 of canonical input/config |
| Maybe(T) | Exactly T or JSON null |
| Quality | `fresh`, `stale`, `unknown` |

**Envelope E** on every MQTT message: `schema: literal`, `site_id: ID`, `run_id: UUID`, `publisher_id: ID`, `publisher_boot_id: UUID`, `seq: Nat`, `ts: UTC`, `correlation_id: Maybe(UUID)`. `seq` increases per publisher boot across its emitted messages; it is not the log's global sequence and is not a grant version. `ts` is not used for acceptance/expiry. Payload ≤32 KiB except Plan ≤128 KiB. Out-of-range input is rejected with a recorded validation code, never coerced to fit.

Receiver freshness high-water marks are per publisher boot **and topic/entity
stream**; an earlier offer arriving after a later meter must not be discarded
solely because the meter had a higher publisher-wide seq. Authority ordering
uses the separate request/epoch/version/binding fields. Retained metadata is
excluded from freshness until a current heartbeat/observation arrives.

Aggregate watt sums (`baseline_sum_w`, `total_exposure_after_w`,
`reserved_member_w`, `unverified_member_reservation_w`, `exposure_w` and
`deficit_w`) use **Nat**, overriding W in model shorthand below. They can
exceed 100 kW during infeasibility/recovery even though each member and the
site cap are bounded by W. Never clamp a displayed overload to a schema limit.

**Result** enum: `applied`, `rejected`, `duplicate`, `expired`. **Reason** enum: `initial`, `renewal`, `cap_change`, `capacity_exhausted`, `baseline_only`, `stale_offer`, `policy_conflict`, `recovery`, `member_budget_exceeded`, `min_run`, `deadline_missed`, `old_version`, `wrong_identity`, `wrong_boot`, `wrong_request`, `wrong_registry`, `expired`, `duplicate`, `invalid_amount`, `enforcer_fault`, `manual_priority`, `simulated_fault`, `validator_veto`. Result success does not imply fresh measurement verification.

## MQTT routing and authority

Root shorthand `S = truss/v1/site/{site_id}`. Every topic component must equal its payload identity. MQTT 5, QoS 1, clean start and zero session expiry for control clients; no retained authority. Commands/requests/grants have broker Message Expiry 6 s as queue hygiene, **not** the safety clock. Will Delay 0, Keep Alive 2 s for demo; application heartbeat 500 ms, stale after 1,500 ms. These are configured demo values, not immediate-failure guarantees.

| Topic suffix | Schema model / publisher → subscribers | Retain |
|---|---|---|
| `member/{m}/status` | Status / member → coordinator, evidence | Yes, display hint only |
| `coordinator/status` | Status / coordinator → members, evidence | Yes, display hint only |
| `member/{m}/offer` | Offer / member → coordinator, evidence | No |
| `member/{m}/lease/request` | LeaseRequest / member → coordinator | No |
| `member/{m}/lease` | Lease / coordinator → that member, evidence | No |
| `member/{m}/lease/ack` | LeaseAck / member → coordinator, evidence | No |
| `member/{m}/meter` | MemberMeter / plant → member, coordinator, evidence | No |
| `member/{m}/plant/bind` | PlantBind / member → own plant | No |
| `member/{m}/plant/ceiling` | PlantCeiling / member → own plant | No |
| `member/{m}/plant/ack` | PlantAck / plant → own member, evidence | No |
| `member/{m}/plant/status` | Status / plant → member, evidence | Yes |
| `member/{m}/device/{d}/discovery` | DeviceDiscovery / plant → own member, demo evidence | Yes |
| `member/{m}/device/{d}/telemetry` | DeviceTelemetry / plant → own member, demo evidence | No |
| `member/{m}/device/{d}/command` | DeviceCommand / member → own plant | No |
| `member/{m}/device/{d}/ack` | DeviceAck / plant → own member, demo evidence | No |
| `event/capacity` | CapacityEvent / API control role → coordinator, evidence | No; durable control state is read on restart |
| `member/{m}/policy` | LocalPolicy / API control role → own member, evidence | No |
| `member/{m}/policy/ack` | PolicyAck / member → API evidence | No |
| `plan` | Plan / coordinator → evidence | Yes, proposed/issued intent only |

This adds member ID to device topics, replacing 06's site-global device namespace. Coordinator ACL allows aggregate topics only and grants/status/plan writes; member ACL allows own private topics and aggregate reports, no grant publish; plant ACL allows own observations/acks, no grant publish; evidence reads demo device topics with the explicit consent of seeded fictional households and cannot write; API control credential writes only capacity/policy. Credentials are role-specific demo credentials. Broker/admin and network confidentiality remain trusted; no TLS/privacy certification claim.

## Complete message models

Every model below includes E. A semicolon separates fields, not program statements. Parentheses specify cross-field constraints.

### Status — `truss.status.v1`

`component: coordinator|member|plant`; `component_id: ID`; `connection_id: UUID`; `source: heartbeat|will|graceful`; `state: starting|recovering|online|offline|at_floor|fault`; `member_id: Maybe(ID)`; `epoch: Maybe(Pos)`; `recovery_ms_remaining: Maybe(Ms)`; `registry_revision: Pos`; `reason: Maybe(Reason)`.

Coordinator requires epoch; other roles use null. Member ID is null only for coordinator. Recovery remaining is present only in recovering, 0–6,400. Will payload has source=will, state=offline, seq=0 because it is constructed at connection setup. Handle Will using matching **connection ID**, not sequence ordering; delayed Wills from older connections cannot overwrite a fresh connection. Retained status alone never makes observations fresh. Graceful offline uses a normal increasing seq.

### Offer — `truss.offer.v1`

`member_id: ID`; `member_boot_id: UUID`; `registry_revision: Pos`; `floor_w: W`; `firm_w: W`; `useful_w: W`; `deadline_energy_wh: Wh`; `deadline_in_ms: Maybe(Ms)`; `debt_wh: Wh`; `debt_revision: Nat`; `reported_curtailment_wh: Wh`.

`floor ≤ firm ≤ useful ≤ registered maximum`; floor must equal registered baseline. Deadline remaining is 0–86,400,000; positive energy requires nonnull remaining; zero energy requires null. This aggregate is advisory and not a feasibility certificate. `debt_wh` mirrors the last coordinator-authoritative service-deficit value/revision; it is **not** trusted as input without matching stored ledger. A mismatch is logged and stored authoritative debt is used. `reported_curtailment_wh` is explicitly member-reported diagnostic only. Remove device_count and wall `deadline_by` from the old offer. Member boot equals publisher boot. Coordinator accepts only monotonically newer offers within the admitted boot; boot change never clears watt reservations.

### LeaseRequest — `truss.lease_request.v1`

`member_id: ID`; `member_boot_id: UUID`; `request_id: UUID`; `request_seq: Pos`; `offer_seq: Nat`; `registry_revision: Pos`; `ttl_ms: integer exactly 6000`.

Member stores its local request-start Mono; **not transmitted upstream**. Coordinator requires the referenced validated offer from this member boot received fresh within 1,500 ms; if missing, it issues no grant and waits for the next request. Duplicate request may only reproduce an already reserved identical grant. A grant rejected due to latency is not reused for a later request. No request may be queued in the coordinator across recovery.

### Lease identity — nested `LeaseRef`

`member_id: ID`; `member_boot_id: UUID`; `request_id: UUID`; `epoch: Pos`; `version: Pos`; `lease_id: UUID`; `plan_id: ID`.

Version increases for every new grant within an epoch, including same-watt renewals. Counter scope is coordinator-wide, not per device. Epoch is durable monotonically increasing authority generation. Neither UUIDs nor counters are authentication by themselves.

### Allocation explanation — nested `Basis`

`snapshot_id: Hash`; `policy_hash: Hash`; `registry_revision: Pos`; `cap_revision: Pos`; `cap_w: W`; `measurement_reserve_w: W`; `external_bound_w: W`; `baseline_sum_w: W`; `surplus_pool_w: W`; `rule: equal_surplus|debt_weighted_surplus`; `debt_scale_wh: Wh`; `weight_cap: finite number exactly 2.0`; `member_floor_w: W`; `member_useful_w: W`; `member_debt_wh: Wh`; `member_weight: finite number [1,2]`; `proposed_budget_w: W`; `issued_budget_w: W`; `reservation_before_w: W`; `reservation_after_w: W`; `total_exposure_after_w: W`; `reason: Reason`.

Cap/sums represent the exact admission snapshot. Surplus pool is nonnegative for feasible plans. Issued amount matches the lease; it can be smaller than the current target because old other-member promises remain. No device/local decision detail belongs in Basis. Per-run cap and sums in live mode remain ≤100 kW; rejected over-cap proposals belong in an event, not a success Basis.

### Lease — `truss.lease.v1`

`ref: LeaseRef`; `registry_revision: Pos`; `budget_w: W`; `ttl_ms: exactly 6000`; `reason: Reason`; `basis: Basis`.

Member acceptance rules are in 18 and are part of this contract. IDs, registry and amount must agree throughout nested objects; `basis.issued_budget_w = budget_w`, registered floor ≤ budget ≤ maximum. One grant is immutable for its lease ID. No wall or coordinator Mono deadline is sent.

### LeaseAck — `truss.lease_ack.v1`

`ref: LeaseRef`; `result: Result`; `reason: Maybe(Reason)`; `accepted_budget_w: W`; `lease_ms_remaining: Ms [0,6000]`; `plant_confirmed: boolean`; `observed_w: Maybe(W)`; `observation_quality: Quality`; `plant_boot_id: Maybe(UUID)`.

Reject/expired require reason. Remaining is sampled on the member clock; it is display evidence, not reallocation permission. `applied` means member accepted authority, not that the plant necessarily received it. Device/plant observations independently determine compliance. Duplicate reply repeats effect/result evidence without changing deadlines; `result=duplicate` identifies repeated delivery. No ack frees a reservation in this MVP.

### PlantBind — `truss.plant_bind.v1`

`member_id: ID`; `member_boot_id: UUID`; `plant_boot_id: UUID`; `binding_id: UUID`; `clock_domain_id: ID`; `registry_revision: Pos`.

Clock domain identifies the host boot, agreed during launcher startup (hashed/sanitised to ID if necessary). Binding is accepted only by the target plant boot at baseline, or as idempotent repeat of current binding. A different member boot waits for the old ceiling to expire. Bind never raises output. Plant boot is learned from status/discovery, and must match before proceeding.

### PlantCeiling — `truss.plant_ceiling.v1`

`member_id: ID`; `member_boot_id: UUID`; `plant_boot_id: UUID`; `binding_id: UUID`; `clock_domain_id: ID`; `registry_revision: Pos`; `ref: LeaseRef`; `budget_w: W`; `expires_mono_ns: Mono`.

Deadline is the original member request-start +6 s in the shared local OS clock. A correct member must not invent/extend it; correct bridging is part of the trusted protocol. Plant checks recipient/binding/domain/version/range/deadline before applying. Changing budget and accepted reference is atomic. This same-host deadline exception is **not** a cross-house clock agreement. Distinct-host hardware would need its own request-anchored sublease protocol; that adapter is cut.

### PlantAck — `truss.plant_ack.v1`

`member_id: ID`; `plant_boot_id: UUID`; `binding_id: UUID`; `kind: bind|ceiling`; `ref: Maybe(LeaseRef)`; `result: Result`; `reason: Maybe(Reason)`; `active_budget_w: W`; `remaining_ms: Ms [0,6000]`; `observed_w: W`.

Bind has null ref; ceiling has nonnull ref. Rejection does not lower the reservation. Values are plant observations from its own emulator.

### MemberMeter — `truss.member_meter.v1`

`member_id: ID`; `plant_boot_id: UUID`; `clock_domain_id: ID`; `sampled_mono_ns: Mono`; `observed_w: W`; `active_budget_w: W`; `floor_w: W`; `active_ref: Maybe(LeaseRef)`; `lease_ms_remaining: Ms [0,6000]`; `at_floor: boolean`; `enforcement_state: healthy|fault`; `sample_seq: Nat`.

Sample sequence increases per plant boot; publisher boot equals plant boot. At-floor requires observed≤floor, null active_ref after expiry and remaining=0. Meter comes from the independent plant, not coordinator inference. Plant total can exceed expected authority only in explicit fault injection; report actual value and fault, never clamp observation to authority.

For the chosen own-PC profile, the evidence service shares the plant's OS clock
domain. It computes freshness from **sample time**, not arrival time. Delay of
all telemetry must not turn old measurements fresh merely because their seqs
increase. Reject future samples/domain mismatches for verification. Across
different hosts, do not subtract monotonic timestamps: quality remains unknown
unless a separately implemented request/response freshness probe bounds sample
age. That probe is outside this event's own-PC scope. Offers still use receipt
freshness as a demand hint; they cannot reduce reserved authority.

### DeviceDiscovery — `truss.device_discovery.v1`

`member_id: ID`; `device_id: ID`; `plant_boot_id: UUID`; `registry_revision: Pos`; `kind: light|router|heater|charger|washer|generic`; `label: Text`; `max_w: W`; `baseline_w: W`; `flexibility: protected|firm|deferrable|deadline`; `control_policy: protected|flexible|unclassified`; `priority: integer [0,100]`; `interruptible: boolean`; `min_run_ms: Ms [0,86400000]`; `min_off_ms: Ms [0,86400000]`.

Baseline≤maximum; sum baselines≤member floor. The primary fixture has interruptible flexible loads; nonzero minimum-run examples cannot bypass the plant ceiling. Retained discovery is metadata, not liveness.

Protected/unclassified control policy requires baseline=max_w for an admitted
profile, and forbids automated off/defer. A profile that cannot reserve that
amount is rejected before run start. See 22; no AI classification changes it.

### DeviceTelemetry — `truss.telemetry.v1`

`member_id: ID`; `device_id: ID`; `plant_boot_id: UUID`; `clock_domain_id: ID`; `sampled_mono_ns: Mono`; `state: idle|requested|running|deferred|completing|fault`; `observed_w: W`; `requested_w: W`; `remaining_energy_wh: Wh`; `deadline_in_ms: Maybe(Ms)`; `min_run_remaining_ms: Ms`; `min_off_remaining_ms: Ms`; `last_command_id: Maybe(UUID)`; `last_command_version: Nat`; `active_ref: Maybe(LeaseRef)`.

Telemetry every 500 ms doubles as heartbeat. Deadline hint uses the same nullable constraints as Offer. Discovery envelope bounds requested/observed values except explicit observed-fault reports. A missing sample is unknown, not zero.

Telemetry sample-time freshness follows MemberMeter's clock-domain rule.
Remaining deadline/minimum-run fields are aged by elapsed local sample time,
not restarted on message receipt. Reported lease remaining in UI is likewise
aged on the API's shared clock before transmission; the browser's subsequent
countdown still remains an estimate.

### DeviceCommand — `truss.command.v1`

`member_id: ID`; `member_boot_id: UUID`; `device_id: ID`; `plant_boot_id: UUID`; `binding_id: UUID`; `command_id: UUID`; `command_version: Pos`; `ref: Maybe(LeaseRef)`; `desired_state: idle|running|deferred`; `desired_w: W`; `clock_domain_id: ID`; `expires_mono_ns: Mono`; `reason: Reason`; `decision: LocalDecision`.

Command version is monotonic per device within binding; not the lease version. Desired idle/deferred means desired_w=0 (baseline distribution is independently applied by plant policy); running must fit device maximum and aggregate ceiling. Commands with null ref cannot authorise above-baseline operation. A command may never extend the plant ceiling or exceed its lifetime; expired commands are rejected even with a higher version. Replace ambiguous old `expires_at_ms` with explicit same-host Mono deadline.

**LocalDecision:** `decision_id: UUID`; `member_id: ID`; `device_id: ID`; `ref: Maybe(LeaseRef)`; `offer_seq: Nat`; `requested_w: W`; `assigned_w: W`; `member_budget_w: W`; `reserved_local_baseline_w: W`; `higher_priority_assigned_w: W`; `reason: Reason`; `deadline_status: none|pending|missed|unknown`; `deadline_in_ms: Maybe(Ms)`.

No `still_satisfiable` claim without a real scheduler. Decision links to aggregate Basis via ref; inspector combines them in the evidence service. The member's device list does not travel in the lease.

### DeviceAck — `truss.ack.v1`

`member_id: ID`; `device_id: ID`; `plant_boot_id: UUID`; `binding_id: UUID`; `command_id: UUID`; `command_version: Pos`; `ref: Maybe(LeaseRef)`; `result: Result`; `reason: Maybe(Reason)`; `observed_state: DeviceTelemetry.state`; `observed_w: W`.

Reject/expired require reason. Repeat delivery returns a cached acknowledgement with duplicate result and fresh envelope sequence, no second state transition. The old “exactly one acknowledgement” requirement is removed.

### CapacityEvent — `truss.capacity.v1`

`event_id: UUID`; `operation_id: UUID`; `cap_revision: Pos`; `expected_previous_revision: Pos`; `cap_w: W`; `source: operator|fixture`; `reason: cap_change|simulated_fault`.

Immediate replacement cap, persists until superseded. No scheduled wall-time start/end or automatic restore in the MVP. API durably commits desired cap and operation before publish; coordinator loads that desired state on restart, so a lost event cannot restore an obsolete cap. Repeated event ID has no second effect. This is Truss capacity JSON; no OpenADR compatibility label.

### LocalPolicy — `truss.local_policy.v1`

`operation_id: UUID`; `member_id: ID`; `device_id: ID`; `policy_revision: Pos`; `protected: boolean`.

Means local priority preference, not baseline increase. Fixed baseline devices cannot be unprotected in this build. Member accepts only if the requested setting can be represented within fixed policy; otherwise records rejected operation with policy_conflict. No automatic baseline mutation.

### Plan — `truss.plan.v1`

`plan_id: ID`; `snapshot_id: Hash`; `policy_hash: Hash`; `registry_revision: Pos`; `cap_revision: Pos`; `epoch: Pos`; `status: proposed|admitted|waiting_release|infeasible|vetoed`; `rule: equal_surplus|debt_weighted_surplus`; `cap_w: W`; `measurement_reserve_w: W`; `external_bound_w: W`; `baseline_sum_w: W`; `deficit_w: W`; `affected_members: list[ID]`; `allocations: list[AllocationRow]`; `validation: ValidationResult`; `timing: StageTiming`.

**AllocationRow:** `member_id: ID`; `floor_w: W`; `useful_w: W`; `debt_wh: Wh`; `weight: number [1,2]`; `target_w: Maybe(W)`; `issued_w: Maybe(W)`; `reserved_w: W`; `latest_ref: Maybe(LeaseRef)`; `reason: Reason`.

**ValidationResult:** `valid: boolean`; `codes: list[Reason]`; `exposure_w: W`; `limit_after_reserves_w: Maybe(W)`.

**StageTiming:** `input_validation_ms`, `allocation_ms`, `plan_validation_ms`, `admission_ms`: each finite nonnegative number or null. Null means not executed/measured. Infeasible has no invented target or issued grants; allocations still show current reservation/floor exposure. Status proposed must never be rendered as applied.

### PolicyAck — `truss.policy_ack.v1`

`operation_id: UUID`; `member_id: ID`; `device_id: ID`; `policy_revision: Pos`; `result: applied|rejected|duplicate`; `reason: Maybe(Reason)`; `protected: boolean`.

Rejected requires a reason; protected reports the effective local priority flag,
not a new registered baseline. API completes the corresponding protect operation
only on this matching acknowledgement. Missing ack leaves it pending until a
3 s timeout marks failed/timeout; a late ack is recorded as late evidence and
reconciles the displayed effective policy without issuing the operation again.
On member restart, boot/request identity changes; API resends the last durable
desired local policy with its original operation ID for reconciliation. Member
deduplicates policy revision/ID. The mandatory `control_policy` additions in 22
cannot be changed through LocalPolicy.

## Internal shared records (also Pydantic specifications)

These are not additional MQTT message variants.

**RunPolicy:** run/site IDs; registry_revision; policy_hash; cap_revision; cap_w; fixed/external reserves; ttl_ms=6000; renew_ms=2000; hold_ms=6400; drift_bound=0.001; enforcement_bound_ms=250; heartbeat_ms=500; stale_ms=1500; debt_scale_wh=10; debt_max_wh=20; enabled_rule; `members: list[MemberRegistration]`. Every numeric field uses its above type and is validated once, frozen during run except cap/debt/rule selection through declared controls.

**MemberRegistration:** `member_id: ID`; `floor_w: W`; `max_w: W`; `host_id: ID`; `baseline_revision: Pos`. Require floor≤maximum. House device profiles live in separate member files, **not this coordinator registry**.

**PlannerSnapshot:** snapshot_id; policy_hash; cap_revision; cap_w; reserves; ordered list of validated Offers plus authoritative debt and received age; registered baselines for absent members. Missing offers get useful=floor for proposal purposes but reservations remain separately accounted. No devices or arbitrary model output.

**ReservationRecord:** ref; member_id; amount_w: W; received_mono_ns: Mono; release_mono_ns: Mono; published: boolean. Both times coordinator-local. Release must be at least hold_ms after receipt; reservation insertion precedes publish. Purged after safe expiry, retaining request high-water metadata.

**EventRecord:** `run_id: UUID`; `event_seq: Pos`; `received_at: UTC`; `received_mono_ns: Mono`; `kind: message|validation|allocation|admission|expiry|fault|operation|gap`; `topic: Maybe(string ≤256)`; `payload_schema: ID-compatible schema string ≤64`; `payload: one of the exact message/internal event models`; `correlation_id: Maybe(UUID)`. Internal event payload: `code: Reason`, `member_id: Maybe(ID)`, `ref: Maybe(LeaseRef)`, `operation_id: Maybe(UUID)`, `detail: Text`. Global event_seq belongs to the evidence writer, not the broker. Append-only; truncated final line is recoverable and disclosed as a gap.

## REST contract

Chosen origin: built Vite assets and API on one FastAPI origin, port 8000. During development Vite 5173 proxies `/api` and `/ws`; mock uses the same proxy target switched by one environment setting. Browser never connects to MQTT. LAN host is explicit. No cloud/CDN fonts, assets, model API or analytics.

All responses JSON except event export; `Cache-Control: no-store`; UTF-8; `/api/v1` namespace. Request body maximum 16 KiB. Errors have `{error: {code: ErrorCode, message: Text, fields: list[FieldError], request_id: UUID, retryable: boolean}}`; FieldError = `{path: string ≤128, code: string ≤64, message: Text}`. No stack traces/credentials.

**ErrorCode:** `invalid_request`, `not_found`, `revision_conflict`, `idempotency_conflict`, `unsupported`, `read_only`, `busy`, `dependency_unavailable`, `timeout`, `internal_error`. Status: 400 malformed/unknown variant; 422 field validation; 404 missing resource; 409 revision/idempotency conflict; 403 read-only/source restriction; 429 bounded job busy; 503 unavailable; 500 unexpected failure. NotImplemented features return 409 unsupported and capability=false; never success with no effect.

Every mutating POST requires `Idempotency-Key: UUID` and body `run_id: UUID`, `expected_control_revision: Nat`; control writes also require `source=live` when applicable. Same key+canonical body returns the original operation, including after timeout/restart; different body with same key returns 409. Store keys for entire run in authority SQLite. No automatic retry with a new key. Expected revision guards changes from two browser tabs. POST success means **accepted**, not physically applied.

**Operation:** `operation_id: UUID`; `run_id: UUID`; `kind: cap|protect|chaos|rule|replay|lab`; `status: queued|running|applied|rejected|failed`; `control_revision: Nat`; `created_at: UTC`; `finished_at: Maybe(UTC)`; `error: Maybe(ErrorCode)`; `message: Maybe(Text)`; `result_id: Maybe(UUID)`. Acceptance HTTP 202 returns Operation plus Location `/api/v1/operations/{id}`. Completion appears via snapshot operations and GET. Cap operation is applied when the coordinator accepts the desired cap, **not** when measured load settles.

Coordinator reads the durable desired cap/rule revision on startup and each
500 ms control tick, in addition to handling capacity notifications. It commits
the matching cap/rule operation result when adopted. Lost MQTT control delivery
therefore cannot strand a committed cap change forever while the coordinator
is healthy. Protect completion uses PolicyAck; chaos completion uses the
supervisor's ActionResult; replay/lab completion uses their job records. API
never infers completion merely from a successful MQTT publish.

| Method / route | Exact input beyond common POST fields | Output / semantics |
|---|---|---|
| GET `/health` | None | `{api: ok|degraded, broker: connected|disconnected, coordinator: online|recovering|offline|unknown, run_id: Maybe(UUID), evidence: ok|gap|unavailable, capabilities: Capabilities}`; 200 API alive, 503 API unable to serve state. Offline coordinator alone is a valid demo state. |
| GET `/state` | `source=live|mock|replay` default live; `replay_id: UUID` required for replay | Snapshot exactly as below, current full replacement. 404 unknown replay, no fallback to live. |
| GET `/events` | run_id, `after_seq: Nat` default 0, `limit: integer 1–500` default 100 | `{run_id, items: list[EventRecord], next_after_seq: Nat, has_more: boolean, gap: boolean}`; ordered, exclusive cursor. |
| GET `/operations/{operation_id}` | UUID path | Operation; 404 if absent. |
| POST `/cap` | `watts: W`; `source: literal live` | CapacityEvent via durable desired state; complete snapshot may remain transitioning/infeasible. |
| POST `/protect` | `member_id: ID`, `device_id: ID`, `protected: boolean`, source=live | Local priority within fixed baseline policy; rejects conflict; never implicitly increases floor. |
| POST `/chaos` | `fault: FaultSpec`, source=live | Managed demo process/fault action only. Never arbitrary shell text or PID. |
| POST `/rule` | `rule: equal_surplus|debt_weighted_surplus`, source=live | Switch policy only if capability enabled; increments revision and snapshots policy. Old grants remain reserved. `cpsat`/`uncoordinated` are unsupported in live mode. |
| POST `/replays` | `recorded_run_id: UUID`, `from_seq: Nat`, `speed: literal 1` | Creates separate read-only replay ID; does not stop/change live run. |
| POST `/replays/{id}/seek` | `from_seq: Nat` | Seek replay cursor only, exact event boundary; operation result_id is replay ID. |
| GET `/export` | `run_id: UUID` | `application/x-ndjson`, attachment `truss-{run_id}.jsonl`; event records; no ZIP. |
| POST `/lab/runs` | `experiment: members|devices`, `seed: Nat`, `rule: equal_surplus|debt_weighted_surplus`, `cap_ratio: number [0,1]` | Isolated benchmark job; never topology mutation or live grants. Ratio scales available surplus relative to aggregate demand after floors. |
| GET `/lab/runs/{id}` | UUID path | LabResult below, running progress or final; no fabricated missing points. |

Table paths are relative to `/api/v1`. The previous `/api/topology`, `/api/bundle` and singular `/api/replay` are deliberately replaced; do not implement undocumented aliases. The three frontend routes still exist.

**Capabilities:** booleans `protect`, `debt_weighting`, `chaos`, `replay`, `lab`; `max_live_members: integer 1–5`; `max_lab_members: integer 1–5000`; `cpsat: literal false`; `hardware: literal false`. The optional AI capability was removed at the user's request on 6 September 2026. UI disables unavailable actions and states why.

**FaultSpec**, discriminated by action: `kill_coordinator`, `restart_coordinator`, `kill_member`, `restart_member`, `stop_member`, `resume_member`, `partition_member`, `drop_acks`, `delay_telemetry`, `clear_faults`. Member actions require member_id; others use member_id=null. All carry `duration_ms: Ms [0,30000]`, `rate: Maybe(number [0,1])`, `delay_ms: Maybe(Ms [0,5000])`. Partition/stop require duration 1–30,000 and automatic restoration by supervisor; drop_acks requires rate, duration; delay_telemetry requires delay and duration; kill/restart/resume/clear use duration=0 and rate/delay=null. Partition suppresses that member's send/receive application delivery paths in the owned transport shim; it is labelled **application-message partition**, not a claim of kernel-level isolation. Delay/drop never touch the plant's local expiry clock. Broker kill is a manual rehearsal action, not a fifth judge control.

## Snapshot contract — one model shared by REST, WS and mock

**Snapshot:** `schema: truss.ui_snapshot.v1`; `run_id: UUID`; `stream_id: UUID`; `revision: Nat`; `control_revision: Nat`; `source: live|mock|replay`; `replay_id: Maybe(UUID)`; `generated_at: UTC`; `event_cursor: Nat`; `site: SiteView`; `members: list[MemberView]`; `events: list[EventView]` (latest 50 ordered ascending); `operations: list[Operation]` (latest 20); `metrics: MetricsView`; `capabilities: Capabilities`.

Revision is strictly increasing per stream when a new snapshot is emitted. Stream ID changes after API restart or replay seek. Run ID identifies a seeded live run and survives coordinator restart. Replay ID is nonnull only for replay. Mock is never labelled live.

**SiteView:** `id: ID`; `cap_w: W`; `cap_revision: Pos`; `measurement_reserve_w: W`; `external_bound_w: W`; `baseline_sum_w: W`; `reserved_member_w: W`; `unverified_member_reservation_w: W`; `available_for_new_grants_w: W`; `exposure_w: W`; `observed_w: Maybe(W)`; `observed_quality: Quality`; `oldest_sample_age_ms: Maybe(Ms)`; `state: starting|recovering|leased|cap_transition|infeasible|unverified`; `coordinator_status: online|recovering|offline|unknown`; `recovering_ms_remaining: Maybe(Ms)`; `compliance: within_cap|over_cap|unknown`; `deficit_w: W`; `affected_members: list[ID]`; `rule: equal_surplus|debt_weighted_surplus`; `plan_id: Maybe(ID)`; `timing: StageTiming`.

`exposure = reserved_member + measurement_reserve + external_bound`; `available=max(0,cap−exposure)`; `unverified_member_reservation` is a **subset** of reserved_member. It is not added again. Site observed is null unless all registered plant meters are fresh; stale last values remain per member. No observed cap-compliance green from allocated/desired watts. Offline coordinator can coexist with fresh verified at-floor observations.

**MemberView:** `id: ID`; `boot_id: Maybe(UUID)`; `plant_boot_id: Maybe(UUID)`; `floor_w: W`; `max_w: W`; `firm_w: W`; `useful_w: W`; `target_w: Maybe(W)`; `issued_w: Maybe(W)`; `reserved_w: W`; `observed_w: Maybe(W)`; `observed_quality: Quality`; `sample_age_ms: Maybe(Ms)`; `debt_wh: Wh`; `reported_curtailment_wh: Maybe(Wh)`; `weight: number [1,2]`; `lease: LeaseView`; `status: joining|ok|stale|offline|at_floor|fault`; `devices: list[DeviceView]`; `device_visibility: demo_observer|hidden`; `basis: Maybe(Basis)`.

**LeaseView:** `ref: Maybe(LeaseRef)`; `remaining_ms: Maybe(Ms [0,6000])`; `sample_age_ms: Maybe(Ms)`; `quality: Quality`; `plant_confirmed: boolean`. Remaining comes from latest plant meter where available, otherwise member ack marked unconfirmed. No cross-host deadline is exposed. A stale countdown may reach displayed zero as an **estimate**, never as proof of applied floor. At-floor comes only from fresh plant evidence.

**DeviceView:** `id: ID`; `kind: DeviceDiscovery.kind`; `label: Text`; `w: Maybe(W)`; `requested_w: W`; `state: DeviceTelemetry.state|unknown`; `quality: Quality`; `sample_age_ms: Maybe(Ms)`; `ack: pending|applied|verified|rejected|stale|none`; `protected: boolean`; `deadline_in_ms: Maybe(Ms)`; `deadline_status: none|pending|missed|unknown`; `command_id: Maybe(UUID)`; `decision: Maybe(LocalDecision)`.

Also required by 22: `control_policy: protected|flexible|unclassified`;
`curtailment_eligible: boolean`. Eligibility is true only for flexible policy.
The legacy `protected` boolean is a local priority flag and is always true for
protected/unclassified policy; UI shows the stronger policy explicitly.

Verified means matching command acknowledgement plus fresh telemetry consistent with it, not merely a sent command. A pending command becomes stale/unverified after 1,500 ms; late matching evidence can restore verification but cannot rewrite original timeout event.

**EventView:** `seq: Pos`; `at: UTC`; `kind: string from EventRecord.kind`; `code: Reason`; `text: Text`; `member_id: Maybe(ID)`; `device_id: Maybe(ID)`; `plan_id: Maybe(ID)`; `correlation_id: Maybe(UUID)`.

**MetricsView:** `observation_window_ms: Ms`; `eligible_samples: Nat`; `within_cap_samples: Nat`; `unknown_samples: Nat`; `cap_compliance_pct: Maybe(number [0,100])`; `time_to_safe_ms: Maybe(Ms)`; `time_to_safe_status: pending|observed|timeout|infeasible|unknown`; `lease_model_violations: Maybe(Nat)`; `issued_commands: Nat`; `applied_commands: Nat`; `ack_success_pct: Maybe(number [0,100])`; `jain_service_ratio: Maybe(number [0,1])`; `fairness_sample_count: Nat`; `max_enforcement_lateness_ms: Maybe(Ms)`; `replay_gaps: Nat`.

Percent compliance uses complete fresh samples only, after the declared transition window; report unknown count next to it. Undefined denominators yield null. Time-to-safe requires a **continuous 1 s fresh within-cap window** after the cap event; report its first sample latency only once the window completes. If already below cap, require fresh post-event evidence, not a carried-forward sample. Infeasible is not zero seconds. `lease_model_violations` is null in live operation unless an actual complete authority oracle is running; sampled telemetry cannot claim it observed every instant. Jain uses nonzero requested flexible energy denominators and at least two participating members; label it diagnostic. Deadline satisfaction is cut until there is a job-completion model.

**LabResult:** `id: UUID`; `status: queued|running|complete|failed`; `experiment`; `seed`; `rule`; `progress: number [0,1]`; `environment: {cpu: Text, os: Text, python: Text, implementation_hash: Hash, timer: Text}`; `points: list[LabPoint]`; `error: Maybe(ErrorCode)`.

**LabPoint:** `members: Pos`; `devices_per_member: Maybe(Pos)`; `batch: integer [1,3]`; `warmups: literal 20`; `samples: list[finite nonnegative number]` in milliseconds, length≤200; `median_ms: Maybe(number)`; `p95_ms: Maybe(number)`; `max_ms: Maybe(number)`; `aggregation_ms: Maybe(number)`; `offer_bytes: Nat`; `invalid_samples: Nat`; `cap_w: Nat`; `baseline_w: Nat`; `distribution: all_saturated|none_saturated|staggered`; `timer_overhead_ms: finite nonnegative number`. Report summaries only after a complete batch; retain all raw samples. Lab tests cannot publish MQTT.

## WebSocket contract

Endpoint `/ws/v1/state?source=live|mock|replay&replay_id=...`. Subprotocol `truss.ui.v1`. Server accepts read-only state streams; **all controls remain REST**, avoiding two command implementations.

Frame tagged by `type`:

- `hello`: `{type, schema: truss.ws.v1, stream_id: UUID, run_id: UUID, source, heartbeat_ms: 1000, snapshot_hz: 4}`.
- `snapshot`: `{type, data: Snapshot}`. Full replacement at most four times per second, including on initial connection. Never apply as a patch.
- `ping`: `{type, id: UUID}`. Client replies `{type: pong, id: UUID}`. No other client frames are supported. Control attempts close 1008.
- `error`: `{type, error: error-envelope.error}`. Wrong protocol closes 1002, oversize (>512 KiB) 1009, server exception 1011, slow consumer 1013.

Keep one pending latest snapshot per connection; coalesce older snapshots rather than queue forever. Events are independently cursor-readable from REST. Close if no pong for 5 s. Client treats no snapshot for 1,500 ms as stale, starts 1 Hz REST polling after WS close or 2 s without snapshots, and reconnects after 0.5, 1, 2, 4, then 5 s with ±20% jitter. One poll at a time, timeout 2 s; retain stale state if both paths fail. When WS delivers a valid newer snapshot, stop polling. No success/green on retained browser state.

Ordering: accept only increasing revision within one stream. A stream change replaces state atomically and resets revision tracking; never merge members/events across runs or sources. During reconnect, first obtain a fresh Snapshot; fetch missing events after stored cursor if needed. Cursor gap triggers explicit gap label; do not manufacture lost events.

Lease animation uses browser `performance.now()` relative to frame receipt and reported remaining; it is an approximate countdown because transit time is unknown. Show `~` or “estimated” in tooltip, and grey it when stale. Browser time never decides floor compliance, initiates grants or moves device state to verified. Resynchronise on each valid snapshot; honour reduced-motion settings.

## Mock required by hour 2; live swap by hour 12

M5 builds the mock against this contract, not a static screenshot. It serves the same REST routes/errors and WS frames, idempotency and revision behaviour. M4 can start using a hand-authored full snapshot at hour 1 while M5 implements transport; neither waits for allocator code.

The frozen 90 s script: 0–10 normal; 10 cap drop with target/issued/reserved disagreement; 10–17 transition; 17–25 verified reduction; 25–35 missing ack with fresh watts; 35–45 member stopped but plant expires; 45–58 coordinator dead with fresh plants; 58–65 recovery; 65–75 impossible cap and real red overload; 75–82 stale all meters with null total; 82–90 restored run. Each frame is marked mock. Also provide named fixtures for zero members, new join, equal offers, null metrics, rejected protection, corrupt frame, stale retained status, duplicate/lower revision, new stream ID, REST 409/422/503, WS disconnect, polling recovery, replay gap and partial lab result.

Controls in mock change the mock scenario only; no process kill, broker connection or live publish. No tests or fixture generators are written before the event. The specification of each fixture and expected state is the deliverable here.
