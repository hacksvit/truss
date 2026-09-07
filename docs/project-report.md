# Truss: sharing power, keeping promises

Final project report | 7 September 2026

Truss is a working software prototype for sharing limited electrical capacity between homes. Each home makes its own appliance decisions. A coordinator shares spare capacity, while a separate permission system checks what has already been promised.

The current demonstration runs five virtual homes through a real local MQTT broker. It includes independent enforcement processes, an operator console, failure drills, recordings, an allocation benchmark, and a six-page explanatory website. It does not control real household electricity.

## 1. The problem we chose

Several homes or hostel rooms can share an inverter, feeder or backup supply. Their combined demand may exceed the capacity available. A useful system must decide which flexible loads can wait without repeatedly favouring the same participant or collecting every household's appliance list in one central planner.

That is the scenario Truss explores. The supplied wattages are fictional configurations, not measurements from a hostel. We have not run a field pilot or established customer demand, financial savings or energy savings.

The central question is: **how can separate homes share a limit when messages can arrive late and some programs can stop?**

## 2. How it works, in everyday language

**Local helper.** Each home has a small program called a member agent. It reads that home's appliance settings and decides what can run within its allowance. The implemented unit is a household; a room could become a member in a future installation.

**Small request.** The home sends an aggregate demand offer. The coordinator receives how much power the home could use, rather than a list of devices to switch. The separate demo observer can see fictional appliance details so visitors can inspect the result.

**Essentials first.** Every member has an approved basic allowance, called its floor. Protected and unclassified loads have their full configured maxima covered before the run starts. Ordinary requests cannot raise those approved floors.

**Fair shares.** The allocator shares the surplus above those floors. Think of filling glasses together: when one home has enough, its extra share stops growing and the others continue. Equal weights are the default.

**Kept promises.** Before a proposed share becomes permission, a reservation gate checks earlier permissions that might still be used. A new plan cannot erase an old promise merely because the dashboard now shows a smaller number.

**Short permission.** Extra power is permitted for six seconds from the time the member began its request. A reply that arrives late has less usable time. It does not receive a fresh six seconds on arrival.

**Local expiry.** A separate virtual plant process enforces each home's allowance. If the member or coordinator stops, that plant can still expire flexible authority and return to the configured floor. This relies on the plant staying healthy and its timing assumptions holding.

**Visible evidence.** The console keeps suggested power, issued permission, reserved capacity and observed draw separate. Missing readings remain unknown. An animation reaching zero is never treated as proof that a real device switched off.

## 3. What we built

| Part | Completed behaviour |
| --- | --- |
| Live runtime | One owned broker, five household agents, five independent virtual plants and one coordinator, supervised on one Linux host. |
| Allocation | Deterministic surplus water-filling, exact rational targets, conservative whole-watt rounding and a separate proposal validator. |
| Authority | Request-anchored leases, retained overlapping reservations, identity and version checks, a single issuer lock and conservative restart recovery. |
| Local decisions | Fixed protected baselines and priority-based flexible assignment, including whole on/off appliance steps. |
| Fairness history | Optional bounded catch-up weighting based on withheld authorisation, checkpointed in SQLite. |
| Operator console | Live/mock selection, cap and rule controls, household explanations, failure drills, evidence downloads and recorded snapshot playback. |
| Lab | Measured allocation and validation over synthetic groups up to 5,000 members, in a bounded worker process. |
| Hosting | One-port application serving the website, live simulation, mock API and WebSockets, with Heroku buildpack and container configurations. |
| Optional display | ESP32 firmware and a read-only USB bridge for virtual site status. The screen has no allocation or appliance-control authority. |

The supplied live registry has a 5,000 W cap, 900 W of household floors and a 100 W site reserve. It contains twenty virtual appliances across five homes. The system is deterministic software; no AI model decides appliance criticality or grants power.

### The website makes the system understandable

**Home** introduces the problem and solution beneath the Truss mark. As visitors scroll, the logo endpoints detach and grow into eight illustrated cards. The carousel has depth and a finite ending. Layered clouds leave the viewport as the story moves into the cards; a large brand footer closes the page.

**Info** opens an illustrated building over twelve short chapters. Rooms rise, the facade opens, a local agent wakes, requests travel, allowances fill, permissions expire and a larger proposed layout appears. The copy distinguishes the five-home runtime from the wider allocator experiment.

**Example** is a walkable three-home illustration. Visitors can inspect appliances and the coordinator enclosure, change the illustrated supply, and see proposals separately from projected appliance draw. It is a browser calculation that follows the tested allocation rule, not the live five-home MQTT run. Movement follows the camera direction, inspection restores the walking view, and the coordinator door folds clear of the information panels.

