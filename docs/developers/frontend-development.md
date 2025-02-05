---
hide:
  - footer
---

## Frontend-ng development

When developing the `frontend-ng` you use the _Vue.js_ frontend server.
Changes will be picked up automatically as soon as a `.vue` file is saved without having
to rebuild the frontend or even refresh your browser.

### Install Node dependencies

To be done once or when you change the `package.json` file.

```bash
$ docker compose exec -it timesketch \
    yarn --cwd=/usr/local/src/timesketch/timesketch/frontend-ng install
```

This will create `node_modules/` directory from `package.json` in the frontend
directory.

### Start the Vue.js development server

You need two shells:

1/ Start the main webserver (for serving the API etc.) in the first shell:

```bash
$ docker compose exec -it timesketch \
    gunicorn \
    --reload \
    -b 0.0.0.0:5000 \
    --log-file - \
    --timeout 600 \
    -c /usr/local/src/timesketch/data/gunicorn_config.py \
    timesketch.wsgi:application
```

2/ Start the development webserver in the second shell:

```bash
$ docker compose exec -it timesketch \
    yarn run --cwd=/usr/local/src/timesketch/timesketch/frontend-ng serve
```

This will spawn a listener on port `5001`.
Point your browser to `http://localhost:5001/login`, login with your dev credentials,
and you should be redirected to the main Timesketch page.
All code changes in `.vue` files will be instantly picked up.

If you already have a yarn process running with the "old" frontend, it might not work.

### Frontend (old) development dependencies

If you develop a new feature, consider changing to `frontent-ng`, the old frontend is
likely to be deprecated in 2023.

The `frontend` development is almost identical than the `frontend-ng` one.
Commands are the same, but paths are different (`frontend` instead of `frontend-ng`).

### Install Node dependencies

As for the frontend-ng, you need to install the Node dependencies.

```bash
$ docker compose exec -it timesketch \
    yarn --cwd=/usr/local/src/timesketch/timesketch/frontend install
```

### Start the Vue.js development server

As for the frontend-ng, you need to start the _Vue.js_ development server (see the
command above).

Then, start the development webserver in the second shell:

```bash
$ docker compose exec -it timesketch \
    yarn run --cwd=/usr/local/src/timesketch/timesketch/frontend serve
```
