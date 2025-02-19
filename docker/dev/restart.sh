#!/bin/bash
export CONTAINER_ID="$(docker container list -f name=timesketch -q)"
docker exec -d $CONTAINER_ID celery -A timesketch.lib.tasks worker --loglevel info
docker exec -d $CONTAINER_ID gunicorn --reload -b 0.0.0.0:5000 --log-file - --timeout 600 -c /usr/local/src/timesketch/data/gunicorn_config.py timesketch.wsgi:application
