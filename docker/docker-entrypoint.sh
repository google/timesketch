#!/bin/bash

# Run the container the default way
if [ "$1" = 'timesketch' ]; then
  # Set SECRET_KEY in /etc/timesketch.conf if it isn't already set
  if grep -q "SECRET_KEY = u'<KEY_GOES_HERE>'" /etc/timesketch.conf; then
    OPENSSL_RAND=$( openssl rand -base64 32 )
    # Using the pound sign as a delimiter to avoid problems with / being output from openssl
    sed -i 's#SECRET_KEY = u\x27\x3CKEY_GOES_HERE\x3E\x27#SECRET_KEY = u\x27'$OPENSSL_RAND'\x27#' /etc/timesketch.conf
  fi

  # Set up the Postgres connection
  if [ $POSTGRES_USER ] && [ $POSTGRES_PASSWORD ] && [ $POSTGRES_ADDRESS ] && [ $POSTGRES_PORT ]; then
    sed -i 's#postgresql://<USERNAME>:<PASSWORD>@localhost#postgresql://'$POSTGRES_USER':'$POSTGRES_PASSWORD'@'$POSTGRES_ADDRESS':'$POSTGRES_PORT'#' /etc/timesketch.conf
  else
    # Log an error since we need the above-listed environment variables
    echo "Please pass values for the POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_ADDRESS, and POSTGRES_PORT environment variables"
    exit 1
  fi

  # Set up the Elastic connection
  if [ $ELASTIC_ADDRESS ] && [ $ELASTIC_PORT ]; then
    sed -i 's#ELASTIC_HOST = u\x27127.0.0.1\x27#ELASTIC_HOST = u\x27'$ELASTIC_ADDRESS'\x27#' /etc/timesketch.conf
    sed -i 's#ELASTIC_PORT = 9200#ELASTIC_PORT = '$ELASTIC_PORT'#' /etc/timesketch.conf
  else
    # Log an error since we need the above-listed environment variables
    echo "Please pass values for the ELASTIC_ADDRESS and ELASTIC_PORT environment variables"
  fi

  # Set up the Redis connection
  if [ $REDIS_ADDRESS ] && [ $REDIS_PORT ]; then
    sed -i 's#UPLOAD_ENABLED = False#UPLOAD_ENABLED = True#' /etc/timesketch.conf
    sed -i 's#^CELERY_BROKER_URL =.*#CELERY_BROKER_URL = \x27redis://'$REDIS_ADDRESS':'$REDIS_PORT'\x27#' /etc/timesketch.conf
    sed -i 's#^CELERY_RESULT_BACKEND =.*#CELERY_RESULT_BACKEND = \x27redis://'$REDIS_ADDRESS':'$REDIS_PORT'\x27#' /etc/timesketch.conf
  else
    # Log an error since we need the above-listed environment variables
    echo "Please pass values for the REDIS_ADDRESS and REDIS_PORT environment variables"
  fi

  # Set up the Neo4j connection
  if [ $NEO4J_ADDRESS ] && [ $NEO4J_PORT ]; then
    sed -i 's#GRAPH_BACKEND_ENABLED = False#GRAPH_BACKEND_ENABLED = True#' /etc/timesketch.conf
    sed -i 's#NEO4J_HOST =.*#NEO4J_HOST = u\x27'$NEO4J_ADDRESS'\x27#' /etc/timesketch.conf
    sed -i 's#NEO4J_PORT =.*#NEO4J_PORT = '$NEO4J_PORT'#' /etc/timesketch.conf
  else
    # Log an error since we need the above-listed environment variables
    echo "Please pass values for the NEO4J_ADDRESS and NEO4J_PORT environment variables if you want graph support"
  fi

  # Set up web credentials
  if [ -z ${TIMESKETCH_USER+x} ]; then
    TIMESKETCH_USER="admin"
    echo "TIMESKETCH_USER set to default: ${TIMESKETCH_USER}";
  fi
  if [ -z ${TIMESKETCH_PASSWORD+x} ]; then
    TIMESKETCH_PASSWORD="$(openssl rand -base64 32)"
    echo "TIMESKETCH_PASSWORD set randomly to: ${TIMESKETCH_PASSWORD}";
  fi

  # Sleep to allow the other processes to start
  sleep 5
  tsctl add_user -u "$TIMESKETCH_USER" -p "$TIMESKETCH_PASSWORD"

  # Run the Timesketch server (without SSL)
  #exec `bash -c "/usr/local/bin/celery -A timesketch.lib.tasks worker --uid nobody --loglevel info & /usr/local/bin/tsctl runserver -h 0.0.0.0 -p 5000"`
  exec `bash -c "gunicorn -b 127.0.0.1:80 --log-file - --timeout 120 timesketch.wsgi:application & /usr/local/bin/tsctl runserver -h 0.0.0.0 -p 5000"`
fi

# Run a custom command on container start
exec "$@"
