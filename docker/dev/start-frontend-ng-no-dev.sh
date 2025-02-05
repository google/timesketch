#!/usr/bin/env bash

docker compose exec -d timesketch \
  celery \
  -A timesketch.lib.tasks \
  worker \
  --loglevel info

docker compose exec -d timesketch \
  gunicorn \
  --reload \
  -b 0.0.0.0:5000 \
  --log-file - \
  --timeout 600 \
  -c /usr/local/src/timesketch/data/gunicorn_config.py \
  timesketch.wsgi:application
