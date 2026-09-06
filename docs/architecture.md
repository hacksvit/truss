# Concrete architecture and file map

Generated from the event checkout by `scripts/build_inventory.py`. This inventories implementation files; the historical `plans/` and `research/` remain the decision/evidence archive. Runtime artifacts, dependencies, caches and the ignored private `pleaseread.md` are excluded from the versioned inventory. Start work from [BUILD_PLAN](../BUILD_PLAN.md), and check [implementation status](implementation-status.md) for evidence versus pending work.

Process separation: supervisor owns Mosquitto, coordinator, five members and five plants; API/evidence observes MQTT in its own process. Pure cores remain separate from `_process.py` adapters. This adds adapter files to plan 19 rather than mixing transport and deterministic arithmetic. Cost: several small lifecycle modules; benefit: unit tests stay independent of broker/process setup.

The frontend tree and state ownership remain as specified in [plan 19](../plans/19-build-map.md). Source of state is the backend Snapshot; browser timers animate presentation only. REST/WS contracts are in [protocol](protocol.md).

## Every implementation file

| File | Owner | Purpose |
|---|---|---|
| [`.gitignore`](../.gitignore) | M2 | Exclude local explanation, credentials, dependencies and run artifacts |
| [`BUILD_PLAN.md`](../BUILD_PLAN.md) | M5 | Build order — start here |
| [`README.md`](../README.md) | M5 | offline startup, limits, demo and evidence entry point |
| [`config/acl`](../config/acl) | M3 | role/topic boundaries, especially coordinator privacy |
| [`config/member-a.json`](../config/member-a.json) | M2 | A's four private virtual-device profiles and baselines |
| [`config/member-b.json`](../config/member-b.json) | M2 | B's four private virtual-device profiles and baselines |
| [`config/member-c.json`](../config/member-c.json) | M2 | C's four private virtual-device profiles and baselines |
| [`config/member-d.json`](../config/member-d.json) | M2 | D's four private virtual-device profiles and baselines |
| [`config/member-e.json`](../config/member-e.json) | M2 | E's four private virtual-device profiles and baselines |
| [`config/mosquitto.conf`](../config/mosquitto.conf) | M5 | Build/configuration artifact; interface defined by consuming module |
| [`config/run.json`](../config/run.json) | M1 | fixed site registry, caps, timing and policy; no device lists |
| [`docs/architecture.md`](../docs/architecture.md) | M5 | Concrete architecture and file map |
| [`docs/backend-extensions.md`](../docs/backend-extensions.md) | M5 | Backend extension handoff — 6 September 2026 |
| [`docs/contributions.md`](../docs/contributions.md) | All | honest file ownership and review record |
| [`docs/demo.md`](../docs/demo.md) | M5 | three-minute live and fallback scripts |
| [`docs/esp32-display.md`](../docs/esp32-display.md) | M5 | Optional ESP32 status screen |
| [`docs/evidence.md`](../docs/evidence.md) | M5 | test/run hashes, counts, gaps and measured results |
| [`docs/frontend-handoff.md`](../docs/frontend-handoff.md) | M5 | Frontend handoff — Claude owns web/ |
| [`docs/implementation-status.md`](../docs/implementation-status.md) | M5 | Current implementation status |
| [`docs/protocol.md`](../docs/protocol.md) | M1 | event-frozen contract and claim assumptions |
| [`docs/runbook.md`](../docs/runbook.md) | M2 | cold start, port/PID recovery and 3 a.m. decisions |
| [`firmware/status-display/include/status_protocol.h`](../firmware/status-display/include/status_protocol.h) | M2 | Bounded ASCII parser and request-anchored display freshness |
| [`firmware/status-display/platformio.ini`](../firmware/status-display/platformio.ini) | M2 | Pinned ESP32-S3 round-screen build and explicit USB upload |
| [`firmware/status-display/src/main.cpp`](../firmware/status-display/src/main.cpp) | M2 | Read-only GC9A01 status renderer and USB polling loop |
| [`firmware/status-display/tests/protocol_test.cpp`](../firmware/status-display/tests/protocol_test.cpp) | M2 | Native malformed/stale/duplicate/clock-rollover display regressions |
| [`fixtures/allocator-cases.json`](../fixtures/allocator-cases.json) | M1 | hand-calculated equal/weighted/rounding/floor cases |
| [`fixtures/demo-events.jsonl`](../fixtures/demo-events.jsonl) | M5 | Six authored mock snapshot events for replay primitives; not a live recording |
| [`fixtures/lab-cases.json`](../fixtures/lab-cases.json) | M5 | distributions, sizes and repeatability specification |
| [`fixtures/mqtt.schema.json`](../fixtures/mqtt.schema.json) | M5 | Generated exact JSON Schema; regenerate with build_fixtures.py |
| [`fixtures/openapi.json`](../fixtures/openapi.json) | M5 | Generated current REST request/success-response contract |
| [`fixtures/race-traces.json`](../fixtures/race-traces.json) | M5 | timed counterexamples and expected corrected outcomes |
| [`fixtures/snapshot.schema.json`](../fixtures/snapshot.schema.json) | M5 | Generated exact JSON Schema; regenerate with build_fixtures.py |
| [`fixtures/snapshots.json`](../fixtures/snapshots.json) | M5 | Checked initial, leased, stale, offline, recovering and infeasible UI fixtures |
| [`fixtures/wire-invalid.json`](../fixtures/wire-invalid.json) | M1 | invalid examples and expected rejection codes |
| [`fixtures/wire-valid.json`](../fixtures/wire-valid.json) | M1 | one valid example per MQTT variant |
| [`pyproject.toml`](../pyproject.toml) | M1 | Python dependencies, package configuration and command entrypoint |
| [`requirements.lock`](../requirements.lock) | M2 | resolved Python versions created during event |
| [`scripts/build_fixtures.py`](../scripts/build_fixtures.py) | M5 | M5: regenerate labelled development fixtures and exact schema artifacts. |
| [`scripts/build_inventory.py`](../scripts/build_inventory.py) | M5 | M5: generate the concrete file inventory and public Python interfaces from this checkout. |
| [`scripts/setup_local_broker.py`](../scripts/setup_local_broker.py) | M2 | M2: optional pinned Arch x86_64 dependency unpack; no root/system install. |
| [`src/truss/__init__.py`](../src/truss/__init__.py) | M1 | Truss protocol demonstrator. Owner M1. Importing this package starts nothing. |
| [`src/truss/allocator.py`](../src/truss/allocator.py) | M1 | Pure O(n log n) weighted-surplus filling. Owner M1; no I/O or clocks. |
| [`src/truss/api.py`](../src/truss/api.py) | M5 | Live/mock operator API. Owner M5. No provider means explicitly unavailable. |
| [`src/truss/api_models.py`](../src/truss/api_models.py) | M5 | Operator-plane views. Owner M5. Constructors fill explicit output defaults only. |
| [`src/truss/authority_store.py`](../src/truss/authority_store.py) | M1 | Durable epoch/controls, separate from event evidence. Owner M1. |
| [`src/truss/cli.py`](../src/truss/cli.py) | M2 | Local development entry points. Owner M2; no invisible mock fallback. |
| [`src/truss/clock.py`](../src/truss/clock.py) | M3 | Injectable monotonic time. Owner M3. Wall time is never control authority. |
| [`src/truss/config.py`](../src/truss/config.py) | M1 | Immutable run and private device configuration. Owner M1. |
| [`src/truss/coordinator.py`](../src/truss/coordinator.py) | M1 | Coordinator core. Owner M1. The MQTT lifecycle lives in coordinator_process.py. |
| [`src/truss/coordinator_process.py`](../src/truss/coordinator_process.py) | M1 | M1: serialized, durable, sole grant issuer. No private device config is read. |
| [`src/truss/devices.py`](../src/truss/devices.py) | M2 | Virtual load effects, no electrical actuation. Owner M2. |
| [`src/truss/display_bridge.py`](../src/truss/display_bridge.py) | M5 | Read-only USB screen bridge. Owner M5; no MQTT credentials or control calls. |
| [`src/truss/events.py`](../src/truss/events.py) | M3 | Append-only ordered JSONL evidence. Owner M3. Not an authority database. |
| [`src/truss/fairness.py`](../src/truss/fairness.py) | M1 | M1: durable service-deficit accounting against equal-surplus authority, never meter use. |
| [`src/truss/faults.py`](../src/truss/faults.py) | M2 | Bounded deterministic delivery faults. Owner M2. Does not alter authority clocks. |
| [`src/truss/lab.py`](../src/truss/lab.py) | M5 | Bounded, isolated synthetic allocation measurement. Owner M5; no MQTT import. |
| [`src/truss/lab_jobs.py`](../src/truss/lab_jobs.py) | M5 | M5: one bounded benchmark child per API, immutable recent job results and cancellation. |
| [`src/truss/lab_worker.py`](../src/truss/lab_worker.py) | M5 | M5: one disposable benchmark child with Linux CPU/memory limits and no broker access. |
| [`src/truss/local_policy.py`](../src/truss/local_policy.py) | M3 | Household-local assignment; only flexible output can yield. Owner M3. |
| [`src/truss/member.py`](../src/truss/member.py) | M3 | Request-anchored receiver core. Owner M3. MQTT lifecycle is in member_process.py. |
| [`src/truss/member_process.py`](../src/truss/member_process.py) | M3 | M3: private household process; aggregate offers out, bounded plant commands in. |
| [`src/truss/metrics.py`](../src/truss/metrics.py) | M5 | Quality-aware metrics. Owner M5. Unknown never becomes zero load. |
| [`src/truss/mock.py`](../src/truss/mock.py) | M5 | Honest interactive UI mock. Owner M5. Never imports MQTT or live processes. |
| [`src/truss/observer.py`](../src/truss/observer.py) | M5 | M5: live MQTT evidence and operator projection; has no grant publisher. |
| [`src/truss/plant.py`](../src/truss/plant.py) | M2 | Independent virtual-plant gate. Owner M2. Its process must outlive the member. |
| [`src/truss/plant_process.py`](../src/truss/plant_process.py) | M2 | M2: independent virtual enforcer process. No coordinator or allocator imports. |
| [`src/truss/process_entry.py`](../src/truss/process_entry.py) | M2 | M2: internal named process entrypoint; launched only by the local supervisor. |
| [`src/truss/recordings.py`](../src/truss/recordings.py) | M5 | M5: bounded, immutable replay sessions over recorded operator snapshots; no controls. |
| [`src/truss/reducer.py`](../src/truss/reducer.py) | M5 | Pure evidence projection. Owner M5. Replay cannot call an allocator or publisher. |
| [`src/truss/replay.py`](../src/truss/replay.py) | M3 | Read-only ordered playback of recorded facts. Owner M3. |
| [`src/truss/reservations.py`](../src/truss/reservations.py) | M1 | Possible authority, not last measured draw. Owner M1. Caller serialises access. |
| [`src/truss/runtime.py`](../src/truss/runtime.py) | M2 | M2: owned local Mosquitto/member/plant/coordinator lifecycle and private run files. |
| [`src/truss/runtime_common.py`](../src/truss/runtime_common.py) | M3 | M3: bounded per-process MQTT inbox, identity and signal lifecycle. |
| [`src/truss/schemas.py`](../src/truss/schemas.py) | M1 | Strict wire models for plan 20. Owner M1; receivers still enforce authority. |
| [`src/truss/supervisor.py`](../src/truss/supervisor.py) | M2 | Own-child process lifecycle only. Owner M2. Never kill arbitrary machine PIDs. |
| [`src/truss/transport.py`](../src/truss/transport.py) | M3 | MQTT 5 adapter and topic mapping. Owner M3. ProcessContext owns bounded delivery. |
| [`src/truss/validator.py`](../src/truss/validator.py) | M1 | Independent plan checks. Owner M1. Deliberately does not import allocator. |
| [`tests/conftest.py`](../tests/conftest.py) | M5 | clocks, in-memory transport and isolated temp run state |
| [`tests/test_allocator.py`](../tests/test_allocator.py) | M1 | theorem domain, integer error and deterministic targets |
| [`tests/test_api_contract.py`](../tests/test_api_contract.py) | M5 | identical mock/live shape, controls and source isolation |
| [`tests/test_authority_store.py`](../tests/test_authority_store.py) | M1 | M1: durable epochs, exclusive issuer lock and persisted operation conflicts. |
| [`tests/test_backend_extensions.py`](../tests/test_backend_extensions.py) | M5 | M5: isolated benchmark API, immutable replay and hardened request boundaries. |
| [`tests/test_config.py`](../tests/test_config.py) | M2 | M2: source config edits cannot alter a run's frozen protected profiles. |
| [`tests/test_coordinator.py`](../tests/test_coordinator.py) | M1 | M1: reject inflated self-declared floors and omitted registered households. |
| [`tests/test_devices.py`](../tests/test_devices.py) | M2 | exactly-once effects and observed acknowledgements |
| [`tests/test_display_bridge.py`](../tests/test_display_bridge.py) | M5 | M5: screen projection, read-only HTTP boundary and actual native parser regressions. |
| [`tests/test_events_replay.py`](../tests/test_events_replay.py) | M3 | canonical reconstruction, gaps and readonly playback |
| [`tests/test_fairness.py`](../tests/test_fairness.py) | M1 | M1: exact service-credit integration, frozen unknown intervals and durable restart behavior. |
| [`tests/test_fault_integration.py`](../tests/test_fault_integration.py) | M2 | real processes, coordinator/member/broker failure |
| [`tests/test_live_extensions.py`](../tests/test_live_extensions.py) | M5 | M5: actual rule persistence, weighted grants, read-only replay and concurrent lab/fault API. |
| [`tests/test_member.py`](../tests/test_member.py) | M3 | pending request, expiry, binding and stale offers |
| [`tests/test_metrics.py`](../tests/test_metrics.py) | M5 | unknown/null denominators and settling-window semantics |
| [`tests/test_plant.py`](../tests/test_plant.py) | M2 | gate/refusal/expiry despite member failure |
| [`tests/test_privacy_acl.py`](../tests/test_privacy_acl.py) | M3 | coordinator cannot subscribe to private topics or forge roles |
| [`tests/test_protocol_stateful.py`](../tests/test_protocol_stateful.py) | M5 | independent action-sequence model and lease oracle |
| [`tests/test_reservations.py`](../tests/test_reservations.py) | M1 | overlap, baselines, cap transitions and no early release |
| [`tests/test_schemas.py`](../tests/test_schemas.py) | M1 | wire parsing, cross-fields, topic and boot mismatches |
| [`web/index.html`](../web/index.html) | M4 | Vite document shell |
| [`web/package-lock.json`](../web/package-lock.json) | M4 | exact npm dependency lock created during event |
| [`web/package.json`](../web/package.json) | M4 | React/Vite/TS, Recharts, test commands, local-only assets |
| [`web/src/App.tsx`](../web/src/App.tsx) | M4 | route shell, boundary banner and state providers |
| [`web/src/api.ts`](../web/src/api.ts) | M4 | REST calls, operation polling and stable idempotency keys |
| [`web/src/assets/favicon.svg`](../web/src/assets/favicon.svg) | M4 | simple event-created local mark; no remote asset fetch |
| [`web/src/components/BenchmarkChart.tsx`](../web/src/components/BenchmarkChart.tsx) | M4 | measured points/error states, no fitted flat line |
| [`web/src/components/BoundaryBanner.tsx`](../web/src/components/BoundaryBanner.tsx) | M4 | live/mock/replay and prototype limits always visible |
| [`web/src/components/DebtTable.tsx`](../web/src/components/DebtTable.tsx) | M4 | authoritative service deficit and weighting disclaimer |
| [`web/src/components/EventTimeline.tsx`](../web/src/components/EventTimeline.tsx) | M4 | ordered event tail and gaps |
| [`web/src/components/JudgeControls.tsx`](../web/src/components/JudgeControls.tsx) | M4 | cap/protect/chaos/replay and async operation state |
| [`web/src/components/LeaseCountdown.tsx`](../web/src/components/LeaseCountdown.tsx) | M4 | approximate display timer, never a control clock |
| [`web/src/components/LoadPath.tsx`](../web/src/components/LoadPath.tsx) | M4 | exact Basis plus LocalDecision arithmetic |
| [`web/src/components/MemberCard.tsx`](../web/src/components/MemberCard.tsx) | M4 | one member's proposal, authority, meter and status |
| [`web/src/components/MemberDrawer.tsx`](../web/src/components/MemberDrawer.tsx) | M4 | private demo device detail and acknowledgement evidence |
| [`web/src/components/MetricsStrip.tsx`](../web/src/components/MetricsStrip.tsx) | M4 | measured metrics with valid denominators/quality |
| [`web/src/components/SiteCapacity.tsx`](../web/src/components/SiteCapacity.tsx) | M4 | cap, floor, reservations, uncertainty and observed bar |
| [`web/src/contracts.ts`](../web/src/contracts.ts) | M4 | mirror 20's API types until event-time generation is useful |
| [`web/src/format.ts`](../web/src/format.ts) | M4 | units, nulls, quality labels and approximate countdowns |
| [`web/src/main.tsx`](../web/src/main.tsx) | M4 | React bootstrap |
| [`web/src/routes/Console.tsx`](../web/src/routes/Console.tsx) | M4 | seven questions, four control groups and one drawer |
| [`web/src/routes/Lab.tsx`](../web/src/routes/Lab.tsx) | M4 | isolated benchmark controls, raw results and limitations |
| [`web/src/routes/Showcase.tsx`](../web/src/routes/Showcase.tsx) | M4 | short static explanation and claim boundary |
| [`web/src/state.tsx`](../web/src/state.tsx) | M4 | atomic observer snapshots and selected source |
| [`web/src/stream.ts`](../web/src/stream.ts) | M4 | WS/poll fallback, revision and source handling |
| [`web/src/styles.css`](../web/src/styles.css) | M4 | existing brand tokens, layout, hatching and reduced motion |
| [`web/tests/console.test.tsx`](../web/tests/console.test.tsx) | M4 | unknown cannot render verified; arithmetic and pending states |
| [`web/tests/routes.test.tsx`](../web/tests/routes.test.tsx) | M4 | sources isolated, capabilities honoured, mock route smoke |
| [`web/tests/stream.test.ts`](../web/tests/stream.test.ts) | M4 | stale/revision/reconnect/poll transitions |
| [`web/tsconfig.json`](../web/tsconfig.json) | M4 | TypeScript project checks |
| [`web/vite.config.ts`](../web/vite.config.ts) | M4 | dev proxy and local build, no external dependencies at runtime |

