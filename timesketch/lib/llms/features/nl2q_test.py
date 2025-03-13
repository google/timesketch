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
"""Tests for the nl2q feature."""

from unittest import mock
import pandas as pd
from flask import current_app
from timesketch.lib.testlib import BaseTest
from timesketch.lib.llms.features.nl2q import Nl2qFeature


# pylint: disable=protected-access
class TestNl2qFeature(BaseTest):
    """Tests for the Nl2qFeature."""

    def setUp(self):
        """Set up the tests."""
        super().setUp()
        self.nl2q_feature = Nl2qFeature()
        current_app.config["PROMPT_NL2Q"] = "./tests/test_data/nl2q/test_prompt_nl2q"
        current_app.config["EXAMPLES_NL2Q"] = (
            "./tests/test_data/nl2q/test_examples_nl2q"
        )

    @mock.patch("timesketch.lib.llms.features.nl2q.utils.run_aggregator")
    def test_sketch_data_types(self, mock_aggregator):
        """Test _sketch_data_types method."""
        mock_AggregationResult = mock.MagicMock()
        mock_AggregationResult.values = [
            {"data_type": "test:data_type:1"},
            {"data_type": "test:data_type:2"},
        ]
        mock_aggregator.return_value = (mock_AggregationResult, {})

        data_types = self.nl2q_feature._sketch_data_types(self.sketch1)

        self.assertEqual(data_types, "test:data_type:1,test:data_type:2")
        mock_aggregator.assert_called_once_with(
            self.sketch1.id, "field_bucket", {"field": "data_type", "limit": "1000"}
        )

    @mock.patch("timesketch.lib.llms.features.nl2q.utils.load_csv_file")
    def test_data_types_descriptions(self, mock_load_csv):
        """Test _data_types_descriptions method."""
        mock_df = pd.DataFrame(
            {
                "data_type": [
                    "test:data_type:1",
                    "test:data_type:1",
                    "test:data_type:2",
                ],
                "field": ["field_test_1", "field_test_2", "field_test_3"],
                "type": ["text", "text", "text"],
                "description": ["desc1", "desc2", "desc3"],
            }
        )
        mock_load_csv.return_value = mock_df

        descriptions = self.nl2q_feature._data_types_descriptions(
            "test:data_type:1,test:data_type:2"
        )

        self.assertIn(
            '* "test:data_type:1" -> "field_test_1", "field_test_2"', descriptions
        )
        self.assertIn('* "test:data_type:2" -> "field_test_3"', descriptions)

    @mock.patch("timesketch.lib.llms.features.nl2q.Nl2qFeature._sketch_data_types")
    @mock.patch(
        "timesketch.lib.llms.features.nl2q.Nl2qFeature._data_types_descriptions"
    )
    def test_build_prompt(self, mock_data_types_desc, mock_sketch_data_types):
        """Test _build_prompt method."""
        mock_sketch_data_types.return_value = "test:data_type:1,test:data_type:2"
        mock_data_types_desc.return_value = (
            '* "test:data_type:1" -> "field_test_1", "field_test_2"\n'
            '* "test:data_type:2" -> "field_test_3"'
        )

        prompt_content = (
            "Examples:\n{examples}\nTypes:\n{data_types}\nQuestion:\n{question}"
        )
        examples_content = "example 1\n\nexample 2"

        m = mock.mock_open()
        m.side_effect = [
            mock.mock_open(read_data=prompt_content).return_value,
            mock.mock_open(read_data=examples_content).return_value,
        ]

        with mock.patch("builtins.open", m):
            prompt = self.nl2q_feature._build_prompt("What happened?", self.sketch1)

        self.assertIn("Examples:", prompt)
        self.assertIn("example 1", prompt)
        self.assertIn("example 2", prompt)
        self.assertIn("Types:", prompt)
        self.assertIn('* "test:data_type:1" -> "field_test_1", "field_test_2"', prompt)
        self.assertIn('* "test:data_type:2" -> "field_test_3"', prompt)
        self.assertIn("Question:", prompt)
        self.assertIn("What happened?", prompt)

    @mock.patch("timesketch.lib.llms.features.nl2q.Nl2qFeature._build_prompt")
    def test_generate_prompt(self, mock_build_prompt):
        """Test generate_prompt method."""
        mock_build_prompt.return_value = "Test prompt"

        prompt = self.nl2q_feature.generate_prompt(
            self.sketch1, form={"question": "What happened?"}
        )

        self.assertEqual(prompt, "Test prompt")
        mock_build_prompt.assert_called_once_with("What happened?", self.sketch1)

    def test_generate_prompt_missing_question(self):
        """Test generate_prompt method with missing question."""
        with self.assertRaises(ValueError):
            self.nl2q_feature.generate_prompt(self.sketch1, form={})

        with self.assertRaises(ValueError):
            self.nl2q_feature.generate_prompt(self.sketch1)

    def test_process_response(self):
        """Test process_response method."""
        result = self.nl2q_feature.process_response("test query")
        self.assertEqual(result["query_string"], "test query")
        self.assertIsNone(result["error"])

        result = self.nl2q_feature.process_response(" \t`test query`\n ")
        self.assertEqual(result["query_string"], "test query")

        result = self.nl2q_feature.process_response("```test query``")
        self.assertEqual(result["query_string"], "test query")

        result = self.nl2q_feature.process_response(" \t```test query```\n ")
        self.assertEqual(result["query_string"], "test query")

        with self.assertRaises(ValueError):
            self.nl2q_feature.process_response(123)
