#!/usr/bin/env python
"""Main entry point for running tests and linters."""
from __future__ import print_function
from __future__ import unicode_literals

import subprocess
import argparse


def run_python_tests(coverage=False):
    try:
        if coverage:
            subprocess.check_call(
                'nosetests --with-coverage'
                + ' --cover-package=timesketch_api_client,timesketch'
                + ' api_client/python/timesketch_api_client/ timesketch/',
                shell=True,
            )
        else:
            subprocess.check_call(['nosetests'])
    finally:
        subprocess.check_call(['rm', '-f', '.coverage'])


def run_python(args):
    if not args.no_tests:
        run_python_tests(coverage=args.coverage)

    if not args.no_lint:
        subprocess.check_call(['./config/travis/run_pylint.sh', '--coverage'])


def parse_cli_args(args=None):
    """Parse command-line arguments to this script.

    Args:
        args: List of cli arguments not including program name

    Returns:
        Instance of argparse.Namespace with the following boolean attributes:
        py, js, selenium, full, no_lint, no_tests, coverage

    Raises:
        SystemExit if arguments are invalid or --help is present.
    """
    p = argparse.ArgumentParser(
        description="Run Python unit tests and linters."
    )
    p.add_argument(
        '--no-lint', action='store_true',
        help='Skip all linters.'
    )
    p.add_argument(
        '--no-tests', action='store_true',
        help='Skip tests, run only linters.'
    )
    p.add_argument(
        '--coverage', action='store_true',
        help='Print code coverage report.'
    )
    return p.parse_args(args)


def main():
    args = parse_cli_args()
    run_python(args)


main()
