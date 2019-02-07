#!/usr/bin/env python
"""Main entry point for running tests and linters."""
from __future__ import print_function
from __future__ import unicode_literals

import subprocess
import argparse
import time

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

def run_python_linter():
    subprocess.check_call(['pylint', 'timesketch'])
    subprocess.check_call(
        'PYTHONPATH=api_client/python/:$PYTHONPATH'
        + ' pylint timesketch_api_client',
        shell=True,
    )
    subprocess.check_call(['pylint', 'run_tests'])
    subprocess.check_call(['pylint', 'setup'])

def run_python(args):
    if not args.no_tests:
        run_python_tests(coverage=args.coverage)
    if not args.no_lint:
        run_python_linter()

def run_javascript_tests(coverage=False):
    if coverage:
        subprocess.check_call(['yarn', 'run', 'test:coverage'])
    else:
        subprocess.check_call(['yarn', 'run', 'test'])

def run_javascript_linter():
    subprocess.check_call(['yarn', 'run', 'lint'])

def run_javascript(args):
    if not args.no_tests:
        run_javascript_tests(coverage=args.coverage)
    if not args.no_lint:
        run_javascript_linter()

def run_selenium(args):
    # pylint: disable=unused-argument
    return NotImplemented

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
        description="Run Python and JS unit tests and linters."
        + " Skip selenium tests by default."
    )
    p.add_argument(
        '--py', action='store_true',
        help='Run Python tests and linters only.'
    )
    p.add_argument(
        '--js', action='store_true',
        help='Run Javascript tests and linters only.'
    )
    p.add_argument(
        '--selenium', action='store_true',
        help='Run end-to-end selenium tests only.'
    )
    p.add_argument(
        '--full', action='store_true',
        help='Run everything, including selenium.'
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
    start_time = time.time()
    args = parse_cli_args()

    if args.py:
        run_python(args)
    elif args.js:
        run_javascript(args)
    elif args.selenium:
        run_selenium(args)
    elif args.full:
        run_python(args)
        run_javascript(args)
        run_selenium(args)
    else:
        run_python(args)
        run_javascript(args)

    print('Done in %.2fs' % (time.time() - start_time))

main()
