# 03 — Prior art, and why it does not close this gap

The fastest way to lose a judge is to describe a solved problem. Here is what
exists, stated fairly, and the specific thing each one does not do.

| What exists | What it genuinely does | What it does not do |
|---|---|---|
| **Smart panels** (SPAN, Lumin) | Circuit-level control, load priority, dynamic EV charging, local operation. Real products. [S13][S14] | Optimise **one property**, behind **proprietary hardware**, with the panel owner holding switching authority. There is no notion of independent households negotiating a shared limit. |
| **Home energy platforms** (Home Assistant Energy) | Multi-brand visibility, device integration, local MQTT with discovery. Excellent. [S15][S16] | Visibility and user-authored automations. No allocation across parties, no fairness, no lease safety, and rules are written per-home rather than negotiated between homes. |
| **Utility demand response** (OpenADR) | Standardised exchange of price/reliability/capacity events between utilities, aggregators and control systems. OpenADR 3.x moves to REST with webhooks. [S05] | Stops at the building boundary. It signals *that* capacity is constrained; it does not decide which of your neighbour's loads yields, or prove that it did. |
| **Matter 1.5** | New energy device types and clusters — Commodity Tariff, Commodity Price, Electrical Grid Conditions, Energy Preference, Power Topology — so devices can report true cost and adjust operation. [S06] | Device interoperability, not allocation. It makes flexibility *expressible per device*. Something still has to decide, fairly, across many owners. That is the gap. |
| **Rotational load shedding** | Universally deployed, well understood, zero infrastructure. | Coarse to the point of cruelty. It cuts by geography, not by need, and it cannot tell a CPAP machine from a water heater. |
| **Packetized Energy Management** (academic, and commercially deployed) | Devices make anonymous, asynchronous requests for fixed-length energy packets; a coordinator grants or denies. Provides statistically fair grid access and preserves privacy and quality of service. [S07] | This is the closest prior art and we should say so out loud. It coordinates a **fleet of like devices** for a utility. It does not model a **household boundary** with its own floor, deadlines and accumulated debt, and it does not provide a per-member safety lease. |

## Where Truss actually sits

Between the utility signal and the device, at the layer nobody owns:

```
  OpenADR 3.x         capacity / price / reliability event
        │             "the feeder has 1.8 kW for the next 30 minutes"
        ▼
  ┌──────────────────────────────────────────────┐
  │                   TRUSS                      │   ← the gap
  │  offers → fair allocation → leases → proof   │
  └──────────────────────────────────────────────┘
        ▲
  Matter 1.5          device-level flexibility, tariff and grid awareness
        │             "this water heater needs 40 min before 06:00"
```

The defensible novelty is not "energy management", which exists. It is the
combination of four things that do not currently appear together:

1. **A household privacy boundary that is also the scaling boundary.** Members
   publish offers, not device lists. The coordinator's problem is `O(members)`.
2. **A safety lease rather than a command.** The cap holds under coordinator
   death, network partition and total message loss — see [08-safety.md](08-safety.md).
3. **Fairness with memory.** Curtailment debt carries between rounds, so the
   same member is not the designated loser twice.
4. **Refusal.** When the constraint cannot be met, the system says so and names
   who it cannot serve, rather than reporting a compliance it did not achieve.

## What we must never claim

- That we implement OpenADR or Matter. We implement one *OpenADR-shaped* JSON
  fixture and we define a Matter adapter interface. Both are labelled as such in
  the UI and in the README.
- That we are more efficient, cheaper or greener than any named product. We have
  measured none of that and will not imply it.
- That Packetized Energy Management is ours. It is prior art, it is good, we
  cite it, and being able to name your nearest neighbour in the literature is a
  strength in front of a technical judge, not a weakness.
