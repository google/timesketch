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
"""Tests for the llm_starred_events_report feature."""

import json
from unittest import mock
import pandas as pd
from flask import current_app
from timesketch.lib.testlib import BaseTest
from timesketch.lib.llms.features.llm_starred_events_report import (
    LLMStarredEventsReportFeature,
)


# pylint: disable=protected-access
class TestLLMStarredEventsReportFeature(BaseTest):
    """Tests for the LLMStarredEventsReportFeature."""

    def setUp(self):
        """Set up the tests."""
        super().setUp()
        self.llm_feature = LLMStarredEventsReportFeature()
        current_app.config["PROMPT_LLM_STARRED_EVENTS_REPORT"] = (
            "./data/llm_starred_events_report/prompt.txt"
        )
        current_app.config["OPENSEARCH_HOSTS"] = [{"host": "localhost", "port": 9200}]

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
        current_app.config["PROMPT_LLM_STARRED_EVENTS_REPORT"] = (
            "/file_does_not_exist.txt"
        )
        with self.assertRaises(FileNotFoundError):
            self.llm_feature._get_prompt_text([])

    def test_get_prompt_text_missing_config(self):
        """Tests _get_prompt_text method with missing config."""
        del current_app.config["PROMPT_LLM_STARRED_EVENTS_REPORT"]
        with self.assertRaises(ValueError):
            self.llm_feature._get_prompt_text([])

    @mock.patch("timesketch.lib.utils.get_validated_indices")
    @mock.patch(
        "timesketch.lib.llms.features.llm_starred_events_report.OpenSearchDataStore"
    )
    def test_run_timesketch_query(self, _mock_datastore_class, mock_get_indices):
        """Tests _run_timesketch_query method."""
        mock_get_indices.return_value = ["test_index"], [1]
        result_df = pd.DataFrame([{"message": "Test event"}])
        mock_datastore_instance = _mock_datastore_class.return_value
        mock_datastore_instance.search.return_value = {"mock": "result"}
        with mock.patch(
            "timesketch.api.v1.export.query_results_to_dataframe",
            return_value=result_df,
        ) as mock_export:
            df = self.llm_feature._run_timesketch_query(
                self.sketch1,
                query_string="test query",
                query_filter={"filter": "test"},
            )
            self.assertEqual(len(df), 1)
            self.assertEqual(df.iloc[0]["message"], "Test event")
            mock_datastore_instance.search.assert_called_once()
            mock_export.assert_called_once()

    @mock.patch("timesketch.lib.utils.get_validated_indices")
    @mock.patch(
        "timesketch.lib.llms.features.llm_starred_events_report.OpenSearchDataStore"
    )
    def test_run_timesketch_query_no_indices(
        self, _mock_datastore_class, mock_get_indices
    ):
        """Tests _run_timesketch_query method with no valid indices."""
        mock_get_indices.return_value = [], []
        with self.assertRaises(ValueError):
            self.llm_feature._run_timesketch_query(self.sketch1)

    @mock.patch(
        "timesketch.lib.llms.features.llm_starred_events_report."
        "LLMStarredEventsReportFeature._run_timesketch_query"
    )
    @mock.patch(
        "timesketch.lib.llms.features.llm_starred_events_report."
        "LLMStarredEventsReportFeature._get_prompt_text"
    )
    def test_generate_prompt(self, mock_get_prompt, mock_run_query):
        """Tests generate_prompt method."""
        # Set up mocks
        mock_run_query.return_value = pd.DataFrame(
            [
                {"message": "Test event 1", "datetime": "2023-01-01T00:00:00"},
                {"message": "Test event 2", "datetime": "2023-01-01T00:00:01"},
                {"message": "Test event 1", "datetime": "2023-01-01T00:00:00"},
            ]
        )
        mock_get_prompt.return_value = "Test prompt"
        # Call the method
        prompt = self.llm_feature.generate_prompt(
            self.sketch1, form={"query": "test", "filter": {}}
        )
        # Verify the result
        self.assertEqual(prompt, "Test prompt")
        mock_run_query.assert_called_once()
        called_events = mock_get_prompt.call_args[0][0]
        self.assertEqual(len(called_events), 2)
        self.assertEqual(called_events[0]["message"], "Test event 1")
        self.assertEqual(called_events[1]["message"], "Test event 2")

    @mock.patch(
        "timesketch.lib.llms.features.llm_starred_events_report."
        "LLMStarredEventsReportFeature._run_timesketch_query"
    )
    def test_generate_prompt_no_events(self, mock_run_query):
        """Tests generate_prompt method with no events."""
        mock_run_query.return_value = pd.DataFrame()
        prompt = self.llm_feature.generate_prompt(
            self.sketch1, form={"query": "test", "filter": {}}
        )
        self.assertEqual(prompt, "No events to analyze for starred events report.")

    @mock.patch(
        "timesketch.lib.llms.features.llm_starred_events_report."
        "LLMStarredEventsReportFeature._run_timesketch_query"
    )
    @mock.patch("timesketch.lib.stories.utils.create_story")
    def test_process_response(self, mock_create_story, mock_run_query):
        """Tests process_response method."""
        mock_run_query.return_value = pd.DataFrame(
            [
                {"message": "Test event 1", "datetime": "2023-01-01T00:00:00"},
                {"message": "Test event 2", "datetime": "2023-01-01T00:00:01"},
            ]
        )
        mock_create_story.return_value = 123
        result = self.llm_feature.process_response(
            {"summary": "This is a test summary"},
            sketch=self.sketch1,
            form={"query": "test", "filter": {}},
        )
        self.assertEqual(result["summary"], "This is a test summary")
        self.assertEqual(result["summary_event_count"], 2)
        self.assertEqual(result["summary_unique_event_count"], 2)
        self.assertEqual(result["story_id"], 123)
        mock_create_story.assert_called_once()

    @mock.patch(
        "timesketch.lib.llms.features.llm_starred_events_report."
        "LLMStarredEventsReportFeature._run_timesketch_query"
    )
    @mock.patch("timesketch.lib.stories.utils.create_story")
    def test_caching_behavior(self, mock_create_story, mock_run_query):
        """Tests that the query is cached and not run twice."""
        mock_run_query.return_value = pd.DataFrame(
            [
                {"message": "Test event 1", "datetime": "2023-01-01T00:00:00"},
            ]
        )
        mock_create_story.return_value = 123

        # Call generate_prompt (first query run)
        self.llm_feature.generate_prompt(
            self.sketch1, form={"query": "test", "filter": {}}
        )

        # Call process_response (should use cache)
        self.llm_feature.process_response(
            {"summary": "Test summary"},
            sketch=self.sketch1,
            form={"query": "test", "filter": {}},
        )

        # Verify query was only run once
        self.assertEqual(mock_run_query.call_count, 1)

    def test_process_response_missing_params(self):
        """Tests process_response method with missing parameters."""
        with self.assertRaises(ValueError):
            self.llm_feature.process_response({"summary": "Test"})

    def test_process_response_invalid_response(self):
        """Tests process_response method with invalid response format."""
        with self.assertRaises(ValueError):
            self.llm_feature.process_response(
                "Not a dict",
                sketch=self.sketch1,
                form={"query": "test", "filter": {}},
            )
        with self.assertRaises(ValueError):
            self.llm_feature.process_response(
                {"not_summary": "Test"},
                sketch=self.sketch1,
                form={"query": "test", "filter": {}},
            )