**Console** exposes the actual local processes and their observations. **Lab** answers a narrower performance question with real measured samples. **Credits** brings five portrait cards into depth one by one, reveals each contribution, and connects them into one team arrangement.

Light and dark themes share a textured sky. The Three.js viewport has a smooth background so the model stays clear. Full cloud stacks belong to Home; Example has one cloud with the small robot inside. Phone layouts and reduced-motion reading views preserve the content without requiring the desktop animation.

## 4. Why the software is more than organising loads

A list of priorities answers only which appliance we would prefer to run. Truss also has to establish what each independently running process is still allowed to do.

### Two valid plans can still conflict

Imagine a 1,000 W site with two homes and no reserve in this simplified example. The old plan gives A 800 W and B 200 W. A new plan gives A 200 W and B 800 W. Each plan totals 1,000 W.

If B receives its increase while A misses its decrease, the two homes could still hold 1,600 W of permission. Merely checking the new plan is insufficient. Truss retains A's earlier 800 W reservation and blocks an incompatible increase for B until the old authority has expired.

This is why proposal validation and permission admission are separate mechanisms.

### Delay must consume the permission's life

If a request begins at second zero and its reply arrives at second five, only about one second of a six-second lease remains. A reply arriving after the deadline is rejected. Duplicating a reply does not renew it. This closes a failure that a receipt-started countdown would introduce.

### A crash must not erase obligations

A restarted coordinator has a new durable epoch, holds the single-issuer lock and waits a full 6.4 seconds before issuing new grants. During that uncertainty it conservatively accounts for registered maxima. It does not require a complete persisted list of old leases to pretend the old obligations disappeared: the recovery wait bounds their remaining lifetime under the model assumptions.

### Silence must not become spare power

A home last observed at 100 W might still be permitted to draw 600 W. Losing its readings does not make either 100 W or zero a sound upper bound on future use. Truss reserves possible authority, while the evidence view separately reports what is known about actual draw.

### Acknowledgement must not become invented proof

Sending a command, receiving a reply and obtaining a fresh matching plant reading are different events. Their identifiers and ages matter. The console can show an unavailable explanation or an inconclusive drill instead of manufacturing a successful result from incomplete evidence.

These are problems of time, concurrency, identity and partial knowledge. They remain even if the power-sharing formula is simple.

## 5. What is distinctive about our contribution

The engineering contribution is the inspectable combination: household-local choice, an explicit surplus-sharing policy, conservative permission accounting, independent virtual enforcement and a public explanation of their failure behaviour.

| Design choice | Why it matters |
| --- | --- |
| Planner separated from admission | A mathematically valid new allocation cannot overrule still-live permissions. |
| Member separated from plant | Killing the decision-making process does not also kill the virtual expiry mechanism. |
| Authority separated from observation | A missing meter reading does not release capacity or turn into zero draw. |
| Coordinator separated from device detail | The central allocation problem uses household offers; local appliance selection stays with the member. |
| Live separated from mock and replay | A teaching animation or old recording cannot silently become current process evidence. |
| Explanation tied to references | The inspector uses matching plan, lease and device-decision records rather than free-form generated explanations. |
| Benchmarks separated from live control | Larger synthetic allocation tests cannot issue permissions or reset the live household registry. |

We do not claim to have invented leases, energy coordination or fair resource allocation. Gray and Cheriton's work established time-limited rights and recovery considerations in distributed systems. Packetized Energy Management already studies distributed energy requests, local autonomy and limited upstream information. EEBus specifies power limits with heartbeat and failsafe behaviour. These are relevant predecessors, not implementations or certifications achieved by Truss. See the linked primary sources at the end of this report.

The defensible claim is that we built and tested this particular software system and made its difficult cases inspectable. A claim that no other system combines similar ideas would require a much broader novelty study.

## 6. Software difficulty and the hardware comparison

For this project, the main engineering difficulty lies in coordinating decisions across time and failures. Connecting a low-voltage indicator or displaying a number does not resolve delayed grants, overlapping permissions, restart recovery, stale evidence or fair surplus allocation. Those behaviours must be designed, implemented and tested regardless of which eventual actuator is used.

The optional ESP32 screen demonstrates that distinction. It can display the result, but disconnecting it has no effect on the allocation. Adding more screens would not solve any of the protocol problems above.

This is an explanation of where the work in the current prototype resides, not a measured comparison of development hours or a claim that electrical hardware is easy. Production hardware introduces its own difficult requirements: appropriate isolation and protection, reliable actuation, independent measurements, startup behaviour, timing bounds, device-specific constraints and physical validation. Real installations would need both sound coordination software and suitable independently reviewed hardware.

