# 10 — Five people

## Roles

| # | Owns | Learns | Ignores | Testable output |
|---|---|---|---|---|
| **M1** | Schemas, coordinator state machine, allocator interface, water-filling, CP-SAT, integration, technical defence | asyncio, paho-mqtt, Pydantic, OR-Tools, Hypothesis | ESP32 wiring, visual styling | `allocate()` passes property tests; coordinator completes lease/ack/replan; architecture doc matches reality |
| **M2** | Device emulator, 20–30 seeded profiles, state machines, idempotence and failure flags | Python state machines, paho-mqtt, pytest | Optimisation maths, frontend | One command launches five members; every node idempotent; failure modes selectable |
| **M3** | Broker, member agent, **lease expiry**, event log, replay | Mosquitto, MQTT 5 Will/expiry/retained, SQLite | UI styling | Broker restart checklist; member self-limits with no coordinator; replay is byte-identical |
| **M4** | Console, load-path inspector, judge controls | Streamlit, Plotly | Solver internals, MQTT internals | Seven questions answered on one screen; lease countdown live; inspector reads from `basis` |
| **M5** | Chaos tooling, scenario QA, ESP32, demo assets, pitch | Bash/Python tooling, ESP32 MQTT | Coordinator internals | Six chaos commands work; three cold-start passes recorded; backup video exists |

## Dependency discipline

The failure mode that kills this project is M1 becoming a bottleneck while four
people wait. Three rules prevent it:

1. **The contract is frozen at hour 1** by M1 and M2 together, with one valid and
   one invalid example per message type committed to the repository. After that,
   schema changes need both of them plus a stated reason in the commit.
2. **Everyone codes against fixtures first.** M4 builds the whole console against
   a static JSON snapshot and connects to live state at hour 12. M5 writes chaos
   commands against a stub coordinator. Nobody waits for anybody.
3. **The allocator is a pure function**, so M1 can develop and test it with zero
   running infrastructure, and M4 can render its output before it is wired up.

## Review rule

M1 reviews rather than rewrites. A teammate's working module that M1 would have
written differently ships as written. The commit history has to show five people
building a system, because it will be read — and because it is true.

## The 20-second rule

Every member can state, without notes: the problem, their subsystem, and one
thing it does that is genuinely hard. Rehearsed at hour 24 and again at hour 40.
Judges split up and ask people individually; a team where only one person can
explain the system is a team that loses to one where five can.
