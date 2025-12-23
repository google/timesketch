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

TEST_DATA_DIR = "./tests/test_data/dfiq/"


class TestDFIQ(BaseTest):
    """Tests for the DFIQ support library."""

    def __init__(self, *args, **kwargs):
        """Initializes the test class."""
        super().__init__(*args, **kwargs)
        self.dfiq = dfiq.DFIQCatalog(TEST_DATA_DIR)

    def test_dfiq_components(self):
        """Test that the DFIQ components are loaded correctly."""
        self.assertIsInstance(self.dfiq.components, dict)
        self.assertEqual(len(self.dfiq.components), 3)
        scenario = self.dfiq.get_by_id("S1001")
        facet = self.dfiq.get_by_id("F1001")
        question = self.dfiq.get_by_id("Q1001")
        self.assertIsInstance(scenario, dfiq.ScenarioTemplate)
        self.assertIsInstance(facet, dfiq.FacetTemplate)
        self.assertIsInstance(question, dfiq.QuestionTemplate)
        self.assertEqual(len(scenario.facets), 1)
        self.assertEqual(len(facet.questions), 1)

    def test_dfiq_component_no_uuid(self):
        """Test that a DFIQ component without a UUID is not loaded."""
        yaml_string_no_uuid = """
name: Test Scenario No UUID
description: Test Scenario
type: scenario
id: S1002
tags:
  - test
dfiq_version: 1.1.0
"""
        with self.assertLogs("timesketch.lib.dfiq", level="ERROR") as cm:
            dfiq_instance = dfiq.DFIQCatalog.from_yaml_list([yaml_string_no_uuid])
            self.assertEqual(len(dfiq_instance.components), 0)
            self.assertIn(
                "DFIQ object 'S1002' ('Test Scenario No UUID') is missing a UUID.",
                cm.output[0],
            )

    def test_dfiq_graph(self):
        """Test that the DFIQ graph is loaded correctly."""
        self.assertEqual(len(self.dfiq.graph.nodes), 3)
        self.assertEqual(len(self.dfiq.graph.edges), 2)
        uuid_to_id_map = {v: k for k, v in self.dfiq.id_to_uuid_map.items()}
        for node in self.dfiq.graph.nodes:
            self.assertIsInstance(node, str)
        graph_node_ids = sorted(
            [uuid_to_id_map.get(node_uuid) for node_uuid in self.dfiq.graph.nodes]
        )
        expected_nodes = sorted(["S1001", "F1001", "Q1001"])
        self.assertEqual(graph_node_ids, expected_nodes)
        for edge in self.dfiq.graph.edges:
            self.assertIsInstance(edge, tuple)
        graph_edge_ids = sorted(
            [
                (uuid_to_id_map.get(u), uuid_to_id_map.get(v))
                for u, v in self.dfiq.graph.edges
            ]
        )
        expected_edges = sorted([("S1001", "F1001"), ("F1001", "Q1001")])
        self.assertEqual(graph_edge_ids, expected_edges)
