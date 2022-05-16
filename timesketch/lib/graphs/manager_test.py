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
"""Tests for graph manager."""

from timesketch.lib.testlib import BaseTest
from timesketch.lib.graphs import manager


class MockGraph:
    """Mock graph class."""

    NAME = "MockGraph"
    DISPLAY_NAME = "MockGraph"


class TestGraphManager(BaseTest):
    """Tests for the functionality of the manager module."""

    manager.GraphManager.clear_registration()
    manager.GraphManager.register_graph(MockGraph)

    def test_get_graphs(self):
        """Test to get graph class objects."""
        graphs = manager.GraphManager.get_graphs()
        graph_list = list(graphs)
        first_graph_tuple = graph_list[0]
        graph_name, graph_class = first_graph_tuple
        self.assertIsInstance(graph_list, list)
        self.assertIsInstance(first_graph_tuple, tuple)
        self.assertEqual(graph_class, MockGraph)
        self.assertEqual(graph_name, "mockgraph")

    def test_get_graph(self):
        """Test to get graph class from registry."""
        graph_class = manager.GraphManager.get_graph("mockgraph")
        self.assertEqual(graph_class, MockGraph)
        self.assertRaises(KeyError, manager.GraphManager.get_graph, "no_such_graph")

    def test_register_graph(self):
        """Test so we raise KeyError when graph is already registered."""
        self.assertRaises(KeyError, manager.GraphManager.register_graph, MockGraph)
