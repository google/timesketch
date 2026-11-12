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
from timesketch.lib.llms.providers import interface
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
            "findings": [
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
        self.assertNotIn("log_records", llm_response_arg)
        self.assertEqual(call_kwargs.get("sketch"), mock_sketch)

    @mock.patch("timesketch.lib.llms.features.log_analyzer.LogAnalyzer.datastore")
    def test_execute_with_empty_findings(self, mock_datastore):
        """Tests the behavior when the LLM returns no findings."""
        mock_provider = mock.Mock()
        mock_provider.SUPPORTS_STREAMING = True
        mock_provider.NAME = "mock_provider"
        # Test with an empty findings list.
        fake_response_content = {"findings": []}
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

    @mock.patch("timesketch.lib.llms.features.log_analyzer.LogAnalyzer.datastore")
    def test_execute_passes_prompt_to_provider(self, mock_datastore):
        """Tests that the custom prompt is passed to the LLM provider."""
        mock_provider = mock.Mock()
        mock_provider.SUPPORTS_STREAMING = True
        mock_provider.NAME = "mock_provider"
        # Test with an empty findings list to avoid processing logic
        fake_response_content = {"findings": []}
        fake_response = json.dumps(fake_response_content)
        mock_provider.generate_stream_from_logs.return_value = [fake_response]

        mock_sketch = mock.Mock()
        mock_sketch.id = 1
        mock_datastore.export_events_with_slicing.return_value = iter([{}])

        feature = log_analyzer.LogAnalyzer()
        feature.process_response = mock.Mock()

        custom_prompt = "Find evil stuff"
        feature.execute(
            sketch=mock_sketch,
            form={},
            llm_provider=mock_provider,
            prompt=custom_prompt,
        )

        mock_provider.generate_stream_from_logs.assert_called_once()
        _, call_kwargs = mock_provider.generate_stream_from_logs.call_args
        self.assertEqual(call_kwargs.get("prompt"), custom_prompt)

    @mock.patch(
        "timesketch.lib.llms.features.log_analyzer.InvestigativeQuestionConclusion"
    )
    @mock.patch("timesketch.lib.llms.features.log_analyzer.InvestigativeQuestion")
    @mock.patch("timesketch.lib.llms.features.log_analyzer.db_session")
    @mock.patch("timesketch.lib.llms.features.log_analyzer.Event")
    def test_process_response_accepts_timesketch_priority_names(
        self, mock_event, mock_db_session, mock_question_cls, mock_conclusion_cls
    ):
        """Timesketch priority names are applied, not silently dropped."""
        mock_event.get_or_create.return_value = mock.Mock(searchindex_id=1)
        mock_conclusion_cls.query.filter_by.return_value.first.return_value = None

        for priority in ("low", "medium", "high"):
            question = mock.Mock()
            question.display_name = ""
            question.get_labels = []
            mock_question_cls.get_or_create.return_value = question

            feature = log_analyzer.LogAnalyzer()
            result = feature.process_response(
                llm_response={
                    "record_ids": ["test_id_1"],
                    "annotations": [
                        {
                            "investigative_question": "test question",
                            "conclusions": ["test conclusion"],
                            "priority": priority,
                        }
                    ],
                },
                sketch=mock.Mock(id=1, active_timelines=[]),
            )

            self.assertEqual(result.get("status"), "success")
            question.add_label.assert_called_once_with(f"__ts_priority_{priority}")
            self.assertEqual(feature._errors_encountered, [])

    @mock.patch(
        "timesketch.lib.llms.features.log_analyzer.InvestigativeQuestionConclusion"
    )
    @mock.patch("timesketch.lib.llms.features.log_analyzer.InvestigativeQuestion")
    @mock.patch("timesketch.lib.llms.features.log_analyzer.db_session")
    @mock.patch("timesketch.lib.llms.features.log_analyzer.Event")
    def test_process_response_reports_unknown_priority(
        self, mock_event, mock_db_session, mock_question_cls, mock_conclusion_cls
    ):
        """A priority we have no mapping for is still reported."""
        mock_event.get_or_create.return_value = mock.Mock(searchindex_id=1)
        mock_conclusion_cls.query.filter_by.return_value.first.return_value = None
        question = mock.Mock()
        question.display_name = ""
        question.get_labels = []
        mock_question_cls.get_or_create.return_value = question

        feature = log_analyzer.LogAnalyzer()
        feature.process_response(
            llm_response={
                "record_ids": ["test_id_1"],
                "annotations": [
                    {
                        "investigative_question": "test question",
                        "conclusions": ["test conclusion"],
                        "priority": "defcon-1",
                    }
                ],
            },
            sketch=mock.Mock(id=1, active_timelines=[]),
        )

        question.add_label.assert_not_called()
        self.assertIn(
            "Unknown priority value: defcon-1", feature._errors_encountered
        )

    def test_execute_rejects_provider_without_streaming_support(self):
        """A provider that cannot stream gets the readable error, not AttributeError."""

        class NoStreamingProvider(interface.LLMProvider):
            NAME = "no_streaming_provider"

        feature = log_analyzer.LogAnalyzer()
        with self.assertRaises(ValueError) as error:
            feature.execute(
                sketch=mock.Mock(id=1),
                form={},
                llm_provider=NoStreamingProvider({}),
            )
        self.assertIn("does not support streaming", str(error.exception))
