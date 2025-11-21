#!/usr/bin/env sh

exec gunicorn \
    --reload \
    -b 0.0.0.0:5000 \
    --log-file - \
    --timeout 600 \
    -c /usr/local/src/timesketch/data/gunicorn_config.py \
    timesketch.wsgi:application
