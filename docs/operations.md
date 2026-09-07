# Setup, hosting and maintenance

Run commands from the repository root. Linux is the verified host platform. Install dependencies before an offline presentation. This is a single-host virtual demonstration.

## Install once

Use Python 3.12+ and Node 22.12+ with npm. Mosquitto and `mosquitto_passwd` must be available; the runtime starts its own broker and does not require a system broker service.

```bash
python -m venv .venv
.venv/bin/python -m pip install -r requirements.lock
.venv/bin/python -m pip install -e . --no-deps
npm --prefix web ci
.venv/bin/truss check-config
```

Set `TRUSS_MOSQUITTO` to the broker executable if it is outside PATH. Runtime discovery also checks Apt's `.apt/usr/sbin` location. `scripts/setup_local_broker.py` is an optional pinned Arch dependency helper; other platforms should use their appropriate installation method.

## Run everything on one port

```bash
npm --prefix web run build
PYTHONPATH=src .venv/bin/uvicorn truss.hosted:create_hosted_app --factory --host 127.0.0.1 --port 8080 --workers 1
```

Open `http://127.0.0.1:8080`. This starts the website, live simulation, separate mock provider and Lab API. Keep the owning terminal open; Ctrl+C performs normal shutdown.

| URL | Service |
| --- | --- |
| `/`, `/info`, `/example`, `/console`, `/lab`, `/credits` | Website |
| `/console-api/v1/health` | Live health |
| `/console-api/v1/state?source=live` | Live snapshot |
| `/api/v1/health` | Mock health |
| `/api/v1/state?source=mock` | Mock snapshot |
| `/console-ws/v1/state?source=live` | Live WebSocket, subprotocol `truss.ui.v1` |
| `/ws/v1/state?source=mock` | Mock WebSocket, same subprotocol |

Override hosted paths/port with `TRUSS_CONFIG_DIR`, `TRUSS_WEB_DIST`, `TRUSS_RUNTIME_ROOT` and `TRUSS_BROKER_PORT`. Default runtime storage is `/tmp/truss-runtime`; the private loopback broker defaults to port 18883. Use exactly one Uvicorn worker because its lifecycle owns the broker and fleet.

## Develop with live page updates

Start three separate terminals:

```bash
.venv/bin/truss live --port 8001
```

```bash
.venv/bin/truss mock --port 8000
```

```bash
npm --prefix web run dev -- --port 5173 --strictPort
```

Open `http://127.0.0.1:5173`. Vite proxies `/console-api` and `/console-ws` to live; `/api` and `/ws` reach mock/Lab. Console defaults to live. For frontend-only work start mock and Vite and explicitly select Mock preview. There is no silent source fallback.

Standalone live runs use `runtime/`. Simultaneous runs need different broker ports and clear source identification. The Example slider changes a browser illustration, not the live console run.

## Heroku buildpack deployment

The root `Procfile`, `Aptfile`, `package.json`, `requirements.txt` and `.python-version` support this path. In app Settings, configure buildpacks in this order:

1. `heroku-community/apt` installs Mosquitto.
2. `heroku/nodejs` installs and builds the website.
3. `heroku/python` installs and runs the Python application.

Deploy committed source containing those files. `web/dist` is generated during the build and is intentionally ignored by Git. After a successful build, Resources should show the `web` process. Run one dyno.

The current Procfile uses `truss.hosted:create_hosted_app --factory`, binds `0.0.0.0:$PORT`, specifies `--workers 1`, and supplies `TRUSS_MOSQUITTO=/app/.apt/usr/sbin/mosquitto`.

Those choices address two earlier startup failures. Heroku can inject `WEB_CONCURRENCY=2`; an already-created application with multiple workers caused Uvicorn's import-string warning and exit status 3. The Procfile now explicitly selects the factory and one worker. Apt also places Mosquitto under `usr/sbin`, which the old discovery missed; the explicit path and expanded discovery address that.

H10 means the web process crashed. Read the earlier startup traceback; the router's 503 alone does not identify the cause.

```bash
heroku logs --tail -a YOUR-APP-NAME
heroku ps -a YOUR-APP-NAME
```

