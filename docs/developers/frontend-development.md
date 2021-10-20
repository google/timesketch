## Frontend development

First we need to get an interactive shell to the container to install the frontend modules:

```bash
$ docker-compose exec timesketch yarn install --cwd=/usr/local/src/timesketch/timesketch/frontend
$ docker-compose exec timesketch yarn run --cwd=/usr/local/src/timesketch/timesketch/frontend build --mode development --watch
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
