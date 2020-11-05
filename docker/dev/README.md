## Docker for development

You can run Timesketch on Docker in development mode.
Make sure to follow the docker [post-install](https://docs.docker.com/engine/install/linux-postinstall/) to run without superuser. If not then make sure to execute all `docker` commands here as *superuser*.

NOTE: It is not recommended to try to run on a system with less than 8 GB of RAM.

### Start a developer version of docker containers in this directory

```
docker-compose up -d
```

The provided container definition runs Timesketch in development mode as a volume from your cloned repo. Any changes you make will appear in Timesketch automatically.

If you see the following message you can continue

```
Timesketch development server is ready!
```
### Find out container ID for the timesketch container

```
CONTAINER_ID="$(docker container list -f name=dev_timesketch -q)"
```
In the output look for CONTAINER ID for the timesketch container

To write the ID to a variable, use:
```
export CONTAINER_ID="$(docker container list -f name=dev_timesketch -q)"
```
and test with
```
echo $CONTAINER_ID
```

### Start a celery container shell
```
docker exec -it $CONTAINER_ID celery -A timesketch.lib.tasks worker --loglevel info
```

### Start development webserver

```
docker exec -it $CONTAINER_ID gunicorn --reload -b 0.0.0.0:5000 --log-file - --timeout 120 timesketch.wsgi:application
```

You now can access your development version at http://127.0.0.1:5000/
Log in with user: dev password: dev

### Non-interactive

Running the following as a script after `docker-compose up -d` will bring up the development environment in the background for you.
```
export CONTAINER_ID="$(docker container list -f name=dev_timesketch -q)"
docker exec $CONTAINER_ID celery -A timesketch.lib.tasks worker --loglevel info
docker exec $CONTAINER_ID gunicorn --reload -b 0.0.0.0:5000 --log-file - --timeout 120 timesketch.wsgi:application
```

### Run tests

```
docker exec -w /usr/local/src/timesketch -it $CONTAINER_ID python3 run_tests.py --coverage
```

That will run all tests in your docker container. It is recommended to run all tests at least before creating a pull request.
