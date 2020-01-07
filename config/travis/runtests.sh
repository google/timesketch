#!/bin/bash
#
# Script to run tests on Travis-CI.

# Exit on error.
set -e;

if test -n "${UBUNTU_VERSION}"; then
	CONTAINER_NAME="ubuntu${UBUNTU_VERSION}";
	CONTAINER_OPTIONS="-e LANG=en_US.UTF-8";

	if test "${TARGET}" = "pylint"; then
		TEST_COMMAND="./config/travis/run_pylint.sh";
	elif test ${TRAVIS_PYTHON_VERSION} = "2.7"; then
		TEST_COMMAND="./config/travis/run_python2.sh";
	else
		TEST_COMMAND="./config/travis/run_python3.sh";
	fi

	# Note that exec options need to be defined before the container name.
	docker exec ${CONTAINER_OPTIONS} ${CONTAINER_NAME} sh -c "cd timesketch && ${TEST_COMMAND}";

elif test "${TRAVIS_OS_NAME}" = "linux"; then
	python3 ./run_tests.py
fi
