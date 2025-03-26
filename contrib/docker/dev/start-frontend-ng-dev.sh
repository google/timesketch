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

docker compose exec -it timesketch \
    yarn --cwd=/usr/local/src/timesketch/timesketch/frontend-ng install

docker compose exec -it -d timesketch \
    yarn run --cwd=/usr/local/src/timesketch/timesketch/frontend-ng serve