## Actual Python public interfaces and dependencies

Signatures are extracted from code, not future promises. Pydantic model fields are fully specified in generated JSON Schema. Methods that orchestrate processes are documented in their modules and BUILD_PLAN gates. Leading-underscore helpers are private. `__init__` constructors are included because their arguments are part of the interface.

### __init__ · M1

Dependencies: none.

```text
```

### allocator · M1

Dependencies: `collections.abc`, `dataclasses`, `fractions`.

```text
Demand — data model
Proposal — data model
allocate(offers: Sequence[Demand], cap_w: int, reserve_w: int=0)
```

### api · M5

Dependencies: `.api_models`, `.lab_jobs`, `.mock`, `.recordings`, `asyncio`, `contextlib`, `fastapi`, `fastapi.exceptions`, `fastapi.responses`, `fastapi.staticfiles`, `json`, `pathlib`, `time`, `uuid`.

```text
create_app(provider=None)
```

### api_models · M5

Dependencies: `.schemas`, `pydantic`, `typing`.

```text
Capabilities — data model
Operation — data model
LeaseView — data model
DeviceView — data model
MemberView — data model
SiteView — data model
EventView — data model
MetricsView — data model
Snapshot — data model
ControlRequest — data model
CapRequest — data model
RuleRequest — data model
FaultRequest.meaningful(self)
ChaosRequest — data model
LabRequest — data model
BenchmarkResult — data model
LabJob — data model
ReplayRequest — data model
ReplaySeek — data model
ReplayPlayback — data model
FairnessMember — data model
FairnessView — data model
RecordingSummary — data model
RecordingCatalog — data model
ReplayView — data model
ProcessView — data model
RuntimeView — data model
```

