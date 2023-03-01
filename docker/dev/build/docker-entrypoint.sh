#!/bin/bash

# Run the container the default way
if [ "$1" = 'timesketch' ]; then

  # Install Timesketch in editable mode from volume
  pip3 install -e /usr/local/src/timesketch/

  # Copy config files
  mkdir /etc/timesketch
  cp /usr/local/src/timesketch/data/timesketch.conf /etc/timesketch/
  cp /usr/local/src/timesketch/data/features.yaml /etc/timesketch/
  cp /usr/local/src/timesketch/data/tags.yaml /etc/timesketch/
  cp /usr/local/src/timesketch/data/intelligence_tag_metadata.yaml /etc/timesketch/
  cp /usr/local/src/timesketch/data/plaso.mappings /etc/timesketch/
  cp /usr/local/src/timesketch/data/generic.mappings /etc/timesketch/
  cp /usr/local/src/timesketch/data/ontology.yaml /etc/timesketch/
  cp /usr/local/src/timesketch/data/data_finder.yaml /etc/timesketch/
  cp /usr/local/src/timesketch/data/bigquery_matcher.yaml /etc/timesketch/
  ln -s /usr/local/src/timesketch/data/sigma_config.yaml /etc/timesketch/sigma_config.yaml
  ln -s /usr/local/src/timesketch/data/sigma_rule_status.csv /etc/timesketch/sigma_rule_status.csv
  ln -s /usr/local/src/timesketch/data/sigma /etc/timesketch/
  ln -s /usr/local/src/timesketch/data/scenarios /etc/timesketch/
  ln -s /usr/local/src/timesketch/data/context_links.yaml /etc/timesketch/context_links.yaml


  # Set SECRET_KEY in /etc/timesketch/timesketch.conf if it isn't already set
  if grep -q "SECRET_KEY = '<KEY_GOES_HERE>'" /etc/timesketch/timesketch.conf; then
    OPENSSL_RAND=$( openssl rand -base64 32 )
    # Using the pound sign as a delimiter to avoid problems with / being output from openssl
    sed -i 's#SECRET_KEY = \x27\x3CKEY_GOES_HERE\x3E\x27#SECRET_KEY = \x27'$OPENSSL_RAND'\x27#' /etc/timesketch/timesketch.conf
  fi

  # Set up the Postgres connection
  if [ $POSTGRES_USER ] && [ $POSTGRES_PASSWORD ] && [ $POSTGRES_ADDRESS ] && [ $POSTGRES_PORT ]; then
    sed -i 's#postgresql://<USERNAME>:<PASSWORD>@localhost#postgresql://'$POSTGRES_USER':'$POSTGRES_PASSWORD'@'$POSTGRES_ADDRESS':'$POSTGRES_PORT'#' /etc/timesketch/timesketch.conf
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
    echo "Please pass values for the ELASTIC_ADDRESS and ELASTIC_PORT environment variables"
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

  # Enable debug for the development server
  sed -i s/"DEBUG = False"/"DEBUG = True"/ /etc/timesketch/timesketch.conf

  # Enable index and sketch analyzers
  sed -i s/"ENABLE_INDEX_ANALYZERS = False"/"ENABLE_INDEX_ANALYZERS = True"/ /etc/timesketch/timesketch.conf
  sed -i s/"ENABLE_SKETCH_ANALYZERS = False"/"ENABLE_SKETCH_ANALYZERS = True"/ /etc/timesketch/timesketch.conf
  sed -i s/"ENABLE_EXPERIMENTAL_UI = False"/"ENABLE_EXPERIMENTAL_UI = True"/ /etc/timesketch/timesketch.conf

  # Disable CSRF checks for the development server
  echo "WTF_CSRF_ENABLED = False" >> /etc/timesketch/timesketch.conf

  # Add web user
  tsctl create-user --password "${TIMESKETCH_USER}" "${TIMESKETCH_USER}"

  # Add Sigma rules
  git clone https://github.com/SigmaHQ/sigma /usr/local/src/sigma
  # for each line in sigma_rules.txt execute the command
  for line in $(cat sigma_rules.txt); do
    tsctl import-sigma-rules $line
  done

  # Wrap up things
  echo "Timesketch development server is ready!"

  # Sleep forever to keep the container running
  sleep infinity
fi

# Run a custom command on container start
exec "$@"
