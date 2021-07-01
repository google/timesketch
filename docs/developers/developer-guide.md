# Getting started

It is recommended to develop Timesketch using a docker container.

Note: Exclamation mark `!` denotes commands that should run in the docker container shell, dollar sign `$` denotes commands to run in your local shell.

## Locations and concepts

* Timesketch provides a webinterface and a REST API
* The configurations is located at ```/data``` sourcecode folder
* The front end uses ```Vue.js``` framework and is stored at ```/timesketch/frontend```
* Code that is used in potentially multiple locations is stored in ```/timesketch/lib```
* Analyzers are located at ```/timesketch/lib/analyzers```
* The API methods are defined in ```/timesketch/api```
* API client code is in ```/api_client/python/timesketch_api_client```
* Data models are defined in ```/timesketch/models```

## Bootstrapping your dev containers

Start a shell, change to the `timesketch/docker/dev` directory

```bash
$ git clone timesketch
$ cd timesketch/docker/dev
$ docker-compose up
```

Check that everything is running smoothly:

```bash
$ docker ps
CONTAINER ID   IMAGE                                                          COMMAND                  CREATED       STATUS       PORTS                                NAMES
d58d55bd53b3   us-docker.pkg.dev/osdfir-registry/timesketch/dev:latest        "/docker-entrypoint.…"   3 hours ago   Up 3 hours   127.0.0.1:5000->5000/tcp             timesketch-dev
0b99c30fbd25   us-docker.pkg.dev/osdfir-registry/timesketch/notebook:latest   "jupyter notebook"       3 hours ago   Up 3 hours   127.0.0.1:8844->8844/tcp, 8899/tcp   notebook
8696f39a2ba3   justwatch/elasticsearch_exporter:1.1.0                         "/bin/elasticsearch_…"   3 hours ago   Up 3 hours   9114/tcp                             es-metrics-exporter
f91d133600ae   grafana/grafana:latest                                         "/run.sh"                3 hours ago   Up 3 hours   127.0.0.1:3000->3000/tcp             grafana
c4b0f954eba6   prom/prometheus:v2.24.1                                        "/bin/prometheus --c…"   3 hours ago   Up 3 hours   127.0.0.1:9090->9090/tcp             prometheus
75dd0ed520fc   redis:6.0.10-alpine                                            "docker-entrypoint.s…"   3 hours ago   Up 3 hours   6379/tcp                             redis
bd10ed3677ca   docker.elastic.co/elasticsearch/elasticsearch-oss:7.10.2       "/tini -- /usr/local…"   3 hours ago   Up 3 hours   9200/tcp, 9300/tcp                   elasticsearch
128ece4be3b5   postgres:13.1-alpine                                           "docker-entrypoint.s…"   3 hours ago   Up 3 hours   5432/tcp                             postgres
```

Wait a few mintues for the installation script to complete.

```bash
$ docker-compose logs timesketch
Attaching to timesketch-dev
timesketch-dev         | Obtaining file:///usr/local/src/timesketch
timesketch-dev         | Installing collected packages: timesketch
timesketch-dev         |   Running setup.py develop for timesketch
timesketch-dev         | Successfully installed timesketch
timesketch-dev         | User dev created/updated
timesketch-dev         | Timesketch development server is ready!
```

Add a user to your Timesketch server (this will add a user `dev` with password `dev`)

```bash
$ docker-compose exec timesketch tsctl add_user --username dev --password dev
User dev created/updated
```

Now, start the `gunicon` server that will serve the Timsesketch WSGI app

In one shell:

```bash
$ docker-compose exec timesketch gunicorn --reload -b 0.0.0.0:5000 --log-file - --timeout 120 timesketch.wsgi:application
[2021-05-25 16:36:32 +0000] [94] [INFO] Starting gunicorn 19.10.0
[2021-05-25 16:36:32 +0000] [94] [INFO] Listening at: http://0.0.0.0:5000 (94)
[2021-05-25 16:36:32 +0000] [94] [INFO] Using worker: sync
/usr/lib/python3.8/os.py:1023: RuntimeWarning: line buffering (buffering=1) isn't supported in binary mode, the default buffer size will be used
  return io.open(fd, *args, **kwargs)
[2021-05-25 16:36:32 +0000] [102] [INFO] Booting worker with pid: 102
[2021-05-25 16:36:33,343] timesketch.wsgi_server/INFO Metrics server enabled
```

