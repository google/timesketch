#!/usr/bin/env python
"""Main entry point for running tests."""
import subprocess


def run_python_tests():
    subprocess.check_call(
        "python3 -m pytest timesketch/ api_client/",
        shell=True,
    )


def main():
    run_python_tests()


main()
