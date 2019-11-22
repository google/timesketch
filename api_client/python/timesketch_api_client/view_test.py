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
from . import view as view_lib
from . import test_lib


class ViewTest(unittest.TestCase):
    """Test View object."""

    @mock.patch('requests.Session', test_lib.mock_session)
    def setUp(self):
        """Setup test case."""
        self.api_client = client.TimesketchApi(
            'http://127.0.0.1', 'test', 'test')
        self.sketch = self.api_client.get_sketch(1)

    def test_view(self):
        """Test View object."""
        view = self.sketch.list_views()[0]
        self.assertIsInstance(view, view_lib.View)
        self.assertEqual(view.id, 1)
        self.assertEqual(view.name, 'test')
