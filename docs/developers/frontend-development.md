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

## (beta) Frontend development (using the VueJS server)

If you want to do some heavy UX hacking, you might want to use the VueJS frontend server, as changes will be picked up
as soon as a `.vue` file is saved, without having to rebuild the whole frontend or even refresh your browser.

Follow the steps in the previous section to get dependencies installed.

### Tweak config files

* In your `timesketch` docker container, edit `/etc/timesketch/config.yaml` and set `WTF_CSRF_ENABLED = False`.
* In your cloned repo, edit the `timesketch/timesketch/frontend/vue.config.js` and set `publicPath` to `'/'`.

### Start the VueJS development server

In your running `timesketch` container, run:

```bash
$ sudo docker-compose exec timesketch yarn run --cwd=/usr/local/src/timesketch/timesketch/frontend serve
```

This will spawn a listener on port `8080`. Point your browser to `http://localhost:8080/login`, login with your
dev credentials, and you should be redirected to the main Timesketch page. All code changes in `.vue` files will
be instantly picked up.
