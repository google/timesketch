#!/usr/bin/env bash

set -e

cd /usr/local/src/timesketch/timesketch/frontend-ng

yarn install
exec yarn run serve
