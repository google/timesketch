#!/usr/bin/env python
"""Main entry point for running tests."""

import os
import subprocess


def run_python_tests():
    # To run pytest in parallel, add "-n" and "auto" (or a specific number
    # of workers like "4") to the list of arguments.
    env = os.environ.copy()
    env["TIMESKETCH_SETTINGS"] = "timesketch.lib.testlib.TestConfig"
    subprocess.check_call(
        [
            "python3",
            "-m",
            "pytest",
            "-n",
            "auto",
            "timesketch/",
            "api_client/",
            "cli_client/",
            "importer_client/",
        ],
        env=env,
    )


def main():
    run_python_tests()


main()
