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
from opensearchpy.exceptions import TransportError

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
        self.assertNotIn("Avoid leading wildcards", str(cm.exception))

        # Test wildcard specific message
        with self.assertRaises(DatastoreTimeoutError) as cm:
            ds.search(sketch_id=1, indices=["test"], query_string="*test")

        self.assertIn("The search timed out", str(cm.exception))
        self.assertIn("Avoid leading wildcards", str(cm.exception))

    @mock.patch("timesketch.lib.datastores.opensearch.OpenSearch")
    def test_proactive_flush_on_size(self, mock_client):
        """Test that indexing flushes proactively when byte size limit is reached."""
        # Initialize datastore with a very small flush_byte_size
        with mock.patch("timesketch.lib.datastores.opensearch.current_app") as mock_app:
            mock_app.config = {
                "OPENSEARCH_FLUSH_INTERVAL": 1000,
                "OPENSEARCH_FLUSH_BYTE_SIZE": 200,  # Very small limit
            }
            ds = OpenSearchDataStore(host="127.0.0.1", port=9200)

        mock_es_instance = mock_client.return_value
        ds.client = mock_es_instance

        # Mock bulk to return success
        mock_es_instance.bulk.return_value = {"errors": False, "items": []}

        # Add a small event (less than 200 bytes)
        event1 = {"message": "short message"}
        ds.import_event("test_index", event1)
        self.assertEqual(len(ds.import_events), 2)
        mock_es_instance.bulk.assert_not_called()

        # Add another event that pushes it over 200 bytes
        event2 = {"message": "a" * 150}  # This will definitely push it over
        ds.import_event("test_index", event2)

        # The first event should have been flushed before adding the second one
        # Because we used "flush-before-add" logic.
        # However, the second event then finishes its add and triggers its OWN flush
        # because IT is now in the queue and exceeds the 200 byte limit alone.
        # So bulk is called twice: once for event1, once for event2.
        self.assertEqual(mock_es_instance.bulk.call_count, 2)
        self.assertEqual(len(ds.import_events), 0)

    @mock.patch("timesketch.lib.datastores.opensearch.OpenSearch")
    def test_reactive_halving_on_413(self, mock_client):
        """Test that indexing splits and retries on HTTP 413 error."""
        with mock.patch("timesketch.lib.datastores.opensearch.current_app") as mock_app:
            mock_app.config = {
                "OPENSEARCH_FLUSH_INTERVAL": 1000,
                "OPENSEARCH_FLUSH_BYTE_SIZE": 1024 * 1024,
            }
            ds = OpenSearchDataStore(host="127.0.0.1", port=9200)

        mock_es_instance = mock_client.return_value
        ds.client = mock_es_instance

        # First call to bulk raises 413, subsequent calls succeed
        def bulk_side_effect(body, **_kwargs):
            if len(body) > 4:  # More than 2 events (4 items)
                raise TransportError(413, "Request Entity Too Large", "")
            return {"errors": False, "items": []}

        mock_es_instance.bulk.side_effect = bulk_side_effect

        # Add 4 events (8 items)
        for i in range(4):
            ds.import_event("test_index", {"msg": i})

        # Force flush
        results = ds.flush_queued_events()

        # Should have called bulk multiple times due to halving
        # 1. 4 events -> 413
        # 2. 2 events (first half) -> success
        # 3. 2 events (second half) -> success
        self.assertEqual(mock_es_instance.bulk.call_count, 3)
        self.assertFalse(results.get("errors_in_upload"))
        self.assertIn("error_container", results)

    @mock.patch("timesketch.lib.datastores.opensearch.OpenSearch")
    def test_single_event_too_large(self, mock_client):
        """Test handling of a single event that exceeds the hard OpenSearch limit."""
        with mock.patch("timesketch.lib.datastores.opensearch.current_app") as mock_app:
            mock_app.config = {
                "OPENSEARCH_FLUSH_INTERVAL": 1000,
                "OPENSEARCH_FLUSH_BYTE_SIZE": 1024 * 1024,
            }
            ds = OpenSearchDataStore(host="127.0.0.1", port=9200)

        mock_es_instance = mock_client.return_value
        ds.client = mock_es_instance

        # Always raise 413
        mock_es_instance.bulk.side_effect = TransportError(413, "Too Large", "")

        # Add one event
        ds.import_event("test_index", {"msg": "too big"})

        # Flush
        results = ds.flush_queued_events()

        # Should have called bulk once and identified it as single event too large
        self.assertEqual(mock_es_instance.bulk.call_count, 1)
        self.assertTrue(results.get("errors_in_upload"))
        error_container = results.get("error_container")
        self.assertIn("test_index", error_container)
        self.assertEqual(
            error_container["test_index"]["types"]["RequestEntityTooLarge"], 1
        )
        self.assertEqual(
            error_container["test_index"]["details"]["SingleEventTooLarge"], 1
        )
