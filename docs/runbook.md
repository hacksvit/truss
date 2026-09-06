# Running it at 3 a.m.

This runbook covers the live virtual-device backend and the independent mock. Current evidence and limits are in [implementation-status](implementation-status.md).

## Live backend cold start

Mosquitto 2.1.2 is available on this PC in the local user cache; no system service was installed. The pinned Arch public-package setup is reproducible with `python scripts/setup_local_broker.py`. It checks archive hashes and keeps dependency code outside the project. Other systems should install Mosquitto normally or set `TRUSS_MOSQUITTO` to their executable. Packages came from the [official Arch package mirror](https://fastly.mirror.pkgbuild.com/extra/os/x86_64/); this identifies the dependency source, not a performance claim.

```bash
.venv/bin/truss check-config
.venv/bin/truss live --port 8001
```

This owns a loopback broker on 18883, five members, five independent plants, coordinator, observer and API. Private profiles are snapshotted at run start; editing source config affects only a new run. Generated credentials/configuration/manifests/logs stay under `runtime/{run_id}/`. The API is on 8001; use `/api/v1/health` and `/api/v1/state?source=live`. Wait through startup/recovery before expecting extra watts. Stop the owning terminal normally to tear down this run only.

Use `--broker-port` when another owned run uses 18883. Do not start a second run accidentally and confuse their evidence. Abruptly killing the supervisor/API can leave its children alive; identify those processes against the recorded manifest and process identity before manual cleanup. There is no automatic orphan takeover.

## Mock and frontend cold start

From the repository root, use the README install commands once while dependency downloads are allowed. Python lock records this Linux/Python 3.14 environment; rebuild/test a new lock if the team's Python platform differs. It excludes the editable project itself, which is installed separately. Node package-lock fixes the frontend resolution. Downloading dependencies is a setup step, not an allowed hidden judged-path network dependency.

Then run:

```bash
.venv/bin/truss check-config
npm --prefix web run build
.venv/bin/truss mock
```

Open `http://127.0.0.1:8000/console`. `/` is the overview; `/lab` runs measured synthetic allocator batches. For frontend editing, leave the backend running and use `npm --prefix web run dev`; open the Vite URL it prints. Every route shows MOCK. `truss api` deliberately exposes an unwired/live-unavailable API, not an automatic mock fallback.

## If something fails

| Symptom | Do this | Do not do this |
|---|---|---|
| Port 8000 already used | Identify the owning terminal/process. Stop only the Truss instance you started, or run `truss mock --port 8001` and point the dev proxy at that port | Kill every Python process or an unrelated service |
| Empty page or old UI | Rebuild `web`, restart the backend if `dist` was absent when it started, reload browser | Debug the allocator before checking static assets |
| Console waiting / 403 | Use mock mode and `source=mock`; check health mode | Relabel mock data as live |
| 409 on a control | Refresh latest snapshot, review the new state, retry a new action with a new key | Blindly resend the old intent with an updated revision |
| Unknown observed watts | Inspect age/quality and publisher boot. Mock stale-C button intentionally produces this | Treat missing readings as zero |
| Cap below 1000 W in supplied profile | Expect infeasible: 900 W household floors + 100 W reserve. Restore cap for next illustration | Cut the protected baseline to make the indicator green |
| Frozen countdown after closing a process | In live integration, check the **independent plant** and freshness. In current mock, restart only its server | Claim local physical expiry from an animation |
| Test fails before a demo | Preserve the failure output/seed; cut the dependent feature and use the labelled mock fallback | Remove assertions, edit measurements or unskip empty integration tests |
| JSONL tail truncated | Preserve original file; record a gap and begin a new segment | Repair history in place and claim exact replay |
| Lab timeout | Use 5/50 members; keep raw partial count and scope. Do not benchmark alongside live timing claims until isolated | Plot missing samples as zeros or assert flat scaling |
| Asked for an AI feature | Explain the explicit non-AI scope and show recorded arithmetic | Add a model or classification path during final integration |

## Broker details

Live startup generates fresh per-role passwords, ACL/config, run identity and a durable authority database. Password files and plaintext local credentials are confined to a mode-0700 run directory and ignored by Git. Broker ACLs restrict coordinator to aggregates, household peers to their own paths, and the evidence account to observation. The API control publisher cannot issue leases. MQTT clients reconnect and subscribe again; each connection gets a new Will/heartbeat connection ID. Will/offline status never releases authority early.

The checked-in `config/mosquitto.conf` is a manual template, not the auto-started live broker configuration. If running it directly, generate `config/passwords` separately. Do not commit either password file. The live supervisor is the primary supported startup path.

## Recovery rules for the live build

Never delete the authority database to escape a recovery delay. Never change run/registry identity underneath active members. Never restart all plants just because the coordinator is down; they must outlive it. Every coordinator boot claims a durable epoch and starts a full 6400 ms conservative wait. A second crash starts the wait again. Expiry/hold equations and assumptions are in plan 18. If the clock domain changes or enforcement lateness exceeds 250 ms, mark the run unverified and withdraw its timing claim.

At hour 30, cut optional work if core evidence is incomplete. At hour 36, freeze dependencies and feature changes. Last hours belong to independent runs, recording and rehearsal. BUILD_PLAN.md is the active order. AI/SGLang were removed; optional work means debt, replay or additional lab measurement only.
