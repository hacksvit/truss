# Frontend handoff — Claude owns web/

Backend work comes first, as requested. The existing frontend is a stable starting point, not a design you must keep. Its last frontend-only check passed **8 tests** and the TypeScript/Vite production build. Codex stopped frontend editing after that handoff instruction.

## Commands and sources

```bash
# Real local virtual-device backend, independent MQTT processes:
.venv/bin/truss live --port 8001

# Independent fictional mock for UI development (optional second terminal):
.venv/bin/truss mock --port 8000

# Your frontend dev server:
npm --prefix web run dev
```

`/api/v1/health` tells you which backend you reached. Live state is `http://127.0.0.1:8001/api/v1/state?source=live`; mock state is `http://127.0.0.1:8000/api/v1/state?source=mock`. Both return the same complete Snapshot model. Cross-source calls are rejected. Read [protocol](protocol.md), [OpenAPI](../fixtures/openapi.json) and [example snapshots](../fixtures/snapshots.json).

At the prior handoff, frontend wiring was mock (Claude may now have changed it): `web/vite.config.ts` proxies to 8000, and `web/src/state.tsx` connects to `mock`. To integrate live, make source an explicit selection, point the proxy at the corresponding server and pass that source consistently to REST/WS. Do not change only the label. BoundaryBanner, Showcase wording and JudgeControls still describe mock and need source-aware wording. `api.ts` already submits the received snapshot's run/source/revision.

## Implement in this order

1. Overview layout and console's capacity/household cards. Keep proposed, issued, reserved and observed values distinct.
2. Unknown/stale/infeasible/recovering states. Null never becomes zero. A countdown reaching zero does not certify that a device stopped.
3. Drawer with protected fictional device policy. `basis` and `decision` may be null; match refs before showing a causal explanation.
4. Cap controls with current revision and UUID idempotency key. 202 means desired cap committed, not immediate physical compliance. Keep transition visible.
5. Real chaos actions: `kill_coordinator`, `restart_coordinator`, `kill_member`, `restart_member`, `kill_broker`, `restart_broker`. Member actions require member_id; other actions use null. Mock-only `stale_member`/`clear_faults` must not be shown on live. Protected policy remains fixed for the run.
6. REST fallback/WS reconnection with `truss.ui.v1`, then responsive/keyboard checks. Assets must be local.
7. Lab polish only after console works. The new backend exposes isolated lab jobs on live/mock, plus live recorded-snapshot replay and rule/fault controls. See `docs/backend-extensions.md` and regenerated OpenAPI; no frontend files were changed to integrate these controls. There is no AI feature or model endpoint.

## Facts you can rely on

The backend returns a coherent Snapshot with `source`, `run_id`, `stream_id`, monotonically increasing view revision, control revision, explicit capabilities and error envelopes. Cap/chaos keys are durable for the live run. Protected/unclassified maxima are reserved in configuration and ordinary code; neither UI nor AI can downgrade them. Real process fault results come from independently running virtual plants.

Do not infer a live feature from a filled button or a green fixture. Check `BUILD_PLAN.md` and `docs/evidence.md`. If a new view field is needed, agree its meaning in the backend model, regenerate fixtures, and update both producer and consumer. UI can keep working against mock while that field is implemented.

## New backend handoff

Read [backend extensions](backend-extensions.md) for exact rule/fairness, faults, runtime, replay and benchmark contracts. Existing Snapshot fields remain compatible; Operation.kind adds `fault`, and LabRequest/BenchmarkResult gain optional fields. Source-aware replay is served on separate REST routes, leaving the primary live/mock WebSocket alone. `/runtime` reports owned process status without exposing credentials. No AI endpoint exists.
