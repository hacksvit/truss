# 08 — Safety

The distinguishing engineering in this project. Read this one twice.

## The idea

A budget is not a command. **A budget is a lease.**

A command says *do this*, and it is only as good as the channel that carried it.
A lease says *you may draw this much until your own clock says stop*, and it is
good even if the channel dies, the coordinator dies, and every message in flight
is lost.

This is Gray & Cheriton's lease mechanism from distributed file cache
consistency, applied to watts rather than cache lines. [S01] Their result is the
one we need: non-Byzantine failures affect *performance*, not *correctness*, and
short lease terms bound the damage.

## The six invariants

Stated so they can be tested, and each one is.

| | Invariant |
|---|---|
| **I1 — Cap** | Sum of observed member draw ≤ top chord, after the response window |
| **I2 — Floor** | No member is allocated below its declared floor while the system reports feasibility |
| **I3 — Lease safety** | At any instant, the sum of **outstanding lease amounts** ≤ top chord − camber |
| **I4 — Honesty** | If I2 cannot hold, the system declares INFEASIBLE and names the unserved members. It never reports compliance it did not achieve |
| **I5 — Idempotence** | Applying the same lease or command twice has the same effect as applying it once |
| **I6 — Monotonicity** | A member never applies a lease older than the one it holds |

**I3 is the load-bearing one.** It is a statement about what the coordinator has
*promised*, not about what it has *observed*. Because the coordinator issues
leases and never over-issues, and because members self-limit on expiry, the cap
holds under:

- **coordinator death** — leases expire, members fall to floor;
- **network partition** — the isolated member self-limits; no split brain;
- **total message loss** — the same as partition, from the member's view;
- **coordinator restart** — it waits one full TTL before issuing, because it
  cannot know what it granted before.

Safety is a property of the **protocol**, not of the planner. The planner may be
wrong, slow, or entirely absent. The cap still holds.

## Camber — unknown is not zero

A member that stops reporting has not stopped drawing power. Treating silence as
zero is the single most dangerous thing this system could do, and it is exactly
what a naive implementation does.

**Camber** is the reserved band under the top chord for load we cannot see:

```
camber_w = Σ last_known_draw(m)  for every stale or unacknowledged member m
           + a fixed measurement reserve
```

Three consequences, all visible:

1. Stale members keep their last known draw reserved. They are not free.
2. The camber band is **drawn on the console**. When a member goes dark you watch
   the band grow and the allocatable power shrink. An invisible safety principle
   becomes a visible rectangle.
3. Camber is repaid the instant the member reports again — the band shrinks and
   power returns to the pool, live, on screen.

The bridge-building sense is exact: camber is deliberate compensation for a load
you know is coming but cannot yet see.

## Failure modes and responses

| Failure | Detection | Response | Judged? |
|---|---|---|---|
| Device ignores a command | Missing ack within window | Reserve its observed draw; replan; mark unverified | Yes |
| Device refuses (mid-cycle) | `result: rejected` | Legitimate. Plan around it, do not insist | Yes |
| Member process dies | MQTT Will message, immediate | Camber grows by last known draw; replan | **Yes — scripted beat 4** |
| Member partitioned | Lease expires locally | Member self-limits to floor with no message | Yes |
| Coordinator dies | Every lease expires | **All members → floor within one TTL** | **Yes — scripted beat 5** |
| Coordinator restarts | `status: recovering` | No lease issued for one full TTL, countdown shown | Yes |
| Broker restarts | Connection loss | Leases expire; members floor; retained state restores on reconnect | Yes |
| Floors exceed cap | Allocator returns INFEASIBLE | Declare it, name unserved members, do not fabricate | **Yes — scripted beat 6** |
| CP-SAT times out | Wall-clock box | Water-filling plan issued; console names the rule | Yes |
| Clock skew across laptops | — | Cannot occur. Expiry is monotonic and local; no decision reads a timestamp | Explain if asked |
| ESP32 absent or dies | Heartbeat | Software node on the identical contract, or use it as the failure demo | Yes |

## Fault injection

Not a testing afterthought — a **build deliverable with an owner**, and the fault
console is a first-class part of the product.

- `truss chaos kill-member C`
- `truss chaos kill-coordinator`
- `truss chaos partition C --seconds 20`
- `truss chaos drop-acks C --rate 0.5`
- `truss chaos delay-telemetry --ms 3000`
- `truss chaos cap --watts 400` (below the sum of floors — forces INFEASIBLE)

Every one of these runs during the rehearsal, and at least three run in front of
the judges.

## Property-based testing

The cheapest credibility available to this team, and it costs about two hours.

```python
@given(offers=offer_sets(), cap=watts(), camber=watts())
def test_never_exceeds_cap(offers, cap, camber):
    result = allocate(offers, cap, camber)
    if result.feasible:
        assert sum(result.budget.values()) <= cap - camber
        assert all(result.budget[m] >= o.floor_w for m, o in offers.items())
    else:
        assert sum(o.floor_w for o in offers.values()) > cap - camber
```

Hypothesis generates thousands of scenarios, including the degenerate ones nobody
thinks to write: zero members, one member, every member at floor, identical
offers, a cap of exactly the floor sum, a cap one watt below it.

"We fuzz-tested the safety invariant across ten thousand generated scenarios" is
a sentence almost no hackathon team can say truthfully. We can, and it takes an
afternoon.
