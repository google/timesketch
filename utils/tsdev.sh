#!/bin/bash

# Display a help message and exit
help(){
	echo
	echo "Usage: tsdev.sh [OPTIONS] COMMAND [FRONTEND]"
	echo
	echo "Run commands to manage resources on your Timesketch development docker container"
	echo
	echo "Options:"
	echo "  -h, --help        Display this help message"
	echo
	echo "Commands:"
	echo "  activate-history  Enable bash history persistence in the container"
	echo "  build-api-cli     Build and install API and CLI clients"
	echo "  celery            Start a celery worker"
	echo "  logs              Follow docker container logs "
	echo "  psql              Connect to the Timesketch PostgreSQL database in the dev container"
	echo "  reset-dev       Stop, remove, and restart the dev environment"
	echo "  restart-dev       Restart key Timesketch services (timesketch, worker, postgres, opensearch)"
	echo "  shell             Open a shell in the docker container"
	echo "  test              Execute run_tests.py --coverage"
	echo "  vue-build         Build the vue frontend. Default: 'frontend-ng'"
	echo "  vue-dev           Serve the vue frontend on port 5001. Default: 'frontend-ng'"
	echo "  vue-install-deps  Install vue frontend dependencies. Default: 'frontend-ng'"
	echo "  vue-test          Test the vue frontend. Default: 'frontend-ng'"
	echo "  web               Start the web frontend bound to port 5000"
 	echo "  postgres          Connect to the Timesketch postgres database."
	echo
	echo "Frontend:"
	echo "  frontend          The old v1 frontend (deprecated)."
	echo "  frontend-ng       The current v2 frontend (vue2)."
	echo "  frontend-v3       The future v3 frontend (vue3)."
	echo
	echo "Examples:"
	echo "  tsdev.sh vue-dev frontend-v3"
	echo "  tsdev.sh logs"
	echo "  tsdev.sh test"
	exit 0
}

# Display the help message if there is no command or if the help option is present
if [ $# -eq 0 ] || [ "$1" == "-h" ]  || [ "$1" == "--help" ]; then
	help
fi

# Use "sudo" for docker commands if sudoless docker is not enabled
# "docker version" will return "true" if sudoless docker is configured
if docker version >/dev/null 2>&1; then
	s=""
else
	s="sudo"
	sudo -v
fi

# Set variables required to execute commands
CONTAINER_ID="$($s docker container list --filter name='timesketch-dev' --quiet)"

# Central check for CONTAINER_ID.
# Exit if the timesketch-dev container is not found, unless the command
# is one that can operate without it (e.g., managing the docker-compose lifecycle or targeting another container).
if [ -z "$CONTAINER_ID" ]; then
  case "$1" in
    reset-dev|restart-dev|postgres)
      # These commands can proceed as they either manage the lifecycle or target a different container.
      ;;
    *)
      echo "Error: Timesketch development container (timesketch-dev) not found or not running." >&2
      echo "You might need to run 'tsdev.sh reset-dev', 'tsdev.sh restart-dev', or ensure Docker services are up." >&2
      exit 1
      ;;
  esac
fi

frontend="frontend-ng"

