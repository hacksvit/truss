# 06 — Protocol

The gusset plate. This is where the project fails if it fails, so this is where
the rigour goes.

## Topic namespace

```
truss/v1/site/{site}/member/{member}/status        retained, Will message
truss/v1/site/{site}/member/{member}/offer
truss/v1/site/{site}/member/{member}/lease
truss/v1/site/{site}/member/{member}/lease/ack
truss/v1/site/{site}/device/{device}/telemetry
truss/v1/site/{site}/device/{device}/command
truss/v1/site/{site}/device/{device}/ack
truss/v1/site/{site}/event/capacity
truss/v1/site/{site}/plan                          retained, latest plan
```

Members subscribe only to their own lease topic. Devices subscribe only to their
own command topic. Nothing subscribes to everything except the logger, and the
logger is read-only by construction.

## The offer — what a member publishes

```json
{
  "schema": "truss.offer.v1",
  "seq": 1043,
  "member_id": "block-c",
  "floor_w": 180,
  "firm_w": 420,
  "useful_w": 1650,
  "deadline_energy_wh": 900,
  "deadline_by": "2026-09-07T06:00:00+05:30",
  "debt_wh": 240,
  "device_count": 6,
  "ts": "2026-09-07T19:41:02+05:30"
}
```

Five numbers describe a household completely enough to allocate to it, and not
nearly well enough to know anything about the people in it. `device_count` is
included only so the console can show fleet health; it is not used by the
allocator.

- `floor_w` — below this the member is harmed. Fridge, router, medical.
- `firm_w` — currently in use, would rather not lose.
- `useful_w` — the most it could productively absorb right now.
- `deadline_energy_wh` — energy it must receive before `deadline_by`.
- `debt_wh` — curtailment absorbed so far this session. Written by the member,
  audited by the coordinator against its own log.

## The lease — what a member receives

```json
{
  "schema": "truss.lease.v1",
  "plan_id": "plan-0042",
  "version": 42,
  "member_id": "block-c",
  "budget_w": 312,
  "ttl_ms": 6000,
  "reason": "cap_drop",
  "basis": {
    "top_chord_w": 1800,
    "camber_w": 240,
    "allocatable_w": 1560,
    "rule": "debt_weighted_water_filling",
    "members_at_floor": 0
  },
  "correlation_id": "cap-event-0007"
}
```

Three properties, and each earns its place:

- **`ttl_ms` is a duration, not a deadline.** The member starts its own monotonic
  countdown on receipt. No clock agreement required.
- **`basis` is the load path.** Everything the console needs to explain this
  number travels with the number. Explanations cannot drift from decisions
  because they are the same message.
- **`version` is monotonic.** A member applies a lease only if its version
  exceeds the last applied version. Duplicates and reordering are normal and
  safe.

### The lease rule, stated exactly

> A member may draw up to `budget_w`. When its countdown reaches zero without a
> newer lease, it reduces to `floor_w` — locally, immediately, and without
> requiring any message.

Everything in [08-safety.md](08-safety.md) follows from that one sentence.

### Coordinator restart

A coordinator that restarts **must not issue any lease for one full TTL**,
because it cannot know what it granted before it died. It publishes
`status: recovering` with a countdown, the console shows it, and it then resumes.
This is Gray & Cheriton's recovery rule, and it is four lines of code. [S01]

## The command — what a device receives

```json
{
  "schema": "truss.command.v1",
  "plan_id": "plan-0042",
  "version": 42,
  "device_id": "washer-1",
  "desired_state": "deferred",
  "expires_at_ms": 4000,
  "reason": "member_budget_exceeded",
  "correlation_id": "cap-event-0007"
}
```

**Device rule:** apply only if `version` exceeds the last applied version and the
command has not expired; then publish exactly one acknowledgement carrying the
*observed* state. Duplicate delivery is normal and must be safe.

```json
{
  "schema": "truss.ack.v1",
  "plan_id": "plan-0042",
  "version": 42,
  "device_id": "washer-1",
  "result": "applied",
  "observed_state": "deferred",
  "observed_w": 0,
  "seq": 88213
}
```

`result` is one of `applied` | `rejected` | `duplicate` | `expired`. A device that
rejects must say why — a washing machine mid-cycle with `min_run_s` remaining is
*allowed* to refuse, and the coordinator must plan around a refusal rather than
insist. Members are autonomous; that is the point of the architecture and it has
to be true in the protocol, not just in the pitch.

## State machines

**Device:** `idle → requested → running → (deferred | completing) → idle`, with
`min_run_s` blocking the exit from `running` and `deadline` forcing entry.

**Member:** `joining → offering → leased → (renewing | expiring) → floor`, where
`floor` is reachable from every state and is the only state reachable without a
message.

**Coordinator:** `recovering → observing → planning → issuing → observing`, with
`infeasible` as a first-class terminal state that is reported, not hidden.

## Message hygiene

- MQTT 5 **message expiry interval** on commands and leases, so the broker itself
  drops stale control messages during a partition.
- **Will messages** on member status, so death is detected by the broker rather
  than by a timeout.
- **Retained** on status and plan, so a joining console is immediately correct.
- QoS 1 everywhere, with idempotence carrying the correctness. QoS 2 buys nothing
  once versioning is right and costs latency.
