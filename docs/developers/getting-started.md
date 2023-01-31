---
hide:
  - footer
---
# Getting started

The supported environment for Timesketch development is Docker.

Note: Exclamation mark `!` denotes commands that should run in the docker
container shell, dollar sign `$` denotes commands to run in your local shell.

## Locations and concepts

- Timesketch provides a webinterface and a REST API
- The configurations is located at `/data` sourcecode folder
- The front end uses `Vue.js` framework and is stored at `/timesketch/frontend`
- Code that is used in potentially multiple locations is stored in `/timesketch/lib`
- Analyzers are located at `/timesketch/lib/analyzers`
- The API methods are defined in `/timesketch/api`
- API client code is in `/api_client/python/timesketch_api_client`
- Data models are defined in `/timesketch/models`

## Setting up your development environment

Start a shell, change to the `timesketch/docker/dev` directory

```bash
$ git clone timesketch
$ cd timesketch/docker/dev
$ docker-compose up
```

Wait a few minutes for the installation script to complete.

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

Per default a user `dev` with password `dev` is created for you. If you want to
add additional users to your Timesketch server, run the following command:

```bash
$ docker-compose exec timesketch tsctl create-user <USER> --password <PW>
User <USER> created/updated
```

### Web server

Now, start the `gunicon` server that will serve the Timsketch WSGI app.

To make this task easier, we recommend using the `timesketch/contrib/tsdev.sh`
script.

In one shell:

```bash
./tsdev.sh web
```

OR

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

By now, you should be able to point your browser to `http://localhost:5000/` and
 log in with the username and password combination you specified earlier (or
 `dev:dev` by default). Any changes to Python files (e.g. in the
 `timesketch/api/v1` directory tree) will be picked up automatically.

### Celery workers

Although they are written in Python, changes on importers, analyzers and other
asynchronous elements of the codebase are not picked up by the Gunicorn servers
but by **Celery workers**.

If you're planning to work on those (or even just import timelines into your
Timesketch instance), you'll need to launch a Celery worker, and re-launch it
every time you bring changes to its code.

You can use `timesketch/contrib/tsdev.sh` for this task as well.

In a new shell, run the following:

```bash
$ ./tsdev.sh celery
```

OR

```bash
$ docker-compose exec timesketch celery -A timesketch.lib.tasks worker --loglevel info
```

### Restarting

To restart the webserver and celery workers, stop the execution. Depending on
your system `ctrl+c` will do it.
Then start them both as outlined before with:

```bash
$ ./tsdev.sh web
$ ./tsdev.sh celery
```

OR

```bash
$ docker-compose exec timesketch gunicorn --reload -b 0.0.0.0:5000 --log-file - --timeout 120 timesketch.wsgi:application
$ docker-compose exec timesketch celery -A timesketch.lib.tasks worker --loglevel info
```

### frontend-ng UI development

For development on the new `frontend-ng` UI, you need to install some
dependencies once and start the new frontend. More on frontend development is
documented [here](https://timesketch.org/developers/frontend-development/).

We recommend using the `timesketch/contrib/tsdev.sh` script for this task as well.

Install frontend-ng dependencies:
```bash
./tsdev.sh vue-install-deps frontend-ng
```

Start the new frondend-ng:
```
./tsdev.sh vue-dev frontend-ng
```

Point your browser to `http://localhost:5001/` to access the new frontend UI.
All changes to the `timesketch/frontend-ng/` path will be automatically build
and loaded in the new frontend.

## API development

Exposing new functionality via the API starts at `/timesketch/api/v1/routes.py`.
In that file the different routes / endpoints are defined that can be used.
Typically every route has a dedicated Resource file in `/timesketch/api/v1/resources`.

A resource can have `GET` as well as `POST`or other HTTP methods each defined in
 the same resource file. A good example of a resource that has a mixture is
 `/timesketch/api/v1/resources/archive.py`.

To write tests for the resource, add a section in `/timesketch/api/v1/resources_test.py`

### Error handling

It is recommended to expose the error with as much detail as possible to the
user / tool that is trying to access the resource.

For example the following will give a human readable information as well as a
HTTP status code that client code can react on

```python
if not sketch:
            abort(HTTP_STATUS_CODE_NOT_FOUND, 'No sketch found with this ID.')
```

On the opposite side the following is not recommended:

```python
if not sketch:
            abort(HTTP_STATUS_CODE_BAD_REQUEST, 'Error')
```

## Writing documentation

Writing documentation is critical for others to use your features, so we
encourage to write documentation along side with shipping new features.

The documentation is auto generated by a Github workflow `https://github.com/google/timesketch/blob/master/.github/workflows/mkdocs.yml` which will execute
`mkdocs gh-deploy --force`and deploy changes to timesketch.org.

To test mkdocs locally, run the following in your container:

```shell
! cd /usr/local/src/timesketch
! pip3 install mkdocs mkdocs-material mkdocs-redirects
! mkdocs serve
```

And visit the results / review remarks, warnings or errors from mkdocs.

## Formatting

Before merging a pull request, we expect the code to be formatted in a certain
manner. You can use VS Code extensions to make your life easier in formatting
your files. For example:
* [Vetur](https://marketplace.visualstudio.com/items?itemName=octref.vetur) for *Vue* files
* [Python](https://marketplace.visualstudio.com/items?itemName=ms-python.python) and [Black](https://github.com/psf/black) for *Python* files.

### Formatting Python files

We use `black` to format Python files. `black` is the uncompromising Python code
 formatter. There are two ways to use it:
1. Manually from the command line:
    * Install `black` following the official [black documentation](https://pypi.org/project/black/).
    * Format your file by running this command: `$ black path/to/python/file`
2. Automatically from [VS Code](https://dev.to/adamlombard/how-to-use-the-black-python-code-formatter-in-vscode-3lo0):
    * Download the VS Code extension `Python`.
    * Navigate to `Code -> Preferences -> Settings` and search for `Python Formatting Provider`. Then, select `black` from the dropdown menu.
    * Enable the `Format on Save` option to automatically format your files every time you save them.
