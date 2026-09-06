# 13 — Pitch and judge defence

## 10-second hook

> A truss carries a load no single beam could, by giving every member only what
> it can bear. Truss does that for a shared electrical feeder — and if you kill
> its coordinator, it gets safer, not more dangerous.

## 30 seconds

> When a hostel inverter or an apartment feeder loses capacity, every home
> decides alone, and you get an overload trip, a blunt whole-floor cut, or one
> unlucky household absorbing all of it. Truss gives each home a member agent
> that keeps its device list private and publishes five numbers: floor, firm,
> useful, deadline energy, and how much it has already given up. A coordinator
> divides the available power by a provably fair rule and hands out leases —
> this much, until this moment. If a lease is not renewed, the home falls back
> to its safe floor on its own. Twenty-plus devices, five members, one hard
> limit, and it refuses to lie about whether it met it.

## Two minutes

Problem — the hostel at 19:40, and the three bad options.
Insight — the flexibility already exists at the edge; the missing thing is a way
to express it without publishing a device list.
Mechanism — offers, water-filling, leases, acknowledgement, replan.
Proof — cap compliance, time to safe, zero lease-safety violations, recovery
time, fairness with memory.
Boundary — no mains switching, no certification, no savings claims.

## The three sentences to land

1. **"The flexibility is already there. What's missing is a way to express it
   without surrendering privacy."**
2. **"A budget isn't a command, it's a lease — so safety is a property of the
   protocol, not the planner."**
3. **"A system that can't meet its constraint has to say so, not fake it."**

## Ten questions we will get

| Question | Answer |
|---|---|
| **Isn't this just load shedding?** | Load shedding cuts by geography. We allocate by declared need, guarantee a floor, and remember who gave up what so the same home isn't the loser twice. Rotational shedding cannot tell a CPAP machine from a water heater. |
| **Why not just sort by priority?** | Then the lowest-priority home is the designated loser every single round, forever. Water-filling gives max-min fairness and debt weighting repays sacrifice. Fairness here is an algorithm with a theorem, not an adjective. |
| **Why water-filling over an optimiser?** | It's deterministic, `O(n log n)`, provably max-min fair, and explainable in one sentence. CP-SAT sits behind the same interface for deadline scheduling and must beat it on the fixture set or we ship without it. |
| **What happens when the optimiser is wrong or times out?** | An independent validator re-checks every plan against the cap and can veto it. A vetoed or timed-out plan is discarded and water-filling's plan is issued. The console names which rule produced the live plan. |
| **What if the network or the coordinator dies?** | Leases expire and every member falls to its floor locally. There is no cloud on the judged path. A restarted coordinator waits one full TTL before issuing, because it can't know what it promised before it died. |
| **How do you know a device actually obeyed?** | We don't assume. Every command is versioned and expiring; every device acknowledges with its *observed* state; the coordinator compares desired against observed watts. Missing acks reserve conservative power and trigger a replan. |
| **Isn't a missing device just zero load?** | No, and that assumption is the most dangerous thing this system could make. A silent member keeps its last known draw reserved as camber, and you can watch the reserve band grow on screen. |
| **How is this fair, really?** | Three commitments: a floor nobody crosses, equal treatment of equal need by construction, and debt that carries between rounds. It's Ostrom's design principles for common-pool resources rendered as an allocation function. The fairness index is an engineering diagnostic, not a moral guarantee — operators still own protected-load policy. |
| **How does it scale?** | The coordinator sees offers, not devices, so its problem is `O(members)`, not `O(devices)`. That's the same boundary that gives privacy — the method-of-sections cut. Nesting coordinators is the next step and we haven't built it. |
| **What would production need that you don't have?** | Per-device identity, TLS, broker ACLs, key rotation, signed firmware, audit retention, certified actuation and real standards adapters. We built none of those in 48 hours and we're not going to imply otherwise. |

## Strongest opening

> Every ship has a painted line that says: load past this and people die. A
> shared electrical feeder has exactly the same line — and nothing draws it, and
> nothing enforces it.

## Strongest closing

> We can show you a system that works. More usefully, we can show you what
> happens when it doesn't: kill the coordinator and every home falls back to its
> safe floor on its own. That's the difference between a demo and a system.

## What we will not say

No market-size slide. No "AI-powered". No savings percentage. No
"revolutionise". No claim of a Matter or OpenADR implementation. No user count,
no pilot, no partner we do not have.
