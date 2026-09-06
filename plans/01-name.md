# 01 — The name, and the vocabulary it gives us

## Why Truss

A good system name is not decoration. It is a compression of the design, and it
should keep paying out every time you reach for a word. Truss does that on three
levels.

### 1. The etymology is the architecture

*Truss* entered English from Old French **trousse** — a bundle; separate things
bound together and carried as one. That is the distributed-systems claim in the
word itself: five independent members, bound by a protocol, behaving as one
structure. Not one machine pretending to be five, and not five machines
pretending to be one.

### 2. The structure is the mechanism

A truss carries a load that no single member could carry. It does this by
**resolving** the load into forces along members that each stay inside their own
limit — some in tension, some in compression. Two properties follow, and both
are properties we want:

- **Every share is computable, not guessed.** The method of joints gives the
  exact force in every member. Truss gives the exact watt budget for every home,
  by a stated rule, with the arithmetic on screen.
- **The load path is traceable.** A structural engineer can follow a load from
  where it is applied to where it is carried. Truss can do the same in reverse:
  click any deferred device and get the causal chain that deferred it. We call
  it the **load path inspector**, and it is the feature judges will remember.

There is a third property that justifies the privacy boundary mathematically.
The **method of sections** lets you cut through a truss and compute the forces
crossing that cut *without solving the rest of the structure*. Truss cuts at the
member boundary: the coordinator reasons about five offers, not thirty devices.
The coordinator's problem size is `O(members)`, not `O(devices)` — which is both
the privacy argument and the scaling argument, and they turn out to be the same
argument.

### 3. Redundancy is the engineering word for fault tolerance

A planar truss with `j` joints is **statically determinate** at `m = 2j − 3`
members. Below that it is a mechanism and it collapses. Above that it is
**statically indeterminate** — it has spare load paths, so losing a member
redistributes force rather than ending the structure.

Structural engineers have called this *redundancy* for two centuries. It is the
same property distributed-systems engineers call fault tolerance, discovered
independently, in the same century, for the same reason. Truss is deliberately
indeterminate: kill a gateway and the remaining members absorb its share.

## The vocabulary

The name handed us these, and every one of them replaced a worse word:

| Truss term | System meaning | What it replaced |
|---|---|---|
| **Member** | One home, room or gateway | "node", "client" — neither of which suggests belonging |
| **Top chord** | Site capacity ceiling. Hard | "cap", "limit" |
| **Bottom chord** | The floor every member keeps | "minimum", "critical load" |
| **Web** | The live allocation between the chords | "the schedule" |
| **Joint** | The coordinator; where forces resolve | "server", "master" |
| **Panel** | One member's repeating section of the structure | "zone" |
| **Camber** | Headroom reserved for load we cannot see | "safety margin", "fudge factor" |
| **Load path** | The causal chain behind one decision | "explanation", "reason code" |
| **Buckling** | Failure by a mode you did not design for | "edge case" |
| **Gusset** | The joint plate — where real trusses actually fail | "the protocol", "the contract" |

**Camber** is worth dwelling on. A bridge truss is fabricated with a deliberate
upward curve so that under full design load it settles *level*. The camber is
not error; it is designed-in compensation for a load you know is coming but
cannot see yet. Truss reserves a camber band under the top chord for exactly
that: load it cannot currently observe. When a member goes dark, its last known
draw stays reserved, the camber band grows on screen, and the allocatable power
shrinks. An invisible safety principle — *unknown is not zero* — becomes a
visible rectangle.

**Gusset** is worth dwelling on for the opposite reason. The I-35W bridge in
Minneapolis collapsed in 2007 because of undersized gusset plates: the members
were fine, the *joints* failed. The lesson transfers exactly. Our members are
easy. The protocol between them is where this project will fail if it fails, so
that is where the versioning, the idempotence and the property tests go.

## Naming rules

- The system is **Truss**. One word. Never "Truss OS", never "TrussGrid", never
  an acronym expansion — there isn't one and inventing one would be a lie.
- Written **Truss** in prose, **TRUSS** only in the wordmark and slide titles.
- The MQTT namespace is `truss/v1/...`, the CLI is `truss`, the repository is
  `truss`.
- A home is a **member**, never a "node" or a "client".
- The cap is the **top chord** in the UI and in the docs. Say "cap" out loud to
  a judge who has not heard the vocabulary yet; say "top chord" once you have
  drawn the diagram.

## Honest notes on the name

- *Truss* also names a hernia support and a UK political figure. Neither
  association survives one sentence of context, and both are absent in the
  technical register the project lives in.
- Search engines will mix us with structural engineering results. That is a
  feature at this stage: the metaphor is the pitch, and the first result being a
  diagram of a bridge is not the worst introduction a project ever had.
