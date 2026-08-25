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
"""Tests for TimesketchLogStore."""

import unittest
from unittest import mock

import pandas as pd

from contrib.secgemini_byot import timesketch_logstore


# pylint: disable=protected-access
class TestTimesketchLogStore(unittest.TestCase):
    """Test TimesketchLogStore helper functions and query construction."""

    def test_escape_opensearch_query(self):
        """Test escaping reserved OpenSearch characters."""
        self.assertEqual(
            timesketch_logstore._escape_opensearch_query("foo:bar"),
            "foo\\:bar",
        )
        self.assertEqual(
            timesketch_logstore._escape_opensearch_query('log"type'),
            'log\\"type',
        )
        self.assertEqual(
            timesketch_logstore._escape_opensearch_query("a\\b"),
            "a\\\\b",
        )
        self.assertEqual(
            timesketch_logstore._escape_opensearch_query("log type"),
            "log\\ type",
        )

    @mock.patch("timesketch_api_client.search.Search")
    def test_search_logs_escaping(self, mock_search_cls):
        """Test that log_type and exclude_log_type are escaped in query string."""
        mock_sketch = mock.MagicMock()
        mock_api = mock.MagicMock()
        mock_api.get_sketch.return_value = mock_sketch

        mock_search_instance = mock.MagicMock()
        mock_search_instance.table = pd.DataFrame()
        mock_search_cls.return_value = mock_search_instance

        store = timesketch_logstore.TimesketchLogStore(mock_api, sketch_id=1)

        # Test single log_type and exclude_log_type as string with special chars
        store._search_logs_sync(
            log_type='syslog:"type"',
            limit=10,
            at_or_after=None,
            at_or_before=None,
            exclude_log_type='bad:"type"',
        )

        self.assertEqual(
            mock_search_instance.query_string,
            'data_type:"syslog\\:\\"type\\"" AND NOT data_type:"bad\\:\\"type\\""',
        )

        # Test exclude_log_type as iterable
        store._search_logs_sync(
            log_type=None,
            limit=10,
            at_or_after=None,
            at_or_before=None,
            exclude_log_type=["type1:a", 'type2"b'],
        )

        self.assertEqual(
            mock_search_instance.query_string,
            'NOT data_type:"type1\\:a" AND NOT data_type:"type2\\"b"',
        )

    @mock.patch("timesketch_api_client.search.Search")
    def test_search_logs_kwargs_forward_compatibility(self, mock_search_cls):
        """Test that unexpected kwargs do not raise TypeError."""
        mock_sketch = mock.MagicMock()
        mock_api = mock.MagicMock()
        mock_api.get_sketch.return_value = mock_sketch

        mock_search_instance = mock.MagicMock()
        mock_search_instance.table = pd.DataFrame()
        mock_search_cls.return_value = mock_search_instance

        store = timesketch_logstore.TimesketchLogStore(mock_api, sketch_id=1)

        # Pass unexpected kwargs that might be added by future SDK updates
        result = store._search_logs_sync(
            log_type="syslog",
            limit=10,
            at_or_after=None,
            at_or_before=None,
            future_param="some_value",
            another_new_flag=True,
        )

        self.assertIsNotNone(result)
        self.assertIsNotNone(result.error_messages)
        self.assertIn(
            "Warning: Unsupported search argument(s) ignored: "
            "another_new_flag, future_param",
            result.error_messages[0],
        )


if __name__ == "__main__":
    unittest.main()