By now, you should be able to point your browser to `http://localhost:5000/` and log in with
the username and password combination you specified earlier. Any changes to Python files
(e.g. in the `timesketch/api/v1` directory tree) will be picked up automatically.

### Celery workers

Although they are written in Python, changes on importers, analyzers and other asynchronous elements of the codebase
are not picked up by the Gunicorn servers but by **Celery workers**.

If you're planning to work on those (or even just import timelines into your Timesketch instance), you'll need to launch
a Celery worker, and re-launch it every time you bring changes to its code.

In a new shell, run the following:

```bash
$ docker-compose exec timesketch celery -A timesketch.lib.tasks worker --loglevel info
```

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

## Running tests and linters

The main entry point is `run_tests.py` in Timesketch root. Please note that for testing
and linting python/frontend code in your local environment you need respectively python/
frontend dependencies installed.

For more information:

```python
! run_tests.py --help
```

To run frontend tests in watch mode, cd to `frontend` directory and use

```bash
! yarn run test --watch
```

To run TSLint in watch mode, use

```bash
! yarn run lint --watch
```

To run a single test (there are multiple ways to do it), open a shell in the docker container:

```shell
$ docker exec -it $CONTAINER_ID /bin/bash
```

Switch to:

```shell
! cd /usr/local/src/timesketch
```

And execute the single test

```shell
! nosetests timesketch/lib/emojis_test.py -v
```

Or all in one:

```bash
$ sudo docker exec -it $CONTAINER_ID nosetests /usr/local/src/timesketch/timesketch/lib/emojis_test.py -v
```

### Writing unittests

It is recommended to write unittests as much as possible.

Test files in Timesketch have the naming convention ```_test.py``` and are stored next to the files they test. E.g. a test file for ```/timesketch/lib/emojis.py``` is stored as ```/timesketch/lib/emojis_test.py```

The unittests for the api client can use ```mock``` to emulate responses from the server. The mocked answers are written in: ```api_client/python/timesketch_api_client/test_lib.py```.

To introduce a new API endpoint to be tested, the endpoint needs to be registered in the ```url_router``` section in ```/api_client/python/timesketch_api_client/test_lib.py``` and the response needs to be defined in the same file.

## end2end tests

End2end (e2e) tests are run on Github with every commit. Those tests will setup and run a full Timesketch instance, with the ability to import data and perform actions with it.
To run the e2e-tests locally execute to setup the e2e docker images and run them:

```bash
$ sh end_to_end_tests/tools/run_end_to_end_tests.sh
```

The tests are stored in:

```shell
end_to_end_tests/*.py
```

And the sample data (currently a plaso file and a csv) is stored in:

```shell
end_to_end_tests/test_data/
```

## Writing end2end tests

While writing end2end tests one approach to make it easier to develop these e2e tests is to create a simlink to the source files, in order for the changes to the files being reflected in the container. Another way is to mount the Timesketch source code from ```/usr/local/src/timesketch/``` to ```/usr/local/lib/python3.8/dist-packages/```

The following example is for changing / adding tests to ```client_test.py```
```shell
$ export CONTAINER_ID="$(sudo -E docker container list -f name=e2e_timesketch -q)"
$ docker exec -it $CONTAINER_ID /bin/bash
! rm /usr/local/lib/python3.8/dist-packages/end_to_end_tests/client_test.py
! ln -s /usr/local/src/timesketch/end_to_end_tests/client_test.py /usr/local/lib/python3.8/dist-packages/end_to_end_tests/client_test.py
```

From now on you can edit the ```client_test.py``` file outside of the docker instance and run it again with

```shell
! python3 /usr/local/src/timesketch/end_to_end_tests/tools/run_in_container.py
```

or run the following outside of the container:
```bash
$ sudo docker exec -it $CONTAINER_ID python3 /usr/local/src/timesketch/end_to_end_tests/tools/run_in_container.py
```