### authority_store · M1

Dependencies: `fcntl`, `json`, `pathlib`, `sqlite3`.

```text
AuthorityStore.__init__(self, path: str | Path)
AuthorityStore.get(self, key: str, default=None)
AuthorityStore.set(self, key: str, value)
AuthorityStore.claim_epoch(self, lock_path: str | Path)
AuthorityStore.remember_operation(self, key: str, body: dict, result: dict)
AuthorityStore.close(self)
```

### cli · M2

Dependencies: `.api`, `.config`, `.lab`, `.mock`, `.observer`, `.runtime`, `argparse`, `json`, `pathlib`, `uvicorn`.

```text
main()
```

### clock · M3

Dependencies: `pathlib`, `time`, `typing`.

```text
Clock.now_ns(self)
SystemClock.now_ns(self)
FakeClock.__init__(self, now_ns: int=0)
FakeClock.now_ns(self)
FakeClock.advance_ms(self, ms: int)
domain_id()
```

### config · M1

Dependencies: `.schemas`, `pathlib`, `pydantic`.

```text
Registration.bounds(self)
RunPolicy.initial_feasibility(self)
RunPolicy.reserve_w(self)
DeviceProfile.protected_maximum(self)
MemberProfile.unique(self)
load_run(path: str | Path)
load_member(path: str | Path, registration: Registration)
```

