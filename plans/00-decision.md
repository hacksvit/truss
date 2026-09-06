# 00 — Executive decision

## The project

**Truss** — a coordination layer for shared electrical capacity, built as a
distributed system of independently-failing agents under one hard constraint.

A group of homes, hostel rooms or small buildings shares a constrained feeder,
inverter or microgrid. Each **member** knows which of its loads are critical,
which can wait, and which have deadlines. Members publish only a **flexibility
offer** — never a device list. A **coordinator** divides the available power by
a provably fair rule and issues **leases**: an amount, valid until an instant.
Members command their own devices, acknowledge, and are measured. Unrenewed
leases expire into a safe floor without anyone being told.

## Why this is a large project and not a dashboard

It is genuinely five hard things at once, and each is visible in the demo:

- **A distributed system.** Five processes that fail independently, asynchronous
  messages that duplicate and reorder, stale state, and recovery. Not one
  program pretending to be five.
- **A leased resource with a formal safety property.** The sum of outstanding
  lease amounts never exceeds the cap, and that holds *even if every message in
  flight is lost*. This is Gray & Cheriton's lease mechanism applied to watts
  instead of cache lines.
- **A constrained allocation with a provable fairness property.** Water-filling
  produces the max-min fair (leximin) allocation. It is deterministic, runs in
  `O(n log n)`, and can be explained to a judge in one sentence.
- **A cyber-physical loop.** Sense → offer → allocate → lease → command →
  acknowledge → measure → replan. It cannot be reduced to CRUD screens.
- **A standards position.** OpenADR 3.x above, MQTT 5 in the middle, Matter 1.5
  below. We implement the middle honestly and define the edges as interfaces.

## What makes it memorable

Most teams demonstrate that their system works. Truss demonstrates what happens
when it *doesn't*:

- **Kill the coordinator and the site gets quieter.** Every lease counts down on
  screen; every member steps to its floor. There is no chaos because there is no
  trust to lose.
- **Ask for the impossible and it refuses.** Set the cap below the sum of safety
  floors and it declares INFEASIBLE and names who it cannot serve. It never
  reports compliance it did not achieve.

Those two beats are the pitch. They are also the engineering.

## Ruthless boundary

Truss is not a utility-grade demand-response platform, a certified smart panel,
a microgrid controller, or a savings product. **It never switches mains
voltage.** The prototype proves exactly six things:

1. Interoperable device messaging under one versioned contract.
2. A maintained device twin where *unknown is not zero*.
3. Constraint-aware, provably fair allocation.
4. Closed-loop command verification.
5. Fail-safe degradation under coordinator loss, partition and restart.
6. An append-only evidence trail that replays deterministically.

That is already a serious 48-hour system, and every one of those six is
measurable.

## What we deliberately do not build

Mains switching. Breaker or inverter integration. A certified Matter controller
or production OpenADR endpoint. Forecasting models. LLM features. Billing,
payments or carbon credits. Accounts, mobile apps, notifications. A general rule
builder. City-scale simulation. Peer-to-peer consensus.

Every one of those has been considered and rejected in [04-mvp.md](04-mvp.md),
with the reason recorded. Rejections are cheaper to defend than features.
