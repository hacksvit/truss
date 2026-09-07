# Host the complete Truss demo on Heroku

The root `heroku.yml` builds the Dockerfile and starts one web dyno. It includes
the production website, live five-home simulation, mock preview, Lab, and a private
Mosquitto broker. No separate MQTT add-on or frontend host is needed.

Use a **Cedar-generation app with the `container` stack**. This is the platform
supported by [Heroku's heroku.yml deployment workflow](https://devcenter.heroku.com/articles/build-docker-images-heroku-yml).

From the repository root, after installing and logging into the Heroku CLI:

```bash
heroku create YOUR-UNIQUE-APP-NAME --stack container
git add heroku.yml Dockerfile .dockerignore src/truss/hosted.py src/truss/observer.py src/truss/runtime_common.py tests/test_hosted.py docs/heroku.md README.md
git commit -m "Add complete Heroku demo hosting"
git push heroku HEAD:main
heroku ps:scale web=1
heroku open
```

For an existing Cedar app, replace the `heroku create` line with:

```bash
heroku git:remote -a YOUR-APP-NAME
heroku stack:set container
```

Commit any website changes you want to publish before pushing. Heroku builds the
committed source, including the website assets, rather than your local `web/dist`.
Select a web dyno plan in Heroku if required by your account; this configuration
does not provision paid add-ons or choose a plan for you.

Open `/example`, `/console`, and `/lab` on the same app URL. Live health is at
`/console-api/v1/health`, and mock health at `/api/v1/health`. Both WebSocket routes
use the same host and work with HTTPS. Use `heroku logs --tail` for startup errors.

Keep **one web dyno and one Python worker**: all visitors share the same interactive
demo, and console actions affect that shared simulation. This showcases virtual
homes; it does not connect hosted MQTT to physical devices. State and recordings
reset when the dyno restarts because [Heroku's filesystem is ephemeral](https://devcenter.heroku.com/articles/dynos#ephemeral-filesystem).
Download recordings you want to keep before a restart.

## Optional local verification

```bash
docker build -t truss-demo .
docker run --rm -p 8080:8080 -e PORT=8080 truss-demo
```

Open `http://localhost:8080`. The image runs as a non-root user and binds the website
to Heroku's `$PORT`; MQTT stays on loopback inside the container.
