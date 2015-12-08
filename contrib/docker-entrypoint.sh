#!/bin/bash

set -x
set -e

if [ "$1" = 'timesketch' ]; then
  # check if SECRET_KEY is configured
  if [[ `grep -c "SECRET_KEY = u''" /etc/timesketch.conf` -eq 1 ]]; then
    NEWKEY=`openssl rand -base64 32`
    #sed -i -e '/^SECRET_KEY = u''/s/^/#/' /etc/timesketch.conf
    echo "SECRET_KEY = u'$NEWKEY'" >> /etc/timesketch.conf
  fi
  su -c 'celery -A timesketch.lib.tasks worker -D --workdir=/tmp --logfile=/usr/local/share/timesketch/celeryd.log' timesketch &
  #su -c 'celery -A timesketch.lib.tasks worker -D --workdir=/tmp --pidfile=/run/celeryd.pid --logfile=/usr/local/share/timesketch/celeryd.log' timesketch &
  if [ $USER_NAME ] && [ $USER_PASSWORD ]; then
    su -c 'tsctl add_user -u "$USER_NAME" -p "$USER_PASSWORD"' timesketch
  else
    su -c 'tsctl add_user -u demo -p demo' timesketch
  fi
  exec `su -c 'tsctl runserver -h 0.0.0.0' timesketch`
else
  exec "$@"
fi
