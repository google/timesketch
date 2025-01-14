# Copyright 2023 Google Inc. All rights reserved.
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
"""Tests for DFIQ."""

from timesketch.lib.testlib import BaseTest
from timesketch.lib import dfiq

TEST_DATA_DIR = "./test_data/dfiq/"


class TestDFIQ(BaseTest):
    """Tests for the DFIQ support library."""

    def __init__(self, *args, **kwargs):
        """Initializes the test class."""
        super().__init__(*args, **kwargs)
        self.dfiq = dfiq.DFIQ(TEST_DATA_DIR)

    def test_dfiq_components(self):
        """Test that the DFIQ components are loaded correctly."""
        self.assertIsInstance(self.dfiq.components, dict)
        self.assertEqual(len(self.dfiq.components), 3)
        self.assertIsInstance(self.dfiq.components.get("S1001"), dfiq.Scenario)
        self.assertIsInstance(self.dfiq.components.get("F1001"), dfiq.Facet)
        self.assertIsInstance(self.dfiq.components.get("Q1001"), dfiq.Question)
        self.assertEqual(len(self.dfiq.components.get("S1001").facets), 1)
        self.assertEqual(len(self.dfiq.components.get("F1001").questions), 1)

    def test_dfiq_graph(self):
        """Test that the DFIQ graph is loaded correctly."""
        self.assertEqual(len(self.dfiq.graph.nodes), 3)
        self.assertEqual(len(self.dfiq.graph.edges), 2)
        for node in self.dfiq.graph.nodes:
            self.assertIsInstance(node, str)
        expected_nodes = ["S1001", "F1001", "Q1001"]
        for idx, component_name in enumerate(expected_nodes):
            self.assertEqual(list(self.dfiq.graph.nodes)[idx], component_name)
        for edge in self.dfiq.graph.edges:
            self.assertIsInstance(edge, tuple)
        expected_edges = [("S1001", "F1001"), ("F1001", "Q1001")]
        for idx, edge in enumerate(expected_edges):
            self.assertEqual(list(self.dfiq.graph.edges)[idx], edge)
