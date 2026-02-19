# Copyright 2020 Google Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Script to run all end to end tests."""

import sys
import os

import time
from collections import Counter

from end_to_end_tests import manager as test_manager

manager = test_manager.EndToEndTestManager()
counter = Counter()


if __name__ == "__main__":
    # We had past cases where tests where not ran, this print ensures we can see
    # which ones run

    print("--- Registered Test Classes ---")

    # Mark the directory as safe for git (same logic as manager)
    try:
        project_root = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        import subprocess

        subprocess.run(
            ["git", "config", "--global", "--add", "safe.directory", project_root],
            capture_output=True,
            check=False,
        )
    except Exception:  # pylint: disable=broad-except
        pass

    for name, cls in manager.get_tests(sort_by_mtime=True):
        try:
            from datetime import datetime
            import inspect

            file_path = inspect.getfile(cls)
            # Use the same logic as the manager to show the time
            import subprocess

            mtime = 0
            try:
                res = subprocess.run(
                    ["git", "log", "-1", "--format=%at", "--", file_path],
                    capture_output=True,
                    text=True,
                    check=False,
                    cwd=os.path.dirname(file_path),
                )
                if res.returncode == 0 and res.stdout.strip():
                    mtime = int(res.stdout.strip())
            except Exception:  # pylint: disable=broad-except
                pass
            if not mtime:
                mtime = os.path.getmtime(file_path)

            time_str = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
            print(f"- {name} (last modified: {time_str})")
        except Exception:  # pylint: disable=broad-except
            print(f"- {name}")
    print("-------------------------------")

    # Sleep to make sure all containers are operational
    time.sleep(30)  # seconds

    for name, cls in manager.get_tests(sort_by_mtime=True):
        test_class = cls()
        # Prepare the test environment.
        test_class.setup()
        # Run all tests.
        run_counter = test_class.run_tests()
        counter["tests"] += run_counter["tests"]
        counter["errors"] += run_counter["errors"]

    successful_tests = counter["tests"] - counter["errors"]
    print(
        "{0:d} total tests: {1:d} successful and {2:d} failed".format(
            counter["tests"], successful_tests, counter["errors"]
        )
    )

    if counter["errors"]:
        sys.exit(1)
