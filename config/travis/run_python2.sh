#!/bin/bash
#
# Script to run Python 2 tests on Travis-CI.

# Exit on error.
set -e;

nosetests

python2 ./setup.py build
python2 ./setup.py sdist
python2 ./setup.py bdist
