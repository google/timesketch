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
"""Interface for end-to-end tests."""

import time
import unittest
import os
import inspect
import traceback
import collections

from timesketch_api_client import client as api_client
from timesketch_import_client import importer

# Default values based on Docker config.
TEST_DATA_DIR = '/usr/local/src/timesketch/end_to_end_tests/test_data'
HOST_URI = 'http://127.0.0.1'
USERNAME = 'test'
PASSWORD = 'test'


class BaseEndToEndTest(object):
    """Base class for end to end tests.

    Attributes:
        api: Instance of an API client
        sketch: Instance of Sketch object
        assertions: Instance of unittest.TestCase
    """

    NAME = 'name'

    def __init__(self):
        """Initialize the end-to-end test object."""
        self.api = api_client.TimesketchApi(
            host_uri=HOST_URI, username=USERNAME, password=PASSWORD)
        self.sketch = self.api.create_sketch(name=self.NAME)
        self.assertions = unittest.TestCase()
        self._counter = collections.Counter()

    def import_timeline(self, filename):
        """Import a Plaso, CSV or JSONL file.

        Args:
            filename (str): Filename of the file to be imported.

        Raises:
            TimeoutError if import takes too long.
        """
        file_path = os.path.join(TEST_DATA_DIR, filename)
        print('Importing: {0:s}'.format(file_path))

        # Import using the importer client.
        with importer.ImportStreamer() as streamer:
            streamer.set_sketch(self.sketch)
            streamer.set_timeline_name(file_path)
            streamer.add_file(file_path)
            timeline = streamer.timeline

        # Poll the timeline status and wait for the timeline to be ready
        max_time_seconds = 600  # Timeout after 10min
        sleep_time_seconds = 5  # Sleep between API calls
        max_retries = max_time_seconds / sleep_time_seconds
        retry_count = 0
        while True:
            if retry_count >= max_retries:
                raise TimeoutError
            _ = timeline.lazyload_data(refresh_cache=True)
            status = timeline.status
            # TODO: Do something with other statuses? (e.g. failed)
            if status == 'ready':
                break
            retry_count += 1
            time.sleep(sleep_time_seconds)

    def _get_test_methods(self):
        """Inspect class and list all methods that matches the criteria.

        Yields:
            Function name and bound method.
        """
        for name, func in inspect.getmembers(self, predicate=inspect.ismethod):
            if name.startswith('test_'):
                yield name, func

    def setup(self):
        """Setup function that is run before any tests.

        This is a good place to import any data that is needed.
        """
        return NotImplementedError

    def run_tests(self):
        """Run all test functions from the class.

        Returns:
            Counter of number of tests and errors.
        """
        print('*** {0:s} ***'.format(self.NAME))
        for test_name, test_func in self._get_test_methods():
            self._counter['tests'] += 1
            print('Running test: {0:s} ...'.format(
                test_name), end='', flush=True)
            try:
                test_func()
            except Exception:  # pylint: disable=broad-except
                # TODO: Change to logging module instead of prints
                print(traceback.format_exc())
                self._counter['errors'] += 1
                continue
            print('[OK]')
        return self._counter
