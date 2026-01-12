#!/bin/bash

# Default Gunicorn settings
NUM_WSGI_WORKERS="${NUM_WSGI_WORKERS:-4}"

if [ "$1" = "timesketch-web" ]; then
  export TIMESKETCH_UI_MODE="ng"
  gunicorn --bind 0.0.0.0:5000 --log-file /var/log/timesketch/wsgi.log \
           --error-logfile /var/log/timesketch/wsgi_error.log --log-level info \
           --capture-output --timeout 600 --limit-request-line 8190 \
           --workers ${NUM_WSGI_WORKERS} \
           --max-requests 1000 --max-requests-jitter 100 \
           timesketch.wsgi:application

elif [ "$1" = "timesketch-web-legacy" ]; then
  export TIMESKETCH_UI_MODE="legacy"
  gunicorn --bind 0.0.0.0:5001 --log-file /var/log/timesketch/wsgi_legacy.log \
           --error-logfile /var/log/timesketch/wsgi_legacy_error.log --log-level info \
           --capture-output --timeout 600 --limit-request-line 8190 \
           --workers ${NUM_WSGI_WORKERS} \
           --max-requests 1000 --max-requests-jitter 100 \
           timesketch.wsgi:application

elif [ "$1" = "timesketch-web-v3" ]; then
  export TIMESKETCH_UI_MODE="v3"
  gunicorn --bind 0.0.0.0:5002 --log-file /var/log/timesketch/wsgi_v3.log \
           --error-logfile /var/log/timesketch/wsgi_v3_error.log --log-level info \
           --capture-output --timeout 600 --limit-request-line 8190 \
           --workers ${NUM_WSGI_WORKERS} \
           --max-requests 1000 --max-requests-jitter 100 \
           timesketch.wsgi:application

elif [ "$1" = "timesketch-worker" ]; then
  celery -A timesketch.lib.tasks worker \
         --logfile=/var/log/timesketch/worker.log \
         --loglevel="${WORKER_LOG_LEVEL}"
fi
