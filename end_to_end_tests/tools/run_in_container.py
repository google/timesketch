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

import logging
import os
import sys
import time
from collections import Counter
from datetime import datetime

# Configure logging
LOG_FORMAT = "%(asctime)s %(levelname)s %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)


# Ensure the latest source code is used by adding the project root to sys.path
# This must happen before importing end_to_end_tests
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# pylint: disable=wrong-import-position
from end_to_end_tests import manager as test_manager

# pylint: enable=wrong-import-position

manager = test_manager.EndToEndTestManager()
counter = Counter()


if __name__ == "__main__":
    # We had past cases where tests where not ran, this print ensures we can see
    # which ones run

    print("--- Registered Test Classes ---")

    git_root = manager.get_git_root()
    for name, cls in manager.get_tests(sort_by_mtime=True):
        mtime = manager.get_last_modified(cls, git_root=git_root)
        time_str = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
        print(f"- {name} (last modified: {time_str})")

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
