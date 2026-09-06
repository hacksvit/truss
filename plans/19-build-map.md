# 19 — Build map and ownership

This tree describes the **future competition repository**, created only after the official start. None of these implementation files is created by this review. Every listed file has a purpose and owner. Runtime/generated outputs are listed separately; optional SGLang files are in 22 and do not enter the core dependency graph.

## Process boundary

Primary profile, reflecting the user's own-PC deployment: Mosquitto; coordinator; API/evidence; supervisor; five members; five plants; browser. Five houses still fail independently as processes. They do not need five laptops to demonstrate that. All judged network communication remains on the local host/LAN; no external service is needed. Alternate-laptop relocation requires stopping the original run and waiting for all authority to expire, not live coordinator failover.

This explicitly replaces 05's five-laptop primary deployment. A browser may
connect over LAN, but control processes and evidence meter sampling share the
user's PC clock domain. Five-host control deployment is not a tested capability
of this reduced MVP; see 20 for the additional observation-freshness problem.

```text
Browser ── REST controls / WS read state ── API + evidence
                                            │ controlled cap / local policy only
                     Mosquitto, topic ACLs ──┤
                         │                  │
                  Coordinator              read-only demo observer
                  offer → allocator         device detail disclosed here
                  → reservation gate
                         │ grants
                   Member A … E
                   private twin + priority policy
                         │ local-domain ceiling and device commands
                   Plant A … E
                   independent aggregate gate + virtual devices
                         │ independent emulated meter / telemetry / ack
```

API keeps running when coordinator is killed. Plant keeps running when its member is killed. Supervisor owns only its own child processes and controlled fault flags; it is not an alternative issuer. A frozen plant is outside the timing theorem and must be visibly unverified. Replay and lab are API-side read-only jobs without MQTT publish credentials.

## Future repository tree — core

The tree is deliberately small enough to navigate at 3 a.m. Purpose text and owner are part of every leaf. Directories have no hidden implementation responsibilities.

