#!/bin/bash

echo "[i] Script (NOT TESTED) to run the frontend in dev mode"
echo "[i] Run this script in timesketch/docker/dev"
echo "[i] Remember to run 'docker compose up -d' to start the containers"

CONTAINER_ID="$(docker container list -f name=timesketch-dev -q)"
docker exec -d $CONTAINER_ID celery -A timesketch.lib.tasks worker --loglevel info
docker compose exec timesketch yarn install --cwd=/usr/local/src/timesketch/timesketch/frontend
docker compose exec -d timesketch yarn run --cwd=/usr/local/src/timesketch/timesketch/frontend build --mode development --watch
docker exec -it $CONTAINER_ID sh -c "cd /usr/local/src/timesketch/timesketch/frontend; npm install >> /dev/null; yarn install >> /dev/null"
docker exec -d $CONTAINER_ID gunicorn --reload -b 0.0.0.0:5000 --log-file - --timeout 600 -c /usr/local/src/timesketch/data/gunicorn_config.py timesketch.wsgi:application
docker compose exec timesketch yarn run --cwd=/usr/local/src/timesketch/timesketch/frontend serve

