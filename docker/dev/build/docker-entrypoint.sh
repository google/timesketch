#!/bin/bash

# Function to setup and refresh configuration
setup_config() {
  # Copy config files
  mkdir -p /etc/timesketch
  cp /usr/local/src/timesketch/data/timesketch.conf /etc/timesketch/
  cp /usr/local/src/timesketch/data/regex_features.yaml /etc/timesketch/
  cp /usr/local/src/timesketch/data/winevt_features.yaml /etc/timesketch/
  cp /usr/local/src/timesketch/data/tags.yaml /etc/timesketch/
  cp /usr/local/src/timesketch/data/intelligence_tag_metadata.yaml /etc/timesketch/
  cp /usr/local/src/timesketch/data/plaso.mappings /etc/timesketch/
  cp /usr/local/src/timesketch/data/generic.mappings /etc/timesketch/
  cp /usr/local/src/timesketch/data/ontology.yaml /etc/timesketch/
  cp /usr/local/src/timesketch/data/data_finder.yaml /etc/timesketch/
  cp /usr/local/src/timesketch/data/bigquery_matcher.yaml /etc/timesketch/
  
  # Use -f to ignore error if link already exists
  ln -sf /usr/local/src/timesketch/data/sigma_config.yaml /etc/timesketch/sigma_config.yaml
  ln -sf /usr/local/src/timesketch/data/sigma /etc/timesketch/
  ln -sf /usr/local/src/timesketch/data/dfiq /etc/timesketch/
  ln -sf /usr/local/src/timesketch/data/context_links.yaml /etc/timesketch/context_links.yaml
  ln -sf /usr/local/src/timesketch/data/plaso_formatters.yaml /etc/timesketch/plaso_formatters.yaml
  ln -sf /usr/local/src/timesketch/data/nl2q /etc/timesketch/
  ln -sf /usr/local/src/timesketch/data/llm_summarize /etc/timesketch/

  # Set SECRET_KEY in /etc/timesketch/timesketch.conf if it isn't already set
  if grep -q "SECRET_KEY = '<KEY_GOES_HERE>'" /etc/timesketch/timesketch.conf; then
    OPENSSL_RAND=$( openssl rand -base64 32 )
    # Using the pound sign as a delimiter to avoid problems with / being output from openssl
    sed -i 's#SECRET_KEY = \x27\x3CKEY_GOES_HERE\x3E\x27#SECRET_KEY = \x27'$OPENSSL_RAND'\x27#' /etc/timesketch/timesketch.conf
  fi

  # Set up the Postgres connection
  if [ $POSTGRES_USER ] && [ $POSTGRES_PASSWORD ] && [ $POSTGRES_ADDRESS ] && [ $POSTGRES_PORT ]; then
    sed -i 's#postgresql://<USERNAME>:<PASSWORD>@localhost#postgresql://'$POSTGRES_USER':'$POSTGRES_PASSWORD'@'$POSTGRES_ADDRESS':'$POSTGRES_PORT'#' /etc/timesketch/timesketch.conf
  fi

  # Set up the OpenSearch connection
  if [ $OPENSEARCH_HOST ] && [ $OPENSEARCH_PORT ]; then
    sed -i 's#OPENSEARCH_HOST = \x27127.0.0.1\x27#OPENSEARCH_HOST = \x27'$OPENSEARCH_HOST'\x27#' /etc/timesketch/timesketch.conf
    sed -i 's#OPENSEARCH_PORT = 9200#OPENSEARCH_PORT = '$OPENSEARCH_PORT'#' /etc/timesketch/timesketch.conf
  fi

  # Set up the Redis connection
  if [ $REDIS_ADDRESS ] && [ $REDIS_PORT ]; then
    sed -i 's#UPLOAD_ENABLED = False#UPLOAD_ENABLED = True#' /etc/timesketch/timesketch.conf
    sed -i 's#^CELERY_BROKER_URL =.*#CELERY_BROKER_URL = \x27redis://'$REDIS_ADDRESS':'$REDIS_PORT'\x27#' /etc/timesketch/timesketch.conf
    sed -i 's#^CELERY_RESULT_BACKEND =.*#CELERY_RESULT_BACKEND = \x27redis://'$REDIS_ADDRESS':'$REDIS_PORT'\x27#' /etc/timesketch/timesketch.conf
  fi

  # Enable debug for the development server
  sed -i s/"DEBUG = False"/"DEBUG = True"/ /etc/timesketch/timesketch.conf

  # Enable index and sketch analyzers
  sed -i s/"ENABLE_INDEX_ANALYZERS = False"/"ENABLE_INDEX_ANALYZERS = True"/ /etc/timesketch/timesketch.conf
  sed -i s/"ENABLE_SKETCH_ANALYZERS = False"/"ENABLE_SKETCH_ANALYZERS = True"/ /etc/timesketch/timesketch.conf
  sed -i s/"ENABLE_EXPERIMENTAL_UI = False"/"ENABLE_EXPERIMENTAL_UI = True"/ /etc/timesketch/timesketch.conf

  # Disable CSRF checks for the development server
  echo "WTF_CSRF_ENABLED = False" >> /etc/timesketch/timesketch.conf
}

# Run the container the default way
if [ "$1" = 'timesketch' ]; then

  # Install dependencies and Timesketch in editable mode from volume
  echo "Installing Timesketch requirements..."
  if ! pip3 install -r /usr/local/src/timesketch/requirements.txt; then
    echo "Failed to install Timesketch requirements."
    exit 1
  fi

  echo "Installing Timesketch in editable mode..."
  if ! pip3 install -e /usr/local/src/timesketch/; then
    echo "Failed to install Timesketch in editable mode."
    exit 1
  fi

  echo "Installing API Client in editable mode..."
  if ! pip3 install -e /usr/local/src/timesketch/api_client/python; then
    echo "Failed to install API Client in editable mode."
    exit 1
  fi

  echo "Installing Importer Client in editable mode..."
  if ! pip3 install -e /usr/local/src/timesketch/importer_client/python; then
    echo "Failed to install Importer Client in editable mode."
    exit 1
  fi

  echo "Installing CLI Client in editable mode..."
  if ! pip3 install -e /usr/local/src/timesketch/cli_client/python; then
    echo "Failed to install CLI Client in editable mode."
    exit 1
  fi

  setup_config

  # Add web user
  tsctl create-user --password "${TIMESKETCH_USER}" "${TIMESKETCH_USER}"

  # Wrap up things
  echo "Timesketch development server is ready!"

  # Sleep forever to keep the container running
  sleep infinity
fi

# Allow tools like Tilt or tsdev.sh to refresh configuration
if [ "$1" = 'refresh-config' ]; then
  setup_config
  exit 0
fi

# Run a custom command on container start
exec "$@"
