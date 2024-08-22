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
from . import scenario as scenario_lib


class SketchTest(unittest.TestCase):
    """Test Sketch object."""

    @mock.patch("requests.Session", test_lib.mock_session)
    def setUp(self):
        """Setup test case."""
        self.api_client = client.TimesketchApi("http://127.0.0.1", "test", "test")
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

    def test_get_event(self):
        """Test to get event data."""
        event_data = self.sketch.get_event(event_id="test_event", index_id="test_index")
        self.assertIsInstance(event_data, dict)
        self.assertTrue("meta" in event_data)
        self.assertTrue("comments" in event_data["meta"])

    def test_add_event_attributes(self):
        """Test to add event attributes."""
        attrs = [{"attr_name": "foo", "attr_value": "bar"}]
        events = [
            {"_id": "1", "_type": "_doc", "_index": "1", "attributes": attrs},
            {"_id": "2", "_type": "_doc", "_index": "1", "attributes": attrs},
        ]

        expected_response = {
            "meta": {
                "attributes_added": 2,
                "chunks_per_index": {"1": 1},
                "error_count": 0,
                "errors": [],
                "events_modified": 2,
            },
            "objects": [],
        }

        response = self.sketch.add_event_attributes(events)
        self.assertEqual(response, expected_response)

    def test_add_event_attributes_invalid(self):
        """Confirm an exception is raised when events isn't a list."""
        events = {"_id": "1", "_type": "_doc", "index": "1", "attributes": []}
        with self.assertRaisesRegex(ValueError, "Events need to be a list."):
            self.sketch.add_event_attributes(events)

    def test_list_aggregations(self):
        """Test the Sketch list_aggregations method."""
        aggregations = self.sketch.list_aggregations()
        self.assertEqual(len(aggregations), 2)
        self.assertEqual(aggregations[0].name, "ip barchart")
        self.assertEqual(
            aggregations[0].description, "Aggregating values of a particular field"
        )
        self.assertEqual(aggregations[1].name, "domain table")
        self.assertEqual(
            aggregations[1].description, "Aggregating values of a particular field"
        )

    def test_list_scenarios(self):
        """Test the Sketch list_scenarios method."""
        scenarios = self.sketch.list_scenarios()
        self.assertIsInstance(scenarios, list)
        self.assertEqual(len(scenarios), 1)
        scenario = scenarios[0]
        self.assertIsInstance(scenario, scenario_lib.Scenario)
        self.assertEqual(scenario.id, 1)
        self.assertEqual(scenario.name, "Test Scenario")
        self.assertEqual(scenario.uuid, "1234a567-b89c-123d-e45f-g6h7ijk8l910")
        self.assertEqual(scenario.dfiq_identifier, "S0001")
        self.assertEqual(scenario.description, "Scenario description!")

    def test_add_scenario(self):
        """Test the Sketch add_scenario method."""
        scenario = self.sketch.add_scenario(dfiq_id="S0001")
        self.assertIsInstance(scenario, scenario_lib.Scenario)
        self.assertEqual(scenario.id, 1)
        self.assertEqual(scenario.name, "Test Scenario")
        self.assertEqual(scenario.uuid, "1234a567-b89c-123d-e45f-g6h7ijk8l910")
        self.assertEqual(scenario.dfiq_identifier, "S0001")
        self.assertEqual(scenario.description, "Scenario description!")

    def test_list_questions(self):
        """Test the Sketch list_questions method."""
        questions = self.sketch.list_questions()
        self.assertIsInstance(questions, list)
        self.assertEqual(len(questions), 1)
        question = questions[0]
        self.assertIsInstance(question, scenario_lib.Question)
        self.assertEqual(question.id, 1)
        self.assertEqual(question.name, "Test Question?")
        self.assertEqual(question.uuid, "1234a567-b89c-123d-e45f-g6h7ijk8l910")
        self.assertEqual(question.dfiq_identifier, "Q0001")
        self.assertEqual(question.description, "Test Question Description")

    def test_add_question(self):
        """Test the Sketch add_question method."""
        question = self.sketch.add_question(dfiq_id="Q0001")
        self.assertIsInstance(question, scenario_lib.Question)
        self.assertEqual(question.id, 1)
        self.assertEqual(question.name, "Test Question?")
        self.assertEqual(question.uuid, "1234a567-b89c-123d-e45f-g6h7ijk8l910")
        self.assertEqual(question.dfiq_identifier, "Q0001")
        self.assertEqual(question.description, "Test Question Description")