```text
truss-event/
├── README.md                         M5 — offline startup, limits, demo and evidence entry point
├── .gitignore                        M2 — omit secrets, caches, environments and run artifacts
├── pyproject.toml                    M1 — Python package, scripts and pinned dependency declarations
├── requirements.lock                 M2 — resolved Python versions created during event
├── config/
│   ├── run.json                      M1 — fixed site registry, caps, timing and policy; no device lists
│   ├── member-a.json                 M2 — A's four private virtual-device profiles and baselines
│   ├── member-b.json                 M2 — B's four private virtual-device profiles and baselines
│   ├── member-c.json                 M2 — C's four private virtual-device profiles and baselines
│   ├── member-d.json                 M2 — D's four private virtual-device profiles and baselines
│   ├── member-e.json                 M2 — E's four private virtual-device profiles and baselines
│   ├── mosquitto.conf                M3 — LAN broker, persistence and authentication settings
│   └── acl                          M3 — role/topic boundaries, especially coordinator privacy
├── src/truss/
│   ├── __init__.py                   M1 — package identity only; no startup side effects
│   ├── cli.py                        M2 — run/process/demo commands with validated options
│   ├── config.py                     M1 — validate run policy and separate private profiles
│   ├── clock.py                      M3 — monotonic interface, fake-clock injection, domain identity
│   ├── transport.py                  M3 — MQTT 5 codec, role subscriptions and bounded fault shim
│   ├── schemas.py                    M1 — all MQTT and internal records from 20, no I/O
│   ├── api_models.py                 M5 — REST, WS, projections and errors from 20
│   ├── allocator.py                  M1 — pure sorted-breakpoint surplus water-filling
│   ├── validator.py                  M1 — independent arithmetic/policy check, no allocator import
│   ├── reservations.py               M1 — serial admission, request deduplication and expiry exposure
│   ├── authority_store.py            M1 — durable epoch, desired controls, debt and idempotency
│   ├── coordinator.py                M1 — recover/observe/plan/admit/issue state machine
│   ├── member.py                     M3 — private twin, offers, anchored requests and plant binding
│   ├── local_policy.py               M3 — deterministic per-device assignment within ceiling
│   ├── plant.py                      M2 — independent aggregate gate and shared-clock expiry
│   ├── devices.py                    M2 — seeded virtual-device states and command idempotence
│   ├── supervisor.py                 M2 — own-process lifecycle, manifest and safe restart actions
│   ├── faults.py                     M2 — bounded drop/delay/partition/pause plans for managed processes
│   ├── events.py                     M3 — append-only ordered JSONL writer and robust reader
│   ├── reducer.py                    M5 — pure event-to-observer-state reconstruction
│   ├── metrics.py                    M5 — defined sample quality, timing and fairness diagnostics
│   ├── replay.py                     M3 — read-only playback cursor and canonical state digest
│   ├── api.py                        M5 — FastAPI routes and bounded WS snapshots
│   ├── lab.py                        M5 — isolated measured allocator jobs, no live topology mutation
│   └── mock.py                       M5 — exact API plus labelled scripted WS without MQTT
├── fixtures/
│   ├── wire-valid.json               M1 — one valid example per MQTT variant
│   ├── wire-invalid.json             M1 — invalid examples and expected rejection codes
│   ├── snapshots.json                M5 — complete UI states for every visual/failure case
│   ├── demo-events.jsonl             M5 — authored 90 s mock event scenario, labelled as mock
│   ├── allocator-cases.json          M1 — hand-calculated equal/weighted/rounding/floor cases
│   ├── race-traces.json              M5 — timed counterexamples and expected corrected outcomes
│   └── lab-cases.json                M5 — distributions, sizes and repeatability specification
├── tests/
│   ├── conftest.py                   M5 — clocks, in-memory transport and isolated temp run state
│   ├── test_schemas.py               M1 — wire parsing, cross-fields, topic and boot mismatches
│   ├── test_allocator.py             M1 — theorem domain, integer error and deterministic targets
│   ├── test_reservations.py          M1 — overlap, baselines, cap transitions and no early release
│   ├── test_protocol_stateful.py     M5 — independent action-sequence model and lease oracle
│   ├── test_member.py                M3 — pending request, expiry, binding and stale offers
│   ├── test_plant.py                 M2 — gate/refusal/expiry despite member failure
│   ├── test_devices.py               M2 — exactly-once effects and observed acknowledgements
│   ├── test_events_replay.py         M3 — canonical reconstruction, gaps and readonly playback
│   ├── test_api_contract.py          M5 — identical mock/live shape, controls and source isolation
│   ├── test_metrics.py               M5 — unknown/null denominators and settling-window semantics
│   ├── test_fault_integration.py     M2 — real processes, coordinator/member/broker failure
│   └── test_privacy_acl.py           M3 — coordinator cannot subscribe to private topics or forge roles
├── web/
│   ├── package.json                  M4 — React/Vite/TS, Recharts, test commands, local-only assets
│   ├── package-lock.json             M4 — exact npm dependency lock created during event
│   ├── index.html                    M4 — Vite document shell
│   ├── vite.config.ts                M4 — dev proxy and local build, no external dependencies at runtime
│   ├── tsconfig.json                 M4 — TypeScript project checks
│   ├── src/
│   │   ├── main.tsx                  M4 — React bootstrap
│   │   ├── App.tsx                   M4 — route shell, boundary banner and state providers
│   │   ├── contracts.ts              M4 — mirror 20's API types until event-time generation is useful
│   │   ├── api.ts                    M4 — REST calls, operation polling and stable idempotency keys
│   │   ├── stream.ts                 M4 — WS/poll fallback, revision and source handling
│   │   ├── state.tsx                 M4 — atomic observer snapshots and selected source
│   │   ├── format.ts                 M4 — units, nulls, quality labels and approximate countdowns
│   │   ├── styles.css                M4 — existing brand tokens, layout, hatching and reduced motion
│   │   ├── assets/
│   │   │   └── favicon.svg           M4 — simple event-created local mark; no remote asset fetch
│   │   ├── routes/
│   │   │   ├── Showcase.tsx          M4 — short static explanation and claim boundary
│   │   │   ├── Console.tsx           M4 — seven questions, four control groups and one drawer
│   │   │   └── Lab.tsx               M4 — isolated benchmark controls, raw results and limitations
│   │   └── components/
│   │       ├── BoundaryBanner.tsx    M4 — live/mock/replay and prototype limits always visible
│   │       ├── SiteCapacity.tsx      M4 — cap, floor, reservations, uncertainty and observed bar
│   │       ├── MemberCard.tsx        M4 — one member's proposal, authority, meter and status
│   │       ├── LeaseCountdown.tsx    M4 — approximate display timer, never a control clock
│   │       ├── MemberDrawer.tsx      M4 — private demo device detail and acknowledgement evidence
│   │       ├── LoadPath.tsx          M4 — exact Basis plus LocalDecision arithmetic
│   │       ├── JudgeControls.tsx     M4 — cap/protect/chaos/replay and async operation state
│   │       ├── EventTimeline.tsx     M4 — ordered event tail and gaps
│   │       ├── DebtTable.tsx         M4 — authoritative service deficit and weighting disclaimer
│   │       ├── MetricsStrip.tsx      M4 — measured metrics with valid denominators/quality
│   │       └── BenchmarkChart.tsx    M4 — measured points/error states, no fitted flat line
│   └── tests/
│       ├── stream.test.ts            M4 — stale/revision/reconnect/poll transitions
│       ├── console.test.tsx          M4 — unknown cannot render verified; arithmetic and pending states
│       └── routes.test.tsx           M4 — sources isolated, capabilities honoured, mock route smoke
└── docs/
    ├── protocol.md                  M1 — event-frozen contract and claim assumptions
    ├── demo.md                      M5 — three-minute live and fallback scripts
    ├── runbook.md                   M2 — cold start, port/PID recovery and 3 a.m. decisions
    ├── evidence.md                  M5 — test/run hashes, counts, gaps and measured results
    └── contributions.md             All — honest file ownership and review record
```

