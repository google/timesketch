#!/bin/bash

set -e

if [ "$1" = 'timesketch' ]; then
  #celery should be running in a separate container
  #su -c 'celery -A timesketch.lib.tasks worker -D' timesketch &
  #sleep 1 # avoid race condition in-between celery <-> tsctl on timesketch.db
  if [ $USER_NAME ] && [ $USER_PASSWORD ]; then
    su -c 'tsctl add_user -u "$USER_NAME" -p "$USER_PASSWORD"' timesketch
  else
    su -c 'tsctl add_user -u demo -p demo' timesketch
  fi
  exec `su -c 'tsctl runserver' timesketch`
else
  exec "$@"
fi
