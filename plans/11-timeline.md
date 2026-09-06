# 11 — Forty-eight hours

| Window | Objective | Deliverable and test | Do not touch |
|---|---|---|---|
| **0–2 h** | Rules confirmed, clean repo, issue board. M1+M2 freeze the six schemas. M3 launches broker. M4 creates console shell. M5 creates scenario and chaos folders. | Two processes exchange a validated heartbeat and command. README states the safety and claim boundary on day one. | CP-SAT, hardware, styling, cloud |
| **2–6 h** | **The vertical slice.** M2 builds five devices; M3 the member agent with local floor fallback; M1 the twin plus water-filling; M4 works from fixtures; M5 the scenario launcher. | A CLI cap change moves at least two devices, both acknowledge, cap check passes. **Recorded.** | Matter, OpenADR, DB abstractions, React |
| **6–12 h** | **Leases.** M3 implements TTL, local expiry and coordinator-restart delay. M2 expands to 20–30 nodes with failure flags. M1 wires versioning and replan. M4 connects live state. | Killing the coordinator drives every member to floor with zero cap violations. This is the acceptance test that matters most. | Forecasting, auth, sensor calibration |
| **12–18 h** | Camber, debt weighting, evidence. M1 adds debt weights and the independent validator. M2 writes idempotence tests. M3 adds replay. M4 builds the load-path inspector. M5 gets chaos commands working. | Water-filling and the validator disagree on nothing across the fixture set. Load path renders from `basis`. Replay is byte-identical. | New device types, redesign, cloud |
| **18–24 h** | Integration and **Review 1** hardening. M5 runs three scripted scenarios. M1 documents the algorithm. M4 fixes the one-screen hierarchy. | Review 1 demo: live messages, complete loop, lease countdown visible, exact roadmap. **Tag a runnable checkpoint.** | Anything a reviewer calls "nice to have" unless it fixes the core |
| **24–30 h** | **Property tests and fault injection.** M1 writes Hypothesis tests over the invariants. M5 runs every chaos command. Hardware gets its final go/kill decision. | The system never reports false compliance under any injected fault. Every fault has visible state and a stored event. | Physical debugging past the kill point, multi-broker replication |
| **30–36 h** | CP-SAT **only if** everything above is green. Otherwise: UX and evidence. M4 freezes controls and layout. M3 exports the replay bundle. M1 profiles planning latency. | Review 2 build runs from a clean start script. Metrics and reason codes legible. **Three consecutive cold-start passes.** | Feature additions, library upgrades |
| **36–42 h** | **Feature freeze.** M5 records the backup video and screenshots. All five rehearse questions and subsystem explanations. | Versioned release, offline run instructions, evidence folder, demo under 2:50. | Unreviewed code generation, refactors, aesthetic experiments |
| **42–48 h** | Bug fixes with rollback only. Rest in rotation. | Final build hash, local backup, copy on an alternate laptop, contribution summary, live *and* recorded demo paths. | Schema changes, allocator redesign, rewiring |

## Kill points

Decisions with a time and an owner, made in advance so they are not made at 3 a.m.

| Hour | Question | If no |
|---|---|---|
| 6 | Does the vertical slice work end to end? | Cut to three members and two device types. Nothing else matters until this is true |
| 12 | Do leases expire correctly with the coordinator dead? | **Stop all feature work.** This is the project |
| 24 | Are the chaos commands real? | Cut CP-SAT and the ESP32 outright |
| 30 | Is CP-SAT beating water-filling on the fixture set? | Cut it. Say so in the pitch as a decision, not an omission |
| 36 | Three consecutive cold-start passes? | Freeze immediately, no exceptions |