Choice change: use plain CSS with the existing tokens, rather than Tailwind, for this small fixed-layout app. It removes version-specific configuration and utility learning for the sole UI builder without changing React/Vite/TypeScript. If M4 already knows Tailwind, add its required event-time config explicitly and subtract equivalent styling time; do not spend an hour debating it. Recharts remains the sole chart library; plain React context replaces optional state libraries.

Generated/untracked files during the event: `runtime/{run_id}/events.jsonl` (M3 event evidence), `authority.sqlite` plus its SQLite journal/WAL files (M1 persistent control state), `coordinator.lock` (M1 singleton), `processes.json` and per-process stdout/stderr `.log` files (M2 supervisor), `faults.json` (M2 bounded fault instructions), `lab-{job_id}.json` (M5 raw benchmark), `replay-{id}.json` (M3 cursor metadata). Broker password database (M3) is generated locally, not committed. `web/dist/`, `.venv/`, `node_modules/`, caches and test reports are generated, not hand-maintained modules. Evidence release adds a recording, screenshots, lockfiles, machine description and hashes. No dependency source is copied as project implementation.

## Public interfaces and dependencies — backend

Signatures below are **interface notation only**. No bodies are implied. Private helpers remain private; add no cross-module database queries or global state. Types refer to 20 or the internal contracts here.