### coordinator · M1

Dependencies: `.allocator`, `.config`, `.reservations`, `.validator`, `time`.

```text
Coordinator.__init__(self, policy: RunPolicy, now_ns: int)
Coordinator.propose(self, demands: list[Demand], cap_w: int)
```

### coordinator_process · M1

Dependencies: `.allocator`, `.authority_store`, `.coordinator`, `.fairness`, `.runtime_common`, `.schemas`, `hashlib`, `json`, `pathlib`, `time`, `uuid`.

```text
canonical_hash(value)
run(manifest)
```

### devices · M2

Dependencies: `.config`, `dataclasses`.

```text
Device.command(self, command_id: str, version: int, desired_w: int, deadline_ns: int, now_ns: int, allowance_w: int)
```

### display_bridge · M5

Dependencies: `.api_models`, `argparse`, `httpx`, `re`, `serial`, `time`.

```text
display_frame(snapshot: Snapshot, nonce: str)
answer_request(line: bytes, client: httpx.Client, source: str)
main()
```

### events · M3

Dependencies: `.schemas`, `os`, `pathlib`.

```text
EventRecord — data model
read_events(path: str | Path)
EventLog.__init__(self, path: str | Path)
EventLog.append(self, **fields)
```

### fairness · M1

Dependencies: `.allocator`, `fractions`, `json`.

