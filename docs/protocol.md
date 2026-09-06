# Current backend contract

This is the executable contract for the deterministic non-AI backend. It refines [plan 20](../plans/20-contracts.md) with the lease repair in [18](../plans/18-protocol-repair.md) and protected-load policy in [22](../plans/22-sglang-and-protected-loads.md). AI/SGLang were removed at the user's request.

Backend additions and their full request/response fields are specified in [backend extensions](backend-extensions.md). Claude owns the frontend; these are backend contracts, not claims about which UI controls are integrated.

## Wire schemas and authority

All 17 MQTT variants are immutable strict Pydantic models in `schemas.py`. The complete field set, discriminators, ranges, nullable fields and cross-field examples are in [mqtt.schema.json](../fixtures/mqtt.schema.json), [wire-valid.json](../fixtures/wire-valid.json) and [wire-invalid.json](../fixtures/wire-invalid.json). Shape validation rejects unknown fields, duplicate JSON keys, nonfinite numbers, booleans/numeric strings as watts, and oversized payloads. Monotonic nanoseconds are decimal strings, never JavaScript floats. UTC timestamps are for display/evidence, not expiry decisions.

`decode(bytes)` checks shape; `validate_delivery(topic,bytes,role)` checks topic/publisher identity and coordinator privacy; broker ACLs constrain who may publish/receive each topic. Process receivers additionally check run, registry, boot, binding, request/ref and version. The coordinator never reads private profiles/device topics; the separately privileged demo observer can show fictional device details. This is household-boundary privacy, not differential privacy.

Lease budget is total household watts, including its fixed baseline. TTL is exactly 6000 ms anchored before the member sends its request. Duplicate delivery never resets the deadline. Coordinator retains each possible grant for at least 6400 ms after admission, including failed publication. Exposure is the per-member maximum of baseline and still-possible grants, plus site reserves. A lower new grant does not cancel an old grant. Every coordinator boot claims a durable epoch and starts the entire recovery wait again.

Protected and unclassified devices reserve their full admitted maxima throughout the run. Only flexible devices yield. A physical cap below baselines plus reserves is infeasible. The plant trusts the member to bridge a genuine grant and its original request deadline; this is not Byzantine-member protection. Admission/expiry logic, not a model or browser, governs power.

## HTTP

Base `/api/v1`; local JSON only. `truss live --port 8001` provides live state; `truss mock --port 8000` provides synthetic state. Both listen on loopback by default. Vite's current proxy points to 8000. No production login/TLS/multi-worker operator layer is claimed. All responses use `Cache-Control: no-store`. Swagger/ReDoc CDN pages are disabled; `/openapi.json` remains available locally.

| Request | Input | Success / failure |
|---|---|---|
| `GET /health` | none | 200 `{api,broker,coordinator,mode,run_id,evidence,capabilities}`. mode is live/mock/unwired. Live broker/coordinator values reflect observed connection/status; evidence can be unavailable after a known gap. |
| `GET /state` | `source=live` or `source=mock`; default live | 200 complete Snapshot; 403 mismatched source; 503 if no provider |
| `POST /cap` | `{run_id:UUID,source,expected_control_revision:Nat,watts:W}` | 202 Operation plus Location. Live: desired cap committed durably; this does not assert immediate compliance. |
| `POST /chaos` | common control fields plus `action`, `member_id:ID|null` | 202 Operation. Live action operates on an actual owned child; mock action changes synthetic state. |
| `GET /operations/{id}` | ID from response | 200 Operation or 404 |
| `GET /events` | `after_seq=0` default | 200 `{items:EventView[],gap:boolean}`; visible event tail, at most 500. It is not the full JSONL log. |
| `POST /lab/benchmark` | `{members:integer 1..5000,seed:Nat}` | 200 measured BenchmarkResult through an isolated subprocess on live/mock; 429 busy; 503 worker failure |
| Other POST paths | no implemented feature | 409 unsupported; no invented success |

Live chaos actions: `kill_coordinator`, `restart_coordinator`, `kill_member`, `restart_member`, `kill_broker`, `restart_broker`. Member actions require a registered member_id; other actions use null. Mock actions: `kill_coordinator`, `restart_coordinator`, `stale_member`, `clear_faults`. Mock stale_member requires a known member; otherwise use null. Bounded partition/delay scenarios are available to backend tests through `TrussRun.set_fault(target,action,duration_ms,delay_ms,rate)`, also exposed through the typed `/faults` endpoint described in the extension contract. Only one fault spec is active at a time, maximum duration 30 seconds and message delay 10 seconds.

Cap/rule/chaos/fault controls require `Idempotency-Key: UUID`. Same key and parsed body/kind returns the original operation; same key/different input returns 409 idempotency_conflict. New key with wrong run/revision returns 409 revision_conflict. Do not auto-reapply a stale draft. Live keys and operations persist in run SQLite; mock keys are memory-only. Live cap revision/control acceptance and operation insert commit together. Coordinator reads cap under the same SQLite write-serialization boundary as admission; the transaction ends before network publication. A separate restricted API publisher emits CapacityEvent after commit as a best-effort notification. Lost notification does not lose the accepted cap; the coordinator reads the durable record.

Live chaos first durably records queued, then performs the actual child action, then records applied/failed. A crash between those steps can leave queued; a retry returns that record and does not blindly repeat the action. Reconcile against the manifest/process state. Applied restart means a new process was launched, not that its recovery wait is complete.

Other new implemented POST routes (`/rule`, `/faults`, `/replays`, `/lab/runs`) and their response types are defined in the extension contract.

