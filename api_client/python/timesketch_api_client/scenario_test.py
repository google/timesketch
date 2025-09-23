# Copyright 2024 Google Inc. All rights reserved.
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
from . import test_lib
from . import scenario as scenario_lib


class ScenarioTest(unittest.TestCase):
    """Test Scenario object."""

    @mock.patch("requests.Session", test_lib.mock_session)
    def setUp(self):
        """Setup test case."""
        self.api_client = client.TimesketchApi("http://127.0.0.1", "test", "test")
        self.sketch = self.api_client.get_sketch(1)

    def test_scenario_to_dict(self):
        """Test Scenario object to dict."""
        scenario = self.sketch.list_scenarios()[0]
        self.assertIsInstance(scenario.to_dict(), dict)

    def test_set_display_name(self):
        """Test setting the scenario display name."""
        scenario = self.sketch.list_scenarios()[0]

        updated_scenario_data = {
            "objects": [
                {
                    "id": 7,
                    "name": "Test Scenario",
                    "display_name": "New Scenario Name",
                    "description": "A test scenario",
                    "dfiq_identifier": "S0001",
                }
            ],
            "meta": {},
        }

        mock_response_updated = mock.Mock()
        mock_response_updated.status_code = 200
        mock_response_updated.json.return_value = updated_scenario_data

        with mock.patch.object(
            self.api_client.session, "get", return_value=mock_response_updated
        ) as mock_get:
            scenario.set_display_name("New Scenario Name")
            resource_url = f"http://127.0.0.1/api/v1/{scenario.resource_uri}"
            mock_get.assert_called_once_with(resource_url, params=None)

        self.assertEqual(scenario.display_name, "New Scenario Name")

    def test_list_facets(self):
        """Test listing facets for a scenario."""
        scenario = self.sketch.list_scenarios()[0]
        facets = scenario.list_facets()
        self.assertIsInstance(facets, list)
        self.assertEqual(len(facets), 1)
        self.assertEqual(facets[0]["name"], "Test Facet")


class ScenarioListTest(unittest.TestCase):
    """Test ScenarioList object."""

    @mock.patch("requests.Session", test_lib.mock_session)
    def setUp(self):
        """Setup test case."""
        self.api_client = client.TimesketchApi("http://127.0.0.1", "test", "test")

    def test_scenario_list(self):
        """Test ScenarioList object."""
        scenario_list = scenario_lib.getScenarioTemplateList(self.api_client)
        self.assertIsInstance(scenario_list, list)
        self.assertEqual(len(scenario_list), 2)
        self.assertEqual(scenario_list[0]["name"], "Test Scenario")
        self.assertEqual(scenario_list[1]["id"], "S0002")


class QuestionTest(unittest.TestCase):
    """Test Question object."""

    @mock.patch("requests.Session", test_lib.mock_session)
    def setUp(self):
        """Setup test case."""
        self.api_client = client.TimesketchApi("http://127.0.0.1", "test", "test")
        self.sketch = self.api_client.get_sketch(1)

    def test_question_to_dict(self):
        """Test Question object to dict."""
        question = self.sketch.list_questions()[0]
        self.assertIsInstance(question.to_dict(), dict)

    def test_question_update(self):
        """Test updating question attributes."""
        question = self.sketch.list_questions()[0]
        resource_url = f"http://127.0.0.1/api/v1/{question.resource_uri}"

        with mock.patch.object(self.api_client.session, "get") as mock_get:
            # --- Test updating the name ---
            updated_name_data = {
                "objects": [
                    {"name": "Updated Question Name?", "description": "A test question"}
                ]
            }
            mock_name_response = mock.Mock(status_code=200)
            mock_name_response.json.return_value = updated_name_data
            mock_get.return_value = mock_name_response

            question.set_name("Updated Question Name?")

            mock_get.assert_called_once_with(resource_url, params=None)
            self.assertEqual(question.name, "Updated Question Name?")
            mock_get.reset_mock()  # Reset the call counter for the next test

            # --- Test updating the description ---
            updated_desc_data = {
                "objects": [
                    {
                        "name": "Updated Question Name?",
                        "description": "Updated description.",
                    }
                ]
            }
            mock_desc_response = mock.Mock(status_code=200)
            mock_desc_response.json.return_value = updated_desc_data
            mock_get.return_value = mock_desc_response

            question.set_description("Updated description.")

            mock_get.assert_called_once_with(resource_url, params=None)
            self.assertEqual(question.description, "Updated description.")
            mock_get.reset_mock()

            # --- Test setting status and priority ---
            mock_get.return_value = mock_desc_response  # Re-use previous response
            question.set_status("verified")
            question.set_priority("__ts_priority_high")
            # Verify get was called twice more
            self.assertEqual(mock_get.call_count, 2)

    def test_question_conclusions(self):
        """Test adding and listing question conclusions."""
        question = self.sketch.list_questions()[0]
        question.add_conclusion("This is a conclusion.")
        conclusions = question.list_conclusions()
        self.assertIsInstance(conclusions, list)
        self.assertEqual(len(conclusions), 1)
        self.assertEqual(conclusions[0]["conclusion"], "This is a conclusion.")


class QuestionListTest(unittest.TestCase):
    """Test QuestionList object."""

    @mock.patch("requests.Session", test_lib.mock_session)
    def setUp(self):
        """Setup test case."""
        self.api_client = client.TimesketchApi("http://127.0.0.1", "test", "test")

    def test_question_list(self):
        """Test QuestionList object."""
        question_list = scenario_lib.getQuestionTemplateList(self.api_client)
        self.assertIsInstance(question_list, list)
        self.assertEqual(len(question_list), 2)
        self.assertEqual(question_list[0]["name"], "Test question?")
        self.assertEqual(question_list[1]["id"], "Q0002")
