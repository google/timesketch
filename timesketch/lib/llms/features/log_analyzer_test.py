# Copyright 2025 Google Inc. All rights reserved.
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
"""Tests for the LogAnalyzer feature."""

import json
from unittest import mock

from timesketch.lib.llms.features import log_analyzer
from timesketch.lib.testlib import BaseTest


class TestLogAnalyzerFeature(BaseTest):
    """Tests for the LogAnalyzer feature."""

    @mock.patch("timesketch.lib.llms.features.log_analyzer.LogAnalyzer.datastore")
    def test_execute_with_summaries_format(self, mock_datastore):
        """
        Tests that the execute method correctly parses the new format
        with a 'summaries' key.
        """
        # Mock the LLM provider to return a response in the new format.
        mock_provider = mock.Mock()
        mock_provider.SUPPORTS_STREAMING = True
        mock_provider.NAME = "mock_provider"

        # The fake response from the LLM provider (raw JSON string).
        fake_response_content = {
            "summaries": [
                {
                    "log_records": [{"record_id": "test_id_1"}],
                    "annotations": [{"investigative_question": "test question"}],
                }
            ]
        }
        fake_response = json.dumps(fake_response_content)

        # Make the provider's streaming method return our fake response.
        mock_provider.generate_stream_from_logs.return_value = [fake_response]

        # Mock the sketch and datastore interactions.
        mock_sketch = mock.Mock()
        mock_sketch.id = 1
        mock_datastore.export_events_with_slicing.return_value = iter(
            [{"_id": "test_id_1"}]
        )

        # Instantiate the feature and mock its process_response method.
        feature = log_analyzer.LogAnalyzer()
        feature.process_response = mock.Mock()

        # Execute the feature.
        feature.execute(sketch=mock_sketch, form={}, llm_provider=mock_provider)

        # Assert that process_response was called.
        feature.process_response.assert_called_once()

        # Assert that it was called with the correctly extracted finding.
        _, call_kwargs = feature.process_response.call_args
        llm_response_arg = call_kwargs.get("llm_response")
        self.assertIsNotNone(llm_response_arg)
        self.assertIn("record_ids", llm_response_arg)
        self.assertEqual(llm_response_arg["record_ids"], ["test_id_1"])
        self.assertIn("annotations", llm_response_arg)
        self.assertEqual(
            llm_response_arg["annotations"][0]["investigative_question"],
            "test question",
        )
        self.assertEqual(call_kwargs.get("sketch"), mock_sketch)

    @mock.patch("timesketch.lib.llms.features.log_analyzer.LogAnalyzer.datastore")
    def test_execute_with_empty_findings(self, mock_datastore):
        """Tests the behavior when the LLM returns no findings."""
        mock_provider = mock.Mock()
        mock_provider.SUPPORTS_STREAMING = True
        mock_provider.NAME = "mock_provider"
        # Test with an empty summaries list.
        fake_response_content = {"summaries": []}
        fake_response = json.dumps(fake_response_content)
        mock_provider.generate_stream_from_logs.return_value = [fake_response]
        mock_sketch = mock.Mock()
        mock_sketch.id = 1
        mock_datastore.export_events_with_slicing.return_value = iter([{}])
        feature = log_analyzer.LogAnalyzer()
        feature.process_response = mock.Mock()

        result = feature.execute(
            sketch=mock_sketch, form={}, llm_provider=mock_provider
        )

        # Assert that process_response was NOT called.
        feature.process_response.assert_not_called()
        # Assert that a specific message is returned.
        self.assertIn(
            "did not identify any specific findings", result.get("message", "")
        )
        self.assertEqual(result.get("status"), "success")
