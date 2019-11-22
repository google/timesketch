# Copyright 2017 Google Inc. All rights reserved.
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
"""Tests for the Timesketch API client"""
from __future__ import unicode_literals

import unittest
import mock

from . import client
from . import sketch as sketch_lib
from . import test_lib


class TimesketchApiTest(unittest.TestCase):
    """Test TimesketchApi"""

    @mock.patch('requests.Session', test_lib.mock_session)
    def setUp(self):
        """Setup test case."""
        self.api_client = client.TimesketchApi(
            'http://127.0.0.1', 'test', 'test')

    def test_fetch_resource_data(self):
        """Test fetch resource."""
        response = self.api_client.fetch_resource_data('sketches/')
        self.assertIsInstance(response, dict)

    # TODO: Add test for create_sketch()

    def test_get_sketch(self):
        """Test to get a sketch."""
        sketch = self.api_client.get_sketch(1)
        self.assertIsInstance(sketch, sketch_lib.Sketch)
        self.assertEqual(sketch.id, 1)
        self.assertEqual(sketch.name, 'test')
        self.assertEqual(sketch.description, 'test')

    def test_get_sketches(self):
        """Test to get a list of sketches."""
        sketches = self.api_client.list_sketches()
        self.assertIsInstance(sketches, list)
        self.assertEqual(len(sketches), 1)
        self.assertIsInstance(sketches[0], sketch_lib.Sketch)
