# 16 — The web front end

Owner: **M4 (+ M5 for assets)**. This is the largest single piece of work that
is not the coordinator, and it is entirely parallelisable — read
[Contract first](#contract-first) before writing a line.

[09-console.md](09-console.md) specifies the *judged operator screen*. This
document specifies the **whole site** that screen lives inside.

---

## What it is

One local web app, served from the primary laptop, with three routes.

| Route | Name | Purpose | Audience |
|---|---|---|---|
| `/` | **Showcase** | Explains what Truss is and why it works, with live animated diagrams | A judge walking past the table |
| `/console` | **Console** | The judged operator screen. Four controls, seven questions | The judge we are demoing to |
| `/lab` | **Lab** | Topology configurator: N houses × M appliances, pick the allocator, watch it scale | The judge who asks "does this scale?" |

No login. No cloud. No external network calls of any kind — it must work with
the venue Wi-Fi switched off.

---

## Stack

| Layer | Choice | Why |
|---|---|---|
| Build | **Vite + React + TypeScript** | Fast HMR, one `npm run dev`, no framework ceremony |
| Styling | **Tailwind** | Fast, and the design tokens drop straight in |
| Charts | **visx** or **Recharts** | Recharts is faster to write; visx if we need the load-path diagram to be custom |
| Live data | **WebSocket** to the backend, JSON frames | One connection, server pushes state at 4 Hz |
| Fallback | REST polling at 1 Hz | If the socket drops, the UI degrades instead of freezing |
| State | **Zustand** or plain context | Do not add Redux |

`npm run dev` on the primary laptop, other machines reach it at
`http://<laptop-ip>:5173`. Bind to `0.0.0.0`, not `localhost`.

---

## Contract first

**The front end is built against a mock server from hour one and does not wait
for the backend.** This is the single most important process rule in this
document — it is what keeps four people from blocking on M1.

`mock/state.json` is a frozen, realistic snapshot committed in the first hour.
`npm run mock` serves it plus a scripted 90-second event replay over the same
WebSocket shape the real backend uses. Every screen must be fully buildable and
demoable against the mock, with the real backend swapped in at hour 12 by
changing one URL.

If the real backend is late, the mock is the demo. That is the point.

### The frame the backend pushes

```jsonc
{
  "t": 1725632462.118,
  "site": {
    "top_chord_w": 1800,
    "camber_w": 240,
    "allocatable_w": 1560,
    "observed_w": 1512,
    "state": "leased",          // leased | recovering | infeasible | uncoordinated
    "rule": "debt_weighted_water_filling",
    "plan_id": "plan-0042",
    "plan_latency_ms": 7.2
  },
  "members": [
    {
      "id": "block-c",
      "budget_w": 340,
      "observed_w": 331,
      "floor_w": 180,
      "debt_wh": 240,
      "lease_ms_remaining": 4820,
      "status": "ok",           // ok | stale | offline | at_floor
      "devices": [
        { "id": "washer-1", "kind": "washer", "w": 0, "state": "deferred",
          "ack": "verified", "deadline": "09:00", "protected": false }
      ]
    }
  ],
  "events": [
    { "seq": 88213, "t": 1725632462.1, "kind": "cap_drop",
      "text": "cap 5000 -> 1800", "plan_id": "plan-0042" }
  ],
  "metrics": {
    "cap_compliance_pct": 100.0,
    "time_to_safe_s": 4.9,
    "lease_violations": 0,
    "ack_success_pct": 98.4,
    "recovery_time_s": 2.1,
    "jain": 0.94
  }
}
```

The commands the UI sends back:

```
POST /api/cap          { "watts": 1800 }
POST /api/protect      { "device_id": "washer-1", "protected": true }
POST /api/chaos        { "action": "kill-coordinator" }
POST /api/topology     { "members": 12, "devices_per_member": 8, "mix": "hostel" }
POST /api/rule         { "rule": "water_filling" | "cpsat" | "uncoordinated" }
POST /api/replay       { "from_seq": 88000 }
GET  /api/bundle       -> incident zip (log + metrics + replay)
```

---

## `/console` — the judged screen

Fully specified in [09-console.md](09-console.md). Build that first; it is the
only route that is not optional. Two elements deserve repeating here because
they are the ones that win:

**The lease countdown.** Every member card shows its lease TTL ticking down and
resetting on renewal — `4.8 s → 4.6 s → … → renewed`. It must be smooth (animate
locally between frames, do not step at 4 Hz) because when the judge kills the
coordinator, five countdowns running to zero *is the demo*. This element is
worth more than any chart on the page.

**The load path inspector.** Click any deferred device, get the causal chain
rendered from the `basis` block that travelled with the lease. Arithmetic, not
adjectives. See 09 for the exact layout.

---

## `/` — Showcase

A scrolling page a judge can read in ninety seconds while we set up. Roughly six
screens:

1. **The moment.** The hostel at 19:40. 4.6 kW against a 1.8 kW inverter, and the
   three bad options. Animated: the bar overruns the line, the line turns red.
2. **What's already there.** The appliance table — water heater, washer, laptop,
   fridge, router, CPAP — each with its real constraint. The point lands on its
   own: this information exists and nothing uses it.
3. **Offers, not device lists.** Animate a house collapsing into five numbers.
   Show explicitly that the device list *stays inside the house*. This is the
   privacy argument and it should be the most memorable animation on the page.
4. **Water-filling.** The glass-filling animation. Five vessels rising together
   until the jug runs out. It explains a fairness theorem in four seconds.
5. **The lease.** A countdown ticking; the coordinator vanishes; every house
   steps down to its floor. Caption: *safety is a property of the protocol, not
   the planner.*
6. **The boundary.** Never switches mains voltage. Not certified. No savings
   claims. Ends on honesty, deliberately.

Every animation must be **pausable and loopable**, and none may autoplay sound.

---

## `/lab` — the scalability answer

This route exists to answer one judge question — *"does this actually scale?"* —
with a demonstration instead of a claim.

### Controls

| Control | Range | Default |
|---|---|---|
| **Houses (members)** | 1 – 50 | 5 |
| **Appliances per house** | 2 – 20 | 6 |
| **Device mix** | `hostel` · `apartment` · `clinic` · `custom` | `hostel` |
| **Allocator** | `uncoordinated` · `water-filling` · `CP-SAT` | `water-filling` |
| **Site capacity** | 200 W – 20 kW | 1800 W |
| **Lease TTL** | 2 – 30 s | 6 s |
| **Tick rate** | 1 – 10 Hz | 4 Hz |
| **Fault injection** | the six chaos actions | none |

Changing houses or appliances **respawns the fleet live** — the backend tears
down and reseeds, and the UI shows the new topology filling in. Going from 5
houses to 50 in front of a judge, and having it just work, is worth more than
any slide about scalability.

### The three panels that make the argument

1. **Planning latency vs member count.** A live-updating scatter. Water-filling
   stays flat and microsecond-scale as houses climb, because the coordinator
   sees *offers*, not devices. **This is the whole scaling argument, drawn.**
   Overlay CP-SAT on the same axes and watch it bend upward — that contrast is
   the most honest thing on the page.
2. **Device count vs coordinator work.** Hold houses at 10 and push appliances
   per house from 2 to 20. Coordinator latency does not move. Member-local work
   does. That is the `O(members)` boundary made visible, and it is the same
   boundary that gives privacy.
3. **Fairness over time.** Delivered ÷ requested flexible energy per member,
   stacked, with the debt ledger beneath it. Run it for two minutes with a
   fluctuating cap and watch curtailment rotate rather than settle on one
   unlucky house.

### Presets

One-click scenarios so nothing has to be typed during a demo:

- `hostel-evening` — 5 houses, 6 appliances, cap drops 5 kW → 1.8 kW
- `apartment-ev` — 8 houses, 4 appliances, two EV chargers, cap 7 kW
- `clinic-outage` — 3 houses, 8 appliances, high protected fraction
- `stress-50` — 50 houses, 12 appliances, cap 30 kW *(the scaling demo)*
- `impossible` — cap below the sum of floors *(forces INFEASIBLE)*

---

## Assets — M5

Everything below is **flat vector, single-weight stroke, no gradients, no
shadows**, matching the console's line-drawing register. Consistency matters far
more than individual quality; twelve icons that share a grid beat six beautiful
ones that do not.

- **Appliance icons**, 24 px grid, 2 px stroke: water heater, washing machine,
  refrigerator, laptop charger, ceiling fan, light, router, EV charger, water
  pump, air conditioner, medical device, generic load.
- **House / member card glyph** in four states: ok, at-floor, stale (hatched),
  offline.
- **State markers**: pending, verified, rejected, stale, over-chord.
- **The logo**, per [../LOGO.md](../LOGO.md) — commissioned separately, not drawn
  by us.
- **Favicon** at 16 / 32 / 180 px.
- **OG image** 1200 × 630 for when the repo link is shared.
- **Six demo screenshots** at 2560 px wide, captured at hour 38 during the
  freeze, for the backup deck.

Icons live in `web/src/assets/icons/` as individual SVGs and are compiled into a
sprite at build time. Do not inline thirty SVGs into components.

---

## Design tokens

Straight from [../LOGO.md](../LOGO.md). Put these in `tailwind.config.ts` in the
first hour so nobody hand-codes a hex value.

```ts
colors: {
  ink:        { DEFAULT: '#0B0D12', 2: '#12151C', 3: '#1A1E27' },
  hairline:   '#272C38',
  chord:      { DEFAULT: '#E8EAED', low: '#6E7686' },
  steel:      '#8B93A3',
  compression:{ DEFAULT: '#F5A524', soft: '#FFD08A' },  // pending / under load
  tension:    '#5B9DD9',                                 // links, rejected
  verified:   '#3FB27F',
  stale:      '#6B7280',                                 // always hatched, never solid
  fault:      '#E5484D',                                 // cap violation ONLY
}
```

Two rules that are not negotiable and will be checked at review:

- **Amber never means error.** It means *working, under load*. A pending command
  is amber. A failure is never amber.
- **Stale is always hatched, never solid.** A flat grey block claims knowledge
  the system does not have.

---

## Definition of done

- [ ] Runs from `npm run dev` on a laptop that has never seen the repo, offline.
- [ ] Every route works against `npm run mock` with the backend switched off.
- [ ] Console answers all seven questions from 09 on one screen, no scrolling,
      at 1920 × 1080 **and** at 1366 × 768 *(assume the venue projector is bad)*.
- [ ] Lease countdowns animate smoothly, not in 4 Hz steps.
- [ ] Killing the coordinator visibly drives all five members to floor.
- [ ] `/lab` goes from 5 to 50 houses without a reload or a crash.
- [ ] Load path inspector opens in one click from any deferred device.
- [ ] No network request leaves the laptop. Verified with the Wi-Fi off.
- [ ] Frozen at hour 36. After that, bug fixes only.

## Anti-requirements

No login, no settings page, no map, no "AI insights" panel, no dark/light
toggle, no onboarding tour, no toast notifications, no gauge that duplicates a
number already on screen, no animation that outlives its transition, and no
chart that exists because the library made it easy.
