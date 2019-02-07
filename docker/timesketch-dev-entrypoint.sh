#!/bin/bash

# Run the container the default way
if [ "$1" = 'timesketch' ]; then

  # Update the base image
  apt-get update && apt-get -y upgrade

  # Setup install environment and Timesketch dependencies
  apt-get -y install apt-transport-https\
                       curl\
                       git\
                       libffi-dev\
                       lsb-release\
                       python-dev\
                       python-pip\
                       python-psycopg2

  curl -sS https://deb.nodesource.com/gpgkey/nodesource.gpg.key | apt-key add -
  VERSION=node_8.x
  DISTRO="$(lsb_release -s -c)"
  echo "deb https://deb.nodesource.com/$VERSION $DISTRO main" > /etc/apt/sources.list.d/nodesource.list
  curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | apt-key add -
  echo "deb https://dl.yarnpkg.com/debian/ stable main" > /etc/apt/sources.list.d/yarn.list

  # Install Plaso and Yarn
  apt-get -y install software-properties-common
  add-apt-repository ppa:gift/stable && apt-get update
  apt-get update && apt-get -y install python-plaso plaso-tools nodejs yarn

  # Install Timesketch from volume
  cd /usr/local/src/timesketch && yarn install && yarn run build
  pip install -e /usr/local/src/timesketch/

  # Copy the Timesketch configuration file into /etc
  cp /usr/local/src/timesketch/timesketch.conf /etc

  # Copy config files in /etc/timesketch
  mkdir /etc/timesketch
  cp /usr/local/src/timesketch/config/* /etc/timesketch/

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

  # Enable debug for the development server
  sed -i s/"DEBUG = False"/"DEBUG = True"/ /etc/timesketch.conf

  # Enable index and sketch analyzers
  sed -i s/"ENABLE_INDEX_ANALYZERS = False"/"ENABLE_INDEX_ANALYZERS = True"/ /etc/timesketch.conf
  sed -i s/"ENABLE_SKETCH_ANALYZERS = False"/"ENABLE_SKETCH_ANALYZERS = True"/ /etc/timesketch.conf
  sed -i s/"ENABLE_EXPERIMENTAL_UI = False"/"ENABLE_EXPERIMENTAL_UI = True"/ /etc/timesketch.conf

  # Add web user
  tsctl add_user --username "${TIMESKETCH_USER}" --password "${TIMESKETCH_USER}"

  echo "Timesketch development server is ready!"

  # Sleep forever to keep the container running
  sleep infinity
fi

# Run a custom command on container start
exec "$@"
