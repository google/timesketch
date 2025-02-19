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
	echo "  build-api-cli     Build and install API and CLI clients"
	echo "  celery            Start a celery worker"
	echo "  logs              Follow docker container logs "
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
CONTAINER_ID="$($s docker container list --filter name='timesketch' --quiet)"
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
	*)
		echo \""$1"\" is not a valid command.; help
esac
