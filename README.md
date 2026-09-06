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
offer**. A **coordinator** proposes a weighted max-min allocation of surplus
above registered floors, then an independent reservation gate decides what can
be issued. A **lease** expires six seconds after the member's request on its
own monotonic clock. The planned live processes command and measure virtual devices.
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
claims. It is a planning-and-control demonstrator using virtual device
processes. Measured results and unverified assumptions are reported separately.

---

## Repository map

| Path | Contents |
|---|---|
| [`plans/`](plans/) | The complete brief: decision, problem, architecture, protocol, planner, safety, team, timeline, demo, pitch. Start at [`plans/README.md`](plans/README.md). |
| [`LOGO.md`](LOGO.md) | The mark, specified in enough detail to draw without further decisions. |
| [`research/`](research/) | Evidence ledger and the PDF build. |

---

## Status and startup

Implementation began after the user confirmed the hackathon had started.
This checkout contains a **working local MQTT backend with independent virtual
plants**, tested protocol cores, and a mock console for frontend development.
Historical plans describe the intended end state; use the
[implementation status](docs/implementation-status.md) to distinguish it from working code.

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.lock
.venv/bin/pip install -e . --no-deps
npm --prefix web ci
npm --prefix web run build
.venv/bin/truss check-config
.venv/bin/truss mock
```

Open `http://127.0.0.1:8000` for `/`, `/console` and `/lab`.
Dependencies must be installed before an offline demonstration. Runtime uses
local assets and no cloud service. Development UI: `npm --prefix web run dev`.

```bash
.venv/bin/pytest -q
npm --prefix web test
npm --prefix web run build
```

Start with [the build guide](docs/architecture.md), [current API contract](docs/protocol.md),
[parallel delivery gates](plans/21-delivery.md) and [the runbook](docs/runbook.md).
Protected fictional loads stay reserved for the full run. AI/SGLang have been
removed from scope; decisions and explanations are deterministic. No medical
devices or mains actuation are connected.

For the real backend, install Mosquitto (or use the pinned local-cache helper
`python scripts/setup_local_broker.py` on this Arch PC), then run:

```bash
.venv/bin/truss live --port 8001
```

Follow [BUILD_PLAN.md](BUILD_PLAN.md) in order. Your frontend handoff is in
[docs/frontend-handoff.md](docs/frontend-handoff.md).