```text
ServiceDeficit.__init__(self, members, now_ns, saved=None, scale_wh=10)
ServiceDeficit.capture(self, now_ns, offers, statuses, ledger, cap_w, reserve_w, connected=True)
ServiceDeficit.advance(self, now_ns)
ServiceDeficit.weight(self, member, rule)
ServiceDeficit.dump(self)
ServiceDeficit.persist(self, store)
```

### faults · M2

Dependencies: `dataclasses`, `random`.

```text
DeliveryFault — data model
delivery_decision(fault: DeliveryFault | None, topic: str, now_ns: int, rng: Random)
```

### lab · M5

Dependencies: `.allocator`, `.validator`, `fractions`, `platform`, `random`, `statistics`, `time`.

```text
benchmark(members: int, seed: int=42, samples: int=200, distribution='uniform', rule='equal_surplus', cap_ratio=0.5)
```

### lab_jobs · M5

Dependencies: `.api_models`, `.mock`, `os`, `subprocess`, `sys`, `threading`, `uuid`.

```text
LabJobs.__init__(self)
LabJobs.submit(self, request, key)
LabJobs.get(self, job_id)
LabJobs.close(self)
```

### lab_worker · M5

Dependencies: `.api_models`, `.lab`, `json`, `os`, `resource`, `sys`.

