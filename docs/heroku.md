# Host the complete Truss demo on Heroku

The hosted app is one HTTP process: production website, live five-home simulation,
mock preview, Lab, and a private Mosquitto broker. No separate MQTT add-on or
frontend host is needed.

## Why Resources can show no web dyno

Heroku only lists dynos for process types it detected on the last successful
build. Two different deploy paths exist; mixing them leaves Resources empty and
the site blank.

| How the app was created | What Heroku reads | What it ignores |
|---|---|---|
| Dashboard / GitHub, default **heroku-24** stack | `Procfile` (`web:`) | `heroku.yml` and `Dockerfile` |
| CLI `--stack container` or **container** stack | `heroku.yml` | `Procfile` |

A dashboard app with only `heroku.yml` (and no `Procfile`) never registers a
`web` process, so there is no Basic dyno to turn on and the URL serves nothing.

After a deploy that includes the `Procfile`, **Resources** should show a `web`
process. Choose a **Basic** dyno and scale it to 1 if it is not already on.

## Default stack (heroku-24)

This is what "New app" plus GitHub usually creates. Buildpacks must be **apt**,
then **nodejs**, then **python**, so Mosquitto, the website build, and
`python -m truss.hosted` are all present.

```bash
heroku create YOUR-UNIQUE-APP-NAME
heroku buildpacks:clear
heroku buildpacks:add --index 1 heroku-community/apt
heroku buildpacks:add --index 2 heroku/nodejs
heroku buildpacks:add --index 3 heroku/python
git push heroku HEAD:main
heroku ps:scale web=1
heroku open
```

For an existing app:

```bash
heroku git:remote -a YOUR-APP-NAME
heroku stack:set heroku-24
heroku buildpacks:clear
heroku buildpacks:add --index 1 heroku-community/apt
heroku buildpacks:add --index 2 heroku/nodejs
heroku buildpacks:add --index 3 heroku/python
```

Then push again. In the Dashboard: Settings → Buildpacks, same three URLs in
that order. **Order is the build sequence, not just a checklist.** If the log
says `1. heroku/python` then `2. heroku/nodejs`, Python's `bin/post_compile`
runs before `npm` exists. Clear and re-add without `--index` so they append
in this sequence:

```bash
heroku buildpacks:clear -a YOUR-APP-NAME
heroku buildpacks:add heroku-community/apt -a YOUR-APP-NAME
heroku buildpacks:add heroku/nodejs -a YOUR-APP-NAME
heroku buildpacks:add heroku/python -a YOUR-APP-NAME
```

If logs show `Website build missing`, `web/dist` was not compiled (`web/dist`
is gitignored). `heroku/nodejs` must appear in the build log and run
`heroku-postbuild`.

## Container stack (Docker)

Cedar apps on the **container** stack build `Dockerfile` from `heroku.yml`.

```bash
heroku create YOUR-UNIQUE-APP-NAME --stack container
git push heroku HEAD:main
heroku ps:scale web=1
heroku open
```

For an existing Cedar app:

```bash
heroku git:remote -a YOUR-APP-NAME
heroku stack:set container
```

Then push again. Process types appear only after that container build succeeds.

## After it is up

Commit website changes before pushing. Heroku builds committed source, not your
local `web/dist`.

Open `/example`, `/console`, and `/lab` on the same app URL. Live health is at
`/console-api/v1/health`, and mock health at `/api/v1/health`. Both WebSocket
routes use the same host and work with HTTPS. Use `heroku logs --tail` for
startup errors.

Keep **one web dyno**. That process is the only Python server; do not add a
separate Heroku worker. All visitors share the same interactive demo, and
console actions affect that shared simulation. This showcases virtual homes; it
does not connect hosted MQTT to physical devices. State and recordings reset
when the dyno restarts because [Heroku's filesystem is ephemeral](https://devcenter.heroku.com/articles/dynos#ephemeral-filesystem).
Download recordings you want to keep before a restart.

The start command explicitly fixes Uvicorn at one worker. Do not set it to
multiple workers: the broker and virtual-home processes belong to that one
server process. Heroku may set `WEB_CONCURRENCY` automatically, but the explicit
`--workers 1` in `Procfile` takes precedence.

The Apt buildpack places Mosquitto at `/app/.apt/usr/sbin/mosquitto`; the
`Procfile` supplies that location, and the runtime also discovers it directly.

## Optional local verification

```bash
docker build -t truss-demo .
docker run --rm -p 8080:8080 -e PORT=8080 truss-demo
```

Open `http://localhost:8080`. The image binds the website to Heroku's `$PORT`;
MQTT stays on loopback inside the container.
