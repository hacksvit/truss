# Ownership and review ledger

M1–M5 are proposed team roles. Real names and skill availability were not supplied. M1 is assumed to be the strong builder. The scaffold was generated with an AI assistant during the event after the user authorised implementation; the table is **ownership to take over**, not a claim that five people wrote these files.

| Role | Stream | First concrete handoff | Required reviewer |
|---|---|---|---|
| M1 | Schemas, registry, allocator, reservation gate, durable coordinator | Checked wire fixtures and gate API immediately; one-member grant producer G12 | M3 receiver checks, M5 independent oracle |
| M2 | Private virtual devices, independent plant, supervisor and machine setup | Core plant input/output examples immediately; separate-process plant G8/G12 | M1 ceiling constraints, M3 binding/commands |
| M3 | MQTT roles, member receiver, private local policy, event ingestion | Broker/topic credentials privately; member–plant contract G2; loop G12 | M2 independent expiry, M1 authority |
| M4 | All three frontend routes, snapshot state, presentation and accessibility | Mock console immediately; same snapshot consumer at G12/G24 | M5 uncertainty/source/capability rendering |
| M5 | Mock/API/evidence projection, invariant oracle, replay/lab, demo | Mock/fixtures immediately; one-house observer G12; evidence gate G24 | M1 metric definitions, M4 contract compatibility |

Do not split M1 across planner, integration rescue and optional features simultaneously. M2 and M3 pair at the plant boundary; M4 never waits for MQTT. M5 starts from fixture events, then swaps in validated real events. The complete dependency schedule is [plan 21](../plans/21-delivery.md).

Record each actual contribution below when it occurs: date/time, person, files, what changed, relevant test command/results, producer/consumer reviewer, and any changed claim. Do not backfill invented hours or authors. No human review is recorded yet.
