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
	echo "  rebuild-dev       Stop, remove, and rebuild the dev environment (docker-compose down && docker-compose up --build -d)"
	echo "  restart-dev       Restart the dev environment (docker-compose restart timesketch)"
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
    rebuild-dev|restart-dev|postgres)
      # These commands can proceed as they either manage the lifecycle or target a different container.
      ;;
    *)
      echo "Error: Timesketch development container (timesketch-dev) not found or not running." >&2
      echo "You might need to run 'tsdev.sh rebuild-dev', 'tsdev.sh restart-dev', or ensure Docker services are up." >&2
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
		$s docker exec --interactive --tty $CONTAINER_ID gunicorn --reload --bind 0.0.0.0:5000 --log-level debug --capture-output --timeout 600 timesketch.wsgi:application
		;;
  	postgres)
		$s docker exec --interactive --tty postgres bash -c "psql -U timesketch -d timesketch"
		;;
	activate-history)
		HISTORY_FILE_PATH="/usr/local/src/timesketch/private/.bash_history"
		HISTORY_DIR="/usr/local/src/timesketch/private"

		echo "Checking bash history status in the container..."
		# Check if the history file already exists as an indicator
		if $s docker exec "$CONTAINER_ID" test -f "$HISTORY_FILE_PATH"; then
			echo "Bash history file ($HISTORY_FILE_PATH) already exists in the container."
			echo "History may already be active if HISTFILE is set correctly in new shells (e.g., via /root/.bashrc or ~/.bashrc)."
		else
			echo "Bash history file not found. Attempting to set up directory..."
			# Use mkdir -p to ensure the directory exists and avoid error if it's already there.
			$s docker exec --interactive --tty "$CONTAINER_ID" mkdir -p "$HISTORY_DIR"
			if $s docker exec "$CONTAINER_ID" test -d "$HISTORY_DIR"; then
				echo "Directory $HISTORY_DIR created (or already existed)."
			else
				echo "Failed to create directory $HISTORY_DIR in the container."
			fi
			echo "To fully activate persistent bash history for new shells in the container:"
			echo "1. Add the following lines to /root/.bashrc (or ~/.bashrc for non-root users) inside the container:"
			echo "   export HISTFILE=$HISTORY_FILE_PATH"
			echo "   export HISTSIZE=10000"
			echo "   export HISTFILESIZE=20000"
			echo "   shopt -s histappend"
			echo "   PROMPT_COMMAND='history -a; history -n; \$PROMPT_COMMAND'"
			echo "2. Source the .bashrc file (e.g., 'source /root/.bashrc') or start a new shell session in the container."
		fi
		;;
	rebuild-dev)
		echo "Rebuilding the development environment..."
		echo "This will stop and remove existing dev containers, then build and start new ones."
		(cd "$COMPOSE_PROJECT_DIR" && $s docker-compose down && $s docker-compose up --build -d)
		echo "Rebuild complete. You might need to re-fetch the CONTAINER_ID if it changed."
		;;
	restart-dev)
		echo "Restarting the Timesketch development services (timesketch, worker, postgres, opensearch)..."
		# Assuming 'timesketch' is the main service name in docker-compose.yml
		# You might want to list all relevant services: timesketch worker postgres opensearch
		(cd "$COMPOSE_PROJECT_DIR" && $s docker-compose restart timesketch worker postgres opensearch)
		;;
	*)
		echo \""$1"\" is not a valid command.; help
esac
