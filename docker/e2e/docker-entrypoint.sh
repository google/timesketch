#!/bin/bash

# Run the container the default way
if [ "$1" = 'timesketch' ]; then

  # Install Timesketch in editable mode from volume
  pip3 install -e /usr/local/src/timesketch/

  # Copy the mappings for plaso ingestion.
  cp /usr/local/src/timesketch/data/plaso.mappings /etc/timesketch/
  cp /usr/local/src/timesketch/data/generic.mappings /etc/timesketch/

  # Set SECRET_KEY in /etc/timesketch/timesketch.conf if it isn't already set
  if grep -q "SECRET_KEY = '<KEY_GOES_HERE>'" /etc/timesketch/timesketch.conf; then
    OPENSSL_RAND=$( openssl rand -base64 32 )
    # Using the pound sign as a delimiter to avoid problems with / being output from openssl
    sed -i 's#SECRET_KEY = \x27\x3CKEY_GOES_HERE\x3E\x27#SECRET_KEY = \x27'$OPENSSL_RAND'\x27#' /etc/timesketch/timesketch.conf
  fi

  # Set up the Postgres connection
  if [ $POSTGRES_PASSWORD ]; then echo "POSTGRES_PASSWORD usage is discouraged. Use Docker Secrets instead and set POSTGRES_PASSWORD_FILE to /run/secrets/secret-name"; fi
  if [ $POSTGRES_PASSWORD_FILE ]; then POSTGRES_PASSWORD=$(cat $POSTGRES_PASSWORD_FILE); fi

  if [ $POSTGRES_USER ] && [ $POSTGRES_PASSWORD ] && [ $POSTGRES_ADDRESS ] && [ $POSTGRES_PORT ]; then
    sed -i 's#postgresql://<USERNAME>:<PASSWORD>@localhost#postgresql://'$POSTGRES_USER':'$POSTGRES_PASSWORD'@'$POSTGRES_ADDRESS':'$POSTGRES_PORT'#' /etc/timesketch/timesketch.conf
    unset POSTGRES_PASSWORD
  else
    # Log an error since we need the above-listed environment variables
    echo "Please pass values for the POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_ADDRESS, and POSTGRES_PORT environment variables"
    exit 1
  fi

  # Set up the OpenSearch connection
  if [ $OPENSEARCH_HOST ] && [ $OPENSEARCH_PORT ]; then
    sed -i 's#OPENSEARCH_HOST = \x27127.0.0.1\x27#OPENSEARCH_HOST = \x27'$OPENSEARCH_HOST'\x27#' /etc/timesketch/timesketch.conf
    sed -i 's#OPENSEARCH_PORT = 9200#OPENSEARCH_PORT = '$OPENSEARCH_PORT'#' /etc/timesketch/timesketch.conf
  else
    # Log an error since we need the above-listed environment variables
    echo "Please pass values for the OPENSEARCH_HOST and OPENSEARCH_PORT environment variables"
  fi

  # Set up the Redis connection
  if [ $REDIS_ADDRESS ] && [ $REDIS_PORT ]; then
    sed -i 's#UPLOAD_ENABLED = False#UPLOAD_ENABLED = True#' /etc/timesketch/timesketch.conf
    sed -i 's#^CELERY_BROKER_URL =.*#CELERY_BROKER_URL = \x27redis://'$REDIS_ADDRESS':'$REDIS_PORT'\x27#' /etc/timesketch/timesketch.conf
    sed -i 's#^CELERY_RESULT_BACKEND =.*#CELERY_RESULT_BACKEND = \x27redis://'$REDIS_ADDRESS':'$REDIS_PORT'\x27#' /etc/timesketch/timesketch.conf
  else
    # Log an error since we need the above-listed environment variables
    echo "Please pass values for the REDIS_ADDRESS and REDIS_PORT environment variables"
  fi

  # Set up web credentials
  if [ -z ${TIMESKETCH_USER:+x} ]; then
    TIMESKETCH_USER="admin"
    echo "TIMESKETCH_USER set to default: ${TIMESKETCH_USER}";
  fi

  if [ $TIMESKETCH_PASSWORD_FILE ]; then TIMESKETCH_PASSWORD=$(cat $TIMESKETCH_PASSWORD_FILE); fi
  if [ -z ${TIMESKETCH_PASSWORD:+x} ]; then
    TIMESKETCH_PASSWORD="$(openssl rand -base64 32)"
    echo "TIMESKETCH_PASSWORD set randomly to: ${TIMESKETCH_PASSWORD}";
  fi

  # Sleep to allow the other processes to start
  sleep 5
  tsctl create-user "$TIMESKETCH_USER" --password "$TIMESKETCH_PASSWORD"
  unset TIMESKETCH_PASSWORD

  cat <<EOF >> /etc/timesketch/data_finder.yaml
test_data_finder:
    description: Testing the data finder in the e2e test.
    notes: Import the partial EVTX file for e2e tests.
    query_string: data_type:"windows:evtx:record" AND event_identifier:7036
EOF

  # Run the Timesketch server (without SSL)
  cd /tmp
  exec `bash -c "/usr/local/bin/celery -A timesketch.lib.tasks worker --uid nobody --loglevel info & \
  gunicorn --reload -b 0.0.0.0:80 --access-logfile - --error-logfile - --log-level info --timeout 120 timesketch.wsgi:application"`
fi

# Run a custom command on container start
exec "$@"
