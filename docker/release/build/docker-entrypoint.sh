#!/bin/bash

if [ "$1" = "timesketch-web" ]; then
  # Get number of WSGI workers from environment, or set it to default value.
  NUM_WSGI_WORKERS="${NUM_WSGI_WORKERS:-4}"
  gunicorn --bind 0.0.0.0:5000 --log-file /var/log/timesketch/wsgi.log \
           --error-logfile /var/log/timesketch/wsgi_error.log --log-level info \
           --capture-output --timeout 600 --limit-request-line 8190 \
           --workers ${NUM_WSGI_WORKERS} timesketch.wsgi:application
# Temporary V2 application of the UI.
# TODO: Remove when V2 is the default.
elif [ "$1" = "timesketch-web-v2" ]; then
  # Get number of WSGI workers from environment, or set it to default value.
  NUM_WSGI_WORKERS="${NUM_WSGI_WORKERS:-4}"
  gunicorn --bind 0.0.0.0:5000 --log-file /var/log/timesketch/wsgi.log \
           --error-logfile /var/log/timesketch/wsgi_error.log --log-level info \
           --capture-output --timeout 600 --limit-request-line 8190 \
           --workers ${NUM_WSGI_WORKERS} timesketch.wsgi:application_v2
elif [ "$1" = "timesketch-worker" ]; then
  celery -A timesketch.lib.tasks worker \
         --logfile=/var/log/timesketch/worker.log \
         --loglevel="${WORKER_LOG_LEVEL}"
fi
