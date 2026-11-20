# Copyright 2026 Google Inc. All rights reserved.
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
"""Tests for the Timesketch API client analyzer result object."""

import unittest
from unittest import mock

from . import analyzer
from . import client
from . import test_lib


class AnalyzerResultTest(unittest.TestCase):
    """Test AnalyzerResult object."""

    @mock.patch("requests.Session", test_lib.mock_session)
    def setUp(self):
        """Setup test case."""
        self.api_client = client.TimesketchApi("http://127.0.0.1", "test", "test")

    def test_analyzer_result_null_fields(self):
        """Test None API values fall back to default status messages."""
        mock_payload = {
            "objects": [
                [
                    {
                        "analysissession_id": 1,
                        "analyzer_name": None,
                        "result": None,
                        "log": None,
                        "parameters": "{}",
                        "status": [{"status": "STARTED", "updated_at": None}],
                        "timeline": {"id": 1, "name": "test"},
                    }
                ]
            ]
        }
        mock_response = mock.Mock(status_code=200)
        mock_response.json.return_value = mock_payload

        analyzer_result = analyzer.AnalyzerResult(
            timeline_id=1, session_id=1, sketch_id=1, api=self.api_client
        )
        with mock.patch.object(
            self.api_client.session, "get", return_value=mock_response
        ):
            self.assertEqual(analyzer_result.results, "[No Name] = No results yet.")
            self.assertEqual(
                analyzer_result.results_dict, {"No Name": ["No results yet."]}
            )
            self.assertEqual(analyzer_result.log, "[No Name] = No recorded logs.")
            self.assertEqual(analyzer_result.status, "[No Name] = STARTED")

    def test_analyzer_result_populated_fields(self):
        """Test populated analyzer session fields."""
        mock_payload = {
            "objects": [
                [
                    {
                        "analysissession_id": 2,
                        "analyzer_name": "domain",
                        "result": "Found 3 domains.",
                        "log": "Completed in 0.2s.",
                        "parameters": "{}",
                        "status": [
                            {
                                "status": "DONE",
                                "updated_at": "2026-06-25T12:00:00",
                            }
                        ],
                        "timeline": {"id": 1, "name": "test"},
                    }
                ]
            ]
        }
        mock_response = mock.Mock(status_code=200)
        mock_response.json.return_value = mock_payload

        analyzer_result = analyzer.AnalyzerResult(
            timeline_id=1, session_id=2, sketch_id=1, api=self.api_client
        )
        self.assertEqual(analyzer_result.id, 2)
        with mock.patch.object(
            self.api_client.session, "get", return_value=mock_response
        ):
            self.assertEqual(analyzer_result.results, "[domain] = Found 3 domains.")
            self.assertEqual(
                analyzer_result.results_dict,
                {"domain": ["Found 3 domains."]},
            )
            self.assertEqual(analyzer_result.log, "[domain] = Completed in 0.2s.")
            self.assertEqual(analyzer_result.status_dict, {"domain": ["DONE"]})


if __name__ == "__main__":
    unittest.main()