| Module / owner | Public contract | Allowed dependencies |
|---|---|---|
| `schemas` M1 | `decode(topic, bytes, role) → Message or Rejection`; `encode(Message) → bytes`; immutable model types | Pydantic, standard library. Topic/role checks delegated data, not broker state. |
| `api_models` M5 | Snapshot/Operation/LabResult/Error/WS union definitions; `validate_snapshot(value) → Snapshot` | Pydantic, schemas nested read models only |
| `config` M1 | `load_run(path) → RunPolicy`; `load_member(path, registration) → MemberProfile`; reject baseline totals/mismatched hashes | schemas, JSON/path library |
| `clock` M3 | `Clock.now_ns() → integer`; `domain_id() → ID`; `schedule(deadline, callback_token)`; fake clock exposes explicit advance | standard clock/event loop only; no wall timestamp control |
| `transport` M3 | `start(role, subscriptions, on_message)`; `publish(topic, Message, expiry_s, retain) → queued/failed`; `close()`; bounded inbound queue | paho-mqtt MQTT5, schemas, faults adapter; marshal callbacks into owning loop |
| `allocator` M1 | `allocate(PlannerSnapshot) → Proposal`; same input exactly same continuous target, rounded budgets and basis | schemas, arithmetic/sort only; no clock/I/O/debt-store access |
| `validator` M1 | `validate_proposal(snapshot, proposal) → ValidationResult`; reject unknown member, below-floor, over-demand, sum and policy mismatch | schemas; **no allocator import** |
| `reservations` M1 | `exposure(now) → ReservationView`; `admit(request, candidate, policy, now) → GrantDecision`; `expire(now) → released IDs`; `begin_recovery(now, registry)` | schemas, passed clock values; no publish; all calls serial |
| `authority_store` M1 | `claim_epoch() → Pos`; `load_desired_state() → ControlState`; `accept_operation(key, body, expected_revision) → Operation`; `finish_operation(id, result)`; `load/save_debt(revision, values)` | sqlite3, file locking, schemas/api models; transactions define durability |
| `coordinator` M1 | `run(policy, transport, clock, store)`; `on_offer`, `on_request`, `on_capacity`, `on_meter`, `tick`; sole grant publisher | allocator, validator, reservations, schemas, authority_store; aggregate topics only |
| `member` M3 | `run(registration, private_profile, transport, clock)`; handlers for lease/plant/device/policy; `make_offer()`; `open_request()` | local_policy, schemas, transport, clock; no API/UI/model serving |
| `local_policy` M3 | `assign(private_twin, accepted_ceiling, local_now) → list[DeviceIntent, LocalDecision]`; never increases aggregate authority | schemas; deterministic priority/id tie ordering |
| `devices` M2 | `initialise(profile, seed) → DeviceState`; `transition(state, command, now, allowance) → state+ack`; `step(state, elapsed) → telemetry` | schemas, passed deterministic timing/random inputs; no autonomous publish |
| `plant` M2 | `run(profile, transport, clock)`; `bind`, `apply_ceiling`, `apply_command`, `tick → telemetry/meter/acks`; independent expiry | devices, schemas, transport, clock; cannot call coordinator |
| `supervisor` M2 | `start_run(profile) → RunManifest`; `act(FaultSpec) → ActionResult`; `stop_run()`; holds child identity and boot domains | subprocess/OS, config, faults; owns no grants and never uses broad kill patterns |
| `faults` M2 | `validate(FaultSpec)`; `delivery_decision(role, topic, now) → pass/drop/delay`; `clear_expired(now)` | schemas/api models, standard library; no change to clock/authority validation |
| `events` M3 | `append(EventInput) → EventRecord`; `read(after,limit) → EventPage`; `flush()`; explicit gap on write failure | schemas, filesystem/JSON; single writer; loss stops evidence assurances, not expiry |
| `reducer` M5 | `reduce(ObserverState, EventRecord) → ObserverState`; `project(state, received_now) → Snapshot` | api_models, schemas, metrics; no publish or live replanning |
| `metrics` M5 | `update(MetricState, observation/event) → MetricState`; `view(state) → MetricsView` | api_models, arithmetic; denominator and time-window contracts in 20 |
| `replay` M3 | `open(run,from_seq) → ReplaySession`; `seek(session,seq)`; `advance(session,delta) → ObserverState`; `digest(state) → Hash` | events, reducer; no transport and no authority-store writes |
| `api` M5 | `create_app(observer, control_store, supervisor, replay, lab) → ASGI application`; exact 20 routes | FastAPI/ASGI, api_models, events/reducer; restricted control publisher through adapter only |
| `lab` M5 | `start(LabRequest) → job ID`; `status(id) → LabResult`; one bounded worker process, 10 s deadline | allocator, validator, fixtures, high-resolution timer; no transport/authority store |
| `mock` M5 | `create_mock_app(script) → ASGI application`; same routes/WS, no live dependencies | api_models, fixture data, fake operation store; never imports coordinator/transport |
| `cli` M2 | `run`, `coordinator`, `member`, `plant`, `api`, `mock`, `chaos`, `replay` entrypoints with validated IDs | above component entrypoints only; startup has no import-time side effects |

**Internal output types:** Proposal = snapshot/policy/cap IDs, rule, feasible boolean, member target map, continuous targets, quantisation remainder, deficit, affected IDs, reason codes. GrantDecision = admitted Lease plus updated reservation view **or** denied reason plus unchanged view. ObserverState = last validated message by publisher boot/topic plus ordered events, operations, metrics, receipt ages and stream/run identity. No unknown `dict of anything` crosses a public boundary.

The authority database has two writers (API desired controls/operations and coordinator epoch/debt), with short transactions and busy handling. Do not hold a transaction across MQTT or a WS send. If a cap write cannot commit, reject its operation; never show a cap the coordinator cannot recover. Recovery state includes the last accepted cap revision even if its event publish was lost.

## Public interfaces — frontend

