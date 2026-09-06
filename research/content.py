# -*- coding: utf-8 -*-
"""Content for the Truss brief. Edit here; build_pdf.py renders it."""

A = lambda s: f'<font color="#B46E00"><b>{s}</b></font>'      # amber emphasis
C = lambda s: f'<font name="Mono" size="8.6">{s}</font>'      # inline code

SECTIONS = [

# ============================================================ 01
{"num": "SECTION 01", "title": "The decision", "blocks": [
 ("lead", "<b>Truss</b> is a coordination layer for shared electrical capacity, built as a "
   "distributed system of independently failing agents under one hard constraint."),
 ("p", "A group of homes, hostel rooms or small buildings shares a constrained feeder, "
   "inverter or microgrid. Each " + A("member") + " knows which of its loads are critical, which "
   "can wait, and which have deadlines. Members publish only a " + A("flexibility offer") +
   " — never a device list. A " + A("coordinator") + " divides the available power by a provably "
   "fair rule and issues " + A("leases") + ": an amount, valid until an instant. Members command "
   "their own devices, acknowledge, and are measured. Unrenewed leases expire into a safe floor "
   "without anyone being told."),
 ("fig", 150),
 ("cap", "The mark is the architecture. Top chord: the cap. Bottom chord: the floor every member "
   "keeps. The web between them: the allocation, five panels for five members. The web touches the "
   "top chord and stops — nothing crosses it."),

 ("h2", "Why this is a large project and not a dashboard"),
 ("p", "Five genuinely hard things at once, and every one of them is visible in the demo."),
 ("table", ["", "What it is", "Why it is not decorative"], [
   ["A distributed system",
    "Five processes that fail independently, asynchronous messages that duplicate and reorder, "
    "stale state, recovery.",
    "Not one program pretending to be five. Kill any one and watch the rest respond."],
   ["A leased resource",
    "The sum of outstanding lease amounts never exceeds the cap — and that holds even if every "
    "message in flight is lost.",
    "Gray &amp; Cheriton's lease mechanism applied to watts instead of cache lines. [S01]"],
   ["A fair allocation",
    "Water-filling produces the max-min fair (leximin) allocation, deterministically, in "
    "O(n log n).",
    "Fairness with a theorem behind it, not an adjective on a slide. [S02]"],
   ["A cyber-physical loop",
    "Sense, offer, allocate, lease, command, acknowledge, measure, replan.",
    "It cannot be reduced to CRUD screens without ceasing to work."],
   ["A standards position",
    "OpenADR 3.x above, MQTT 5 in the middle, Matter 1.5 below.",
    "We implement the middle honestly and define the edges as interfaces we do not claim."],
  ], [0.17, 0.40, 0.43]),

 ("h2", "What makes it memorable"),
 ("p", "Most teams demonstrate that their system works. Truss demonstrates what happens when it "
   "does not — and that is a far harder thing to fake."),
 ("call", "Kill the coordinator and the site gets quieter.",
   ["Every lease counts down on screen. Every member steps to its floor. There is no chaos, "
    "because there was never any trust to lose. Restart it and it refuses to issue a lease for one "
    "full lease term, because it cannot know what it promised before it died."]),
 ("callr", "Ask for the impossible and it refuses.",
   ["Set the cap below the sum of the declared safety floors and the system declares INFEASIBLE "
    "and names the members it cannot serve. It never reports a compliance it did not achieve. "
    "A system that lies about its constraint is worse than no system, because someone would trust it."]),
 ("p", "Those two beats are the pitch. They are also the engineering. Neither is available to a "
   "team that built a monitoring dashboard, at any level of polish."),

 ("h2", "Ruthless boundary"),
 ("p", "Truss is not a utility-grade demand-response platform, a certified smart panel, a microgrid "
   "controller, or a savings product. " + A("It never switches mains voltage.") + " The prototype "
   "proves exactly six things, and every one of them is measured:"),
 ("ol", ["Interoperable device messaging under one versioned contract.",
   "A maintained device twin in which <b>unknown is not zero</b>.",
   "Constraint-aware, provably fair allocation.",
   "Closed-loop command verification against observed watts.",
   "Fail-safe degradation under coordinator loss, partition and restart.",
   "An append-only evidence trail that replays deterministically."]),
 ("p", "That is already a serious 48-hour system. Everything outside those six is recorded as a "
   "rejection with a reason, because rejections are cheaper to defend than features."),
]},

# ============================================================ 02
{"num": "SECTION 02", "title": "The name", "blocks": [
 ("lead", "A good system name is a compression of the design. It should keep paying out every time "
   "you reach for a word. Truss does that on three levels, and all three are load-bearing."),

 ("h2", "The etymology is the architecture"),
 ("p", "<i>Truss</i> entered English from Old French " + A("trousse") + " — a bundle: separate "
   "things bound together and carried as one. That is the distributed-systems claim sitting inside "
   "the word. Five independent members, bound by a protocol, behaving as one structure. Not one "
   "machine pretending to be five, and not five machines pretending to be one."),

 ("h2", "The structure is the mechanism"),
 ("p", "A truss carries a load that no single member could carry, by " + A("resolving") + " it into "
   "forces along members that each stay inside their own limit. Two properties follow, and both are "
   "properties we want."),
 ("ul", ["<b>Every share is computable, not guessed.</b> The method of joints gives the exact force "
   "in every member. Truss gives the exact watt budget for every home, by a stated rule, with the "
   "arithmetic on screen.",
   "<b>The load path is traceable.</b> A structural engineer follows a load from where it is applied "
   "to where it is carried. Truss does the same in reverse: click any deferred device and get the "
   "causal chain that deferred it."]),
 ("p", "There is a third property, and it justifies the privacy boundary mathematically. The "
   + A("method of sections") + " lets you cut through a truss and compute the forces crossing that "
   "cut without solving the rest of the structure. Truss cuts at the member boundary: the "
   "coordinator reasons about five offers, not thirty devices. Its problem is " + C("O(members)") +
   ", not " + C("O(devices)") + " — which is the privacy argument and the scaling argument, and they "
   "turn out to be the same argument."),

 ("h2", "Redundancy is the engineering word for fault tolerance"),
 ("p", "A planar truss with " + C("j") + " joints is <i>statically determinate</i> at " +
   C("m = 2j − 3") + " members. Below that it is a mechanism and it collapses. Above that it is "
   + A("statically indeterminate") + " — it has spare load paths, so losing a member redistributes "
   "force rather than ending the structure."),
 ("pull", "Structural engineers have called this <i>redundancy</i> for two centuries. It is the same "
   "property distributed-systems engineers call fault tolerance — discovered independently, in the "
   "same century, for the same reason."),
 ("p", "Truss is deliberately indeterminate. Kill a gateway and the remaining members absorb its share."),

 ("np",),
 ("h2", "The vocabulary"),
 ("p", "The name handed us these, and every one replaced a worse word. This is not branding varnish: "
   "a team that shares precise vocabulary argues faster and builds fewer misunderstandings."),
 ("table", ["Truss term", "System meaning", "What it replaced"], [
   ["<b>Member</b>", "One home, room or gateway. Structural <i>and</i> social — both readings are correct.",
    "“node”, “client” — neither suggests belonging"],
   ["<b>Top chord</b>", "Site capacity ceiling. Hard. Never crossed.", "“cap”, “limit”"],
   ["<b>Bottom chord</b>", "The floor every member keeps.", "“minimum”, “critical load”"],
   ["<b>Web</b>", "The live allocation between the chords — the part that moves.", "“the schedule”"],
   ["<b>Joint</b>", "The coordinator; where members meet and forces resolve.", "“server”, “master”"],
   ["<b>Camber</b>", "Headroom reserved for load we cannot currently see.", "“safety margin”, “fudge factor”"],
   ["<b>Load path</b>", "The causal chain behind one decision.", "“explanation”, “reason code”"],
   ["<b>Buckling</b>", "Failure by a mode you did not design for.", "“edge case”"],
   ["<b>Gusset</b>", "The joint plate — where real trusses actually fail.", "“the protocol”, “the contract”"],
  ], [0.17, 0.47, 0.36]),

 ("h3", "Two of these deserve a paragraph"),
 ("p", A("Camber") + " — a bridge truss is fabricated with a deliberate upward curve so that under "
   "full design load it settles <i>level</i>. The camber is not error; it is designed-in "
   "compensation for a load you know is coming but cannot see yet. Truss reserves a camber band "
   "under the top chord for exactly that. When a member goes dark, its last known draw stays "
   "reserved, the band grows on screen, and the allocatable power shrinks. An invisible safety "
   "principle becomes a visible rectangle."),
 ("p", A("Gusset") + " — the I-35W bridge in Minneapolis collapsed in 2007 because of undersized "
   "gusset plates. The members were fine; the <i>joints</i> failed. The lesson transfers exactly. "
   "Our members are easy. The protocol between them is where this project will fail if it fails, "
   "so that is where the versioning, the idempotence and the property tests go."),

 ("h2", "Naming rules"),
 ("ul", ["The system is <b>Truss</b>. One word. Never “Truss OS”, never “TrussGrid”, and never an "
   "acronym expansion — there is not one, and inventing one would be a lie.",
   "Written <b>Truss</b> in prose; <b>TRUSS</b> only in the wordmark and slide titles.",
   "The MQTT namespace is " + C("truss/v1/…") + ", the CLI is " + C("truss") + ", the repository is "
   + C("truss") + ".",
   "A home is a <b>member</b>, never a “node”. The cap is the <b>top chord</b> once the diagram is "
   "drawn, and plain “cap” before it."]),
]},

# ============================================================ 03
{"num": "SECTION 03", "title": "The problem", "blocks": [
 ("h2", "One operating moment"),
 ("lead", "A hostel block loses grid supply at 19:40. The inverter takes over. Normal draw across "
   "the block is about 4.6 kW. The inverter can hold 1.8 kW."),
 ("p", "Exactly three things can happen today."),
 ("ol", ["<b>The inverter trips on overload.</b> Everyone loses everything — including the corridor "
   "lights, the water pump and the router.",
   "<b>The warden cuts a floor.</b> Forty rooms lose everything so that forty other rooms lose "
   "nothing. The choice of floor is not a policy; it is whoever the warden thought of.",
   "<b>Somebody walks the corridors unplugging things.</b> This is the humane option and it takes "
   "twenty minutes, which is nineteen minutes too long."]),
 ("p", "All three are blunt instruments applied to a problem that has structure."),

 ("h2", "The structure nobody uses"),
 ("p", "Most of that 4.6 kW is not urgent, and the building already knows it. The knowledge is "
   "simply stranded at the edge."),
 ("table", ["Load", "The real constraint"], [
   ["Water heater", "Needs 40 minutes of heat before 06:00. Does not care when."],
   ["Washing machine", "Has a <b>deadline</b>, not a schedule. Once started, must not be interrupted mid-cycle."],
   ["Laptop charger at 82%", "Can pause for an hour with no consequence at all."],
   ["Refrigerator", "Can coast 20 minutes. Cannot coast 3 hours."],
   ["Router, corridor lights", "Small, constant, and everything else depends on them."],
   ["CPAP machine", "Cannot wait one second — and nobody will say which room it is in."],
  ], [0.28, 0.72]),
 ("call", "The insight",
   ["Every one of those distinctions already exists. None of them is expressible to whatever "
    "decides who loses power.",
    "<b>The flexibility is already there. What is missing is a way to express it that does not "
    "require surrendering privacy or control.</b>"]),
 ("p", "That final clause is why this is not solved by a smarter breaker. A device list is an "
   "intimate document — it says who is home, who is ill, who does laundry at two in the morning. "
   "No hostel resident and no apartment neighbour should have to publish one to keep their fridge "
   "running. Any design that requires it will be refused by the people it is for, and rightly."),

 ("np",),
 ("h2", "Who this is for"),
 ("ul", ["<b>Hostels and dormitories</b> on inverter or generator backup, where a warden currently "
   "makes these decisions by hand and by memory.",
   "<b>Apartment blocks</b> sharing a service transformer, where simultaneous EV charging and "
   "evening cooking collide.",
   "<b>Small institutional microgrids</b> — clinics, schools, field offices — that island during "
   "outages and must keep specific loads alive.",
   "<b>Distribution utilities</b>, one layer up, who want a flexibility envelope from a building "
   "rather than switching authority over its appliances."]),

 ("h2", "Why now, and why in India"),
 ("p", "India is installing the measurement layer and has not yet built the coordination layer above it."),
 ("ul", ["The " + A("RDSS") + " programme targets <b>25 crore smart meters</b> with an implementation "
   "deadline of <b>March 2028</b>, against roughly ₹2.83 lakh crore of sanctioned investment. That is "
   "a nationwide rollout of devices that can <i>observe</i> consumption. [S12]",
   "Observation is not coordination. A meter that reports a 4.6 kW draw against a 1.8 kW inverter "
   "has told you that you are failing. It has not decided, acted, or proved recovery.",
   "The IEA's work identifies the same gap globally: flexible demand is systematically under-used, "
   "and grid-interactive buildings are named specifically as an Indian opportunity joining "
   "efficiency, digital technology and peak shifting. [S09][S10][S11]"]),
 ("pull", "Truss is the layer that turns the meters India is already installing into something that "
   "can act — fairly, and provably."),

 ("h2", "What “fair” has to mean here"),
 ("p", "Fair cannot be a vibe on a dashboard. In this system it has three concrete commitments, and "
   "each one is testable."),
 ("ol", ["<b>A floor nobody crosses.</b> Every member declares a safety floor. While the system "
   "reports feasibility, no member is allocated below it. If the cap cannot cover the sum of floors, "
   "the system says so and names the members it cannot serve — it does not quietly pick losers.",
   "<b>Equal treatment of equal need.</b> Surplus above the floors is allocated by water-filling, "
   "which maximises the smallest allocation first. Two members with identical offers get identical "
   "budgets. Always, and by construction.",
   "<b>Sacrifice is remembered and repaid.</b> A member curtailed heavily in one round carries "
   "<b>debt</b>, and debt weights the next allocation. Nobody is the designated loser twice."]),
 ("p", "Those three are Elinor Ostrom's design principles for common-pool resources — clear "
   "boundaries, congruence between rules and local conditions, monitoring, and graduated response — "
   "rendered as an allocation function. [S08] The commons literature is not decoration here. It is "
   "the reason the fairness rule has the shape it has, and it is the answer when a judge asks why we "
   "did not simply sort by priority."),
]},

# ============================================================ 04
{"num": "SECTION 04", "title": "Where this sits", "blocks": [
 ("lead", "The fastest way to lose a judge is to describe a solved problem. Here is what exists, "
   "stated fairly, and the specific thing each one does not do."),
 ("table", ["What exists", "What it genuinely does", "What it does not do"], [
   ["<b>Smart panels</b><br/>SPAN, Lumin",
    "Circuit-level control, load priority, dynamic EV charging, local operation. Real products. [S13][S14]",
    "Optimise <b>one property</b>, behind <b>proprietary hardware</b>, with the panel owner holding "
    "switching authority. No notion of independent households negotiating a shared limit."],
   ["<b>Home energy platforms</b><br/>Home Assistant",
    "Multi-brand visibility, device integration, local MQTT with discovery. Excellent at this. [S15][S16]",
    "Visibility and user-authored automations. No allocation across parties, no fairness, no lease "
    "safety. Rules are written per home rather than negotiated between homes."],
   ["<b>Utility demand response</b><br/>OpenADR 3.x",
    "Standardised exchange of price, reliability and capacity events between utilities, aggregators "
    "and control systems. REST with webhooks. [S05]",
    "Stops at the building boundary. It signals <i>that</i> capacity is constrained; it does not "
    "decide which of your neighbour's loads yields, or prove that it did."],
   ["<b>Matter 1.5</b>",
    "New energy device types and clusters — Commodity Tariff, Commodity Price, Electrical Grid "
    "Conditions, Energy Preference, Power Topology — so devices report true cost and adjust. [S06]",
    "Device interoperability, not allocation. It makes flexibility <i>expressible per device</i>. "
    "Something still has to decide, fairly, across many owners. That is the gap."],
   ["<b>Rotational load shedding</b>",
    "Universally deployed, well understood, zero infrastructure.",
    "Coarse to the point of cruelty. It cuts by geography, not by need, and cannot tell a CPAP "
    "machine from a water heater."],
   ["<b>Packetized Energy Management</b><br/>academic and deployed",
    "Devices make anonymous asynchronous requests for fixed-length energy packets; a coordinator "
    "grants or denies. Statistically fair grid access, preserved privacy and quality of service. [S07]",
    "<b>The closest prior art, and we say so out loud.</b> It coordinates a fleet of like devices "
    "for a utility. It does not model a household boundary with its own floor, deadlines and "
    "accumulated debt, and it provides no per-member safety lease."],
  ], [0.19, 0.38, 0.43]),

 ("np",),
 ("h2", "The layer nobody owns"),
 ("code", """
   OpenADR 3.x         capacity / price / reliability event
         |             "the feeder has 1.8 kW for the next 30 minutes"
         v
   +----------------------------------------------------+
   |                      TRUSS                         |   <-- the gap
   |     offers  ->  fair allocation  ->  leases        |
   |                      -> proof                      |
   +----------------------------------------------------+
         ^
   Matter 1.5          device-level flexibility and tariff awareness
         |             "this water heater needs 40 min before 06:00"
"""),

 ("h2", "The four things that are actually novel"),
 ("p", "The defensible novelty is not “energy management”, which exists. It is this combination, "
   "which does not currently appear together anywhere we could find:"),
 ("ol", ["<b>A household privacy boundary that is also the scaling boundary.</b> Members publish "
   "offers, not device lists. The coordinator's problem is " + C("O(members)") + ".",
   "<b>A safety lease rather than a command.</b> The cap holds under coordinator death, network "
   "partition and total message loss.",
   "<b>Fairness with memory.</b> Curtailment debt carries between rounds, so the same member is not "
   "the designated loser twice.",
   "<b>Refusal.</b> When the constraint cannot be met, the system says so and names who it cannot "
   "serve, rather than reporting a compliance it did not achieve."]),

 ("callr", "What we must never claim",
   ["That we implement OpenADR or Matter. We ship one OpenADR-<i>shaped</i> JSON fixture and a "
    "Matter adapter <i>interface</i>. Both are labelled as such in the UI and the README.",
    "That we are more efficient, cheaper or greener than any named product. We have measured none "
    "of that and will not imply it.",
    "That Packetized Energy Management is ours. It is prior art, it is good, we cite it — and being "
    "able to name your nearest neighbour in the literature is a strength in front of a technical "
    "judge, not a weakness."]),
]},

# ============================================================ 05
{"num": "SECTION 05", "title": "The mechanism", "blocks": [
 ("h2", "1 — Offers, not device lists"),
 ("p", "A member aggregates its own devices into one offer. Five numbers describe a household well "
   "enough to allocate to it, and nowhere near well enough to know anything about the people in it."),
 ("code", """
{
  "schema": "truss.offer.v1",
  "seq": 1043,
  "member_id": "block-c",
  "floor_w": 180,                 // below this the member is harmed
  "firm_w": 420,                  // in use, would rather not lose
  "useful_w": 1650,               // most it could productively absorb
  "deadline_energy_wh": 900,      // must receive before deadline_by
  "deadline_by": "2026-09-07T06:00:00+05:30",
  "debt_wh": 240,                 // curtailment absorbed this session
  "device_count": 6,
  "ts": "2026-09-07T19:41:02+05:30"
}
"""),
 ("p", C("device_count") + " exists only so the console can show fleet health. The allocator never "
   "reads it. The coordinator cannot leak a device list it was never given — that is an "
   "architectural guarantee rather than an operational promise, which is the only kind worth making."),

 ("h2", "2 — Debt-weighted water-filling"),
 ("call", "The rule, in one sentence",
   ["Give every member its floor, then raise all members together at the same rate until each is "
    "satisfied or the power runs out."]),
 ("p", "That is water-filling, and it produces the " + A("max-min fair") + " allocation: it "
   "maximises the smallest allocation, then the second smallest, and so on — the <i>leximin</i> "
   "order. [S02] Four properties worth stating to a judge:"),
 ("ul", ["<b>Deterministic.</b> Same snapshot, same answer, always.",
   "<b>" + C("O(n log n)") + ".</b> Sort by demand, fill in one pass. Microseconds for five members, "
   "and still microseconds for five thousand.",
   "<b>Provably fair.</b> Two members with identical offers receive identical budgets. That is a "
   "theorem, not a hope.",
   "<b>Explainable in one breath.</b> “We fill everyone's glass at the same rate until the jug is "
   "empty.” A judge understands it faster than we can draw it."]),
 ("code", """
allocate(offers, top_chord_w, camber_w):
    allocatable = top_chord_w - camber_w

    # 1. Floors are not negotiable
    floors = sum(o.floor_w for o in offers)
    if floors > allocatable:
        return INFEASIBLE(unserved = members_beyond(allocatable))

    budget  = {o.member: o.floor_w for o in offers}
    surplus = allocatable - floors

    # 2. Debt weighting: those who gave up more are filled faster.
    #    Capped at 2.0 so debt can never starve a debt-free member.
    w = {o.member: 1.0 + min(o.debt_wh / DEBT_SCALE, 1.0) for o in offers}

    # 3. Water-filling over weighted remaining demand
    remaining = {o.member: o.useful_w - o.floor_w for o in offers}
    while surplus > EPSILON and any(v > 0 for v in remaining.values()):
        active = [m for m in remaining if remaining[m] > 0]
        rate   = surplus / sum(w[m] for m in active)
        step   = min(min(remaining[m] / w[m] for m in active), rate)
        for m in active:
            take = step * w[m]
            budget[m] += take;  remaining[m] -= take;  surplus -= take

    return Allocation(budget, rule="debt_weighted_water_filling")
"""),
 ("p", C("DEBT_SCALE") + " is a declared constant shown in the UI, not a tuned magic number. The "
   "weight cap of 2.0 is a fairness decision and it is deliberate: unbounded debt weighting is its "
   "own injustice, because it lets a member's history starve a neighbour who has never been "
   "curtailed."),

 ("np",),
 ("h2", "3 — Leases, not commands"),
 ("lead", "A budget is not a command. A budget is a lease."),
 ("p", "A command says <i>do this</i>, and it is only as good as the channel that carried it. A "
   "lease says <i>you may draw this much until your own clock says stop</i>, and it is good even if "
   "the channel dies, the coordinator dies, and every message in flight is lost."),
 ("code", """
{
  "schema": "truss.lease.v1",
  "plan_id": "plan-0042",
  "version": 42,
  "member_id": "block-c",
  "budget_w": 312,
  "ttl_ms": 6000,                 // a DURATION, never a deadline
  "reason": "cap_drop",
  "basis": {                      // the load path travels with the decision
    "top_chord_w": 1800,
    "camber_w": 240,
    "allocatable_w": 1560,
    "rule": "debt_weighted_water_filling",
    "members_at_floor": 0
  },
  "correlation_id": "cap-event-0007"
}
"""),
 ("h3", "Three properties, each earning its place"),
 ("ul", [C("ttl_ms") + " <b>is a duration, not a deadline.</b> The member starts its own monotonic "
   "countdown on receipt. Five laptops on a hotspot will never agree on wall time and do not need to.",
   C("basis") + " <b>is the load path.</b> Everything the console needs to explain this number "
   "travels with the number, so explanations cannot drift from decisions — they <i>are</i> the decision.",
   C("version") + " <b>is monotonic.</b> A member applies a lease only if its version exceeds the "
   "last applied. Duplicates and reordering are normal and safe."]),
 ("call", "The lease rule, stated exactly",
   ["A member may draw up to " + C("budget_w") + ". When its countdown reaches zero without a newer "
    "lease, it reduces to " + C("floor_w") + " — locally, immediately, and without requiring any message."]),
 ("p", "Everything in the next section follows from that one sentence."),

 ("h2", "Why not a market, an auction, or peer-to-peer consensus"),
 ("p", "All three were considered and rejected, and the reasons are worth having ready."),
 ("ul", ["<b>Auctions</b> need a currency, and introducing money into a hostel corridor changes the "
   "ethics of the product. Ability to pay is not the same as need, and we would be rebuilding the "
   "thing we set out to replace.",
   "<b>Peer-to-peer consensus</b> is a research project. A shared feeder genuinely has a single "
   "physical constraint; modelling it as a distributed agreement problem adds failure modes to solve "
   "a problem that physics already solved.",
   "<b>Priority sorting</b>, the obvious choice, fails the fairness test outright: the same member "
   "is the designated loser every round, forever. Debt weighting exists precisely to prevent that."]),
]},

# ============================================================ 06
{"num": "SECTION 06", "title": "Safety", "blocks": [
 ("lead", "The distinguishing engineering in this project. If a technical judge probes one thing, "
   "it will be this — and it should be."),

 ("h2", "The six invariants"),
 ("table", ["", "Invariant"], [
   ["<b>I1 — Cap</b>", "Sum of observed member draw ≤ top chord, after the response window."],
   ["<b>I2 — Floor</b>", "No member is allocated below its declared floor while the system reports feasibility."],
   ["<b>I3 — Lease safety</b>", "At any instant, the sum of <b>outstanding lease amounts</b> ≤ top chord − camber."],
   ["<b>I4 — Honesty</b>", "If I2 cannot hold, the system declares INFEASIBLE and names the unserved "
    "members. It never reports a compliance it did not achieve."],
   ["<b>I5 — Idempotence</b>", "Applying the same lease or command twice has the same effect as applying it once."],
   ["<b>I6 — Monotonicity</b>", "A member never applies a lease older than the one it holds."],
  ], [0.22, 0.78]),
 ("call", "I3 is the load-bearing one",
   ["It is a statement about what the coordinator has <i>promised</i>, not about what it has "
    "<i>observed</i>. Because the coordinator never over-issues, and members self-limit on expiry, "
    "the cap holds under coordinator death, network partition, total message loss, and coordinator "
    "restart.",
    "<b>Safety is a property of the protocol, not of the planner.</b> The planner may be wrong, "
    "slow, or entirely absent. The cap still holds."]),
 ("p", "A coordinator that restarts " + A("must not issue any lease for one full TTL") + ", because "
   "it cannot know what it granted before it died. It publishes " + C("status: recovering") + " with "
   "a countdown, the console shows it, and it then resumes. This is Gray &amp; Cheriton's recovery "
   "rule and it is four lines of code. [S01]"),

 ("h2", "Camber — unknown is not zero"),
 ("p", "A member that stops reporting has not stopped drawing power. Treating silence as zero is the "
   "single most dangerous thing this system could do, and it is exactly what a naive implementation "
   "does. Camber is the reserved band under the top chord for load we cannot see:"),
 ("code", """
camber_w = SUM last_known_draw(m)  for every stale or unacknowledged member m
         + a fixed measurement reserve
"""),
 ("ol", ["Stale members keep their last known draw reserved. They are not free.",
   "The camber band is <b>drawn on the console</b>. When a member goes dark you watch the band grow "
   "and the allocatable power shrink.",
   "Camber is repaid the instant the member reports again — the band shrinks and power returns to "
   "the pool, live, on screen."]),

 ("np",),
 ("h2", "Failure modes and responses"),
 ("table", ["Failure", "Detection", "Response", "In the demo?"], [
   ["Device ignores a command", "Missing ack within window",
    "Reserve its observed draw; replan; mark unverified", "Yes"],
   ["Device refuses (mid-cycle)", C("result: rejected"),
    "Legitimate. Plan around it, do not insist", "Yes"],
   ["Member process dies", "MQTT Will message, immediate",
    "Camber grows by last known draw; replan", "<b>Beat 3</b>"],
   ["Member partitioned", "Lease expires locally",
    "Member self-limits to floor with no message", "Yes"],
   ["Coordinator dies", "Every lease expires",
    "<b>All members to floor within one TTL</b>", "<b>Beat 5</b>"],
   ["Coordinator restarts", C("status: recovering"),
    "No lease for one full TTL, countdown shown", "Yes"],
   ["Broker restarts", "Connection loss",
    "Leases expire; members floor; retained state restores", "Yes"],
   ["Floors exceed cap", "Allocator returns INFEASIBLE",
    "Declare it, name unserved members, do not fabricate", "<b>Beat 6</b>"],
   ["CP-SAT times out", "Wall-clock box",
    "Water-filling plan issued; console names the rule", "Yes"],
   ["Clock skew across laptops", "—",
    "Cannot occur. Expiry is monotonic and local; no decision reads a timestamp", "Explain if asked"],
  ], [0.22, 0.20, 0.42, 0.16]),

 ("h2", "Fault injection is a build deliverable"),
 ("p", "Not a testing afterthought. It has an owner, it ships, and the fault console is a "
   "first-class part of the product."),
 ("code", """
truss chaos kill-member C
truss chaos kill-coordinator
truss chaos partition C --seconds 20
truss chaos drop-acks C --rate 0.5
truss chaos delay-telemetry --ms 3000
truss chaos cap --watts 400        # below the sum of floors: forces INFEASIBLE
"""),
 ("p", "Every one of these runs during rehearsal. At least three run in front of the judges."),

 ("h2", "Property-based testing"),
 ("p", "The cheapest credibility available to this team, and it costs about two hours."),
 ("code", """
@given(offers=offer_sets(), cap=watts(), camber=watts())
def test_never_exceeds_cap(offers, cap, camber):
    result = allocate(offers, cap, camber)
    if result.feasible:
        assert sum(result.budget.values()) <= cap - camber
        assert all(result.budget[m] >= o.floor_w for m, o in offers.items())
    else:
        assert sum(o.floor_w for o in offers.values()) > cap - camber
"""),
 ("p", "Hypothesis generates thousands of scenarios, including the degenerate ones nobody thinks to "
   "write by hand: zero members, one member, every member at floor, identical offers, a cap exactly "
   "equal to the floor sum, a cap one watt below it. [S21]"),
 ("pull", "“We fuzz-tested the safety invariant across ten thousand generated scenarios” is a "
   "sentence almost no hackathon team can say truthfully. We can, and it takes an afternoon."),
]},

# ============================================================ 07
{"num": "SECTION 07", "title": "Architecture and protocol", "blocks": [
 ("h2", "Three planes, kept separate on purpose"),
 ("code", """
                  OpenADR-shaped capacity event  (fixture / slider)
                                 |
                  +--------------v--------------+
                  |        COORDINATOR          |   the joint
                  |  twin . allocator . leases  |
                  |  -- independent validator --|   can veto any plan
                  +--------------+--------------+
                                 |
            offer ^              |              v lease
      +-----------+------+-------+------+-------+-----------+
      |           |             |              |           |
  +---v----+  +---v----+   +----v---+    +-----v--+   +----v---+
  |member A|  |member B|   |member C|    |member D|   |member E|
  +---+----+  +---+----+   +----+---+    +-----+--+   +----+---+
      |           |             |              |           |
   telemetry -> twin -> command -> ack -> observed -> replan
      |           |             |              |           |
   4-6 emulated devices each  +  one optional ESP32 low-voltage light

  CONTROL PLANE    versioned MQTT 5 topics on the local LAN
  EVIDENCE PLANE   append-only event log, monotonic sequence, replayable
  OPERATOR PLANE   one console, four controls, one load-path inspector
"""),
 ("p", "The separation is not tidiness. It is what lets the operator plane be rebuilt, the evidence "
   "plane be replayed, and the control plane be fuzzed, without any of the three touching the others."),

 ("h2", "The clock"),
 ("p", "This is where distributed systems quietly go wrong, so it is decided up front — and it is "
   "the first thing a strong technical judge will probe."),
 ("ul", ["<b>Lease expiry is measured on the member's own monotonic clock</b>, never on wall time and "
   "never on a timestamp carried in a message.",
   "The coordinator sends a <b>duration</b>, not an absolute deadline. The member starts its own "
   "countdown on receipt.",
   "Message timestamps exist for the event log and for human reading. <b>No control decision depends "
   "on them.</b>",
   "Sequence numbers are per-publisher and monotonic. Ordering is decided by sequence number, never "
   "by arrival order or timestamp."]),

 ("np",),
 ("h2", "Component decisions"),
 ("table", ["Component", "Why it exists", "Failure fallback"], [
   ["<b>Eclipse Mosquitto</b>",
    "Lightweight local MQTT 5 broker. Sessions, QoS, retained messages and Will messages for "
    "abnormal disconnect — the last is what makes member death detectable in milliseconds rather "
    "than seconds. [S03][S04]",
    "Broker and core services collapse onto the primary laptop"],
   ["<b>Member agent</b>",
    "Owns device detail, forms the offer, holds the lease, enforces the floor locally",
    "Last valid budget plus fixed local priority. It keeps working with no coordinator at all"],
   ["<b>Coordinator</b>", "Maintains twins, validates events, calls the allocator, issues and renews leases",
    "Last good plan; on restart, one full TTL of silence"],
   ["<b>Allocator</b>", "Pure function: snapshot to allocation. No I/O, no clock, no network",
    "It <i>is</i> the fallback. CP-SAT sits behind it, never in front"],
   ["<b>Cap validator</b>", "Separate module that independently re-checks any plan before it is issued",
    "If it rejects, the previous plan stands and the UI says a plan was vetoed"],
   ["<b>Device nodes</b>", "Deterministic seeded behaviour; make five laptops behave like five homes",
    "One laptop runs every process with distinct IDs"],
   ["<b>SQLite event log</b>", "Append-only telemetry, offers, allocations, leases, acks, expiries",
    "Newline-delimited JSON file"],
   ["<b>Console</b>", "Streamlit and Plotly — fastest route to a legible operator screen in Python",
    "Static seeded state plus live event counter. Do not rebuild in React mid-event"],
   ["<b>ESP32 node</b>", "Makes one lease physically visible; proves protocol parity",
    "Software node with an on-screen LED on the identical contract"],
  ], [0.17, 0.50, 0.33]),

 ("h2", "Topic namespace"),
 ("code", """
truss/v1/site/{site}/member/{member}/status        retained, Will message
truss/v1/site/{site}/member/{member}/offer
truss/v1/site/{site}/member/{member}/lease
truss/v1/site/{site}/member/{member}/lease/ack
truss/v1/site/{site}/device/{device}/telemetry
truss/v1/site/{site}/device/{device}/command
truss/v1/site/{site}/device/{device}/ack
truss/v1/site/{site}/event/capacity
truss/v1/site/{site}/plan                          retained, latest plan
"""),
 ("p", "Members subscribe only to their own lease topic. Devices subscribe only to their own command "
   "topic. Nothing subscribes to everything except the logger, and the logger is read-only by "
   "construction."),

 ("h2", "Command and acknowledgement"),
 ("code", """
{ "schema": "truss.command.v1", "plan_id": "plan-0042", "version": 42,
  "device_id": "washer-1", "desired_state": "deferred",
  "expires_at_ms": 4000, "reason": "member_budget_exceeded",
  "correlation_id": "cap-event-0007" }

{ "schema": "truss.ack.v1", "plan_id": "plan-0042", "version": 42,
  "device_id": "washer-1", "result": "applied",
  "observed_state": "deferred", "observed_w": 0, "seq": 88213 }
"""),
 ("p", A("Device rule:") + " apply only if " + C("version") + " exceeds the last applied version and "
   "the command has not expired; then publish exactly one acknowledgement carrying the "
   "<i>observed</i> state. Duplicate delivery is normal and must be safe."),
 ("p", C("result") + " is one of " + C("applied | rejected | duplicate | expired") + ". A device that "
   "rejects must say why — a washing machine mid-cycle with " + C("min_run_s") + " remaining is "
   + A("allowed") + " to refuse, and the coordinator must plan around a refusal rather than insist. "
   "Members are autonomous; that is the point of the architecture, and it has to be true in the "
   "protocol, not merely in the pitch."),

 ("h2", "Message hygiene"),
 ("ul", ["MQTT 5 <b>message expiry interval</b> on commands and leases, so the broker itself drops "
   "stale control messages during a partition.",
   "<b>Will messages</b> on member status, so death is detected by the broker rather than by a timeout.",
   "<b>Retained</b> on status and plan, so a joining console is immediately correct.",
   "QoS 1 everywhere, with idempotence carrying the correctness. QoS 2 buys nothing once versioning "
   "is right and costs latency."]),

 ("h2", "Security boundary, stated honestly"),
 ("p", "The judged build uses explicit demo credentials on an isolated LAN with no public exposure. "
   "A production system would need per-device identity, TLS, broker ACLs, key rotation, signed "
   "firmware, audit retention and safety-certified actuation. We have built none of those and will "
   "say so before a judge has to ask. What we <i>do</i> build is the privacy boundary, because that "
   "one is architectural rather than operational."),
]},

# ============================================================ 08
{"num": "SECTION 08", "title": "Scope and proof", "blocks": [
 ("h2", "Must build"),
 ("ul", ["Versioned MQTT 5 schema with validation, retained discovery and status, and Will messages.",
   "20+ emulated devices across five member processes, launched by one seeded command.",
   "Debt-weighted water-filling allocator, with an <b>independent</b> cap validator in a separate "
   "module that can veto any plan.",
   "The lease mechanism: local expiry, coordinator restart delay, and the visible countdown.",
   "Command, acknowledgement, heartbeat, stale detection and replan loop.",
   "Append-only event log with monotonic sequence numbers, and one-click replay.",
   "Live console with the four judge controls and the load path inspector.",
   "Automated tests plus <b>property-based tests</b> over the safety invariants."]),

 ("h2", "Nice to have, in this order"),
 ("ol", ["CP-SAT deadline planner behind the existing interface. [S20]",
   "One ESP32 with an LED on the identical contract.",
   "OpenADR-shaped event adapter translating a capacity event into a site cap.",
   "Downloadable incident bundle: log, plan trace, metrics, replay.",
   "Greedy-versus-CP-SAT comparison on the same seed."]),

 ("h2", "Do not build"),
 ("p", "Each of these was considered. The reason is recorded so the absence can be defended rather "
   "than apologised for."),
 ("table", ["Not building", "Because"], [
   ["Mains switching, breaker or inverter integration",
    "Safety — and it would make the demo a liability rather than an asset"],
   ["A real Matter controller or production OpenADR endpoint",
    "Cannot be done honestly in 48 hours. We ship interfaces and label them"],
   ["Forecasting or any ML",
    "Adds a dependency and a failure mode to buy nothing the demo needs"],
   ["LLM features", "There is no question in this product that a language model answers"],
   ["Billing, payments, carbon credits", "Unverifiable claims attached to a system that measures watts"],
   ["Accounts, mobile apps, notifications", "Not on the judged path"],
   ["A general automation rule builder", "It is a product, not a feature, and it dilutes the mechanism"],
   ["City-scale simulation", "Claims a scale we cannot demonstrate"],
   ["Peer-to-peer consensus", "Research, not a weekend. The hierarchy <i>is</i> the design"],
  ], [0.42, 0.58]),

 ("np",),
 ("h2", "Acceptance criteria"),
 ("p", "Numbered so they can be ticked in front of a judge."),
 ("ol", ["All seeded devices appear within <b>10 s</b> of scenario start.",
   "A cap change produces a validated plan within <b>1 s</b>; if CP-SAT exceeds its box, "
   "water-filling returns immediately and the UI says which ran.",
   "Observed controlled load is below the top chord within <b>5 s</b> of a cap drop, whenever a "
   "feasible plan exists.",
   "Commands are idempotent: replaying any command cannot toggle a device twice.",
   "A killed member goes stale within its timeout, its last known draw stays reserved as camber, "
   "and the plan is redone conservatively.",
   "<b>Killing the coordinator drives every member to its floor within one lease TTL, with zero cap "
   "violations.</b>",
   "A restarted coordinator issues no lease for one full TTL, and says so on screen.",
   "If the sum of floors exceeds the cap, the system declares INFEASIBLE and names the unserved "
   "members.",
   "The same seed produces the same plan and a byte-identical event trace.",
   "Every one of 1–9 has an automated test, and 3, 6 and 8 have property-based tests over generated "
   "scenarios."]),

 ("h2", "Measured outputs"),
 ("table", ["Metric", "Definition"], [
   ["<b>Cap compliance</b>", "% of samples at or below the top chord after the response grace period"],
   ["<b>Time to safe</b>", "Cap event timestamp to first verified below-cap timestamp"],
   ["<b>Lease safety violations</b>", "Instants where outstanding leases exceeded the cap. <b>Must be 0</b>"],
   ["<b>Acknowledgement success</b>", "Applied acks ÷ issued commands"],
   ["<b>Deadline satisfaction</b>", "Deadline jobs completed by their requested time"],
   ["<b>Recovery time</b>", "Failed-member detection to replacement plan published"],
   ["<b>Fairness</b>", "Leximin gap, plus Jain's index over delivered ÷ requested flexible energy — "
    "reported only where every denominator is valid, and described as an engineering diagnostic, "
    "never as a moral guarantee"],
   ["<b>Coordinator-loss margin</b>", "Peak observed load during a coordinator kill, as a fraction of the cap"],
  ], [0.30, 0.70]),
]},

# ============================================================ 09
{"num": "SECTION 09", "title": "The console", "blocks": [
 ("lead", "One screen. It answers seven questions, and any panel that answers none of them is deleted."),
 ("ol", ["What is the limit? — the <b>top chord</b>, drawn as a hard line",
   "What are we actually drawing? — observed load, live, against that line",
   "What can't we see? — the <b>camber</b> band, hatched, under the chord",
   "Who has what? — five member panels with budget, draw and lease countdown",
   "What changed, and why? — plan timeline with reason codes",
   "Did the devices obey? — pending / verified / rejected / stale markers",
   "Who has given up the most? — the <b>debt ledger</b>"]),
 ("code", """
+----------------------------------------------------------------------+
|  TRUSS   site: hostel-block-c        * LEASED   rule: water-filling  |
+----------------------------------------------------------------------+
|  TOP CHORD =========================================== 1800 W        |
|  ///// camber 240 W (member D stale) /////////////////                |
|  ############################### observed 1512 W                     |
|  BOTTOM CHORD ----------------------------------------  820 W        |
+----------------------------------------------------------------------+
| +--------+ +--------+ +--------+ +--------+ +--------+               |
| |   A    | |   B    | |   C    | |   D    | |   E    |               |
| | 312 W  | | 298 W  | | 340 W  | | STALE  | | 322 W  |               |
| | 4.8 s  | | 4.8 s  | | 4.8 s  | |  --    | | 4.8 s  |  lease TTL    |
| | debt 0 | | debt 0 | | 240 Wh | | 180 Wh | | debt 0 |               |
| +--------+ +--------+ +--------+ +--------+ +--------+               |
+----------------------------------------------------------------------+
|  PLAN TIMELINE   > 19:41:02  cap_drop 5000->1800  plan-0042          |
|                  > 19:41:02  6 devices deferred . 0 rejected          |
|                  > 19:41:07  verified below chord (4.9 s)             |
+----------------------------------------------------------------------+
|  [ TOP CHORD ---o--- ]  [ PROTECT ]  [ CHAOS ]  [ REPLAY ]           |
+----------------------------------------------------------------------+
"""),

 ("h2", "The lease countdown is the centrepiece"),
 ("p", "Every member panel shows its lease TTL ticking down and resetting on renewal. It looks like "
   "a heartbeat, and that is exactly what it is. It costs almost nothing to build and it does "
   "something no other element can: it makes the safety mechanism " + A("visible while it is working") +
   ". When the judge kills the coordinator, they do not have to take our word for what happens next. "
   "They watch five countdowns run to zero and five panels drop to their floor."),

 ("h2", "The load path inspector"),
 ("p", "Click any deferred device. A panel opens with the causal chain, read directly from the "
   + C("basis") + " block that travelled with the lease — so the explanation cannot drift from the "
   "decision, because it <i>is</i> the decision."),
 ("code", """
washer-1 . deferred . 19:41:02

  top chord              1800 W
  - camber                240 W   member D stale, last draw 240 W
  = allocatable          1560 W

  rule                   debt_weighted_water_filling
  member C weight        1.24     (debt 240 Wh)
  member C budget         340 W
  member C floor          180 W

  local decision         washer-1 (520 W) deferred
                         fridge, router, light held
  deadline               09:00 . 2 of 3 slots remain . still satisfiable
  debt accrued           +180 Wh

  [ show event trace ]   [ replay from here ]
"""),
 ("p", "Judges ask “why did it do that?”. This answers in five seconds, with arithmetic rather than "
   "adjectives, at any depth they care to push."),

 ("h2", "Colour, and one rule about it"),
 ("table", ["State", "Colour", "Meaning"], [
   ["Verified", "green", "Commanded, acknowledged, observed"],
   ["Pending", "amber", "Commanded, not yet acknowledged — <b>working, not broken</b>"],
   ["Stale", "hatched grey", "Unknown. Reserved as camber"],
   ["Rejected", "blue", "Device legitimately refused. Not an error"],
   ["Over chord", "red", "Reserved exclusively for a genuine cap violation"],
  ], [0.22, 0.22, 0.56]),
 ("p", A("Amber never means error.") + " Red appears only for a real violation of I1. If red is on "
   "screen at the end of a demo run, we have a bug — not a colour choice. That is precisely why the "
   "rule exists."),
 ("h3", "Anti-requirements"),
 ("p", "No login. No settings page. No map. No “AI insights” panel. No gauge that duplicates a number "
   "already on screen. No animation that outlives its transition."),
]},

# ============================================================ 10
{"num": "SECTION 10", "title": "Execution", "blocks": [
 ("h2", "Five people"),
 ("table", ["", "Owns", "Testable output"], [
   ["<b>M1</b>", "Schemas, coordinator state machine, allocator interface, water-filling, CP-SAT, "
    "integration, technical defence",
    C("allocate()") + " passes property tests; coordinator completes lease/ack/replan; the "
    "architecture doc matches reality"],
   ["<b>M2</b>", "Device emulator, 20–30 seeded profiles, state machines, idempotence and failure flags",
    "One command launches five members; every node idempotent; failure modes selectable"],
   ["<b>M3</b>", "Broker, member agent, <b>lease expiry</b>, event log, replay",
    "Broker restart checklist; member self-limits with no coordinator; replay is byte-identical"],
   ["<b>M4</b>", "Console, load-path inspector, judge controls",
    "Seven questions answered on one screen; lease countdown live; inspector reads from " + C("basis")],
   ["<b>M5</b>", "Chaos tooling, scenario QA, ESP32, demo assets, pitch",
    "Six chaos commands work; three cold-start passes recorded; backup video exists"],
  ], [0.08, 0.44, 0.48]),

 ("h3", "Dependency discipline"),
 ("p", "The failure mode that kills this project is M1 becoming a bottleneck while four people wait. "
   "Three rules prevent it."),
 ("ol", ["<b>The contract is frozen at hour 1</b> by M1 and M2 together, with one valid and one "
   "invalid example per message type committed. After that, schema changes need both of them plus a "
   "stated reason in the commit.",
   "<b>Everyone codes against fixtures first.</b> M4 builds the whole console against a static JSON "
   "snapshot and connects to live state at hour 12. M5 writes chaos commands against a stub. Nobody "
   "waits for anybody.",
   "<b>The allocator is a pure function</b>, so M1 develops and tests it with zero running "
   "infrastructure, and M4 renders its output before it is wired up."]),
 ("p", "M1 reviews rather than rewrites. A teammate's working module that M1 would have written "
   "differently ships as written. The commit history has to show five people building a system — "
   "because it will be read, and because it is true."),

 ("np",),
 ("h2", "Forty-eight hours"),
 ("table", ["Window", "Objective", "Deliverable and test"], [
   ["<b>0–2 h</b>", "Rules confirmed, clean repo, issue board. M1+M2 freeze the six schemas. M3 "
    "launches broker. M4 console shell. M5 scenario and chaos folders.",
    "Two processes exchange a validated heartbeat and command. README states the safety boundary on day one."],
   ["<b>2–6 h</b>", "<b>The vertical slice.</b> Five devices, member agent with local floor, twin "
    "plus water-filling, console on fixtures.",
    "A CLI cap change moves two devices, both acknowledge, cap check passes. <b>Recorded.</b>"],
   ["<b>6–12 h</b>", "<b>Leases.</b> TTL, local expiry, coordinator-restart delay. Expand to 20–30 "
    "nodes with failure flags. Versioning and replan.",
    "Killing the coordinator drives every member to floor with zero cap violations. The test that "
    "matters most."],
   ["<b>12–18 h</b>", "Camber, debt weighting, evidence. Independent validator. Idempotence tests. "
    "Replay. Load-path inspector. Chaos commands.",
    "Allocator and validator disagree on nothing across the fixture set. Replay is byte-identical."],
   ["<b>18–24 h</b>", "Integration and Review 1 hardening. Three scripted scenarios. One-screen "
    "hierarchy fixed.",
    "Review 1: live messages, complete loop, lease countdown visible, exact roadmap. <b>Tag a checkpoint.</b>"],
   ["<b>24–30 h</b>", "<b>Property tests and fault injection.</b> Hypothesis over the invariants. "
    "Every chaos command run. Hardware go/kill decision.",
    "The system never reports false compliance under any injected fault."],
   ["<b>30–36 h</b>", "CP-SAT <b>only if</b> everything above is green. Otherwise UX and evidence. "
    "Freeze controls and layout.",
    "Review 2 build runs from a clean start script. <b>Three consecutive cold-start passes.</b>"],
   ["<b>36–42 h</b>", "<b>Feature freeze.</b> Backup video and screenshots. All five rehearse "
    "questions and subsystem explanations.",
    "Versioned release, offline run instructions, evidence folder, demo under 2:50."],
   ["<b>42–48 h</b>", "Bug fixes with rollback only. Rest in rotation.",
    "Final build hash, local backup, alternate laptop copy, live <i>and</i> recorded demo paths."],
  ], [0.10, 0.42, 0.48]),

 ("h2", "Kill points"),
 ("p", "Decisions with a time and an owner, made in advance so they are not made at three in the morning."),
 ("table", ["Hour", "Question", "If no"], [
   ["<b>6</b>", "Does the vertical slice work end to end?",
    "Cut to three members and two device types. Nothing else matters until this is true"],
   ["<b>12</b>", "Do leases expire correctly with the coordinator dead?",
    "<b>Stop all feature work.</b> This is the project"],
   ["<b>24</b>", "Are the chaos commands real?", "Cut CP-SAT and the ESP32 outright"],
   ["<b>30</b>", "Is CP-SAT beating water-filling on the fixture set?",
    "Cut it. Say so in the pitch as a decision, not an omission"],
   ["<b>36</b>", "Three consecutive cold-start passes?", "Freeze immediately, no exceptions"],
  ], [0.08, 0.42, 0.50]),
]},

# ============================================================ 11
{"num": "SECTION 11", "title": "The demo", "blocks": [
 ("lead", "Three minutes, six beats. Beats 5 and 6 are the ones no other team will have."),

 ("h3", "0:00–0:20 · The moment"),
 ("p", "“A hostel block loses grid power at 19:40. The inverter can hold 1.8 kW. The block is "
   "drawing 4.6. Today, three things can happen: the inverter trips and everyone loses everything, "
   "the warden cuts a whole floor, or somebody spends twenty minutes walking corridors unplugging "
   "things.”"),
 ("h3", "0:20–0:40 · Why monitoring is not enough"),
 ("p", "Switch to <b>Uncoordinated</b> and drag the chord to 1.8 kW. The chord turns red; an overload "
   "timer runs. “Monitoring tells us we are failing. It does not decide, act, or prove recovery.”"),
 ("h3", "0:40–1:00 · The insight"),
 ("p", "“Most of that load is not urgent, and the building already knows it. But none of it is "
   "expressible to whatever decides who loses power — and nobody should have to publish a device "
   "list to keep their fridge running. So each home publishes five numbers instead. Nothing else "
   "leaves the home.”"),
 ("h3", "1:00–2:10 · The live loop"),
 ("ol", ["<b>Judge drags the chord to 1.8 kW.</b> Plan in under a second. Water heaters and the "
   "washer defer; fridge, router and the protected device hold. Amber pending dots turn to green "
   "verified ticks. Observed load crosses below the chord. <b>Time to safe: 4.9 s.</b>",
   "<b>Judge clicks “protect this washer”.</b> The plan changes <i>elsewhere</i>. The cap is never "
   "violated. “It bent; it did not break the constraint.”",
   "<b>Judge kills member C.</b> Its panel goes hatched. The camber band visibly grows — “its last "
   "known draw is still reserved, because unknown is not zero” — and another member's flexible slot moves.",
   "<b>Click the deferred washer.</b> The load path opens. “That is not a log message. That is the "
   "arithmetic that made the decision, travelling with the decision.”"]),

 ("h3", "2:10–2:35 · The two beats nobody else has"),
 ("call", "5 — “Kill the coordinator.”",
   ["Five lease countdowns run to zero. Five members step down to their floors. No overload. No "
    "flapping. The site gets <i>quieter</i>.",
    "“A budget here is not a command — it is a lease with a six-second life. If it is not renewed, "
    "every home falls back to its safe floor on its own, without being told. Safety is a property of "
    "the protocol, not of the planner. Kill the brain and this gets safer, not more dangerous.”",
    "Restart it. It refuses to issue a lease for one full TTL and says so on screen. “It cannot know "
    "what it promised before it died, so it waits.”"]),
 ("callr", "6 — “Now set the chord below the sum of the safety floors.”",
   ["The system goes INFEASIBLE and names the members it cannot serve.",
    "“It will not report a compliance it did not achieve. A system that lies about its constraint is "
    "worse than no system, because someone would trust it.”"]),
 ("h3", "2:35–3:00 · Boundary and next step"),
 ("p", "“Truss never switches mains voltage. It is not a smart panel, not certified, and it makes no "
   "savings claims. It is the coordination layer between a grid event and a home's own gateway — the "
   "layer that turns the smart meters India is already installing into something that can act fairly "
   "and prove it did. Next: one real Home Assistant household on the same contract, and policy "
   "validation with a hostel operator.”"),

 ("h2", "The wow moment, named"),
 ("pull", "It is not the slider. Every energy project has a slider. It is killing the coordinator and "
   "watching the system get safer — a distributed-systems result, visible without explanation, and "
   "physically unavailable to a team that only built a dashboard."),

 ("h2", "Failure proofing"),
 ("table", ["If", "Then"], [
   ["Internet is down", "Nothing changes. Broker, allocator, console and devices are all on the LAN"],
   ["A laptop cannot join", "Launch that member's IDs on the primary laptop. Single-laptop profile is rehearsed"],
   ["ESP32 is absent", "Software node on the identical contract, on-screen LED"],
   ["ESP32 dies mid-demo", "<b>Use it as beat 3.</b> A planned failure demo absorbs an unplanned one"],
   ["Broker restarts", "Leases expire, members floor, retained state restores. Narrate it"],
   ["The live run fails entirely", "<b>Replay.</b> One click, deterministic, animates the exact stored event log"],
   ["Everything fails", "90-second recording, labelled as a recording, plus screenshots of all six beats"],
  ], [0.30, 0.70]),
]},

# ============================================================ 12
{"num": "SECTION 12", "title": "Pitch and defence", "blocks": [
 ("h2", "10-second hook"),
 ("pull", "A truss carries a load no single beam could, by giving every member only what it can "
   "bear. Truss does that for a shared electrical feeder — and if you kill its coordinator, it gets "
   "safer, not more dangerous."),

 ("h2", "The three sentences to land"),
 ("ol", ["<b>“The flexibility is already there. What's missing is a way to express it without "
   "surrendering privacy.”</b>",
   "<b>“A budget isn't a command, it's a lease — so safety is a property of the protocol, not the "
   "planner.”</b>",
   "<b>“A system that can't meet its constraint has to say so, not fake it.”</b>"]),

 ("h2", "Ten questions we will get"),
 ("table", ["Question", "Answer"], [
   ["<b>Isn't this just load shedding?</b>",
    "Load shedding cuts by geography. We allocate by declared need, guarantee a floor, and remember "
    "who gave up what so the same home isn't the loser twice. Rotational shedding cannot tell a CPAP "
    "machine from a water heater."],
   ["<b>Why not just sort by priority?</b>",
    "Then the lowest-priority home is the designated loser every round, forever. Water-filling gives "
    "max-min fairness and debt weighting repays sacrifice. Fairness here is an algorithm with a "
    "theorem, not an adjective."],
   ["<b>Why water-filling over an optimiser?</b>",
    "Deterministic, " + C("O(n log n)") + ", provably max-min fair, explainable in one sentence. "
    "CP-SAT sits behind the same interface and must beat it on the fixture set or we ship without it."],
   ["<b>What if the optimiser is wrong or times out?</b>",
    "An independent validator re-checks every plan against the cap and can veto it. A vetoed or "
    "timed-out plan is discarded and water-filling's plan is issued. The console names which rule ran."],
   ["<b>What if the network or coordinator dies?</b>",
    "Leases expire and every member falls to its floor locally. No cloud on the judged path. A "
    "restarted coordinator waits one full TTL, because it can't know what it promised before it died."],
   ["<b>How do you know a device obeyed?</b>",
    "We don't assume. Every command is versioned and expiring; every device acknowledges with its "
    "<i>observed</i> state; the coordinator compares desired against observed watts. Missing acks "
    "reserve conservative power and trigger a replan."],
   ["<b>Isn't a missing device just zero load?</b>",
    "No, and that assumption is the most dangerous thing this system could make. A silent member "
    "keeps its last known draw reserved as camber, and you can watch the reserve band grow on screen."],
   ["<b>How is this fair, really?</b>",
    "Three commitments: a floor nobody crosses, equal treatment of equal need by construction, and "
    "debt that carries between rounds. Ostrom's design principles rendered as an allocation function. "
    "The fairness index is an engineering diagnostic, not a moral guarantee."],
   ["<b>How does it scale?</b>",
    "The coordinator sees offers, not devices, so its problem is " + C("O(members)") + ". That's the "
    "same boundary that gives privacy — the method-of-sections cut. Nesting coordinators is next and "
    "we haven't built it."],
   ["<b>What would production need that you don't have?</b>",
    "Per-device identity, TLS, broker ACLs, key rotation, signed firmware, audit retention, certified "
    "actuation and real standards adapters. We built none of those in 48 hours and we're not going to "
    "imply otherwise."],
  ], [0.27, 0.73]),

 ("h2", "Strongest closing"),
 ("pull", "We can show you a system that works. More usefully, we can show you what happens when it "
   "doesn't: kill the coordinator and every home falls back to its safe floor on its own. That is the "
   "difference between a demo and a system."),
 ("h3", "What we will not say"),
 ("p", "No market-size slide. No “AI-powered”. No savings percentage. No “revolutionise”. No claim of "
   "a Matter or OpenADR implementation. No user count, no pilot, and no partner we do not have."),
]},

# ============================================================ 13
{"num": "SECTION 13", "title": "Risks", "blocks": [
 ("table", ["#", "Risk", "L", "I", "Mitigation"], [
   ["R1", "<b>M1 becomes the bottleneck</b> and four people wait", "High", "Fatal",
    "Contract frozen at hour 1; everyone builds against fixtures; allocator is a pure function"],
   ["R2", "<b>Distributed integration eats the event</b> — five subsystems that never connect",
    "High", "Fatal",
    "Vertical slice by hour 6 is a hard kill point. Three members is an acceptable retreat; six "
    "disconnected demos is not"],
   ["R3", "Lease semantics subtly wrong — expiry fires late, or a member over-draws", "Med", "Fatal",
    "Hour-12 kill point is exactly this test. Property tests on I3. Monotonic clocks only"],
   ["R4", "CP-SAT consumes hours and delivers nothing", "Med", "High",
    "Behind an interface and time-boxed. Hour-30 kill point. Cutting it is a defensible answer"],
   ["R5", "Demo laptop cannot join the LAN at the venue", "Med", "High",
    "Single-laptop profile rehearsed as often as the distributed one. Own router <i>and</i> hotspot"],
   ["R6", "ESP32 fails at the venue", "Med", "Low",
    "Bonus only. If it dies mid-demo it becomes beat 3"],
   ["R7", "Console becomes a second project", "Med", "Med",
    "Seven-questions rule; anything answering none is deleted. Frozen at hour 36"],
   ["R8", "Judges read it as “just load shedding”", "Med", "High",
    "Beats 5 and 6 exist for this. Lead with the lease and the refusal, not the slider"],
   ["R9", "Someone claims Matter/OpenADR compliance under pressure", "Low", "Fatal",
    "The boundary is on slide one and in the README. Rehearsed as a scripted sentence"],
   ["R10", "Scope creep from mentor feedback at Review 1", "High", "Med",
    "Feedback is logged, not implemented. Only core-loop fixes are actioned before Review 2"],
   ["R11", "Event dates or submission deadline missed", "Low", "Fatal",
    "Open items confirmed directly, today, with a written record of who said what"],
   ["R12", "Fatigue-driven breakage in the last six hours", "High", "High",
    "Hours 42–48 are bug fixes with rollback only. Rest in rotation. Schema and allocator frozen"],
  ], [0.06, 0.30, 0.07, 0.07, 0.50]),

 ("h2", "The three that actually decide the outcome"),
 ("ul", ["<b>R2</b> — if the vertical slice is not alive at hour 6, nothing else in this document "
   "matters. Everything is subordinate to that.",
   "<b>R3</b> — the lease mechanism is the difference between this project and a nicer dashboard. "
   "Without it we have an ordinary submission with good vocabulary.",
   "<b>R8</b> — the idea is genuinely distinguishable, but only if we lead with the distinguishing "
   "parts. The slider is the setup; the coordinator kill and the refusal are the pitch."]),

 ("h2", "Competition constraints"),
 ("p", "Code2Create requires projects to be built during the event, from scratch, with no pre-built "
   "projects, prior commits or reused code. AI tool use is permitted; hardware is allowed but "
   "self-supplied. [S17][S18]"),
 ("p", A("What that does not forbid:") + " deciding what to build, freezing interfaces on paper, "
   "learning the tools with disposable exercises, brand and pitch material, and rehearsal. The "
   "preparation repository holds plans, brand, protocol specification and research — and no "
   "implementation code. The competition repository is created after the clock starts."),
 ("callr", "Four things to confirm directly with organisers — do not infer any of them",
   ["<b>The event dates.</b> The official graVITas page and ACM-VIT's promotional material disagreed "
    "(6–8 vs 7–9 September). [S17][S19]",
    "<b>Idea submission state and deadline.</b> Sources gave conflicting internal and external deadlines.",
    "<b>What “from scratch” permits.</b> Ask explicitly whether written interface specifications "
    "prepared in advance are acceptable. Until answered, assume the strictest reading.",
    "<b>Judging weights.</b> The official page listed criteria as TBD."]),
]},

# ============================================================ 14
{"num": "SECTION 14", "title": "Sources", "blocks": [
 ("h3", "Confidence vocabulary"),
 ("ul", ["<b>Verified</b> — the linked source directly supports the limited claim made.",
   "<b>Strong inference</b> — two credible facts align, but no single source joins them. Labelled "
   "wherever used.",
   "<b>Speculation</b> — labelled, and excluded from every strategy claim."]),
 ("p", "Three standing rules. Commercial product pages establish that a <b>feature exists</b>, not "
   "independent performance. Standards references establish <b>protocol direction</b>, not "
   "interoperability or certification of this prototype. Problem-class evidence establishes that "
   "<b>the problem is real</b>, not demand or savings for Truss."),

 ("h3", "Core mechanism"),
 ("table", ["ID", "Source", "What it supports"], [
   ["S01", "Gray &amp; Cheriton, <i>Leases: An Efficient Fault-Tolerant Mechanism for Distributed "
    "File Cache Consistency</i>, SOSP '89",
    "The lease mechanism, fail-safe expiry, and the coordinator-restart rule. Non-Byzantine failures "
    "affect performance, not correctness; short terms bound the damage"],
   ["S02", "Max-min fairness / leximin / water-filling literature (Bertsekas &amp; Gallager; "
    "Radunović &amp; Le Boudec)",
    "Water-filling yields the max-min fair allocation; max-min fair allocations are the "
    "lexicographically maximal feasible ones"],
   ["S07", "Packetized Energy Management — Almassalkhi, Frolik, Hines et al.",
    "Nearest prior art: anonymous asynchronous packet requests, statistical fairness, preserved "
    "privacy and quality of service"],
   ["S08", "Ostrom, <i>Governing the Commons</i> (1990); Ostrom Workshop design principles",
    "Boundaries, congruence, collective choice, monitoring, graduated sanctions, conflict resolution "
    "— the frame for the member boundary and the debt ledger"],
  ], [0.07, 0.40, 0.53]),

 ("h3", "Standards"),
 ("table", ["ID", "Source", "What it supports"], [
   ["S03", "OASIS MQTT 5.0 specification", "Lightweight pub/sub for IoT. Sessions, QoS, message expiry, Will messages"],
   ["S04", "Eclipse Mosquitto documentation", "Open-source lightweight MQTT 5/3.x broker"],
   ["S05", "OpenADR Alliance — OpenADR 3.x, VTN/VEN architecture",
    "Standardised demand-response event exchange; 3.0 moves to REST with webhooks; 3.1 is not "
    "backwards compatible. Upstream signal direction only"],
   ["S06", "Connectivity Standards Alliance — Matter 1.5",
    "Electrical energy tariff device type; Commodity Tariff, Commodity Price, Electrical Grid "
    "Conditions, Energy Preference, Power Topology clusters. <b>Not</b> evidence that we implement Matter"],
  ], [0.07, 0.40, 0.53]),

 ("h3", "Problem class and prior art"),
 ("table", ["ID", "Source", "What it supports"], [
   ["S09", "IEA, <i>Electricity 2026</i> — flexibility analysis", "Flexible demand systematically under-used"],
   ["S10", "IEA, <i>Efficient Grid-Interactive Buildings in India</i>",
    "Grid-interactive buildings as an Indian opportunity joining efficiency, digital technology and peak shifting"],
   ["S11", "IEA, <i>Scaling Up Demand Flexibility</i>", "Reliability, cost, renewable integration, network-constraint benefits"],
   ["S12", "India RDSS programme reporting",
    "25 crore smart meters, March 2028 deadline, ~₹2.83 lakh crore sanctioned. Supports “measurement "
    "arriving, coordination missing”. <b>Does not</b> establish demand for Truss"],
   ["S13", "SPAN official material", "Circuit control, load priority, dynamic EV charging. Feature existence only"],
   ["S14", "Lumin official material", "Power limit, load management, scheduling, local control. Feature existence only"],
   ["S15", "Home Assistant energy documentation", "Multi-brand energy visibility and device integration"],
   ["S16", "Home Assistant MQTT documentation", "Local broker, discovery, MQTT 5 integration"],
  ], [0.07, 0.40, 0.53]),

 ("h3", "Tooling and event"),
 ("table", ["ID", "Source", "What it supports"], [
   ["S20", "Google OR-Tools documentation", "CP-SAT suitability for discrete on/off loads, deadlines, minimum runs, capacity"],
   ["S21", "Hypothesis documentation", "Property-based test generation over the safety invariants"],
   ["S22", "Wokwi documentation", "ESP32 Wi-Fi/MQTT simulation. <b>Rehearsal aid only</b> — its public gateway cannot reach our LAN"],
   ["S17", "Official graVITas '26 / Code2Create 7.0 page",
    "Venue, duration, team size, hardware self-supply, from-scratch rule, AI allowance. Criteria "
    "listed as TBD. <b>Date conflict unresolved</b>"],
   ["S18", "Unstop organiser listing",
    "Registration, eligibility, round sequence, eliminatory prototype review, prohibition on "
    "pre-built projects and prior commits"],
   ["S19", "ACM-VIT public material", "Open Innovation framing, submission deadlines, and a "
    "conflicting 7–9 September date. <b>Confirm directly</b>"],
  ], [0.07, 0.40, 0.53]),

 ("call", "What we must never say",
   ["That we implement OpenADR or Matter. We ship one OpenADR-<i>shaped</i> fixture and a Matter "
    "adapter <i>interface</i>.",
    "That Truss is cheaper, greener or more efficient than any named product. We have measured none of that.",
    "That Packetized Energy Management is our idea. It is prior art, and naming your nearest "
    "neighbour in the literature is a strength.",
    "That any Indian policy document mandates or endorses this. Draft consultation material is not law."]),
]},

]
