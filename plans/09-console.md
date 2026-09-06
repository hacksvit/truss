# 09 — The console

## One screen. It answers seven questions.

1. What is the limit? → **top chord**, drawn as a hard line
2. What are we actually drawing? → observed load, live, against that line
3. What can't we see? → the **camber** band, hatched, under the chord
4. Who has what? → five member panels with budget, draw and lease countdown
5. What changed, and why? → plan timeline with reason codes
6. Did the devices obey? → pending / verified / rejected / stale markers
7. Who has given up the most? → the **debt ledger**

If a panel does not answer one of those seven, it is deleted. This is the rule
that keeps the screen legible under demo pressure.

## Layout

```
┌──────────────────────────────────────────────────────────────────────┐
│  TRUSS   site: hostel-block-c        ● LEASED    rule: water-filling │
├──────────────────────────────────────────────────────────────────────┤
│  TOP CHORD ══════════════════════════════════════════ 1800 W         │
│  ▒▒▒▒▒ camber 240 W (member D stale) ▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒             │
│  ████████████████████████████████ observed 1512 W                    │
│  BOTTOM CHORD ────────────────────────────────────────  820 W        │
├──────────────────────────────────────────────────────────────────────┤
│ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐               │
│ │   A    │ │   B    │ │   C    │ │   D    │ │   E    │               │
│ │ 312 W  │ │ 298 W  │ │ 340 W  │ │ STALE  │ │ 322 W  │               │
│ │ ▓▓▓▓▓░ │ │ ▓▓▓▓░░ │ │ ▓▓▓▓▓▓ │ │ ▒▒▒▒▒▒ │ │ ▓▓▓▓▓░ │               │
│ │ 4.8 s  │ │ 4.8 s  │ │ 4.8 s  │ │ ──     │ │ 4.8 s  │  lease TTL    │
│ │ 6 dev  │ │ 5 dev  │ │ 6 dev  │ │ 5 dev  │ │ 5 dev  │               │
│ │ debt 0 │ │ debt 0 │ │ 240 Wh │ │ 180 Wh │ │ debt 0 │               │
│ └────────┘ └────────┘ └────────┘ └────────┘ └────────┘               │
├──────────────────────────────────────────────────────────────────────┤
│  PLAN TIMELINE     ▸ 19:41:02  cap_drop 5000→1800  plan-0042         │
│                    ▸ 19:41:02  6 devices deferred · 0 rejected        │
│                    ▸ 19:41:07  verified below chord (4.9 s)           │
├──────────────────────────────────────────────────────────────────────┤
│  [ TOP CHORD ────●──── ]  [ PROTECT ▾ ]  [ CHAOS ▾ ]  [ REPLAY ]     │
└──────────────────────────────────────────────────────────────────────┘
```

## The lease countdown is the centrepiece

Every member panel shows its lease TTL ticking down and resetting on renewal —
`4.8 s → 4.6 s → … → renewed`. It looks like a heartbeat, and that is exactly
what it is.

It costs almost nothing to build and it does something no other element can: it
makes the safety mechanism **visible while it is working**. When the judge kills
the coordinator, they do not have to take our word for what happens next. They
watch five countdowns run to zero and five panels drop to their floor.

That is the moment the project stops being a dashboard.

## The load path inspector

Click any deferred device. A panel opens with the causal chain, read directly
from the `basis` block that travelled with the lease — so the explanation cannot
drift from the decision, because it *is* the decision:

```
washer-1 · deferred · 19:41:02

  top chord              1800 W
  − camber                240 W   member D stale, last draw 240 W
  = allocatable          1560 W

  rule                   debt_weighted_water_filling
  member C weight        1.24     (debt 240 Wh)
  member C budget         340 W
  member C floor          180 W

  local decision         washer-1 (520 W) deferred
                         fridge, router, light held
  deadline               09:00 · 2 of 3 slots remain · still satisfiable
  debt accrued           +180 Wh

  [ show event trace ]  [ replay from here ]
```

Judges ask "why did it do that?" This answers in five seconds, with arithmetic
rather than adjectives, at any depth they want to push.

## The four judge controls

Exactly four. Every additional control is a way for the demo to go wrong.

| Control | What it proves |
|---|---|
| **Top chord slider** | Constraint-aware allocation, live, under a limit they chose |
| **Protect ▾** | The plan bends elsewhere rather than violating the cap |
| **Chaos ▾** | Kill member · kill coordinator · partition · drop acks · impossible cap |
| **Replay** | Deterministic reconstruction from the event log |

## Colour, and one rule about it

| State | Colour | Meaning |
|---|---|---|
| Verified | green | Commanded, acknowledged, observed |
| Pending | amber | Commanded, not yet acknowledged — **working, not broken** |
| Stale | hatched grey | Unknown. Reserved as camber |
| Rejected | blue | Device legitimately refused. Not an error |
| Over chord | red | Reserved exclusively for a genuine cap violation |

**Amber never means error.** Red appears only for a real violation of I1. If red
is on screen at the end of a demo run, we have a bug, not a colour choice — and
that is precisely why the rule exists.

## Anti-requirements

No login. No settings page. No map. No "AI insights" panel. No gauges that
duplicate a number already on screen. No animation that outlives its transition.
No dark-pattern green when the state is not verified.
