---
hide:
  - footer
---
### Frontend (old) development dependencies

When developing the frontend you use the VueJS frontend server. Changes will be picked up automatically
as soon as a `.vue` file is saved without having to rebuild the frontend or even refresh your browser.

If you develop a new feature, consider changing to `frontent-ng`, the old frontend is likely to be deprecated in 2023.

First we need to get an interactive shell to the container to install the frontend modules:

```bash
docker compose exec timesketch yarn install --cwd=/usr/local/src/timesketch/timesketch/frontend
docker compose exec timesketch yarn run --cwd=/usr/local/src/timesketch/timesketch/frontend build --mode development --watch
```

Then inside the container shell go to the Timesketch frontend directory.

```bash
! cd /usr/local/src/timesketch/timesketch/frontend
```

Note that this directory in the container is mounted as volume from your local repo and mirrors changes to your local repo.

Install node dependencies

```bash
! npm install
```

This will create `node_modules/` folder from `package.json` in the frontend directory.

```bash
! yarn install
```

### Tweak config file

* In your `timesketch` docker container, edit `/etc/timesketch/timesketch.conf` and set `WTF_CSRF_ENABLED = False`.

### Start the VueJS development server

Follow the steps in the previous section to get dependencies installed and the config file tweaked.

You need two shells:

1. Start the main webserver (for serving the API etc) in the first shell:

```bash
CONTAINER_ID="$(docker container list -f name=timesketch-dev -q)"
docker exec -it $CONTAINER_ID gunicorn --reload -b 0.0.0.0:5000 --log-file - --timeout 600 -c /usr/local/src/timesketch/data/gunicorn_config.py timesketch.wsgi:application
```

2. Start the development webserver in the second shell:

```bash
CONTAINER_ID="$(docker container list -f name=timesketch-dev -q)"
docker compose exec timesketch yarn run --cwd=/usr/local/src/timesketch/timesketch/frontend serve
```

This will spawn a listener on port `5001`. Point your browser to `http://localhost:5001/login`, login with your
dev credentials, and you should be redirected to the main Timesketch page. All code changes in `.vue` files will
be instantly picked up.

## Frontend-ng development

When developing the `frontend-ng` you use the VueJS frontend server. Changes will be picked up automatically
as soon as a `.vue` file is saved without having to rebuild the frontend or even refresh your browser.

### Install dependencies

Inside the container shell go to the Timesketch frontend-ng directory.

```bash
cd /usr/local/src/timesketch/timesketch/frontend-ng
```

Note that this directory in the container is mounted as volume from your local repo and mirrors changes to your local repo.

Install node dependencies

```bash
npm install
```

This will create `node_modules/` folder from `package.json` in the frontend directory.

```bash
yarn install
```

### Tweak config file

* In your `timesketch` docker container, edit `/etc/timesketch/timesketch.conf` and set `WTF_CSRF_ENABLED = False`.

### Start the VueJS development server

You need two shells:

1. Start the main webserver (for serving the API etc) in the first shell:

```bash
CONTAINER_ID="$(docker container list -f name=timesketch-dev -q)"
docker exec -it $CONTAINER_ID gunicorn --reload -b 0.0.0.0:5000 --log-file - --timeout 600 -c /usr/local/src/timesketch/data/gunicorn_config.py timesketch.wsgi:application
```

2. Start the development webserver in the second shell:

```bash
CONTAINER_ID="$(docker container list -f name=timesketch-dev -q)"
docker compose exec timesketch yarn run --cwd=/usr/local/src/timesketch/timesketch/frontend-ng serve
```

This will spawn a listener on port `5001`. Point your browser to `http://localhost:5001/login`, login with your
dev credentials, and you should be redirected to the main Timesketch page. All code changes in `.vue` files will
be instantly picked up.

If you already have a yarn process running with the "old" frontend, it might not work.

### Build UI for production

Generate UI builds:

```bash
CONTAINER_ID="$(docker container list -f name=timesketch-dev -q)"
docker exec -it $CONTAINER_ID timesketch bash
cd /usr/local/src/timesketch/timesketch/frontend-ng
npm run build
```