The strongest presentation wording is: **“We concentrated on the coordination and failure behaviour that a switch alone cannot provide. Our current enforcement is virtual; real deployment requires further hardware and systems work.”**

## 7. Scale, limitations and useful next steps

The coordinator sees one offer per member. Adding appliances inside a home increases that home's local work and observation traffic; it does not add those appliances to the allocator's input. Adding homes still increases central work. The sorted allocator is O(n log n) in member count, not constant time.

The current live runtime has five homes. The Lab can time the pure allocation path for up to 5,000 synthetic offers. It excludes MQTT delivery, persistence, interprocess communication, appliance enforcement and browser rendering. A fast Lab result is useful evidence about that algorithm, not proof of a 5,000-home deployment.

The next useful experiment is a measured multi-host test: grow the member count, record memory and message volume, measure request-to-grant latency and independent expiry lateness, and repeat under loss and overload. Cross-host freshness and actuator deadlines require explicit design; local monotonic timestamps cannot simply be compared across machines.

Whole appliances are another important extension. A 650 W binary heater cannot use a 325 W remainder. The current local policy skips the heater and reports unused permission. Returning those watts to another home in the same round would require a second admission-aware allocation pass or a richer aggregate offer. That trades utilisation against protocol complexity and potentially more information disclosure.

A practical progression would be operator interviews, realistic flexible-load traces, a supervised low-voltage actuator experiment, multi-host timing tests, then a narrowly scoped real installation with appropriate hardware expertise. Standards adapters, secure device-verifiable authority, persistent hosted evidence and reviewed non-interruptible scheduling are future work. None is already delivered by the current UI.

## 8. Evidence and the boundaries of the result

The current verification run passed 68 Python tests with no skips and 73 frontend tests. Configuration validation passed. The Python run includes real broker/process tests, not only simulated return values; it completed in 98.26 seconds on the development host. The frontend run completed in 3.21 seconds. Exact scope and known warnings are recorded in the verification guide.

These checks cover allocation, reservation sequences, delayed and duplicate messages, recovery, independent virtual plant fallback, source isolation, APIs and UI behaviour. Finite tests do not prove correctness under arbitrary scheduling, malicious actors or hardware faults.

The plant still trusts the member to forward genuine coordinator authority with the correct request deadline. The broker, host and local software are trusted. Protected floors cannot create power when the source cannot supply them. An abruptly lowered cap may remain below outstanding permission until expiry. A stopped or frozen enforcer cannot execute its expiry code. Those are explicit boundaries of the demonstrated result.

No energy-saving percentage, installation count, customer endorsement, electrical certification, standards conformance or medical continuity claim is made.

## 9. Five people, one shared idea

The names and contributions below were supplied by the team. They replace the earlier speculative M1-M5 planning assignments; they are not inferred from commit counts.

| Person | Role | Contribution |
| --- | --- | --- |
| Prashanth Manokar | Team leadership | Led the team and organised delivery. |
| Kalyan K | Concept and presentation | Shaped the idea and the presentation. |
| Pranav Vijay | Interface design | Designed the website layouts in Figma. |
| Logesh M S | Software engineering | Built and connected the complete software. |
| Kevin Solomon | Brand design | Created the brand and visual identity. |

The Credits page uses generic silhouettes alongside the team's names and contributions. AI assistance was used during implementation and documentation, alongside the team's direction, design and review. The role descriptions record team responsibility, not exclusive manual authorship of every line.

## Primary references and further reading

- [Gray and Cheriton, Leases, SOSP 1989](https://web.stanford.edu/class/cs240/readings/leases.pdf): prior work on time-limited rights and failure recovery; not a proof of electrical safety for Truss.
- [Almassalkhi and colleagues, Asynchronous coordination with Packetized Energy Management](https://madsalma.github.io/pubs/2018_springer_asynchCoord.pdf): prior work on distributed energy requests, autonomy and aggregation.
- [EEBus, Limitation of Power Consumption v1.0.0](https://www.eebus.org/wp-content/uploads/2023/04/EEBus_UC_TS_LimitationOfPowerConsumption_V1.0.0_public.pdf): an established power-limitation approach with heartbeat and failsafe concepts.
- [Project source](https://github.com/hacksvit/truss): implementation and tests. This report describes the local working tree based on commit `3e52f7e`, including the subsequent website and documentation changes; those changes may not yet be in the remote repository.

The companion guides provide the current [software design](software-design.md), [verification record](verification.md), [next steps](next-steps.md), [demo script](demo-guide.md) and [setup instructions](operations.md).
