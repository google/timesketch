## Docker for Development

You can run Timesketch on Docker in development mode.
Make sure to follow the docker [post-install](https://docs.docker.com/engine/install/linux-postinstall/)
to run without superuser. If not, make sure to execute all `docker` commands here
as *superuser*.

**Note:** It is not recommended to try to run on a system with less than 8 GB of RAM.

### 1. Start the Developer Containers

```bash
cd timesketch/docker/dev/

docker compose up -d
```

The provided container definition runs Timesketch in development mode as a
volume from your cloned repo. Any changes you make will appear in Timesketch
automatically.

Wait until you see the "Timesketch development server is ready!" message in the logs:

```bash
docker compose logs -f timesketch
```

### 2. Start the Application Services

Since the container starts in a "sleeping" state to allow for debugging, you
need to manually start the worker and the webserver.

**Option A: Interactive (Recommended for debugging)**
Open two new terminal tabs/windows and run:

*Terminal 1 (Celery Worker):*

```bash
docker compose exec timesketch celery -A timesketch.lib.tasks worker --loglevel info
```

OR

```bash
bash utils/tsdev.sh celery
```

*Terminal 2 (Webserver):*

```bash
docker compose exec timesketch gunicorn --reload -b 0.0.0.0:5000 --log-file - --timeout 600 -c /usr/local/src/timesketch/timesketch/gunicorn_config.py timesketch.wsgi:application
```

OR

```bash
bash utils/tsdev.sh web
```

**Option B: Non-interactive (Background)**
Run these commands to start everything in the background:

```bash
docker compose exec -d timesketch celery -A timesketch.lib.tasks worker --loglevel info
docker compose exec -d timesketch gunicorn --reload -b 0.0.0.0:5000 --log-file - --timeout 120 timesketch.wsgi:application
```

**Option C: Tilt**

For instructions on how to run the dev environment using Tilt check this guide:
* https://github.com/google/timesketch/blob/master/docs/developers/tilt-development.md

### 3. Access the Application

* **Timesketch UI:** http://127.0.0.1:5000/
* **User:** `dev`
* **Password:** `dev`
* Note: Your login session will persist across container restarts.
  * The "secret key" is randomly generated and stored in a `.dev_secret_key` file.


* **Metrics (Prometheus):** http://127.0.0.1:9090/

### Run Tests

To run all tests inside the container:

```bash
docker compose exec -w /usr/local/src/timesketch timesketch python3 run_tests.py --coverage
```

It is recommended to run all tests at least before creating a pull request.

### Pull new images

To update the docker image run:

```bash
docker compose pull
```
