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

    # Find the git root (same logic as manager)
    git_root = None
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        while current_dir != os.path.dirname(current_dir):
            if os.path.exists(os.path.join(current_dir, ".git")):
                git_root = current_dir
                break
            current_dir = os.path.dirname(current_dir)

        if git_root:
            import subprocess
            import shutil

            git_path = shutil.which("git")
            print(f"Debug: git_root={git_root}, git_path={git_path}")

            subprocess.run(
                ["git", "config", "--global", "--add", "safe.directory", git_root],
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
            print(f"Debug: name={name}, file_path={file_path}")
            mtime = 0

            if git_root:
                import subprocess

                try:
                    rel_path = os.path.relpath(file_path, git_root)
                    cmd = ["git", "log", "-1", "--format=%at", "--", rel_path]
                    res = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        check=False,
                        cwd=git_root,
                    )
                    if res.returncode == 0 and res.stdout.strip():
                        mtime = int(res.stdout.strip())
                    elif res.returncode != 0:
                        print(
                            f"Debug: Git failed for {name} ({rel_path}): {res.stderr.strip()}"
                        )
                        print(f"Debug: Command was: {' '.join(cmd)}")
                except Exception as e:  # pylint: disable=broad-except
                    print(f"Debug: Exception for {name}: {str(e)}")
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