Operation fields: operation_id, run_id, kind, status, control_revision, created_at, finished_at, error, message, result_id. Nullable fields serialize as null. Status is queued/running/applied/rejected/failed. `GET /operations` is not an implemented list route; recent operations are in Snapshot.

Errors use `{error:{code:string,message:string,fields:[],request_id:UUID,retryable:boolean}}`. Expected statuses: 400 malformed Content-Length; 403 wrong source; 404 not found; 409 conflict/unsupported; 413 declared body over 16 KiB; 422 invalid input; 429 busy; 503 unavailable. Streamed bodies are also limited to 16 KiB and duplicate/nonfinite JSON is rejected. Production authentication is not implemented; this is a local fictional operator service. Input constraints and success models are generated in [openapi.json](../fixtures/openapi.json); this document specifies custom errors and WebSocket frames.

## Snapshot and freshness

[snapshot.schema.json](../fixtures/snapshot.schema.json) is the complete nested contract. Snapshot includes schema, run_id, stream_id, revision, control_revision, source, replay_id, generated_at, event_cursor, site, members, events, operations, metrics, capabilities. The primary state/WS provider serves live/mock. Separate replay sessions return historical Snapshots with source=replay through `/replays/{id}` and support seek/play/pause; they do not change the primary provider. AI capability fields were removed, not left disabled.

Live observed wattages come from independent plant reports. The observer uses their source monotonic sample time and shared Linux boot domain, not merely receipt age. Samples older than 1500 ms, from another clock domain, from a retired boot or from a faulted plant cannot verify compliance. Complete fresh member readings are required for site observed_w; otherwise it is null. Stale per-device/member values may remain with quality and age explicitly stale.

Household devices declare `actuation`: `modulating` accepts any setpoint between baseline and maximum, `binary` reaches only those two. A binary device whose whole step exceeds the remaining budget is skipped in priority order and a lower-priority device may still fit; a partial step is never commanded. The watts a household is permitted but cannot reach are reported as `unusable_w` on the member and summed on the site. This never raises draw and never relaxes a floor, so cap, lease and reservation semantics are unchanged.

Proposed, issued, reserved and observed values are different facts. Live reserved watts conservatively include possibly outstanding grants; observer startup/reconnection can temporarily reserve full registered maxima. A cap drop can show exposure above cap during transition. Do not replace this with a green observed bar. Cap below floors+reserves stays infeasible and reports deficit/affected members.

Lease.remaining_ms is a sample-age-adjusted display estimate. `plant_confirmed` requires a fresh independent report. Device `ack=verified` requires matching command/ack/telemetry IDs, grant refs, observed watts and freshness. Basis/LocalDecision may be null; only matched references support a causal explanation. New live runs start with equal_surplus; `/rule` can select authoritative service-deficit weights. Fresh Plan rows carry actual credit/weight. `/fairness` exposes the last durable checkpoint and any disabled accounting state. Neither is measured curtailment energy.

Compliance metrics use complete fresh samples; missing denominators are null. The current compliance percentage is a diagnostic across collected fresh observations, including cap transitions, not a post-settling safety theorem. Time-to-safe is measured after an observed cap change using complete fresh post-change reports; it is not coordinator-kill latency. A broker disconnect records an explicit observation gap. Real process kill timing is established by the integration tests and plant samples, not by a UI timer.

## WebSocket

URL `/ws/v1/state?source=live` (or mock), required subprotocol `truss.ui.v1`. Text JSON only. Wrong source, absent provider or missing subprotocol closes with 1008.

1. Server: `{type:"hello",schema:"truss.ws.v1",stream_id,run_id,source,heartbeat_ms:1000,snapshot_hz:4}`.
2. Server every second: `{type:"ping",id:UUID}`. Client: `{type:"pong",id:same UUID}`. Invalid replies or five seconds without pong close the connection.
3. Server up to four times per second: `{type:"snapshot",data:Snapshot}`. Whole snapshot replaces state atomically; revision increases within stream. Control revision changes on accepted operations only.
4. Two-second send timeout; no final frame guaranteed. Reconnect obtains a new complete snapshot; no delta/resume cursor.

Client rejects wrong source and older/equal revision in its stream. A new stream can reset revision. Mark stale around 1.5 seconds without updates and disable controls. Poll state once per second after WS updates have been absent for two seconds; reconnect with bounded jitter/backoff. An old poll must not replace a newer WS update. Current TS guard is lightweight validation for the trusted local server; use the generated schema before ingesting untrusted external producers.

## Mock and lab handoff

Run mock without broker/control processes. Checked fixtures cover initial baseline, leases, stale member, offline coordinator, recovery and infeasible cap. Mock never supplies live compliance/time-to-safe evidence. Future replay/device-fault/operation-pending cases need explicit additional fixtures before UI claims them.

BenchmarkResult is `{members,seed,samples_ms,complete,median_ms,p95_ms,python,os,timer,scope,warmups}`. It measures the actual pure allocator over synthetic inputs: 20 warmups, up to 200 samples, a 10-second sample-loop budget excluding warmup and an already-running iteration. Browser timeout is 15 seconds; it does not terminate an in-progress Python thread. No live workload, MQTT timing, job persistence or flat-latency claim. Live capability remains false.

Regenerate contracts with `.venv/bin/python scripts/build_fixtures.py`. Authority changes need M1 plus producer/consumer review; presentation changes need backend/frontend agreement. Keep source isolation and null semantics intact.
