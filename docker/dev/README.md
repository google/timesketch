## Docker for development

You can run Timesketch on Docker in development mode.

### Start a developer version of docker containers in this directory

```
docker-compose up -d
```

### Find out container ID for the timesketch container

```
CONTAINER_ID="$(sudo docker container list -f name=development_timesketch -q)"
```
In the output look for CONTAINER ID for the timesketch container

To write the ID to a variable, use:
```
export CONTAINER_ID="$(sudo docker container list -f name=development_timesketch -q)"
```
and test with
```
echo $CONTAINER_ID
```

### Start a celery container shell
```
sudo docker exec -it $CONTAINER_ID celery -A timesketch.lib.tasks worker --loglevel info
```

### Start development webserver

```
sudo docker exec -it $CONTAINER_ID gunicorn --reload -b 0.0.0.0:5000 --log-file - --timeout 120 timesketch.wsgi:application
```

You now can access your development version at http://127.0.0.1:5000/
Log in with user: dev password: dev

