# Evidence record

Evidence classes follow [research/sources.md](../research/sources.md). These are local software and virtual-device results, not electrical certification or medical-device performance.

## Verified local results — 6 September 2026

- `truss check-config`: all five fictional profiles fit their registered baseline/maxima. Total floor 900 W; reserve 100 W; configured cap 5000 W.
- A real Mosquitto run reported 4900 W total from five independent plant processes, alongside five member processes and the coordinator. All child processes remained running and all plant enforcement reports were healthy.
- Killing the actual coordinator left the API and plants alive. Fresh plant reports returned to 900 W total within the six-second lease lifetime plus observation cadence. Protected fictional loads retained their configured maxima.
- Repeated restart, cap-drop transition, infeasible floors, member kill/restart, broker loss/reconnect, partition healing and grants delayed seven seconds were exercised by real-process tests. Broker-outage fallback was checked using fresh independent plant state files, because MQTT observation is unavailable while its broker is dead.
- Real authenticated broker tests deny wrong credentials, deny private device telemetry to coordinator while allowing aggregate offers, and deny a member's attempt to publish a lease. Static ACL inspection is a separate test, not the enforcement evidence.
- Final full backend run: **38 passed, 0 skipped**, in **82.52 seconds**. Two dependency deprecation warnings did not affect the result. Earlier scaffold skips are no longer the state of this checkout.
- Frontend contract recheck after AI removal: **8 tests passed**, TypeScript/Vite build passed. A chart-containing bundle size warning remains; it is not a failed build.

## What the tests establish

Hypothesis checks allocation envelopes, exact continuous normalized-surplus ratios, deterministic ordering and conservative timed authority sequences. Unit regressions cover delayed/duplicate grants, no early reclaim, fixed floors, protected command rejection/expiry, idempotent virtual effects, durable epochs/singletons and unknown/null metrics. Live tests add actual process boundaries, MQTT delivery and independent plant observations. Trace tests require a matching emitted Plan for each recorded grant's plan_id and snapshot hash.

Known broker disconnects are now explicitly recorded as observation gaps; do not call a deliberately disconnected run gap-free merely because the local event sequence is contiguous. Source timestamps and clock domains govern freshness. Old readings cannot verify zero draw. Event history and secrets are separate from durable control authority.

A finite test campaign is not a formal proof of arbitrary failures. Independent clock rates at their stated worst-case bounds fit the 6400 ms hold algebraically; no hardware drift benchmark or universal OS scheduling bound was measured. The plant detects a loop gap over 250 ms and withdraws normal enforcement status. Whole-PC suspend, a dead/frozen enforcer, lying registered maxima and Byzantine actors remain outside the stated model. No savings, mains-switching or clinical continuity result is asserted.

## Coverage map using original invariant names

| Invariant | Current evidence |
|---|---|
| I1 Cap after response window | Plant meter process tests under feasible cap; cap-drop transition measured separately from steady compliance |
| I2 Floor | Registered floor equality, missing-member rejection, allocator properties, protected expiry and infeasible-baseline tests |
| I3 Possible authority | Conservative ledger state machine, overlap/duplicate/recovery tests; fixed-baseline and drift assumptions explicit |
| I4 Honesty | Null/stale source tests, impossible cap remains infeasible/over-cap, real broker outage leaves observed total unknown |
| I5 Idempotence | Lease/command duplicate tests, durable cap/chaos operation retries and conflict handling |
| I6 Monotonicity | Request/ref/version checks, delayed expired grants, member/coordinator reboot cases |
| Additional obligations from plans 17/18 | Separate enforcer process, exact identities/refs, role ACLs, source isolation, conservative uncertainty and replay gaps |

The original six invariants alone were insufficient. The repaired trust/clock/baseline/identity/evidence obligations remain part of every claim.

## Reproducing and preserving evidence

Run `.venv/bin/pytest -q` with Mosquitto available. Without a broker dependency, real-process fixtures explicitly skip; that environment has not reproduced the result. Dependencies are locked in requirements.lock/package-lock and the local broker helper checks package hashes. Current stack: Linux, Python 3.14.7, Mosquitto 2.1.2; these are observed versions, not portability claims.

Live runtime writes `runtime/{run_id}/events.jsonl`, `plant-*-state.json`, process logs/manifest and the authority database. Test fixture runs use pytest temporary directories. For a release recording, preserve the selected complete run, software/diff hash, config/policy hashes, exact locks, host/clock domain, fault times, seeds, sample/unknown/gap counts and raw event-log hash. Do not publish credentials. Replay is read-only event/latest-topic reconstruction; full time-dependent UI replay is not implemented.

Browser visual inspection was blocked by the in-app browser's local-URL policy. Build/tests and HTTP/WS checks are verified; visual browser QA is not claimed. The user owns frontend work after 9. AI/SGLang are removed from the implementation scope; no model result enters evidence.

## Saved local verification artifacts

The final test event log and independent plant-state records were copied to ignored `runtime/verification-2026-09-06/`; its summary records counts and hashes. Maximum reported virtual expiry lateness in that run was **19.7149 ms**. That finite observed maximum does not establish a universal scheduler bound. Event-log SHA-256: `84e307b4516f7d6f3c14677203578a2eddc4a3b0296029fc045a9e9b050aa96e`.

Live and mock HTTP routes/assets and real WebSocket hello/ping/pong/snapshot were checked against the running servers. Python formatting preserved identical ASTs; unused-import/undefined-name checks passed.
