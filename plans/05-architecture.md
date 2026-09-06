# 05 — Architecture

## Three planes, kept separate on purpose

```
                    OpenADR-shaped capacity event  (fixture / slider)
                                   │
                    ┌──────────────▼──────────────┐
                    │        COORDINATOR          │   the joint
                    │  twin · allocator · leases  │
                    │  ── independent validator ──│   can veto any plan
                    └──────────────┬──────────────┘
                                   │
              offer ▲              │              ▼ lease
        ┌────────────┬─────────────┼─────────────┬────────────┐
        │            │             │             │            │
   ┌────▼───┐   ┌────▼───┐    ┌────▼───┐    ┌────▼───┐   ┌────▼───┐
   │member A│   │member B│    │member C│    │member D│   │member E│
   └────┬───┘   └────┬───┘    └────┬───┘    └────┬───┘   └────┬───┘
        │            │             │             │            │
    telemetry → twin → command → ack → observed → replan
        │            │             │             │            │
     4–6 emulated devices each  +  one optional ESP32 low-voltage light

  CONTROL PLANE    versioned MQTT 5 topics on the local LAN
  EVIDENCE PLANE   append-only event log, monotonic sequence, replayable
  OPERATOR PLANE   one console, four controls, one load-path inspector
```

The separation is not tidiness. It is what lets the operator plane be rebuilt,
the evidence plane be replayed, and the control plane be fuzzed, without any of
the three touching the others.

## Component decisions

| Component | Why it exists | Failure fallback |
|---|---|---|
| **Eclipse Mosquitto** | Lightweight local MQTT 5 broker. Sessions, QoS, retained messages and Will messages for abnormal disconnect — the last is what makes member death detectable in milliseconds rather than seconds. [S03][S04] | Broker and all core services collapse onto the primary laptop. Second broker config only after the core is green |
| **Member agent** | Owns device detail, forms the offer, holds the lease, enforces the floor locally | Last valid budget plus fixed local priority policy. It keeps working with no coordinator at all |
| **Coordinator** | Maintains twins, validates events, calls the allocator, issues and renews leases | Last good plan; on restart, one full TTL of silence before issuing leases |
| **Allocator** | Pure function: snapshot → allocation. No I/O, no clock, no network | It is already the fallback. CP-SAT sits *behind* it, never in front |
| **Cap validator** | Separate module that independently re-checks any plan against the cap before it is issued | If it rejects, the previous plan stands and the UI says a plan was vetoed |
| **Device nodes** | Deterministic, seeded device behaviour; make five laptops behave like five homes | One laptop runs every process with distinct IDs |
| **Pydantic schemas** | Reject malformed or stale messages with explainable errors | Hand-validated minimum field set |
| **SQLite event log** | Append-only telemetry, offers, allocations, leases, acks, expiries | Newline-delimited JSON file |
| **FastAPI read API** | Separates system state from UI; exposes health and replay | Console imports a read-only state adapter directly |
| **Console** (Streamlit + Plotly) | Fastest route to a legible operator screen in Python | Static seeded state plus live event counter. Do not rebuild in React mid-event |
| **ESP32 node** | Makes one lease physically visible; proves protocol parity | A software node with an on-screen LED on the identical contract |

## The clock

This is where distributed systems quietly go wrong, so it is decided up front.

- **Lease expiry is measured on the member's own monotonic clock**, never on wall
  time and never on a timestamp carried in a message. Five laptops on a hotspot
  will not agree on wall time and do not need to.
- The coordinator sends a **duration** (`ttl_ms`), not an absolute deadline. The
  member starts its own countdown on receipt.
- Message timestamps exist for the event log and for human reading. **No control
  decision depends on them.**
- Sequence numbers are per-publisher and monotonic. Ordering is decided by
  sequence number, never by arrival order or timestamp.

The safety argument in [08-safety.md](08-safety.md) depends on this, and it is
the first thing a strong technical judge will probe.

## Deployment

One team-controlled router, or the primary laptop's hotspot. Primary laptop runs
broker, coordinator, API, database and console. Four other laptops run one member
plus four to six devices each. Everything binds to the private LAN. **No cloud on
the judged path.** A single-laptop profile runs every process with distinct IDs
and is tested at least as often as the distributed one.

## Security boundary, stated honestly

The judged build uses explicit demo credentials on an isolated LAN with no public
exposure. A production system would need per-device identity, TLS, broker ACLs,
key rotation, signed firmware, audit retention and safety-certified actuation. We
have built none of those and will say so before a judge has to ask.

What we *do* build is the privacy boundary, because that one is architectural
rather than operational: the coordinator cannot leak a device list it was never
given.
