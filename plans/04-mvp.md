# 04 — Exact MVP

## The five features, and nothing else

### 1. Member and device contract
Twenty to thirty emulated device nodes behind five member processes. Each device
publishes identity, member, observed watts, operating state, flexibility class
(`protected` / `firm` / `deferrable` / `deadline`), priority, deadline where it
has one, minimum run time, heartbeat and a monotonic sequence number. One node
may be a real ESP32 driving a low-voltage LED. **Physical and emulated nodes use
the identical topic and payload contract** — the ESP32 is not a special case, it
is one more implementation of the same interface.

### 2. Offers, not device lists
A member aggregates its own devices into one **offer**: floor watts, firm watts,
useful watts, deadline energy outstanding, and accumulated curtailment debt. The
coordinator never learns what devices exist. This is the privacy boundary and
the scaling boundary at once, and it is the single most defensible design
decision in the project.

### 3. Fair allocation with memory
The coordinator computes budgets by **debt-weighted water-filling**, which
yields the max-min fair allocation in `O(n log n)` deterministically. A CP-SAT
model sits behind the same interface for deadline-aware scheduling over a twelve
slot horizon, hard-time-boxed, with the water-filling result as the validated
fallback. See [07-planner.md](07-planner.md).

### 4. Leases, not commands
Every budget is a **lease**: an amount and an expiry measured on the member's own
monotonic clock. Members renew every 2 s with a 6 s TTL. An unrenewed lease
expires into the member's floor, locally, with no message required. Commands to
devices carry `plan_id`, a monotonically increasing version, desired state,
expiry and a reason. Devices acknowledge `applied` / `rejected` / `duplicate` /
`expired`. See [06-protocol.md](06-protocol.md).

### 5. One-screen console with a load path
Top chord, camber band, observed load, five member panels with live lease
countdowns, device state, plan timeline, debt ledger, and the **load path
inspector**: click any deferred device and read the causal chain that deferred
it. The judge gets exactly four controls. See [09-console.md](09-console.md).

---

## MUST BUILD

- Versioned MQTT 5 schema with validation, retained discovery and status, and
  Will messages for abnormal disconnect.
- 20+ emulated devices across five member processes, launched by one seeded
  command.
- Debt-weighted water-filling allocator, with an **independent** cap validator in
  a separate module that can veto any plan.
- The lease mechanism, including local expiry, coordinator restart delay, and the
  visible countdown.
- Command / acknowledgement / heartbeat / stale detection / replan loop.
- Append-only event log with monotonic sequence numbers, and one-click replay.
- Live console with the four judge controls and the load path inspector.
- Automated tests: cap compliance, lease safety, idempotent commands, missed
  acknowledgements, infeasible floors, coordinator restart.
- **Property-based tests** over the safety invariants using Hypothesis —
  generated scenarios, not hand-picked ones. This is cheap and it is the single
  most credible thing we can say to a technical judge.

## NICE TO HAVE — in this order

1. CP-SAT deadline planner behind the existing interface.
2. One ESP32 with an LED on the identical contract.
3. OpenADR-shaped event adapter translating a capacity event into a site cap.
4. Downloadable incident bundle: log, plan trace, metrics, replay.
5. Greedy-versus-CP-SAT comparison on the same seed.

## DO NOT BUILD

Each of these was considered. The reason is recorded so we can defend the
absence rather than apologise for it.

| Not building | Because |
|---|---|
| Mains switching, breaker or inverter integration | Safety, and it would make the demo a liability rather than an asset |
| A real Matter controller or production OpenADR endpoint | Cannot be done honestly in 48 hours; we ship interfaces and label them |
| Forecasting or any ML | Adds a dependency and a failure mode to buy nothing the demo needs |
| LLM features | There is no question in this product that a language model answers |
| Billing, payments, carbon credits | Unverifiable claims attached to a system that measures watts |
| Accounts, mobile apps, notifications | Not on the judged path |
| A general automation rule builder | It is a product, not a feature, and it dilutes the mechanism |
| City-scale simulation | Claims scale we cannot demonstrate |
| Peer-to-peer consensus | Research, not a weekend. The hierarchy *is* the design |

## Acceptance criteria

Numbered so they can be ticked in front of a judge.

1. All seeded devices appear within **10 s** of scenario start.
2. A cap change produces a validated plan within **1 s**; if CP-SAT exceeds its
   time box, water-filling returns immediately and the UI says which ran.
3. Observed controlled load is below the top chord within **5 s** of a cap drop,
   whenever a feasible plan exists.
4. Commands are idempotent: replaying any command cannot toggle a device twice.
5. A killed member goes stale within its timeout, its last known draw stays
   reserved as camber, and the plan is redone conservatively.
6. **Killing the coordinator drives every member to its floor within one lease
   TTL, with zero cap violations.**
7. A restarted coordinator issues no lease for one full TTL, and says so on screen.
8. If the sum of floors exceeds the cap, the system declares INFEASIBLE and names
   the unserved members. It never reports false compliance.
9. The same seed produces the same plan and a byte-identical event trace.
10. Every one of 1–9 has an automated test, and 3, 6 and 8 have property-based
    tests over generated scenarios.

## Measured outputs

| Metric | Definition |
|---|---|
| **Cap compliance** | % of samples at or below the top chord after the response grace period |
| **Time to safe** | Cap event timestamp → first verified below-cap timestamp |
| **Lease safety violations** | Count of instants where outstanding leases exceeded the cap. **Must be 0** |
| **Acknowledgement success** | Applied acks ÷ issued commands |
| **Deadline satisfaction** | Deadline jobs completed by their requested time |
| **Recovery time** | Failed-member detection → replacement plan published |
| **Fairness** | Leximin gap, plus Jain's index over delivered ÷ requested flexible energy — reported only where every denominator is valid, and described as an engineering diagnostic, never as a moral guarantee |
| **Coordinator-loss margin** | Peak observed load during a coordinator kill, as a fraction of the cap |
