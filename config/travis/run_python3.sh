#!/bin/bash
#
# Script to run Python 3 tests on Travis-CI.

# Exit on error.
set -e;

nosetests3

python3 ./setup.py build
python3 ./setup.py sdist
python3 ./setup.py bdist
