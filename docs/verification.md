# Verification record

7 September 2026 | Local working tree based on `3e52f7e`, including the current website changes. These results concern software and virtual appliances.

## Current checks

| Check | Result | What it establishes |
| --- | --- | --- |
| `.venv/bin/truss check-config` | Passed; five households | Supplied baselines and protected maxima fit their registrations. |
| `.venv/bin/pytest -q` | 68 passed, 0 skipped, 98.26 seconds | Core, property, API, hosted-route, broker ACL and real-process integration tests. |
| `npm --prefix web test` | 73 passed across 14 files, 3.21 seconds | Frontend contracts, model arithmetic, movement, source handling, controls, evidence and Info navigation. |

The Python run reported two dependency deprecation warnings involving Starlette's HTTPX test client and AnyIO's BlockingPortal alias. They did not fail the suite. Build and final visual checks are recorded below after completion.

## What the test groups cover

- **Allocation:** registered bounds, feasible/infeasible cases, deterministic ordering, exact continuous surplus fairness and whole-watt rounding.
- **Authority:** overlapping grants, duplicate/late replies, no early reclaim, epochs, binding and independent state-sequence checks.
- **Real processes:** coordinator stop/restart, repeated recovery, cap reductions, infeasible floors, member death, broker loss/reconnect, application partition and delayed grants.
- **Independent observations:** virtual plants remain alive when a member/coordinator stops; broker-outage tests use plant state files because MQTT observations are unavailable.
- **Privacy and contracts:** real broker credentials/ACL denial cases, strict wire parsing, source isolation, revision/idempotency conflicts and bounded inputs.
- **Extensions:** fairness checkpoints, recorded replay, isolated benchmark jobs, fault controls and native display parser/bridge behaviour.
- **Frontend:** unknown/null values, control retries and recovery, replay cleanup, evidence classification, three-home profile parity and camera-relative movement.

These groups overlap; do not add older test-run counts to create a larger total. The source tests describe their assertions more precisely than a headline count.

## How to reproduce

Use the install steps in [operations](operations.md), then run the three checks above and `npm --prefix web run build`. Read the skipped-test count. Missing Mosquitto can skip integration tests; passing only the remaining tests does not reproduce process evidence. Do not run disruptive integration tests during a timed live demonstration on the same host.

For a preserved demonstration, record software revision and local diff, configuration, dependencies, machine/clock domain, exact fault times, seeds, unknown/gap counts and hashes of selected event records. Do not publish generated credentials.

## Evidence has several scopes

The Example is a local arithmetic illustration. Mock is synthetic UI state. Console Live runtime observes real processes with virtual appliances. Replay contains historical snapshots whose ages and values belong to those frames. Lab measures synthetic allocation and validation, excluding broker, persistence, interprocess communication and enforcement. The optional screen displays virtual status; it measures no physical power.

Previous ESP32 compilation/upload/serial records and earlier expiry-lateness measurements remain in the local archive and runtime evidence. This pass did not repeat the hardware upload or establish optical screen correctness. Older results were tied to their original configurations and are not new measurements.

Finite tests increase confidence within their stated model. They do not certify electrical safety, establish universal scheduler bounds, prove hostile-device security or demonstrate energy savings. A recorded gap remains a gap. An inconclusive drill remains inconclusive until additional evidence resolves it.
