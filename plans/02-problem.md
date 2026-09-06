# 02 — The problem

## One operating moment

A hostel block loses grid supply at 19:40. The inverter takes over. Normal draw
across the block is about 4.6 kW; the inverter can hold 1.8 kW.

Exactly three things can happen today:

1. **The inverter trips on overload.** Everyone loses everything — including the
   corridor lights, the water pump and the router.
2. **The warden cuts a floor.** Forty rooms lose everything so that forty other
   rooms lose nothing. The choice of floor is not a policy; it is whoever the
   warden thought of.
3. **Somebody walks the corridors unplugging things.** This is the humane option
   and it takes twenty minutes, which is nineteen minutes too long.

All three are blunt instruments applied to a problem that has structure.

## The structure nobody uses

Most of that 4.6 kW is not urgent, and the building already knows it — the
knowledge is just stranded at the edge:

| Load | Real constraint |
|---|---|
| Water heater | Needs 40 minutes of heat before 06:00. Does not care when. |
| Washing machine | Has a **deadline**, not a schedule. Once started, must not be interrupted mid-cycle. |
| Laptop charger at 82% | Can pause for an hour with no consequence at all. |
| Refrigerator | Can coast 20 minutes. Cannot coast 3 hours. |
| Router, corridor lights | Small, constant, and everything else depends on them. |
| CPAP machine | Cannot wait one second, and nobody will admit which room it is in. |

Every one of those distinctions exists. None of them is expressible to whatever
decides who loses power. **The flexibility is already there. What is missing is
a way to express it that does not require surrendering privacy or control.**

That last clause is the reason this is not solved by a smarter breaker. A device
list is an intimate document — it says who is home, who is ill, who does laundry
at 2 a.m. No hostel resident, and no apartment neighbour, should have to publish
one to keep their fridge running.

## Who this is for

- **Hostels and dormitories** on inverter or generator backup, with a warden who
  currently makes these decisions by hand and by memory.
- **Apartment blocks** sharing a service transformer where simultaneous EV
  charging and evening cooking collide.
- **Small institutional microgrids** — clinics, schools, field offices — that
  island during outages and must keep specific loads alive.
- **Distribution utilities**, one layer up, who want a flexibility envelope from
  a building rather than switching authority over its appliances.

## Why now, and why in India

India is installing the measurement layer and has not yet built the coordination
layer above it.

- The **RDSS** programme targets **25 crore smart meters** with an
  implementation deadline of **March 2028**, against roughly ₹2.83 lakh crore of
  sanctioned investment. That is a nationwide rollout of devices that can
  *observe* consumption. [S12]
- Observation is not coordination. A meter that reports a 4.6 kW draw against a
  1.8 kW inverter has told you that you are failing. It has not decided, acted,
  or proved recovery.
- The IEA's work on demand flexibility identifies the same gap globally:
  flexible demand is systematically under-used, and grid-interactive buildings
  are named specifically as an Indian opportunity joining efficiency, digital
  technology and peak shifting. [S09][S10][S11]

Truss is the layer that turns the meters India is already installing into
something that can act, fairly, and prove that it did.

## What "fair" has to mean here

"Fair" cannot be a vibe on a dashboard. In this system it has three concrete
commitments, and each is testable:

1. **A floor nobody crosses.** Every member declares a safety floor. While the
   system reports feasibility, no member is allocated below it. If the cap
   cannot cover the sum of floors, the system says so and names the members it
   cannot serve — it does not quietly pick losers.
2. **Equal treatment of equal need.** Surplus above the floors is allocated by
   water-filling, which produces the max-min fair allocation: raise everybody
   together until either they are satisfied or the cap binds. Two members with
   identical offers get identical budgets, always.
3. **Sacrifice is remembered and repaid.** A member curtailed heavily in one
   round carries **debt**, and debt weights the next allocation. Nobody is the
   designated loser twice.

Those three are Elinor Ostrom's design principles for common-pool resources —
clear boundaries, congruence between rules and conditions, monitoring, and
graduated response — rendered as an allocation function. [S08] The commons
literature is not decoration here: it is the reason the fairness rule has the
shape it has, and it is the answer when a judge asks why we did not just sort by
priority.
