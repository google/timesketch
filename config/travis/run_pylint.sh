#!/bin/bash
#
# Script to run pylint on Travis-CI.

# Exit on error.
set -e;

pylint --version
echo "BRANCH: $TRAVIS_BRANCH"
env
for FILE in `git diff --name-only master | grep \.py$`;
do
	echo "Checking: ${FILE}";
	pylint --rcfile=.pylintrc ${FILE};
done
