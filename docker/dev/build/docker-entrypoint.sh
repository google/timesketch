#!/bin/bash

# Function to setup and refresh configuration
setup_config() {
  # Copy config files
  mkdir -p /etc/timesketch
  cp /usr/local/src/timesketch/data/timesketch.conf /etc/timesketch/

  # Use -f to ignore error if link already exists
  ln -sf /usr/local/src/timesketch/data/sigma /etc/timesketch/
  ln -sf /usr/local/src/timesketch/data/dfiq /etc/timesketch/
  ln -sf /usr/local/src/timesketch/data/nl2q /etc/timesketch/
  ln -sf /usr/local/src/timesketch/data/llm_summarize /etc/timesketch/
  ln -s /usr/local/src/timesketch/data/llm_starred_events_report /etc/timesketch/
  CONFIG_FILES=(
    "regex_features.yaml"
    "winevt_features.yaml"
    "tags.yaml"
    "intelligence_tag_metadata.yaml"
    "plaso.mappings"
    "generic.mappings"
    "ontology.yaml"
    "data_finder.yaml"
    "bigquery_matcher.yaml"
    "plaso_formatters.yaml"
    "context_links.yaml"
    "sigma_config.yaml"
  )
  for f in "${CONFIG_FILES[@]}"; do
    ln -sf "/usr/local/src/timesketch/data/$f" "/etc/timesketch/$f"
  done

  # Set SECRET_KEY in /etc/timesketch/timesketch.conf if it isn't already set
  # We generate a locally stored key on the first start that gets re-used for
  # later sessions. If you need a new key, just delete the ".dev_secret_key"
  # file in your project root dir and restart the container.
  KEY_FILE="/usr/local/src/timesketch/.dev_secret_key"

  if [ ! -f "$KEY_FILE" ]; then
    echo "Generating new persistent development secret key..."
    openssl rand -base64 32 > "$KEY_FILE"
  fi

  SECRET_KEY=$(cat "$KEY_FILE")
  if grep -q 'SECRET_KEY = "<KEY_GOES_HERE>"' /etc/timesketch/timesketch.conf; then
    # Use double quotes for the variable expansion to be safe
    sed -i 's#SECRET_KEY = "<KEY_GOES_HERE>"#SECRET_KEY = "'"$SECRET_KEY"'"#' /etc/timesketch/timesketch.conf
  fi

  # Set up the Postgres connection
  if [ "$POSTGRES_USER" ] && [ "$POSTGRES_PASSWORD" ] && [ "$POSTGRES_ADDRESS" ] && [ "$POSTGRES_PORT" ]; then
    sed -i 's#postgresql://<USERNAME>:<PASSWORD>@localhost#postgresql://'$POSTGRES_USER':'$POSTGRES_PASSWORD'@'$POSTGRES_ADDRESS':'$POSTGRES_PORT'#' /etc/timesketch/timesketch.conf
  fi

  # Set up the OpenSearch connection
  if [ "$OPENSEARCH_HOST" ] && [ "$OPENSEARCH_PORT" ]; then
    sed -i 's#OPENSEARCH_HOSTS = \[{"host": "opensearch", "port": 9200}\]#OPENSEARCH_HOSTS = [{"host": "'$OPENSEARCH_HOST'", "port": '$OPENSEARCH_PORT'}]#' /etc/timesketch/timesketch.conf
  fi

  # Set up the Redis connection
  if [ "$REDIS_ADDRESS" ] && [ "$REDIS_PORT" ]; then
    sed -i 's#^UPLOAD_ENABLED = False#UPLOAD_ENABLED = True#' /etc/timesketch/timesketch.conf
    sed -i 's#^CELERY_BROKER_URL =.*#CELERY_BROKER_URL = "redis://'$REDIS_ADDRESS':'$REDIS_PORT'"#' /etc/timesketch/timesketch.conf
    sed -i 's#^CELERY_RESULT_BACKEND =.*#CELERY_RESULT_BACKEND = "redis://'$REDIS_ADDRESS':'$REDIS_PORT'"#' /etc/timesketch/timesketch.conf
  fi

  # Enable debug for the development server
  sed -i 's/DEBUG = False/DEBUG = True/' /etc/timesketch/timesketch.conf

  # Enable index and sketch analyzers
  sed -i 's/ENABLE_INDEX_ANALYZERS = False/ENABLE_INDEX_ANALYZERS = True/' /etc/timesketch/timesketch.conf
  sed -i 's/ENABLE_SKETCH_ANALYZERS = False/ENABLE_SKETCH_ANALYZERS = True/' /etc/timesketch/timesketch.conf
  sed -i 's/ENABLE_EXPERIMENTAL_UI = False/ENABLE_EXPERIMENTAL_UI = True/' /etc/timesketch/timesketch.conf

  # Disable CSRF checks for the development server
  sed -i 's/^# WTF_CSRF_ENABLED = False.*/WTF_CSRF_ENABLED = False/' /etc/timesketch/timesketch.conf
}

# Run the container the default way
if [ "$1" = 'timesketch' ]; then

  echo "Installing Timesketch and clients in editable mode..."
  if ! pip3 install \
    -e /usr/local/src/timesketch/ \
    -e /usr/local/src/timesketch/api_client/python \
    -e /usr/local/src/timesketch/importer_client/python \
    -e /usr/local/src/timesketch/cli_client/python; then
    echo "Failed to install Timesketch and/or clients in editable mode."
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