```text
main()
```

### local_policy · M3

Dependencies: `.config`.

```text
assign(profile: MemberProfile, budget_w: int)
```

### member · M3

Dependencies: `.config`, `.schemas`, `dataclasses`.

```text
AcceptedLease — data model
MemberReceiver.__init__(self, registration: Registration, boot_id: str, site_id: str, run_id: str, registry_revision: int)
MemberReceiver.open_request(self, request_id: str, now_ns: int)
MemberReceiver.accept(self, lease: Lease, now_ns: int)
MemberReceiver.budget(self, now_ns: int)
```

### member_process · M3

Dependencies: `.clock`, `.config`, `.local_policy`, `.member`, `.runtime_common`, `.schemas`, `pathlib`, `time`, `uuid`.

```text
run(manifest, member_id)
```

### metrics · M5

Dependencies: `collections.abc`.

```text
percentage(numerator: int, denominator: int)
observed_total(samples: Sequence[tuple[int | None, int | None]], stale_ms: int=1500)
jain(ratios: Sequence[float])
```

### mock · M5

Dependencies: `.allocator`, `.api_models`, `.config`, `.local_policy`, `.schemas`, `datetime`, `pathlib`, `time`, `uuid`.

```text
utc_now()
MockState.__init__(self, config_dir: str | Path='config')
MockState.add_event(self, code, text)
MockState.set_cap(self, watts: int)
MockState.chaos(self, action: str, member_id: str | None)
MockState.snapshot(self)
```

