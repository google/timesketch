## Docker for development

You can run Timesketch on Docker in development mode.
Make sure to follow the docker [post-install](https://docs.docker.com/engine/install/linux-postinstall/) to run without superuser. If not then make sure to execute all `docker` commands here as *superuser*.

NOTE: It is not recommended to try to run on a system with less than 8 GB of RAM.

### Prepare a .env file

Compose requires a `.env` file with top level environment variables to be set.
To create it, just copy the `.env.template` file as a base.

```bash
cp .env.template .env
```

Note the `.env` is ignored by Git: you can safely write sensitive data in it.

You can optionally edit the `.env` file.
This is useful if you need to build images with some company restrictions (accessing
remote Ubuntu, PyPI or Node repositories).

### Start a developer version of docker containers in this directory

```bash
docker compose up -d
```

The provided container definition runs Timesketch in development mode as a volume from your cloned repo. Any changes you make will appear in Timesketch automatically.

If you see the following message you can continue

```text
Timesketch development server is ready!
```

### Start a celery container shell

Start the container in foreground (add `-d` to run in background):

```bash
docker compose exec timesketch \
  celery \
  -A timesketch.lib.tasks \
  worker \
  --loglevel info
```

### Start development webserver (and metrics server)

Start the container in foreground (add `-d` to run in background):

```bash
docker compose exec timesketch \
  gunicorn \
  --reload \
  -b 0.0.0.0:5000 \
  --log-file - \
  --timeout 600 \
  -c /usr/local/src/timesketch/data/gunicorn_config.py \
  timesketch.wsgi:application
```

You now can access your development version at http://127.0.0.1:5000/

Log in with user: dev password: dev

You can also access a metrics dashboard at http://127.0.0.1:3000/

### Non-interactive

A script applies the previous commands in background for you.

```bash
docker compose up -d
./start-frontend-ng-no-dev.sh
```

A second script starts an additional development server for the frontend
(http://127.0.0.1:5001/).
You need to wait a few seconds before accessing it.

```bash
docker compose up -d
./start-frontend-ng-dev.sh
```

### Run tests

```bash
docker compose exec \
    -w /usr/local/src/timesketch \
    -it \
    timesketch \
    python3 run_tests.py --coverage
```

That will run all tests in your docker container. It is recommended to run all tests at least before creating a pull request.

### Jupyter Notebook

To access a Jupyter notebook that has access to the Timesketch development
environment start a browser and visit http://localhost:8844/ . The password to
gain access is "timesketch".

By default, the /tmp directory is mapped as the data directory to store all
notebooks. To change that, modify the line:

```yaml
      - /tmp/:/usr/local/src/picadata/
```

in the _compose.yaml_ file to point to a directory of your choosing.
In order for the jupyter notebook to be able to make use of that folder it has
to have read and write permission for the user with the UID 1000.

By default, the latest checked in code of the timesketch API client and
timesketch import client are installed. In order to install a new version, if
you are modifying the clients you'll need to make sure that the timesketch
source code on your machine is readable by the user with the UID 1000 and
gid 1000.
If that is done, then the code is mapped into the `/usr/local/src/timesketch`
folder on the docker container.

New versions of timesketch api client can then be installed using:

```bash
!pip install -e /usr/local/src/timesketch/api_client/python/
```

And the importer client:

```bash
!pip install -e /usr/local/src/timesketch/importer_client/python
```

Just remember to restart the kernel runtime in order for the changes to be
active.

To update the docker image run:

```bash
$ sudo docker image pull us-docker.pkg.dev/osdfir-registry/timesketch/notebook:latest
```
