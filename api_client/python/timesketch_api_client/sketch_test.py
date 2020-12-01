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
from . import search
from . import test_lib
from . import timeline as timeline_lib


class SketchTest(unittest.TestCase):
    """Test Sketch object."""

    @mock.patch('requests.Session', test_lib.mock_session)
    def setUp(self):
        """Setup test case."""
        self.api_client = client.TimesketchApi(
            'http://127.0.0.1', 'test', 'test')
        self.sketch = self.api_client.get_sketch(1)

    # TODO: Add test for upload()

    def test_get_searches(self):
        """Test to get a search."""
        searches = self.sketch.list_saved_searches()
        self.assertIsInstance(searches, list)
        self.assertEqual(len(searches), 2)
        self.assertIsInstance(searches[0], search.Search)

    def test_get_timelines(self):
        """Test to get a timeline."""
        timelines = self.sketch.list_timelines()
        self.assertIsInstance(timelines, list)
        self.assertEqual(len(timelines), 2)
        self.assertIsInstance(timelines[0], timeline_lib.Timeline)
