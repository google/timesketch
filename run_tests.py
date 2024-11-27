#!/usr/bin/env python
"""Main entry point for running tests."""
import subprocess


def run_python_tests():
    subprocess.check_call(
        ["pipenv", "run", "pytest", "timesketch/", "api_client/"]
    )


def main():
    run_python_tests()


main()
