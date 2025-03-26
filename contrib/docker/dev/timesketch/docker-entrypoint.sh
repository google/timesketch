#!/usr/bin/env bash

# Function to send SIGTERM to all other processes except the current one
# Useful to properly stop the other processes to be started (gunicorn, tests, etc.)
# when the container is being stopped.
function kill_other_processes() {
  processes="$(pgrep -P 0 | grep -v "$$")"
  if [[ -n "${processes}" ]]; then
    for p in ${processes}; do
      kill -TERM "${p}"
    done
    while [[ -n "${processes}" ]]; do
      sleep 0.1
      processes="$(pgrep -P 0 | grep -v "$$")"
    done
  fi
  exit 0
}

. "/opt/venv/bin/activate"

# Run the container the default way
if [[ "$1" = 'timesketch' ]]; then
  CONF_DIR="/etc/timesketch"

  # Install Timesketch in editable mode from volume
  pip install -e /usr/local/src/timesketch/

  # Add web user
  tsctl create-user --password "${TIMESKETCH_PASSWORD}" "${TIMESKETCH_USER}"

  # Add Sigma rules
  git clone --depth 1 https://github.com/SigmaHQ/sigma /usr/local/src/sigma
  # for each line in sigma_rules.txt execute the command
  while IFS= read -r line; do
    if [ -f "${line}" ]; then
      tsctl import-sigma-rules "${line}" &
    else
      echo "Skipping non existing Sigma rule: ${line}"
    fi
  done < "${CONF_DIR}/sigma_rules.txt"
  wait

  # Wrap up things
  echo "Timesketch development server is ready!"

  # Sleep forever to keep the container running
  trap kill_other_processes SIGTERM
  sleep infinity &
  wait $!
fi

# Run a custom command on container start
exec "$@"
