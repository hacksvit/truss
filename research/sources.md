# Evidence ledger

> **Review amendment, 6 September 2026:** Several load-bearing interpretations
> below are overstated. Read [the research review](2026-09-06-review.md) before
> using S01/S02/S07 in the pitch. S01 does not prove the receipt-started watt
> protocol safe; S02 must be applied to normalised surplus with fixed weights;
> S07 does not restrict PEM to like-device fleets. The original entries remain
> below for traceability, not as an endorsement of those interpretations.

Every claim in the plans that rests on an outside source carries a `[Sxx]` tag
that resolves here. Anything without a tag is our own design reasoning and should
be argued on its merits, not cited.

## Confidence vocabulary

- **Verified** — the linked source directly supports the limited claim made.
- **Strong inference** — two credible facts align, but no single source joins
  them. Labelled wherever used.
- **Speculation** — labelled, and excluded from every strategy claim.

Three standing rules:

1. Commercial product pages establish that a **feature exists**. They do not
   establish independent performance claims.
2. Standards references establish **protocol direction**. They do not establish
   interoperability or certification of this prototype.
3. Problem-class evidence (IEA, RDSS) establishes that **the problem is real**.
   It does not establish demand, savings, or policy approval for Truss.

---

## Core mechanism

| ID | Source | What it supports |
|---|---|---|
| **S01** | Gray & Cheriton, *Leases: An Efficient Fault-Tolerant Mechanism for Distributed File Cache Consistency*, SOSP '89 | The lease mechanism, the fail-safe expiry argument, and the coordinator-restart rule (a recovering server must honour leases it cannot remember by waiting out the maximum term). Non-Byzantine failures affect performance, not correctness; short terms bound the damage. |
| **S02** | Max-min fairness / leximin / water-filling literature (Bertsekas & Gallager; Radunović & Le Boudec, *A Unified Framework for Max-Min and Min-Max Fairness*) | Water-filling yields the max-min fair allocation; the set of max-min fair allocations is the set of lexicographically maximal feasible allocations. Justifies the allocator and its fairness claim. |
| **S07** | Packetized Energy Management — Almassalkhi, Frolik, Hines et al.; asynchronous, anonymous coordination of distributed energy resources | Nearest prior art. Devices make anonymous asynchronous requests for fixed-length energy packets; the coordinator needs only those requests plus aggregate deviation. Establishes that offer/grant coordination with privacy and statistical fairness is a real, published approach — and marks the boundary of what is ours. |
| **S08** | Ostrom, *Governing the Commons* (1990); Ostrom Workshop design-principle materials | The eight design principles for common-pool resource governance — clear boundaries, congruence with local conditions, collective choice, monitoring, graduated sanctions, conflict resolution, recognised rights to organise, nested enterprises. The intellectual frame for the member boundary, the debt ledger and the fairness rule. |

## Standards

| ID | Source | What it supports |
|---|---|---|
| **S03** | OASIS MQTT 5.0 specification | Lightweight publish/subscribe for M2M and IoT. Sessions, QoS, message expiry, Will messages. |
| **S04** | Eclipse Mosquitto documentation | Open-source lightweight MQTT 5/3.x broker. |
| **S05** | OpenADR Alliance — OpenADR 3.x material, VTN/VEN architecture | Standardised exchange of demand-response price, reliability and capacity events. OpenADR 3.0 moves to a REST API with webhook push; 3.1 is not backwards compatible with 3.0. Establishes the upstream signal direction only. |
| **S06** | Connectivity Standards Alliance — Matter 1.5 release material | New energy capabilities: the electrical energy tariff device type and the Commodity Tariff, Commodity Price, Electrical Grid Conditions, Energy Preference, Meter Identification, Commodity Metering and Power Topology clusters. Establishes that device-level flexibility is becoming standard-expressible. **Not** evidence that we implement Matter. |

## Problem class

| ID | Source | What it supports |
|---|---|---|
| **S09** | IEA, *Electricity 2026* — flexibility analysis | Demand response and flexible building loads are systematically under-used; system benefits are real. Problem class only. |
| **S10** | IEA, *Efficient Grid-Interactive Buildings in India* | Grid-interactive buildings named as an Indian opportunity joining efficiency, digital technology and peak shifting. |
| **S11** | IEA, *Scaling Up Demand Flexibility* | Reliability, cost, renewable integration and network-constraint benefits of demand flexibility. |
| **S12** | India RDSS programme reporting (Ministry of Power / DISCOM coverage) | Smart-meter rollout targeting 25 crore meters with a March 2028 implementation deadline against roughly ₹2.83 lakh crore of sanctioned investment. Supports the "measurement layer is arriving, coordination layer is missing" argument. **Does not** establish demand for Truss. |

