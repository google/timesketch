# Copyright 2021 Google Inc. All rights reserved.
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
"""Tests for search command."""

import unittest
import mock
import pandas as pd

from click.testing import CliRunner

from timesketch_api_client import test_lib as api_test_lib
from .. import test_lib
from .search import saved_searches_group
from .search import search_group


EXPECTED_OUTPUT = """query_string: test:"foobar"
query_filter: {
  "size": 10000,
  "terminate_after": 10000,
  "indices": "_all",
  "order": "asc",
  "chips": []
}
"""


class SearchTest(unittest.TestCase):
    """Test Search."""

    @mock.patch("requests.Session", api_test_lib.mock_session)
    def setUp(self):
        """Setup test case."""
        self.ctx = test_lib.get_cli_context()

    def test_list_saved_searches(self):
        """Test to list saved searches."""
        runner = CliRunner()
        result = runner.invoke(saved_searches_group, ["list"], obj=self.ctx)
        assert result.output == "1 test\n2 more test\n"

    def test_describe_saved_search(self):
        """Test to get details for a saved search."""
        runner = CliRunner()
        result = runner.invoke(saved_searches_group, ["describe", "1"], obj=self.ctx)
        assert result.output == EXPECTED_OUTPUT

    def test_describe_non_existent_saved_search(self):
        """Test describing a non-existent saved search."""
        runner = CliRunner()
        # MockSketch.get_saved_search returns None for IDs not in its list (e.g., 999)
        result = runner.invoke(saved_searches_group, ["describe", "999"], obj=self.ctx)
        self.assertEqual(result.exit_code, 0)  # Command exits 0 even if not found
        self.assertIn("No such saved search", result.output)

    @mock.patch("timesketch_cli_client.commands.search.search.Search")
    def test_search_describe_flag(self, MockSearchClient):
        """Test the 'search --describe' command."""
        # MockSearchClient is the mock for the Search class.
        # MockSearchClient.return_value is the mock instance returned by Search().
        mock_search_instance = MockSearchClient.return_value

        # Configure the mock instance's attributes that are read by the command
        mock_search_instance.query_string = "test query"
        mock_search_instance.query_filter = {
            "chips": [{"type": "label", "value": "test"}]
        }
        mock_search_instance.return_fields = "message,timestamp"

        runner = CliRunner()
        result = runner.invoke(
            search_group,
            [
                "--query",
                "test query",
                "--label",
                "test",
                "--return-fields",
                "message,timestamp",
                "--describe",
            ],
            obj=self.ctx,
        )
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Query string: test query", result.output)
        self.assertIn("Return fields: message,timestamp", result.output)
        self.assertIn('"type": "label"', result.output)
        self.assertIn('"value": "test"', result.output)

    @mock.patch("timesketch_cli_client.commands.search.search.Search")
    def test_search_with_results_text_output(self, MockSearchClient):
        """Test the 'search' command with text output."""
        # MockSearchClient is the mock for the Search class.
        # MockSearchClient.return_value is the mock instance returned by Search().
        mock_search_instance = MockSearchClient.return_value
        mock_df = pd.DataFrame(
            {
                "message": ["event1", "event2"],
                "timestamp": [1234567890123, 4567890123456],
                "datetime": ["2023-01-01T00:00:00", "2023-01-02T00:00:00"],
            }
        )
        mock_search_instance.to_pandas.return_value = mock_df
        mock_search_instance.return_fields = (
            "message,timestamp,datetime"  # Explicitly set for clarity
        )
        self.ctx.output_format_from_flag = "text"
        runner = CliRunner()
        result = runner.invoke(search_group, ["--query", "some query"], obj=self.ctx)

        self.assertEqual(result.exit_code, 0)
        # Normalize whitespace for robust comparison
        normalized_output = " ".join(result.output.split())
        self.assertIn("message timestamp datetime", normalized_output)
        self.assertIn("event1 1234567890123 2023-01-01T00:00:00", normalized_output)
        self.assertIn("event2 4567890123456 2023-01-02T00:00:00", normalized_output)
        mock_search_instance.to_pandas.assert_called_once()
