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
counter: Counter[str] = Counter()


def resolve_tests_to_run(test_mgr, requested_arg=None):
    """Resolves registered E2E test classes to execute.

    Default invocations (`requested_arg=None`) omit opt-in suites registered
    with `exclude_from_list=True` (such as browser UI tests). Explicit CLI
    invocations (`requested_arg='ui_test'`) search all registered suites so
    opt-in tests can be executed on demand.

    Args:
        test_mgr (EndToEndTestManager): Manager class or instance.
        requested_arg (str): Optional comma-separated list of test names.

    Returns:
        list[tuple[str, type]]: Ordered `(test_name, test_class)` pairs.

    Raises:
        KeyError: If one or more explicitly requested test names do not exist.
    """
    if not requested_arg:
        return list(test_mgr.get_tests(sort_by_mtime=True, include_excluded=False))

    all_available = list(test_mgr.get_tests(sort_by_mtime=True, include_excluded=True))
    available_names = {name for name, _ in all_available}
    test_filters = [t.strip().lower() for t in requested_arg.split(",") if t.strip()]

    missing_tests = [t for t in test_filters if t not in available_names]
    if missing_tests:
        raise KeyError(", ".join(missing_tests))

    return [(name, cls) for name, cls in all_available if name in test_filters]


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
    import socket
    from urllib.parse import urlparse

    # Dynamically resolve target host and port from configuration settings
    server_url = os.environ.get("TIMESKETCH_SERVER_URL", "http://127.0.0.1")
    parsed = urlparse(server_url)
    host = parsed.hostname or "127.0.0.1"
    port = parsed.port or (80 if parsed.scheme == "http" else 443)

    # Print dynamic diagnostics variables for GitHub Actions debugging
    print("--- wait-for-it Diagnostics ---")
    print(f"TIMESKETCH_SERVER_URL: {os.environ.get('TIMESKETCH_SERVER_URL')}")
    print(f"Parsed Hostname: {host}")
    print(f"Parsed Port: {port}")
    try:
        resolved_ip = socket.gethostbyname(host)
        print(f"DNS Resolution: {host} -> {resolved_ip}")
    except socket.gaierror as e:
        print(f"DNS Resolution FAILED for {host}: {e}")
    print("--------------------------------")

    # Poll target server socket up to a safe maximum duration of 120 seconds
    start_time = time.monotonic()
    print(f"Waiting for Timesketch server to become active on {host}:{port}...")
    server_is_active = False

    while True:
        try:
            with socket.create_connection((host, port), timeout=2):
                print("Timesketch server is active! Starting E2E tests...")
                server_is_active = True
                break
        except OSError as e:
            elapsed = time.monotonic() - start_time
            print(
                f"[{elapsed:.1f}s] Connection to {host}:{port} failed: {e!r}. "
                "Retrying in 2 seconds..."
            )
            if elapsed >= 120:
                break
            time.sleep(2)

    if not server_is_active:
        print(f"Timeout: Server did not become active within 120s on {host}:{port}.")
        sys.exit(1)

    cli_test_filter = sys.argv[1] if len(sys.argv) > 1 else None
    try:
        tests_to_run = resolve_tests_to_run(manager, requested_arg=cli_test_filter)
    except KeyError as e:
        missing_str = e.args[0] if e.args else str(e)
        print(f"Error: The following requested tests do not exist: {missing_str}")
        print("Available test classes:")
        for name, _ in manager.get_tests(sort_by_mtime=True, include_excluded=True):
            print(f"  - {name}")
        sys.exit(1)

    for name, cls in tests_to_run:
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
