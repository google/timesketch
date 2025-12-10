#!/usr/bin/env sh

exec celery \
    -A timesketch.lib.tasks \
    worker \
    --loglevel debug