# Check if a second frontend argument is provided
if [ $# -eq 2 ]; then
  frontend="$2"
fi

# Run the provided command
case "$1" in
 	build-api-cli)
		# CLI client
		$s docker exec --workdir '/usr/local/src/timesketch/cli_client/python' --interactive --tty $CONTAINER_ID python3 setup.py build
		$s docker exec --workdir '/usr/local/src/timesketch/cli_client/python' --interactive --tty $CONTAINER_ID python3 setup.py install
		# API client
		$s docker exec --workdir '/usr/local/src/timesketch/api_client/python' --interactive --tty $CONTAINER_ID python3 setup.py build
		$s docker exec --workdir '/usr/local/src/timesketch/api_client/python' --interactive --tty $CONTAINER_ID python3 setup.py install
		;;
 	celery)
		$s docker exec --interactive --tty $CONTAINER_ID celery --app timesketch.lib.tasks worker --loglevel=info
		;;
	logs)
		$s docker logs --follow $CONTAINER_ID
		;;
	shell)
		$s docker exec --interactive --tty $CONTAINER_ID /bin/bash
		;;
	test)
		$s docker exec --workdir /usr/local/src/timesketch --interactive --tty $CONTAINER_ID python3 run_tests.py --coverage
		;;
	vue-build)
		$s docker exec --interactive --tty $CONTAINER_ID yarn run --cwd=/usr/local/src/timesketch/timesketch/$frontend build
		;;
	vue-dev)
		$s docker exec --interactive --tty $CONTAINER_ID yarn run --cwd=/usr/local/src/timesketch/timesketch/$frontend $(if [ "$frontend" == "frontend-v3" ]; then echo "dev"; else echo "serve"; fi)
		;;
	vue-install-deps)
		$s docker exec --interactive --tty $CONTAINER_ID yarn install --cwd=/usr/local/src/timesketch/timesketch/$frontend
		;;
	vue-test)
		$s docker exec --interactive --tty $CONTAINER_ID yarn run --cwd=/usr/local/src/timesketch/timesketch/$frontend test
		;;
	web)
		$s docker exec --interactive --tty $CONTAINER_ID gunicorn --reload --bind 0.0.0.0:5000 --log-level debug --capture-output --timeout 600 --workers 4 timesketch.wsgi:application
		;;
  	postgres)
		$s docker exec --interactive --tty postgres bash -c "psql -U timesketch -d timesketch"
		;;
	activate-history)
		HISTORY_FILE_PATH="/usr/local/src/timesketch/private/.bash_history"
		HISTORY_DIR_IN_CONTAINER="/usr/local/src/timesketch/private"
		# Assuming the primary user in the dev container is root.
		# Adjust if a different user's .bashrc should be targeted (e.g., /home/user/.bashrc).
		BASHRC_PATH_IN_CONTAINER="/root/.bashrc"
		BASH_HISTORY_MARKER_START="# TIMESKETCH_BASH_HISTORY_CONFIG_START"
		BASH_HISTORY_MARKER_END="# TIMESKETCH_BASH_HISTORY_CONFIG_END"

		echo "Attempting to activate persistent bash history in the container..."

		echo "Ensuring history directory ($HISTORY_DIR_IN_CONTAINER) exists in the container..."
		# Create the directory if it doesn't exist.
		# The `docker exec` for mkdir doesn't need -i or -t.
		if ! $s docker exec "$CONTAINER_ID" mkdir -p "$HISTORY_DIR_IN_CONTAINER"; then
			echo "Error: Failed to create or ensure history directory $HISTORY_DIR_IN_CONTAINER in the container." >&2
			echo "Please check permissions or create it manually within the container and then re-run this command." >&2
			exit 1 # Exit if we can't create the directory
		else
			echo "Bash history file not found. Attempting to set up directory..."
			# Use mkdir -p to ensure the directory exists and avoid error if it's already there.
			$s docker exec "$CONTAINER_ID" mkdir -p "$HISTORY_DIR"
			if $s docker exec "$CONTAINER_ID" test -d "$HISTORY_DIR"; then
				echo "Directory $HISTORY_DIR created (or already existed)."
			else
				echo "History file $HISTORY_FILE_PATH ensured."
			fi

			echo "Updating bash history configuration in $BASHRC_PATH_IN_CONTAINER..."

			# Prepare the new content block.
			# The `\` before `${PROMPT_COMMAND...}` ensures that `printf` outputs a literal `$`
			# which `echo` then processes, resulting in the desired `${...}` in the final file.
			CONFIG_CONTENT=$(printf "%s\n" \
				"" \
				"$BASH_HISTORY_MARKER_START" \
				"export HISTFILE=\"$HISTORY_FILE_PATH\"  # Path to the history file" \
				"export HISTSIZE=10000                 # Number of commands to keep in memory" \
				"export HISTFILESIZE=20000             # Max number of commands in the history file" \
				"shopt -s histappend                  # Append to history file, don't overwrite" \
				"$BASH_HISTORY_MARKER_END" \
			)

			# Append the new configuration block. tee -a will create .bashrc if it doesn't exist.
			if echo "$CONFIG_CONTENT" | $s docker exec -i "$CONTAINER_ID" bash -c "tee -a \"$BASHRC_PATH_IN_CONTAINER\" > /dev/null"; then
				echo "Bash history configuration successfully updated in $BASHRC_PATH_IN_CONTAINER."
				echo "To activate, open a new shell in the container (e.g., 'tsdev.sh shell')"
				echo "or source the file in an existing shell: 'source $BASHRC_PATH_IN_CONTAINER'"
			else
				echo "Error: Failed to update bash history configuration in $BASHRC_PATH_IN_CONTAINER." >&2
			fi
		fi
		;;
	reset-dev)
		echo "Resetting the development environment..."
		echo "This will stop and remove existing dev containers, then start new ones."
		(cd docker/dev && $s docker-compose down && $s docker-compose up --pull always -d)
		echo "Reset complete. You might need to re-fetch the CONTAINER_ID if it changed."
		;;
	restart-dev)
		echo "Restarting the Timesketch development services (timesketch, worker, postgres, opensearch)..."
		(cd docker/dev && $s docker-compose restart timesketch worker postgres opensearch)
		;;
	psql)
		if ! $s docker exec -i -t "$CONTAINER_ID" bash -c "command -v psql > /dev/null 2>&1"; then
			echo "psql client not found in the container. Attempting to install postgresql-client..."
			# Run apt-get update and install postgresql-client non-interactively (-y).
			if $s docker exec -i -t "$CONTAINER_ID" bash -c "apt-get update && apt-get install -y postgresql-client"; then
				echo "postgresql-client installed successfully."
			else
				echo "Error: Failed to install postgresql-client in the container." >&2
				echo "Please install it manually inside the container (e.g., 'tsdev.sh shell' then 'apt-get update && apt-get install postgresql-client') and try again." >&2
				exit 1 # Exit if installation fails
			fi
		fi
		echo "Opening psql prompt in the container..."
		$s docker exec -i -t "$CONTAINER_ID" bash -c "PGPASSWORD=password psql -h postgres -U timesketch -d timesketch"
		;;
	*)
		echo \""$1"\" is not a valid command.; help
esac
