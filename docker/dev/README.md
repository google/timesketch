# Docker for development

## Start the deployment

```
docker compose up -d
```

The provided container definition runs Timesketch in development mode as a volume from your cloned repo. Any changes you make will appear in Timesketch automatically.

If you see the following message you can continue

```
Timesketch development server is ready!
```

### Start a celery container shell

```
docker exec -it timesketch celery -A timesketch.lib.tasks worker --loglevel info
```

### Start development webserver (and metrics server)

```
docker exec -it timesketch gunicorn --reload -b 0.0.0.0:5000 --log-file - --timeout 600 -c /usr/local/src/timesketch/data/gunicorn_config.py timesketch.wsgi:application
```

You now can access your development version at <http://127.0.0.1:5000/>

Log in with user: dev password: dev

### Non-interactive

Running the following as a script after `docker compose up -d` will bring up the development environment in the background for you.

```
docker exec timesketch celery -A timesketch.lib.tasks worker --loglevel info
docker exec timesketch gunicorn --reload -b 0.0.0.0:5000 --log-file - --timeout 120 timesketch.wsgi:application
```

### Run tests

```
docker exec -w /usr/local/src/timesketch -it timesketch python3 run_tests.py --coverage
```

That will run all tests in your docker container. It is recommended to run all tests at least before creating a pull request.

### Jupyter Notebook

To access a Jupyter notebook that has access to the Timesketch development
environment start a browser and visit <http://localhost:8844/> . The password to
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
