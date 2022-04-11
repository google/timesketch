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
"""Tests for the Timesketch API client"""
import unittest
import mock

from . import client
from . import graph
from . import test_lib


class GraphTest(unittest.TestCase):
    """Test Graph object."""

    @mock.patch("requests.Session", test_lib.mock_session)
    def setUp(self):
        """Setup test case."""
        self.api_client = client.TimesketchApi("http://127.0.0.1", "test", "test")
        self.sketch = self.api_client.get_sketch(1)

    def test_from_manual(self):
        """Test setting up a graph from manual."""
        data = {0: {1: {"weight": 1}}}
        graph_obj = graph.Graph(self.sketch)
        graph_obj.from_manual(data)
        self.assertEqual(graph_obj.graph.size(), 1)