### observer · M5

Dependencies: `.api_models`, `.authority_store`, `.clock`, `.config`, `.events`, `.fairness`, `.recordings`, `.runtime_common`, `.schemas`, `.transport`, `json`, `pathlib`, `sqlite3`, `threading`, `time`, `uuid`.

```text
LiveState.__init__(self, run)
LiveState.start(self)
LiveState.close(self)
LiveState.append_event(self, event)
LiveState.record_gap(self, reason, lost_messages=None)
LiveState.ingest(self, m, now)
LiveState.control_state(self)
LiveState.control_revision(self)
LiveState.operations(self)
LiveState.control(self, body, key, kind)
LiveState.get_operation(self, operation_id)
LiveState.fairness_state(self)
LiveState.snapshot(self)
```

### plant · M2

Dependencies: `.config`, `.devices`, `.schemas`.

```text
Plant.__init__(self, registration: Registration, profile: MemberProfile, boot_id: str, domain: str, registry_revision: int | None=None)
Plant.budget(self, now_ns: int)
Plant.bind(self, binding: PlantBind, now_ns: int)
Plant.apply_ceiling(self, ceiling: PlantCeiling, now_ns: int)
Plant.tick(self, now_ns: int)
Plant.command(self, device_id: str, command_id: str, version: int, watts: int, deadline_ns: int, now_ns: int)
```

### plant_process · M2

Dependencies: `.clock`, `.config`, `.plant`, `.runtime_common`, `.schemas`, `json`, `os`, `pathlib`, `time`.

```text
run(manifest, member_id)
```

### process_entry · M2

Dependencies: `.coordinator_process`, `.member_process`, `.plant_process`, `sys`.

```text
main()
```

### recordings · M5

Dependencies: `.api_models`, `.events`, `bisect`, `hashlib`, `pathlib`, `threading`, `time`, `uuid`.

```text
Recordings.__init__(self, root=None)
Recordings.catalog(self)
Recordings.create(self, run_id, from_seq=0)
Recordings.get(self, replay_id, from_seq=None)
Recordings.delete(self, replay_id)
Recordings.playback(self, replay_id, action)
```

### reducer · M5

Dependencies: `.events`, `copy`.

```text
reduce(state: dict, event: EventRecord)
```

### replay · M3

Dependencies: `.events`, `.reducer`, `hashlib`, `json`.

```text
replay(path, through_seq: int | None=None)
digest(state: dict)
```

### reservations · M1

Dependencies: `.config`, `dataclasses`.

```text
Reservation — data model
ReservationLedger.__init__(self, members: list[Registration], hold_ms: int=6400)
ReservationLedger.begin_recovery(self, now_ns: int)
ReservationLedger.expire(self, now_ns: int)
ReservationLedger.exposure(self, now_ns: int)
ReservationLedger.admit(self, *, member_id: str, boot_id: str, request_id: str, request_seq: int, amount_w: int, cap_w: int, reserve_w: int, now_ns: int)
```

### runtime · M2

