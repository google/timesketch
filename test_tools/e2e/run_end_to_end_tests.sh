#!/bin/bash
#
# Script to run end-to-end tests.

# Fail on any error
set -e

# Defaults
DEFAULT_ELASTICSEARCH_VERSION=7.6.2

# Set Elasticsearch version to run
[ -z "$ELASTICSEARCH_VERSION" ] && export ELASTICSEARCH_VERSION=$DEFAULT_ELASTICSEARCH_VERSION

# Container ID for the web server
export CONTAINER_ID="$(sudo -E docker container list -f name=e2e_timesketch -q)"

# Start containers if necessary
if [ -z "$CONTAINER_ID" ]; then
  sudo -E docker-compose -f ./docker/e2e/docker-compose.yml up -d
  /bin/sleep 120  # Wait for all containers to be available
  export CONTAINER_ID="$(sudo -E docker container list -f name=e2e_timesketch -q)"
fi

sudo -E docker exec $CONTAINER_ID python3 /usr/local/src/timesketch/test_tools/e2e/run_in_container.py
