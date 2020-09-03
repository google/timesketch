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

import time
import unittest
import os
import inspect
import traceback
from collections import Counter

from timesketch_api_client.client import TimesketchApi

# Default values based on Docker config.
TEST_DATA_DIR = '/usr/local/src/timesketch/end_to_end_tests/test_data'
HOST_URI = 'http://127.0.0.1'
USERNAME = 'test'
PASSWORD = 'test'


class BaseEndToEndTest(object):
    """Base class for end to end tests.

    Attributes:
        name: Test name
        client: Instance of an API client
        sketch: Instance of Sketch object
        assertions: Instance of unittest.TestCase
    """

    NAME = 'name'

    def __init__(self):
        """Initialize the analyzer object."""
        self.name = self.NAME
        self.client = TimesketchApi(
            host_uri=HOST_URI, username=USERNAME, password=PASSWORD)
        self.sketch = self.client.create_sketch(name=self.name)
        self.assertions = unittest.TestCase()
        self._counter = Counter()
        print('*** {0:s} ***'.format(self.name))

    def import_timeline(self, filename):
        file_path = os.path.join(TEST_DATA_DIR, filename)
        print('Importing: {0:s}'.format(file_path))

        # TODO: Replace this with the import client
        timeline = self.sketch.upload(
            timeline_name=file_path, file_path=file_path)

        # Poll the timeline status and wait for it to be ready
        while True:
            _ = timeline.lazyload_data(refresh_cache=True)
            status = timeline.status
            if status == 'ready':
                break
            time.sleep(5)

    def _get_test_methods(self):
        for name, func in inspect.getmembers(self, predicate=inspect.ismethod):
            if name.startswith('test_'):
                yield name, func

    def run_tests(self):
        for test_name, test_func in self._get_test_methods():
            self._counter['tests'] += 1
            print('Running test: {0:s} ...'.format(
                test_name), end="", flush=True)
            try:
                test_func()
            except Exception:  # pylint: disable=broad-except
                print(traceback.format_exc())
                self._counter['errors'] += 1
                continue
            print('[OK]')
        return self._counter
