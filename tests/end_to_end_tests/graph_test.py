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
"""End to end tests of Timesketch graph functionality."""

from timesketch_api_client import graph

from . import interface
from . import manager


class GraphTest(interface.BaseEndToEndTest):
    """End to end tests for query functionality."""

    NAME = "graph_test"

    def setup(self):
        """Import test timeline."""
        self.import_timeline("evtx.plaso")

    def test_graph(self):
        """Test pulling graphs from the backend."""
        empty_list = self.sketch.list_graphs()

        self.assertions.assertEqual(empty_list, [])

        graph_obj = graph.Graph(self.sketch)
        graph_obj.from_plugin("winservice")
        self.assertions.assertEqual(graph_obj.graph.size(), 12)

        graph_obj.name = "foobar"
        graph_obj.description = "this is it"

        graph_obj.save()

        _ = self.sketch.lazyload_data(refresh_cache=True)
        graph_list = self.sketch.list_graphs()
        self.assertions.assertEqual(len(graph_list), 1)
        graph_saved = graph_list[0]
        self.assertions.assertEqual(graph_saved.graph.size(), 12)
        self.assertions.assertEqual(graph_saved.name, "foobar")
        self.assertions.assertEqual(graph_saved.description, "this is it")


manager.EndToEndTestManager.register_test(GraphTest)
