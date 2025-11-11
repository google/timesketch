# Docker Compose for development

## Prepare a .env file

Compose requires a `.env` file with top level environment variables to be set.
To create it, just copy the `.env.template` file as a base.

```bash
cp contrib/docker/dev/.env.template contrib/docker/dev/.env
```

Note the `.env` is ignored by Git: You can safely write sensitive data in it.

You can optionally edit the `.env` file.
This is useful if you need to build images with some company restrictions
(accessing remote Ubuntu, PyPI or Node repositories).

The default Timesketch user is `dev` and its password is `dev`.

## Build or rebuild images

To build images:

```bash
docker compose -f contrib/docker/dev/compose.yaml build
```

## Start services

To start all services:

```bash
docker compose -f contrib/docker/dev/compose.yaml up -d
```

On the first run, the _setup_ service will:

- Create the Timesketch user (defaults `dev` with password `dev`),
- Clone (fetch on subsequent runs) the
  [SigmaHQ/sigma](https://github.com/SigmaHQ/sigma) repository,
- Import the sigma rules set in [sigma_rules.txt](timesketch/sigma_rules.txt)

Go to your browser:

- <http://127.0.0.1:5000/>: Frozen frontend (_dist_ compiled files), backend
  with latest sources and live reload,
- <http://127.0.0.1:5001/>: Frontend and backend with latest sources and live
  reload (slower to be available).
- <http://localhost:8844/>: Jupyter notebook with (password: `timesketch`).

## Stop services

To stop services and remove related containers:

```bash
docker compose -f contrib/docker/dev/compose.yaml down
```

To delete service data at once:

```bash
docker compose -f contrib/docker/dev/compose.yaml down -v
```
