# TRUSS

**A coordination layer for shared electrical capacity.**

> A truss carries a load no single beam could, by giving every member only what
> it can bear. Truss does the same for a shared electrical feeder.

---

## The one-paragraph version

A hostel block, an apartment stack, or a small microgrid shares one constrained
supply. When that supply shrinks — an inverter cuts in, a feeder browns out, a
generator takes over — every home decides alone, and the result is an overload
trip, a blunt whole-floor shutdown, or one unlucky household absorbing all of
the inconvenience.

Truss gives each home a **member**: a local agent that knows its own devices in
detail, keeps that detail private, and publishes one thing — a **flexibility
offer**. A **coordinator** divides the available power across members by a
provably fair rule, and hands each member a **lease**: this much power, until
this moment. Members command their own devices, acknowledge, and are measured.
If a lease is not renewed, the member falls back to its safe floor on its own,
without being told.

That last sentence is the whole design. **Safety is a property of the protocol,
not of the planner.** Kill the coordinator and the site gets quieter, not more
dangerous.

---

## Why "Truss"

Three levels, and all three are load-bearing.

**1. The etymology is the architecture.** *Truss* comes from Old French
*trousse* — a bundle: separate things bound into one. Five independent gateways
bound into one system that behaves as a whole.

**2. The structure is the mechanism.** A truss carries a load no single member
could, by resolving it into forces that each member *can* bear. Every member's
share is not guessed — it is computed exactly, and you can trace the **load
path** from where the load is applied to where it is carried. Truss computes
every home's share exactly, and you can click any deferred device to see the
chain of reasoning that deferred it.

**3. Redundancy is the engineering word for fault tolerance.** A statically
determinate truss (members `m = 2j − 3`) collapses if you remove one member. A
*statically indeterminate* one has spare load paths, so when a member is lost
the load redistributes and the structure stands. Truss is deliberately
indeterminate: lose a gateway and the remaining members absorb its share.

The name also hands us a vocabulary that made the product design itself —
see [plans/01-name.md](plans/01-name.md).

| Truss term | What it means here |
|---|---|
| **Member** | One home / room / gateway. Structural *and* social — both readings are correct. |
| **Top chord** | The site capacity ceiling. Hard. Never crossed. |
| **Bottom chord** | The guaranteed floor every member keeps. Never breached while the system claims feasibility. |
| **Web** | The live allocation between floor and ceiling — the part that moves. |
| **Joint** | The coordinator: where members meet and forces resolve. |
| **Camber** | Deliberate headroom reserved for load we cannot currently see. |
| **Load path** | The audit trail: why *this* device, *this* watt, *this* moment. |
| **Buckling** | The failure mode you didn't design for. We inject it on purpose. |

---

## What it is not

This goes on the first slide, not the appendix.

**Truss never switches mains voltage.** It is not a smart panel, not an inverter
controller, not a certified demand-response platform, and it makes no savings
claims. It is a planning-and-control demonstrator: emulated device nodes plus,
optionally, one ESP32 driving a low-voltage LED. Every claim it makes is one it
measures.

---

## Repository map

| Path | Contents |
|---|---|
| [`plans/`](plans/) | The complete brief: decision, problem, architecture, protocol, planner, safety, team, timeline, demo, pitch. Start at [`plans/README.md`](plans/README.md). |
| [`LOGO.md`](LOGO.md) | The mark, specified in enough detail to draw without further decisions. |
| [`research/`](research/) | Evidence ledger and the PDF build. |

---

## Status

Preparation only. No implementation code lives here — see
[plans/14-rules.md](plans/14-rules.md) for why that constraint exists and what
it does and does not forbid.
