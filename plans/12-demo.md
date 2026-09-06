# 12 — The three-minute demo

## Six beats

### 0:00–0:20 · The moment
"A hostel block loses grid power at 19:40. The inverter can hold 1.8 kW. The
block is drawing 4.6. Today, three things can happen: the inverter trips and
everyone loses everything, the warden cuts a whole floor, or somebody spends
twenty minutes walking corridors unplugging things."

Screen: five members drawing 4.6 kW against a 5 kW top chord.

### 0:20–0:40 · Why monitoring is not enough
Switch to **Uncoordinated** and drag the chord to 1.8 kW. The chord turns red;
an overload timer runs.

"Monitoring tells us we are failing. It does not decide, act, or prove recovery."

### 0:40–1:00 · The insight
"Most of that load is not urgent, and the building already knows it. A water
heater needs forty minutes before six. A washer has a deadline, not a schedule. A
laptop at 82% can wait. But none of that is expressible to whatever decides who
loses power — and nobody should have to publish a device list to keep their
fridge running."

"So each home publishes five numbers instead: floor, firm, useful, deadline
energy, and how much it has already given up. Nothing else leaves the home."

Switch to **Truss**.

### 1:00–2:10 · The live loop
1. **Judge drags the chord to 1.8 kW.** Plan in under a second. Water heaters and
   the washer defer; fridge, router and the protected device hold. Amber pending
   dots turn to green verified ticks. The physical light dims if hardware is
   green. Observed load crosses below the chord. **Time to safe: 4.9 s.**
2. **Judge clicks "protect this washer."** The plan changes *elsewhere*. Cap never
   violated. "It bent, it did not break the constraint."
3. **Judge kills member C.** Its panel goes hatched. The camber band visibly
   grows — "its last known draw is still reserved, because unknown is not zero" —
   and another member's flexible slot moves.
4. **Click the deferred washer.** The load path opens: chord, camber,
   allocatable, rule, weight, budget, local decision, deadline, debt. "That is
   not a log message. That is the arithmetic that made the decision, travelling
   with the decision."

### 2:10–2:35 · The two beats nobody else has

5. **"Kill the coordinator."**

   Five lease countdowns run to zero. Five members step down to their floors. No
   overload. No flapping. The site gets *quieter*.

   "A budget here is not a command — it is a lease with a six-second life. If it
   is not renewed, every home falls back to its safe floor on its own, without
   being told. Safety is a property of the protocol, not of the planner. Kill the
   brain and this gets safer, not more dangerous."

   Restart it. It refuses to issue a lease for one full TTL, and says so on
   screen. "It cannot know what it promised before it died, so it waits."

6. **"Now set the chord below the sum of the safety floors."**

   The system goes INFEASIBLE and names the members it cannot serve.

   "It will not report a compliance it did not achieve. A system that lies about
   its constraint is worse than no system, because someone would trust it."

### 2:35–3:00 · Boundary and next step
"Truss never switches mains voltage. It is not a smart panel, not certified, and
it makes no savings claims. It is the coordination layer between a grid event and
a home's own gateway — the layer that turns the smart meters India is already
installing into something that can act fairly and prove it did."

"Next: one real Home Assistant household on the same contract, and policy
validation with a hostel operator."

## The wow moment, named

It is not the slider. Every energy project has a slider.

**It is killing the coordinator and watching the system get safer.** That is a
distributed-systems result, it is visible without explanation, and it is
something a team that only built a dashboard physically cannot show.

## Failure proofing

| If | Then |
|---|---|
| Internet is down | Nothing changes. Broker, allocator, console and devices are all on the LAN |
| A laptop cannot join | Launch that member's IDs on the primary laptop. Single-laptop profile is rehearsed |
| ESP32 is absent | Software node on the identical contract, on-screen LED |
| ESP32 dies mid-demo | **Use it as beat 3.** A planned failure demo absorbs an unplanned one |
| Broker restarts | Leases expire, members floor, retained state restores. Narrate it |
| The live run fails entirely | **Replay.** One click, deterministic, animates the exact stored event log |
| Everything fails | 90-second recording, labelled as a recording, plus screenshots of all six beats |

## Rehearsal

Three consecutive cold-start passes before hour 36, from `git clone` on a laptop
that has never run it. Timed. If any pass exceeds 2:50, cut a beat — beat 4 goes
first, then beat 2.
