# Handoff prompt

Paste everything below the line into a fresh session, with the model given read
access to this folder (`~/truss`). Written for a long-horizon reasoning model
doing a deep research-plus-architecture pass.

**Before you paste:** confirm the event dates and the "from scratch" ruling with
the organisers first (see [plans/14-rules.md](plans/14-rules.md)). If written
interface specs prepared in advance are *not* permitted, tell the model so in the
prompt — it changes what it should output.

---

You have read access to the folder `~/truss`. Read all of it before you write
anything: `README.md`, `LOGO.md`, every file in `plans/` (00 through 16), and
`research/sources.md`. That corpus is the current state of a project called
**Truss** and it is the ground truth for this task.

## What Truss is

A coordination layer for shared electrical capacity. Homes, hostel rooms or
small buildings share a constrained feeder or inverter. Each **member** (one
home) keeps its device list private and publishes only a **flexibility offer** —
floor watts, firm watts, useful watts, deadline energy, accumulated curtailment
debt. A **coordinator** allocates the available power by debt-weighted
water-filling, which is provably max-min fair, and issues **leases**: an amount,
valid for a duration measured on the member's own monotonic clock. An unrenewed
lease expires into the member's safe floor, locally, with no message required.

The thesis of the whole system, and the thing to protect in every decision you
make: **safety is a property of the protocol, not of the planner.** Kill the
coordinator and every member falls to its floor. The site gets quieter, not more
dangerous.

## Context and constraints

- This is a 48-hour hackathon build (Code2Create 7.0, ACM-VIT, graVITas '26) by
  a team of five. One strong builder, four less experienced.
- Competition rules require the project to be built **during** the event, from
  scratch, with no prior commits and no reused project code. `~/truss` therefore
  contains **plans only, no implementation**. Respect that: see below for what
  you may and may not output.
- The judged path runs entirely on a local LAN. No cloud, no internet dependency.
- Python for the backend, React + Vite + TypeScript for the front end, MQTT 5 via
  Mosquitto, Pydantic for schemas, OR-Tools CP-SAT as an optional second
  allocator, Hypothesis for property tests. Deviate only with a stated reason.
- The prototype **never switches mains voltage**, claims no certification, and
  makes no savings claims. Do not let any output drift across that line.

## Your task, in four parts

### 1. Research and challenge

Go deep on the problem space and come back with things the plans do not already
know. Specifically:

- **Verify or refute the technical claims.** The lease argument leans on Gray &
  Cheriton (SOSP '89). The fairness claim leans on water-filling producing the
  max-min fair (leximin) allocation. The nearest prior art is claimed to be
  Packetized Energy Management. Check all three. If any is overstated, say so
  plainly — that matters more to us than agreement.
- **Find prior art we missed.** Especially: transactive energy, local flexibility
  markets, EEBus, IEEE 2030.5, CTA-2045, OpenADR 3.1, Matter 1.5 energy clusters,
  and any academic work on privacy-preserving load coordination with household
  boundaries. If something out there already does what we claim is novel, we need
  to know now, not from a judge.
- **Stress the fairness design.** Debt-weighted water-filling with a weight cap
  of 2.0 — is that defensible? What are its failure modes? Is there a better
  rule with an equally short explanation? Consider what happens with adversarial
  or simply mistaken offers: a member that overstates its floor gets more power
  forever, and we have no answer for that yet. Propose one.
- **Attack the safety argument.** Invariant I3 says the sum of outstanding lease
  amounts never exceeds `cap − camber`, under arbitrary message loss. Try to
  break it. Consider clock drift, lease renewal races, a member that applies a
  lease it should have rejected, a coordinator that restarts twice inside one
  TTL, and a partition that heals mid-renewal.

Report findings with confidence levels and links. Follow the evidence discipline
in `research/sources.md`: distinguish verified from inferred from speculative,
and never present a commercial product page as evidence of performance.

### 2. Refine the existing plans

Do not rewrite them wholesale — they represent decisions we have already argued
through. Instead produce a **change list**: what is wrong, what is missing, what
should be cut, each with a reason. Be specific and blunt. In particular:

- Is the 48-hour timeline in `plans/11-timeline.md` actually achievable by four
  inexperienced builders plus one strong one? Where does it break first?
- Is the MVP in `plans/04-mvp.md` still too large? What would you cut, in order?
- The `/lab` scalability demo in `plans/16-frontend.md` claims that planning
  latency stays flat as members grow. Is that true for our actual design, and
  what would we need to measure to prove it live?
- Do the six invariants in `plans/08-safety.md` cover everything they need to?

### 3. Design the architecture and the file tree

Produce the complete structure for both backend and front end:

- Full directory tree with every file that will exist, each with a one-line
  purpose.
- For every module: its public interface, its dependencies, and which of the
  five team members owns it.
- The complete Pydantic schema set for all message types in
  `plans/06-protocol.md`, as specifications.
- The exact WebSocket and REST contract between backend and front end — extend
  what `plans/16-frontend.md` sketches into something both sides can build
  against independently from hour one.
- The component tree for the three front-end routes (`/`, `/console`, `/lab`),
  with state ownership marked.
- The test plan: which invariants get property-based tests, which get unit tests,
  and what the mock server has to produce so the front end never blocks.

### 4. Sequence the build

Rewrite the hour-by-hour plan as a dependency graph rather than a list. Mark the
critical path. Identify every point where a person could be blocked waiting on
someone else, and say how to remove it. Give each of the five members a
parallelisable stream with explicit handoff moments.

## Output rules — read carefully

- **Do not write implementation code.** Competition rules forbid it and it would
  invalidate the entry. You may produce: directory trees, empty files with
  docstring headers stating purpose and interface, type and schema
  *specifications*, function *signatures* with contracts, prose, and diagrams.
  No function bodies, no algorithms in executable form, no config that runs.
- Where you would reach for code to explain an algorithm, use pseudocode clearly
  marked as such, in the style already used in `plans/07-planner.md`.
- Write to the same standard as the existing plans: specific, argued, honest
  about limits. Match their register. If you disagree with a decision in there,
  argue against it directly rather than quietly designing around it.
- Flag every assumption you make, and every place you needed information you did
  not have.
- Where you propose something new, say what it replaces and what it costs.

## What good looks like

The team reads your output and knows exactly what to build, who builds it, in
what order, and what to do when it goes wrong at 3 a.m. on day two. Nobody is
blocked on anybody. Every claim we plan to make in front of a judge is one we can
defend or one we have already dropped.

Start with the research pass. Tell us what we got wrong first.
