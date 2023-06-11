## Docker for development

You can run Timesketch on Docker in development mode.
Make sure to follow the docker [post-install](https://docs.docker.com/engine/install/linux-postinstall/) to run without superuser. If not then make sure to execute all `docker` commands here as *superuser*.

NOTE: It is not recommended to try to run on a system with less than 8 GB of RAM.

### Start a developer version of docker containers in this directory

```
docker compose up -d
```

The provided container definition runs Timesketch in development mode as a volume from your cloned repo. Any changes you make will appear in Timesketch automatically.

If you see the following message you can continue

```
Timesketch development server is ready!
```
### Find out container ID for the timesketch container

```
CONTAINER_ID="$(docker container list -f name=timesketch-dev -q)"
```
In the output look for CONTAINER ID for the timesketch container

To write the ID to a variable, use:
```
export CONTAINER_ID="$(docker container list -f name=timesketch-dev -q)"
```
and test with
```
echo $CONTAINER_ID
```

### Start a celery container shell
```
docker exec -it $CONTAINER_ID celery -A timesketch.lib.tasks worker --loglevel info
```

### Start development webserver (and metrics server)

```
docker exec -it $CONTAINER_ID gunicorn --reload -b 0.0.0.0:5000 --log-file - --timeout 600 -c /usr/local/src/timesketch/data/gunicorn_config.py timesketch.wsgi:application
```

You now can access your development version at http://127.0.0.1:5000/

Log in with user: dev password: dev

You can also access a metrics dashboard at http://127.0.0.1:3000/

### Non-interactive

Running the following as a script after `docker compose up -d` will bring up the development environment in the background for you.
```
export CONTAINER_ID="$(docker container list -f name=timesketch-dev -q)"
docker exec $CONTAINER_ID celery -A timesketch.lib.tasks worker --loglevel info
docker exec $CONTAINER_ID gunicorn --reload -b 0.0.0.0:5000 --log-file - --timeout 120 timesketch.wsgi:application
```

### Run tests

```
docker exec -w /usr/local/src/timesketch -it $CONTAINER_ID python3 run_tests.py --coverage
```

That will run all tests in your docker container. It is recommended to run all tests at least before creating a pull request.

### Jupyter Notebook

To access a Jupyter notebook that has access to the Timesketch development
environment start a browser and visit http://localhost:8844/ . The password to
gain access is "timesketch".

By default the /tmp directory is mapped as the data directory to store all
notebooks. To change that, modify the line:

```
      - /tmp/:/usr/local/src/picadata/
```

in the docker-compose.yml file to point to a directory of your choosing.
In order for the jupyter notebook to be able to make use of that folder it has
to have read and write permission for the user with the UID 1000.

By default the latest checked in code of the timesketch API client and
timesketch import client are installed. In order to install a new version, if
you are modifying the clients you'll need to make sure that the timesketch
source code on your machine is readable by the user with the UID 1000 and gid
1000. If that is done, then the code is mapped into the
      /usr/local/src/timesketch folder on the docker container.

New versions of timesketch api client can then be installed using:

```python
!pip install -e /usr/local/src/timesketch/api_client/python/
```

And the importer client:

```python
!pip install -e /usr/local/src/timesketch/importer_client/python
```

Just remember to restart the kernel runtime in order for the changes to be
active.

To update the docker image run:

```shell
$ sudo docker image pull us-docker.pkg.dev/osdfir-registry/timesketch/notebook:latest
```