This documentation pass did not redeploy or verify the remote app. Check both deployed health endpoints after the next deployment.

## Container alternative

`Dockerfile` and `heroku.yml` provide the container path. A buildpack app reads `Procfile`; a container-stack deployment reads `heroku.yml`. Docker files do not automatically change an existing app's stack.

```bash
docker build -t truss-demo .
docker run --rm -p 8080:8080 truss-demo
```

The image's local default serves port 8080. The Heroku run command uses the assigned `$PORT`. Keep one web process and one dyno; extra workers would create independent runtimes rather than scale one shared authority system.

All visitors share the same virtual run and its controls. Runtime files disappear on dyno replacement or restart. Export wanted evidence beforehand; external recording storage and operator access controls are future work. [Heroku ephemeral filesystem](https://devcenter.heroku.com/articles/dynos#ephemeral-filesystem).

## Recovery and troubleshooting

| Symptom | Check and response |
| --- | --- |
| Website build missing | Build the frontend; on Heroku confirm Node ran before Python. |
| Mosquitto unavailable | Check broker/password-tool installation and executable path. |
| Console unavailable or wrong source | Check the matching health endpoint and selected source. |
| Low allocation after restart | Wait through 6.4-second recovery and ordinary request cadence; inspect status. |
| Draw differs from allowance | Inspect local decisions and `unusable_w`; a binary step may not fit. |
| Unknown readings | Check sample age, clock domain and plant health. Missing data is not zero. |
| Accepted lower cap but still over cap | Earlier permission can remain usable; inspect exposure and transition. |
| Minimums do not fit | Restore a feasible cap for further demonstrations; do not silently reduce protected floors. |
| Control conflict | Refresh actual state and review the intent before submitting a new action. |
| Operation queued after API failure | Reconcile owned process state; retrying its key will not blindly repeat it. |
| Lab busy or timed out | Wait or reduce members/samples; missing results are not zero latency. |

Never erase authority storage during coordinator recovery. Stop runs through their owning service. An abruptly killed supervisor can leave children; identify them against the run manifest before cleanup. Avoid killing unrelated processes.

## Optional ESP32 display

Firmware targets ESP32-S3 with 16 MB flash, 8 MB PSRAM and a 240x240 GC9A01 SPI display. Configured GPIOs are clock 12, MOSI 11, DC 13, CS 10 and reset 14. Verify actual hardware/wiring before use; these are configuration facts. The display has no appliance-control authority.

```bash
.venv/bin/python -m pip install -e '.[display]'
pio run --project-dir firmware/status-display
.venv/bin/pytest -q tests/test_display_bridge.py
```

Uploading deliberately replaces firmware; explicitly select the actual device using PlatformIO's `--upload-port`. For an already-flashed board and standalone live server:

```bash
.venv/bin/truss-display --port /dev/serial/by-id/YOUR-DEVICE --url http://127.0.0.1:8001 --source live
```

The board polls at 115200 baud. Replies echo a nonce and include source, state, cap, observed watts, baseline and coordinator status. Values expire 2.5 seconds from the board's request. Duplicates and late replies cannot extend freshness. `NO DATA` concerns the display, not authority. The bridge uses read-only HTTP calls.

Earlier local records describe compilation, upload, accepted replies and expiry, but not optical inspection. This pass did not flash or visually inspect hardware. Native parser and bridge tests remain in the software suite.

## Document and design recovery

Start from the [documentation index](README.md). Final guides replace obsolete briefs, schedules, fictional ownership tables and contradictory handoffs. Media licences and the homepage/first-Credits rollback files under `web/archive/` are preserved.

Before replacement, 48 original documentation/tooling files were stored at `/home/medrid/truss-document-backups/2026-09-07-before-final-docs/original-documents.tar.gz`. Every archived file was checked against the adjacent SHA-256 manifest. This local archive includes the former private explanatory note. Extract into a separate folder and review selected files before copying them back; do not overwrite the active project indiscriminately.

The optional `scripts/build_inventory.py` now generates a local source inventory under `runtime/`, without reading deleted plans or overwriting final documents.
