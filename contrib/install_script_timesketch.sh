#!/bin/bash

set -x

: ${DOCKER:=false}

pip install timesketch
useradd -d /usr/local/share/timesketch -s /bin/bash timesketch
chown timesketch /usr/local/share/timesketch

#if $DOCKER; then
#fi
