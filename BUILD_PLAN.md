# Build order — start here

Updated for the user's instruction: **backend first; frontend work starts after 9**. Assumption: 9 means 21:00 local time; this is a handoff order, not a scheduled automatic action. Codex owns the backend implementation now. The user takes the frontend after 9. M1–M5 below are review/team ownership roles, not invented personal contributions.

Check a box only after its acceptance test passes. A file existing is not completion.

## 1. Foundation and architecture

- [x] Establish fixed household baselines/maxima and protected/unclassified load policy.
- [x] Create backend and frontend module structure, strict schemas and checked wire examples.
- [x] Implement/test allocator, conservative reservations, anchored member lease receiver and virtual plant core.
- [x] Supply labelled mock API and all three frontend route shells, so frontend does not wait for MQTT.
- [x] Add ignored `pleaseread.md` for the plain-language hackathon explanation.
- [x] Freeze current Snapshot contract and document target-vs-current differences.
- [x] Finish current file/interface inventory, including live process entrypoints.

## 2. Backend first — critical path

- [x] **B1 Broker:** run a real local Mosquitto with separate role credentials; no anonymous client; negative read/write ACL tests pass.
- [x] **B2 Runtime:** one bounded receive queue per process; exact role/topic/run/boot checks; MQTT 5 reconnect, Will and graceful stop behavior.
- [x] **B3 Plant:** a separate process owns virtual devices, local deadline enforcement, independent meter, telemetry and acknowledgements. Member loss must not stop this process.
- [x] **B4 Member:** read private profile; publish aggregate offers; anchor one request; accept only valid grants; bind plant; forward a bounded ceiling and valid per-device commands.
- [x] **B5 Coordinator:** durable epoch/singleton, full restart wait, fresh input snapshot, independent proposal validator, reserve **before** publish, immutable retry response, no ack-based early reclaim.
- [x] **B6 One-house proof:** real MQTT grant → command → independently observed draw; stop coordinator and see measured return to baseline; protected virtual load remains.
- [x] **B7 Five-house run:** one supervisor owns five members, five plants and coordinator; ordinary draw respects admitted ceilings; privacy negative tests pass.
- [x] **B8 Live observer/API:** observe actual MQTT events; preserve unknown/stale data; stable Snapshot over REST/WS; durable revision/idempotency for cap controls. Mock and live sources cannot masquerade as each other.
- [x] **B9 Cap/recovery:** lower cap without erasing old authority; refuse new excess; show infeasible baseline; restart coordinator twice inside TTL; no stale grant revival.
- [x] **B10 Failure evidence:** broker loss/reconnect, member kill, delayed/duplicated grants, partition healing, stale telemetry; preserve logs/seeds and actual timing limits.
- [x] **B11 Handoff:** give the user working backend command, endpoint URL, generated schema/examples, error cases and exact known limitations. Frontend can still use mock if a live gate remains red.

Critical dependency chain:

```text
Schemas + registry
  → B1/B2 transport
  → B3 plant + B4 member + B5 coordinator (cores can advance independently)
  → B6 real one-house loop
  → B7 five houses + B8 live projection
  → B9/B10 adversarial runs
  → B11 backend handoff

Frozen snapshot → mock/fixtures → user's frontend after 9
                                 ↑ live provider joins at B8, no UI redesign required
```

## 3. User's frontend order after 9

- [ ] Read `docs/protocol.md`; run the existing mock console before changing the design.
- [ ] Own the layout and styling of `/`; keep fictional/prototype/source labels visible.
- [ ] Build `/console` capacity overview, household cards, unknown/stale states and source indicator.
- [ ] Add household drawer with protected policy and exact evidence. Missing evidence stays unavailable.
- [ ] Connect existing cap/chaos controls to typed operations; retain conflict/pending/error states.
- [ ] Swap to live Snapshot only when B8 passes; do not remove MOCK to make a demo look complete.
- [ ] Keep `/lab` measured and explicitly synthetic. Improve it only after console workflow works.
- [ ] Check keyboard/mobile layout, reconnect/polling, nulls and offline assets; run frontend tests/build.

Existing frontend tests/build are green (8 tests); these boxes mean the user's intended frontend work and final live handoff, not that the current shells are absent. Codex will not spend backend time redesigning these screens.

## 4. Optional, in this order

- [x] Inspect `~/ccode` hardware configuration; build a separate read-only ESP32 screen and USB bridge with stale/unknown handling. See `docs/esp32-display.md`.
- [x] Upload to the user-connected ESP32; verify three real serial updates and local NO DATA expiry with replies withheld.
- [ ] Visually inspect physical screen appearance. Firmware/serial evidence and visual observation must be distinguished. Budget at most 30 minutes; the laptop demo is independent.
- [x] Authoritative service-deficit accounting, bounded weights and durable `/rule` control; live weighted-grant/restart tests pass.
- [x] Read-only recorded-snapshot replay backend with gap detection, seek and play/pause.
- [ ] Replay UI integration — Claude/frontend ownership; no backend dependency remains.
- [x] Measured lab distributions and allocation/validation samples in a bounded subprocess; live stage timing and 5000-member coexistence test pass.
- [x] Expose bounded delivery faults, process health, durable historical operation lookup and hardened API input handling.
- [x] Scope decision: AI and SGLang removed at the user’s request. Use explicit protection rules and deterministic evidence explanations.

CP-SAT, real appliance adapters, medical-device classification, mains switching and cloud paths stay out. These do not become implied requirements because an optional box exists.

## Handoffs and unblockers

| Owner | Works independently from | Handoff |
|---|---|---|
| M1 / Codex core | schemas, registry, fake-clock tests | B5 grant producer; M3 reviews receiver assumptions |
| M2 / Codex plant/runtime | private profile + wire fixtures | B3 meter/ack stream; M3 pairs on binding |
| M3 / Codex transport/member | fixed protocol examples + local broker | B2 credentials/queue; B4 member loop |
| M4 / user after 9 | mock API + checked Snapshot fixtures | UI consumes B8 without moving safety into browser |
| M5 / Codex evidence/API | fixture events + independent oracle | B8 projection and B10 reproducible evidence |

If a backend gate fails, keep dependent boxes unchecked and fix the smallest failing trace. Do not disable validation or rewrite evidence. At 3 a.m., use `docs/runbook.md`. The first cuts are extra lab, replay polish and debt weighting; the reservation/expiry/protected-baseline checks are never scope cuts.

Current frontend owner: Claude, as directed by the user. Backend work does not edit `web/`. See `docs/backend-extensions.md` for the latest parallel-build interfaces and limitations.
