# Demo run-sheet

Keep this open on a second screen. Everything below is what the UI can actually do today.

## Before you walk in

Two servers, two terminals. Start them in this order and leave them running.

```bash
.venv/bin/truss mock --port 8000
```

```bash
npm --prefix web run dev
```

Open **http://localhost:5173**. Check the banner says `MOCK WORKSPACE`.

If the console shows "Waiting for the mock server", the first command isn't running.

## The one honesty rule

The console is wired to the **mock** backend. The controls change synthetic state — they are
illustrations, not measurements. Say so once, early, in plain words:

> "This screen is our mock. The numbers move by the real allocation rule, but these are
> synthetic observations, not a live measurement. The real process evidence is the test run —
> I'll show you that at the end."

Never say a mock control "killed a process". It didn't. What actually kills real processes is
`pytest`, and that is your evidence, not this screen.

## Where you put values in

All of it is on `/console`, section `03 / MOCK CONTROLS`.

| Control | What it is | What to say |
|---|---|---|
| **Capacity slider + Apply cap** | Sets the site ceiling in watts | The main lever. Drag it down and watch the split re-resolve. |
| **Stop coordinator** | Illustrates the coordinator dying | Leases run out, homes fall to their floors on their own. |
| **Stale home C** | Makes one household go silent | Shows `UNKNOWN`, never `0 W`. |
| **Clear state** | Resets the illustration | Use between runs so you always start clean. |
| **Fixed baseline / Replay** | Disabled | Capability flags are off. Don't click them and don't promise them. |

Everything else on the page is read-only output.

## The four numbers to name out loud

On each household card, point at these and say they are **four different facts** that the console
never merges:

- **Baseline** — the floor this home always keeps
- **Proposed** — what the planner suggested
- **Issued** — what was actually granted
- **Reserved** — what might still be outstanding, held conservatively

The gap between *issued* and *reserved* is the whole safety argument. Reserved can sit above the
new cap during a transition, because permission already given does not vanish when you drag a slider.

## Six-minute run

**0:00 — Home page.** Scroll the six topic cards. One line each, don't read them out. Land on
card 05: "kill the coordinator and it gets quieter, not more dangerous."

**1:00 — Console, steady state.** Cap at 5000 W. Name the four numbers above. Point out
`Compliance: Not measured` and say plainly that the mock does not fake evidence.

**2:00 — Drop the cap.** Slider to ~2300 W → **Apply cap**. Watch the split re-resolve. Say:
"small askers keep what they asked for; the big ones share what's left equally."

**3:00 — Drop it below the floors.** Slider to ~500 W → **Apply cap**. It reports **INFEASIBLE**
and names the shortfall. Line: *"a system that can't meet its constraint has to say so, not fake it."*

**4:00 — Stop coordinator.** Leases expire, homes fall to their floors. Nothing was sent to them —
there was nobody left to send it.

**4:45 — Stale home C.** It shows `UNKNOWN`, not zero. Line: *"silence is not proof of zero draw."*

**5:15 — The evidence.** Switch to a terminal:

```bash
.venv/bin/pytest -q
```

45 tests, ~84s, against a real Mosquitto broker and 12 real processes. This is where the
coordinator actually gets killed. Let it run while you talk.

**5:45 — Close on the boundary.** No mains switching, no certification, no savings claims, no AI
deciding what's essential, no real appliances or medical devices.

## If something breaks

- **Console stuck on "Waiting for the mock server"** — `truss mock --port 8000` isn't running.
- **Page won't load** — `npm --prefix web run dev` isn't running.
- **A control does nothing** — hit **Clear state**, then retry once. Don't debug live; move on.
- **Everything is broken** — close the browser and run `pytest -q` instead. The test output is
  stronger evidence than the UI, and judges notice which one you reached for.

## Questions you will get

**"Are you actually switching power?"** No. Nothing touches mains voltage. The appliances are
Python objects holding a watts number. The hard part isn't the switch — you can buy a relay this
afternoon. The hard part is deciding who gets how much, privately, and surviving the coordinator
dying. That's what's built.

**"Why 6 seconds?"** It's 3× the 2s renewal cadence, so a home can lose two consecutive renewals
before shedding. It's also the blackout after a coordinator restart, since a restarted coordinator
must wait one full lease lifetime before issuing anything.

**"How do you know a device obeyed?"** We don't assume. Commands are versioned and expiring; the
enforcer replies with its *observed* watts. Desired and observed are separate columns.

**"What's missing for production?"** Per-device identity, TLS, key rotation, signed firmware,
certified actuation, standards adapters. None of it changes the protocol — it changes the driver
behind the same message.
