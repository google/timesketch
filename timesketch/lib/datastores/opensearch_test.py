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
"""Tests for OpenSearch datastore."""

from unittest import mock
from opensearchpy.exceptions import ConnectionTimeout

from timesketch.lib.datastores.opensearch import OpenSearchDataStore
from timesketch.lib.testlib import BaseTest
from timesketch.lib.errors import DatastoreTimeoutError


class OpenSearchDataStoreTest(BaseTest):
    """Tests for OpenSearchDataStore."""

    @mock.patch("timesketch.lib.datastores.opensearch.current_user")
    @mock.patch("timesketch.lib.datastores.opensearch.OpenSearch")
    def test_search_timeout(self, mock_client, mock_user):
        """Test that search raises DatastoreTimeoutError on ConnectionTimeout."""
        mock_user.username = "testuser"

        # Setup mock client to raise ConnectionTimeout
        mock_es_instance = mock_client.return_value
        mock_es_instance.search.side_effect = ConnectionTimeout(
            "Timeout", "Timeout", "Timeout"
        )

        # Initialize datastore (mocking config is handled by BaseTest/TestConfig)
        ds = OpenSearchDataStore(host="127.0.0.1", port=9200)

        # Ensure the client in the datastore is indeed our mock (it should be)
        ds.client = mock_es_instance

        # Test generic timeout message
        with self.assertRaises(DatastoreTimeoutError) as cm:
            ds.search(sketch_id=1, indices=["test"], query_string="test")

        self.assertIn("The search timed out", str(cm.exception))
        self.assertIn("Try to narrow down your search", str(cm.exception))

        # Test wildcard specific message
        with self.assertRaises(DatastoreTimeoutError) as cm:
            ds.search(sketch_id=1, indices=["test"], query_string="*test")

        self.assertIn("The search timed out", str(cm.exception))
        self.assertIn("avoid leading wildcards", str(cm.exception))
