# Truss — the plans

## Research and build-contract amendment — 6 September 2026

Start with [what the original plans got wrong](../research/2026-09-06-review.md).
The original 00–16 are preserved; the following documents propose explicit
corrections and a smaller build. No implementation files have been created.

| Document | Contents |
|---|---|
| [17 — Change list](17-change-list.md) | Wrong/missing/cut decisions, scope order and honest scalability experiments |
| [18 — Protocol repair](18-protocol-repair.md) | Counterexamples, request anchoring, reservation proof, assumptions and revised invariants |
| [19 — Build map](19-build-map.md) | Complete future file tree, public interfaces, dependencies, ownership and component trees |
| [20 — Contracts](20-contracts.md) | Pydantic specifications, MQTT messages, REST/WS, state views and mock behaviour |
| [21 — Delivery](21-delivery.md) | Critical-path graph, five work streams, handoffs, test obligations and 3 a.m. runbook |
| [22 — Protected loads and SGLang](22-sglang-and-protected-loads.md) | Mandatory protected-load policy; optional local AI explanation with hardware/cost gates |

Within this amendment set, 22's protected-load requirements supplement 18/20;
SGLang remains optional. Proposed timings, hardware feasibility and engineering
assumptions are not recorded test results.

## Original plans

Read in order the first time. After that, `04-mvp.md` and `08-safety.md` are the
two you will come back to.

| # | Document | Answers |
|---|---|---|
| 00 | [decision.md](00-decision.md) | What we build, why it is big enough, and where the boundary is |
| 01 | [name.md](01-name.md) | Why "Truss", and the vocabulary it gives the whole system |
| 02 | [problem.md](02-problem.md) | The operating moment, who is hurt, and the evidence |
| 03 | [prior-art.md](03-prior-art.md) | What already exists and why it does not solve this |
| 04 | [mvp.md](04-mvp.md) | Exact scope: must / nice / never. Acceptance criteria |
| 05 | [architecture.md](05-architecture.md) | Three planes, components, deployment |
| 06 | [protocol.md](06-protocol.md) | Topics, payloads, the lease contract, state machines |
| 07 | [planner.md](07-planner.md) | Water-filling leximin, debt weighting, CP-SAT |
| 08 | [safety.md](08-safety.md) | The six invariants, camber, fault injection |
| 09 | [console.md](09-console.md) | One screen, three controls, the load-path inspector |
| 10 | [team.md](10-team.md) | Five roles and what each owns |
| 11 | [timeline.md](11-timeline.md) | Hour by hour across 48 |
| 12 | [demo.md](12-demo.md) | The three-minute script and the six beats |
| 13 | [pitch.md](13-pitch.md) | Hooks, pitches, and the judge questions we will get |
| 14 | [rules.md](14-rules.md) | Competition constraints and what preparation is legitimate |
| 15 | [risks.md](15-risks.md) | Risk register and kill points |
| 16 | [frontend.md](16-frontend.md) | The whole website: showcase, console, lab. Stack, contract, assets |

## The three sentences that matter

1. **The flexibility already exists at the edge; what is missing is a way to
   express it without surrendering privacy or control.**
2. **A budget is not a command — it is a lease, and an unrenewed lease expires
   into safety.**
3. **A system that cannot meet its constraint must say so, not fake it.**

Everything else in these documents is consequence.