| Module / owner | Interface and state ownership | Dependencies |
|---|---|---|
| contracts M4 | Static TS types mirroring 20; exported discriminated view/operation types | No runtime dependencies |
| api M4 | `getState(source)`, `submitControl(body,key)`, `getOperation(id)`, `getEvents(cursor)`, replay/lab calls; typed result/error | browser fetch, contracts |
| stream M4 | `connect(source,onSnapshot,onStatus) → unsubscribe`; rejects stale revision and wrong source; owns retries and in-flight polls | WebSocket, api, contracts |
| state M4 | `SnapshotProvider`, `useSnapshot`, `useConnection`, `setSource`; owns authoritative received snapshot/source | React context, stream; never derives new device truth from timer |
| format M4 | `watts`, `energy`, `qualityLabel`, `estimatedRemaining`; explicit null handling | contracts and passed time |
| App M4 | route selection and BoundaryBanner; source-aware providers mount/unmount cleanly | React/router or minimal History routing, state |
| Showcase M4 | static narrative; own optional illustration play/pause state | BoundaryBanner; no live control hook |
| Console M4 | selected member/device and drawer state; takes Snapshot from provider | components, api operation submission |
| Lab M4 | owns job ID, form values, progress polling and result; separate from live state | api, BenchmarkChart; no topology mutation |
| BoundaryBanner M4 | source, connection quality and literal prototype boundary props; stateless | contracts |
| SiteCapacity M4 | SiteView props, no state | CSS and format; hatched subset is not double-added |
| MemberCard M4 | MemberView + onSelect; stateless apart from child countdown | LeaseCountdown, format |
| LeaseCountdown M4 | LeaseView props; owns animation timestamp only | performance clock/animation frame, reduced-motion preference |
| MemberDrawer M4 | MemberView + selectedDevice + onClose/onSelect; no copied device truth | LoadPath, format |
| LoadPath M4 | Basis + LocalDecision + refs; stateless; mismatched refs show “basis unavailable” | contracts, format; never invents causal text |
| JudgeControls M4 | owns draft cap, selected action, pending Operation IDs/errors; submits only with current revisions | api, capabilities; four groups preserved |
| EventTimeline M4 | EventView list + gap flag; optional selected correlation ID | format |
| DebtTable M4 | MemberView[]; stateless labelled deficit display | format |
| MetricsStrip M4 | MetricsView; stateless, null ≠ 0 | format |
| BenchmarkChart M4 | LabResult; optional hovered point only | Recharts, format; full raw export link |

Files in tests/fixtures/config/docs have the public contract stated by their purpose and by 20/21; they are not additional runtime modules. `__init__`, build manifests and asset/style files export no application functions.

## Component trees with state boundaries

```text
App [route + provider lifecycle]
├── BoundaryBanner [stateless, always visible]
├── / Showcase [local illustration play/pause only]
│   ├── scenario description [static, fictional wattages labelled]
│   ├── household → aggregate offer diagram [static]
│   ├── fairness and lease explanation [static, qualified theorem]
│   └── links to Console/Lab and limitations [static]
├── /console SnapshotProvider [source, snapshot, connection]
│   └── Console [selected member/device; drawer open]
│       ├── SiteCapacity [server facts]
│       ├── MemberCard × registered members [server facts]
│       │   └── LeaseCountdown [display animation time only]
│       ├── MetricsStrip [server calculations]
│       ├── DebtTable [server ledger]
│       ├── EventTimeline [server event order]
│       ├── JudgeControls [draft input; pending operation IDs]
│       └── MemberDrawer [selection passed from Console]
│           └── LoadPath [server Basis + exact local decision]
└── /lab Lab [isolated form, job ID, result and poll status]
    ├── experiment selector [members / devices; declared fixed settings]
    ├── BenchmarkChart [server measured samples]
    └── environment/measurement table [server metadata]
```

Browser derives presentation only. It does not recompute debt, allocate watts, declare capacity feasible, or infer an expired appliance from animation. This is what lets mock and real data share the same UI without turning presentation into control.

## Ownership edges that need explicit handoffs

M1 owns safety decisions; M3/M2 implement receivers and must review them. M5 owns independent tests and does not copy the gate's arithmetic into the oracle. M4 owns rendering and cannot change the API silently. Every schema change after hour 2 has a short reason, fixture change, and sign-off by **producer and consumer**; M1 is required only for authority changes. Handoff schedule and fallback gates are in 21.
