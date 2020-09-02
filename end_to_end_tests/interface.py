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

from timesketch_api_client.client import TimesketchApi

TEST_DATA_DIR = '/usr/local/src/timesketch/end_to_end_tests/test_data'
HOST_URI = 'http://127.0.0.1'
USERNAME = 'test'
PASSWORD = 'test'


class BaseEndToEndTest(object):
    """Base class for end to end tests.

    Attributes:
        name: Test name.
        client: Instance of an API client.
        sketch: Instance of Sketch object.
    """

    NAME = 'name'

    def __init__(self):
        """Initialize the analyzer object."""
        self.name = self.NAME
        self.client = TimesketchApi(
            host_uri=HOST_URI, username=USERNAME, password=PASSWORD)
        self.sketch = self.client.create_sketch(name=self.name)
        self.assertions = unittest.TestCase()

    def import_timeline(self, filename, wait=True):
        file_path = os.path.join(TEST_DATA_DIR, filename)
        print('Importing: {}'.format(file_path))
        timeline = self.sketch.upload(
            timeline_name=file_path, file_path=file_path)

        if wait:
            while True:
                _ = timeline.lazyload_data(refresh_cache=True)
                status = timeline.status
                if status == 'ready':
                    break
                time.sleep(5)

    def run_wrapper(self):
        """A wrapper method to run the test."""
        print('Running tests from: {}'.format(self.name))
        self.run()

    def run(self):
        """Entry point for the analyzer."""
        raise NotImplementedError