Dependencies: `.authority_store`, `.config`, `.faults`, `.supervisor`, `json`, `os`, `pathlib`, `secrets`, `shutil`, `socket`, `subprocess`, `sys`, `threading`, `time`, `uuid`.

```text
broker_binary()
TrussRun.__init__(self, config_dir='config', runtime_root='runtime', broker_port=18883)
TrussRun.snapshot_profiles(self)
TrussRun.prepare(self)
TrussRun.start_child(self, name)
TrussRun.start(self)
TrussRun.write_processes(self)
TrussRun.act(self, action, member_id=None)
TrussRun.validate_fault(self, target, action, duration_ms=8000, delay_ms=0, rate=1.0)
TrussRun.set_fault(self, target, action, duration_ms=8000, delay_ms=0, rate=1.0)
TrussRun.close(self)
```

### runtime_common · M3

Dependencies: `.config`, `.faults`, `.schemas`, `.transport`, `datetime`, `json`, `pathlib`, `queue`, `random`, `signal`, `time`, `uuid`.

```text
utc_now()
ProcessContext.__init__(self, manifest_path, role, member_id=None, epoch=None)
ProcessContext.envelope(self, schema, **fields)
ProcessContext.status_message(self, state, source='heartbeat', recovery=None)
ProcessContext.enqueue(self, message)
ProcessContext.fault(self)
ProcessContext.start(self, subscriptions)
ProcessContext.drain(self, limit=64)
ProcessContext.publish(self, message, retain=False)
ProcessContext.close(self)
ProcessContext.root(self)
```

### schemas · M1

Dependencies: `__future__`, `datetime`, `json`, `pydantic`, `typing`.

```text
Model — data model
Envelope.timestamp(self)
Status.consistency(self)
Offer.envelope_valid(self)
LeaseRequest — data model
LeaseRef — data model
Basis — data model
Lease.matches_basis(self)
LeaseAck — data model
PlantBind — data model
PlantCeiling — data model
PlantAck.ref_kind(self)
MemberMeter.floor_observation(self)
DeviceDiscovery.baseline(self)
DeviceTelemetry — data model
LocalDecision — data model
DeviceCommand.command_state(self)
DeviceAck — data model
CapacityEvent — data model
LocalPolicy — data model
PolicyAck — data model
AllocationRow — data model
ValidationResult — data model
StageTiming — data model
Plan — data model
decode(payload: bytes)
encode(message: Envelope)
```

### supervisor · M2

Dependencies: `collections.abc`, `subprocess`.

```text
Supervisor.__init__(self)
Supervisor.start(self, name: str, argv: Sequence[str], **popen_options)
Supervisor.stop(self, name: str, abrupt: bool=False)
Supervisor.close(self)
```

### transport · M3

Dependencies: `.schemas`, `collections.abc`, `paho.mqtt`, `paho.mqtt.packettypes`, `paho.mqtt.properties`, `threading`.

```text
topic_for(message: Envelope)
validate_delivery(topic: str, payload: bytes, role: str)
MQTTTransport.__init__(self, client_id: str, role: str, username: str, password: str)
MQTTTransport.set_will(self, message: Status)
MQTTTransport.start(self, host: str, port: int, subscriptions: list[str], callback: Callable[[Envelope], None])
MQTTTransport.publish(self, message: Envelope, *, retain: bool=False)
MQTTTransport.close(self)
```

### validator · M1

Dependencies: `collections.abc`.

```text
validate_proposal(offers: Sequence, budgets: Mapping[str, int], cap_w: int, reserve_w: int=0)
```

## Generated/local-only files

`runtime/{run_id}/`: manifest.json, run.json, credentials.json (0600), hashed broker passwords, ACL/config, authority.sqlite and WAL/SHM, coordinator.lock, processes.json, per-role logs, frozen profiles/, events.jsonl, per-plant state.json and atomic temporary files, optional bounded faults.json. Supervisor owns this run directory. Never commit credentials or fabricate evidence from its logs.

`.venv/`, `web/node_modules/`, `web/dist/`, test caches and dependency downloads under the user cache are public dependencies/build output, not reused project implementation. `pleaseread.md` is deliberately ignored and explains the project privately in plain language.

AI and SGLang have been removed from the build scope. No model helper files or runtime dependencies are planned.