## Prior art we are measured against

| ID | Source | What it supports |
|---|---|---|
| **S13** | SPAN official material | Circuit control, load priority, dynamic EV charging in a smart panel. Feature existence only. |
| **S14** | Lumin official material | Power limit, load management, scheduling, local control. Feature existence only. |
| **S15** | Home Assistant energy documentation | Multi-brand energy visibility and device integration. |
| **S16** | Home Assistant MQTT documentation | Local broker, discovery, MQTT 5 integration. |

## Tooling

| ID | Source | What it supports |
|---|---|---|
| **S20** | Google OR-Tools documentation | CP-SAT suitability for constraint and scheduling problems with discrete on/off loads, deadlines, minimum runs and capacity constraints. |
| **S21** | Hypothesis documentation | Property-based test generation over the safety invariants. |
| **S22** | Wokwi documentation | ESP32 Wi-Fi/MQTT simulation. **Rehearsal aid only** — its public gateway cannot reach our local LAN. |

## Event

| ID | Source | What it supports | Status |
|---|---|---|---|
| **S17** | Official graVITas '26 / Code2Create 7.0 event page | Venue, duration, team size, hardware self-supply, from-scratch rule, AI allowance, deliverable links. Judging criteria listed as TBD. | **Date conflict unresolved — see [plans/14-rules.md](../plans/14-rules.md)** |
| **S18** | Unstop organiser listing | Registration, eligibility, round sequence, eliminatory prototype review, listed criteria without weights, prohibition on pre-built projects and prior commits. | Verified as of the source research pass |
| **S19** | ACM-VIT public material | Open Innovation framing, idea-submission deadlines, and a conflicting 7–9 September date. | **Conflicts with S17. Confirm directly.** |

---

## What we must never say

- That we implement OpenADR or Matter. We ship one OpenADR-*shaped* JSON fixture
  and a Matter adapter *interface*. Both are labelled in the UI and the README.
- That Truss is cheaper, greener or more efficient than any named product. We
  have measured none of that.
- That Packetized Energy Management is our idea. It is prior art, we cite it, and
  naming your nearest neighbour in the literature is a strength in front of a
  technical judge.
- That any Indian policy document mandates or endorses this. Draft consultation
  material is not law and is not cited here for anything load-bearing.

## Review sources and additional scope

The linked [review register](2026-09-06-review.md#source-register-and-what-it-actually-establishes)
contains **S23–S38**, with direct source links, publication/version details,
access limitations and confidence labels. These extend this ledger; they do not
renumber S01–S22. In particular, EEBus, IEEE 2030.5 operating envelopes,
FlexOffers and household-local privacy research are now part of the comparison.

| ID | Source | Limited use |
|---|---|---|
| **S39** | [Pydantic strict mode](https://docs.pydantic.dev/latest/concepts/strict_mode/) and [discriminated unions](https://docs.pydantic.dev/latest/concepts/unions/#discriminated-unions) | Schema facilities only; freshness, authority and physical safety need separate checks. |
| **S40** | [SGLang official project](https://github.com/sgl-project/sglang), [installation](https://docs.sglang.io/docs/get-started/install), [structured-output documentation](https://github.com/sgl-project/sglang/blob/main/docs_new/docs/advanced_features/structured_outputs.mdx) | Local model-serving and constrained-output capabilities. No verified throughput, semantic correctness or hardware compatibility for Truss. |
| **S41** | [Qwen2.5-1.5B-Instruct model card](https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct) | Candidate model architecture/size and published SGLang use path; no medical competence or local performance claim. |
| **S42** | [FDA, medical-device power-outage preparation](https://www.fda.gov/media/80782/download) and [disaster guidance](https://www.fda.gov/medical-devices/emergency-situations-medical-devices/fda-offers-tips-about-medical-devices-and-natural-disasters) | Need for device-specific outage planning. Does not certify Truss or establish safe interruption times. |

SGLang and protected-load decisions are specified in
[plans/22](../plans/22-sglang-and-protected-loads.md). Local hardware observations
there are read-only observations from this session; the inference feasibility
verdict is explicitly an inference, not a completed experiment.
