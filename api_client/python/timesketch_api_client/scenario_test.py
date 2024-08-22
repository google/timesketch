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
        scenario = self.sketch.list_questions()[0]
        self.assertIsInstance(scenario.to_dict(), dict)


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