## Building Timesketch frontend

To build frontend files and put bundles in `timesketch/static/dist/`, use

```bash
! yarn run build
```

To watch for changes in code and rebuild automatically, use

```bash
! yarn run build --watch
```

This is what you would normally use when making changes to the frontend.
Changes are not instantaneous, it takes a couple of seconds to rebuild. It's best to
keep this interactive shell to your container running so you can monitor the re-build.

Don't forget to refresh page if your browser doesn't automatically load the changes.

## Packaging

Before pushing package to PyPI, make sure you build the frontend before.

## Local development

You may work on the frontend for your local environment for integration with your IDE or other reasons. This is not recommended however as it may cause clashes with your installed NodeJS.

Add Node.js 8.x repo

```bash
$ curl -sS https://deb.nodesource.com/gpgkey/nodesource.gpg.key | sudo apt-key add -
$ echo "deb https://deb.nodesource.com/node_8.x $(lsb_release -s -c) main"  | sudo tee /etc/apt/sources.list.d/nodesource.list
```

Add Yarn repo

```bash
$ curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | sudo apt-key add -
$ echo "deb https://dl.yarnpkg.com/debian/ stable main" | sudo tee /etc/apt/sources.list.d/yarn.list
```

Install Node.js and Yarn

```bash
$ apt-get update && apt-get install nodejs yarn
```

After that you would run the same steps as with docker container to install frontend
dependencies and build/test.

## Using Notebook

The development container contains a jupyter notebook environment to expirement
with the developer instance.

To access the notebook access it in a browser using the URL:
http://localhost:8844/?token=timesketch

(you can also just access http://localhost:8844 and type in `timesketch` as the
password).

To get you started there are snippets you can use (look for the `snippets`
drop-down menu and select the code snippet you want to test.

To be able to use the notebook container using
[colab](https://colab.research.google.com) start by creating a notebook and then
click the little triangle/arrow button in the upper right corner to connect to a
local runtime, see:

![Connect to Local Runtime](/assets/images/colab_local_runtime.png)

This will create a pop-up that you need to enter the URL for the local runtime.
Use: http://localhost:8844/?token=timesketch as the URL.

![Enter Local Runtime Information](/assets/images/notebook_connect.png)

This will connect to the notebook container, where you can start executing code.

![Running In Colab](/assets/images/colab_connected.png)

*There are some things that work better in the Jupyter container though.*

### Developing the API Client Using the Notebook

Using the notebook can be very helpful when developing the API client. New features
can be easily tested.

In order to load changes made in the code, two things need to happen:

1. The code needs to be accessible from the container
2. The code needs to be installed and the kernel restarted

For the code to be accessible, it has to be readable by the user with the UID of 1000 or GID
of 1000. One way of making sure is to run

```shell
$ sudo chgrp -R 1000 timesketch
```

Against the source folder. Then inside a notebook to run:

```python
!pip install /usr/local/src/timesketch/api_client/python
```

After the code is installed the kernel needs to restarted to make the changes take
effect. In the menu select `Kernel | Restart`, now you should be able to go back
into the notebook and make use of the latest changes in the API client.

![Restarting Kernel](/assets/images/kernel_restart.png)

## API development

Exposing new functionality via the API starts at ```/timesketch/api/v1/routes.py```. In that file the different routes / endpoints are defined that can be used.
Typically every route has a dedicated Resource file in ```/timesketch/api/v1/resources```.

A resource can have ```GET``` as well as ```POST```or other HTTP methods each defined in the same resource file. A good example of a resource that has a mixture is ```/timesketch/api/v1/resources/archive.py```.

To write tests for the resource, add a section in ```/timesketch/api/v1/resources_test.py```

### Error handling

It is recommended to expose the error with as much detail as possible to the user / tool that is trying to access the resource.

For example the following will give a human readable information as well as a HTTP status code that client code can react on
```python
if not sketch:
            abort(HTTP_STATUS_CODE_NOT_FOUND, 'No sketch found with this ID.')
```

On the opposite side the following is not recommended:

```python
if not sketch:
            abort(HTTP_STATUS_CODE_BAD_REQUEST, 'Error')
```
