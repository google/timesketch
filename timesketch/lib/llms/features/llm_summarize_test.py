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
"""Tests for the llm_summarize feature."""

import json
from unittest import mock
import pandas as pd
from flask import current_app
from timesketch.lib.testlib import BaseTest
from timesketch.lib.testlib import MockDataStore
from timesketch.lib.llms.features.llm_summarize import LLMSummarizeFeature


# pylint: disable=protected-access
class TestLLMSummarizeFeature(BaseTest):
    """Tests for the LLMSummarizeFeature."""

    def setUp(self):
        """Set up the tests."""
        super().setUp()
        self.llm_feature = LLMSummarizeFeature()
        current_app.config["PROMPT_LLM_SUMMARIZATION"] = (
            "./data/llm_summarize/prompt.txt"
        )
        self.datastore = MockDataStore("noserver", 4711)

    @mock.patch(
        "builtins.open", mock.mock_open(read_data="Analyze these events: <EVENTS_JSON>")
    )
    def test_get_prompt_text(self):
        """Tests _get_prompt_text method."""
        events_dict = [{"message": "Test event 1"}, {"message": "Test event 2"}]
        prompt = self.llm_feature._get_prompt_text(events_dict)

        self.assertEqual(prompt, f"Analyze these events: {json.dumps(events_dict)}")

    @mock.patch(
        "builtins.open",
        mock.mock_open(read_data="Analyze these events without placeholder"),
    )
    def test_get_prompt_text_missing_placeholder(self):
        """Tests _get_prompt_text method with missing placeholder."""
        events_dict = [{"message": "Test event"}]
        with self.assertRaises(ValueError) as context:
            self.llm_feature._get_prompt_text(events_dict)
        self.assertIn(
            "missing the required <EVENTS_JSON> placeholder", str(context.exception)
        )

    def test_get_prompt_text_missing_file(self):
        """Tests _get_prompt_text method with missing file."""
        current_app.config["PROMPT_LLM_SUMMARIZATION"] = "/file_does_not_exist.txt"

        with self.assertRaises(FileNotFoundError):
            self.llm_feature._get_prompt_text([])

    def test_get_prompt_text_missing_config(self):
        """Tests _get_prompt_text method with missing config."""
        del current_app.config["PROMPT_LLM_SUMMARIZATION"]

        with self.assertRaises(ValueError):
            self.llm_feature._get_prompt_text([])

    @mock.patch("timesketch.lib.utils.get_validated_indices")
    def test_run_timesketch_query(self, mock_get_indices):
        """Tests _run_timesketch_query method."""
        mock_get_indices.return_value = ["test_index"], [1]
        result_df = pd.DataFrame([{"message": "Test event"}])

        with mock.patch.object(
            self.datastore, "search", return_value={"mock": "result"}
        ) as mock_search:
            with mock.patch(
                "timesketch.api.v1.export.query_results_to_dataframe",
                return_value=result_df,
            ) as mock_export:
                df = self.llm_feature._run_timesketch_query(
                    self.sketch1,
                    query_string="test query",
                    query_filter={"filter": "test"},
                    datastore=self.datastore,
                )

                self.assertEqual(len(df), 1)
                self.assertEqual(df.iloc[0]["message"], "Test event")
                mock_search.assert_called_once()
                mock_export.assert_called_once()

    def test_run_timesketch_query_no_datastore(self):
        """Tests _run_timesketch_query method with no datastore."""
        with self.assertRaises(ValueError):
            self.llm_feature._run_timesketch_query(self.sketch1)

    @mock.patch("timesketch.lib.utils.get_validated_indices")
    def test_run_timesketch_query_no_indices(self, mock_get_indices):
        """Tests _run_timesketch_query method with no valid indices."""
        mock_get_indices.return_value = [], []

        with self.assertRaises(ValueError):
            self.llm_feature._run_timesketch_query(
                self.sketch1, datastore=self.datastore
            )

    @mock.patch(
        "timesketch.lib.llms.features.llm_summarize."
        "LLMSummarizeFeature._run_timesketch_query"
    )
    @mock.patch(
        "timesketch.lib.llms.features.llm_summarize."
        "LLMSummarizeFeature._get_prompt_text"
    )
    def test_generate_prompt(self, mock_get_prompt, mock_run_query):
        """Tests generate_prompt method."""
        # Set up mocks
        mock_run_query.return_value = pd.DataFrame(
            [
                {"message": "Test event 1"},
                {"message": "Test event 2"},
                {"message": "Test event 1"},  # Add duplicate event on purpose
            ]
        )
        mock_get_prompt.return_value = "Test prompt"

        # Call the method
        prompt = self.llm_feature.generate_prompt(
            self.sketch1, form={"query": "test", "filter": {}}, datastore=self.datastore
        )

        # Verify the result
        self.assertEqual(prompt, "Test prompt")
        mock_run_query.assert_called_once()
        called_events = mock_get_prompt.call_args[0][0]
        self.assertEqual(len(called_events), 2)
        self.assertEqual(called_events[0]["message"], "Test event 1")
        self.assertEqual(called_events[1]["message"], "Test event 2")

    @mock.patch(
        "timesketch.lib.llms.features.llm_summarize.LLMSummarizeFeature."
        "_run_timesketch_query"
    )
    def test_generate_prompt_no_events(self, mock_run_query):
        """Tests generate_prompt method with no events."""
        mock_run_query.return_value = pd.DataFrame()

        prompt = self.llm_feature.generate_prompt(
            self.sketch1, form={"query": "test", "filter": {}}, datastore=self.datastore
        )

        self.assertEqual(prompt, "No events to summarize based on the current filter.")

    def test_generate_prompt_missing_form(self):
        """Tests generate_prompt method with missing form."""
        with self.assertRaises(ValueError):
            self.llm_feature.generate_prompt(self.sketch1, datastore=self.datastore)

    def test_process_response(self):
        """Tests process_response method."""
        self.llm_feature._total_events_count = 3
        self.llm_feature._unique_events_count = 2

        result = self.llm_feature.process_response(
            {"summary": "This is a test summary"},
            sketch_id=1,
        )

        self.assertEqual(result["response"], "This is a test summary")
        self.assertEqual(result["summary_event_count"], 3)
        self.assertEqual(result["summary_unique_event_count"], 2)

    def test_process_response_missing_params(self):
        """Tests process_response method with missing parameters."""
        with self.assertRaises(ValueError):
            self.llm_feature.process_response({"summary": "Test"})

    def test_process_response_invalid_response(self):
        """Tests process_response method with invalid response format."""
        with self.assertRaises(ValueError):
            self.llm_feature.process_response(
                "Not a dict",
                sketch_id=1,
            )
        with self.assertRaises(ValueError):
            self.llm_feature.process_response(
                {"not_summary": "Test"},
                sketch_id=1,
            )
