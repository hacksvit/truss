# 07 — The allocator

## Design rule

**The allocator is a pure function.** Snapshot in, allocation out. No I/O, no
network, no clock, no randomness. It can therefore be tested exhaustively,
replayed deterministically, and reasoned about without running the system. Every
temptation to let it read the world must be refused; the world arrives in the
snapshot.

## Tier 1 — debt-weighted water-filling

This is the default, and it is not a fallback we apologise for. It is the
primary rule; CP-SAT is an *enhancement* that must beat it or be discarded.

### The rule in one sentence

> Give every member its floor, then raise all members together at the same rate
> until each is satisfied or the power runs out.

That is water-filling, and it produces the **max-min fair** allocation: it
maximises the smallest allocation, then the second smallest, and so on — the
*leximin* order. [S02] Properties worth stating to a judge:

- **Deterministic.** Same snapshot, same answer, always.
- **`O(n log n)`.** Sort by demand, fill in one pass. Microseconds for five
  members, and it would still be microseconds for five thousand.
- **Provably fair.** Two members with identical offers receive identical budgets.
  This is a theorem, not a hope.
- **Explainable in one breath.** "We fill everyone's glass at the same rate until
  the jug is empty." A judge understands it faster than we can draw it.

### The algorithm

```
allocate(offers, top_chord_w, camber_w):
    allocatable = top_chord_w - camber_w

    # 1. Floors are not negotiable
    floors = sum(o.floor_w for o in offers)
    if floors > allocatable:
        return INFEASIBLE(unserved = members_beyond(allocatable))

    budget  = {o.member: o.floor_w for o in offers}
    surplus = allocatable - floors

    # 2. Debt weighting: those who gave up more are filled faster
    #    w in [1.0, 2.0]; capped so debt can never starve a debt-free member
    w = {o.member: 1.0 + min(o.debt_wh / DEBT_SCALE, 1.0) for o in offers}

    # 3. Water-filling over weighted demand
    remaining = {o.member: o.useful_w - o.floor_w for o in offers}
    while surplus > EPSILON and any(remaining.values() > 0):
        active = [m for m in remaining if remaining[m] > 0]
        rate   = surplus / sum(w[m] for m in active)
        step   = min(min(remaining[m] / w[m] for m in active), rate)
        for m in active:
            take          = step * w[m]
            budget[m]    += take
            remaining[m] -= take
            surplus      -= take

    return Allocation(budget, rule="debt_weighted_water_filling")
```

`DEBT_SCALE` is a declared constant, shown in the UI, not a tuned magic number.
The weight is capped at 2.0 so that accumulated debt accelerates a member's
recovery but can never starve a member who has never been curtailed. That cap is
a fairness decision and it is deliberate: unbounded debt weighting is its own
injustice.

## Tier 2 — CP-SAT, behind the same interface

Water-filling allocates **power now**. It does not schedule **energy over time**,
so it cannot reason about a water heater that needs 40 minutes before 06:00.
CP-SAT does that.

For device `i` and five-minute slot `t`, binary `x[i,t]` (or one of a small set of
allowed power levels):

**Maximise** delivered utility − missed-deadline penalty − switching penalty −
member curtailment-debt penalty

**Subject to**
- scheduled watts in each slot ≤ member budget for that slot;
- protected devices remain on while the system reports feasibility;
- deadline jobs receive their required slots before their deadline;
- minimum run and minimum off times prevent oscillation;
- no member exceeds its published envelope;
- stale or unacknowledged load reserves conservative watts.

**Hard rules around it, and these are not negotiable:**

1. **Wall-clock time box.** Exceed it and the result is discarded.
2. **Identical output schema.** CP-SAT and water-filling are indistinguishable
   downstream.
3. **The independent validator sees both.** A CP-SAT plan that fails cap
   validation is thrown away and water-filling's plan is issued instead.
4. **The console names which rule produced the live plan.** Always.

If CP-SAT is not green by hour 18, it is cut. The demo does not depend on it, and
saying "we implemented the optimal planner and it lost to the simple one on this
scenario, so we shipped the simple one" is a *stronger* answer than showing a
solver that sometimes times out.

## Why not a market, an auction, or peer-to-peer consensus

All three were considered.

- **Auctions** need a currency, and introducing money into a hostel corridor
  changes the ethics of the product. Ability to pay is not the same as need, and
  we would be building the thing we set out to replace.
- **Peer-to-peer consensus** is a research project. The hierarchy is not a
  compromise — a shared feeder genuinely has a single physical constraint, and
  modelling it as a distributed agreement problem adds failure modes to solve a
  problem physics already solved.
- **Priority sorting**, the obvious choice, fails the fairness test: the same
  member is the designated loser every round, forever. Debt weighting exists
  precisely to prevent that, and it is why we can answer "how is this fair?" with
  an algorithm instead of an adjective.

## Testing the allocator

Because it is pure, it can be tested properly, and this is the cheapest
credibility in the project:

- **Unit** — floors respected, cap respected, INFEASIBLE when floors exceed cap.
- **Property-based** (Hypothesis) over generated offer sets:
  - allocation never exceeds `top_chord − camber`;
  - no member below its floor in any feasible result;
  - identical offers receive identical budgets;
  - adding power never reduces any member's budget (monotonicity);
  - the result is leximin-dominant over any hand-built alternative.
- **Regression** — every scenario in the demo script, frozen as a fixture with
  its expected allocation.
