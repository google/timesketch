#!/bin/bash

set -x

: ${DOCKER:=false}

pip install timesketch
useradd -d /usr/local/share/timesketch -s /bin/bash timesketch
chown timesketch /usr/local/share/timesketch

if $DOCKER; then
  echo "change tsctl listener to 0.0.0.0"
  sed -i -e 's/127.0.0.1/0.0.0.0/' /usr/local/bin/tsctl
fi
