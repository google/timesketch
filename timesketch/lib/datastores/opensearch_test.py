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

# pylint: disable=protected-access

from unittest import mock
from opensearchpy.exceptions import ConnectionTimeout
from opensearchpy.exceptions import TransportError

from timesketch.lib.datastores.opensearch import OpenSearchDataStore
from timesketch.lib.testlib import BaseTest
from timesketch.lib.errors import DatastoreTimeoutError
from timesketch.lib.errors import UnsupportedDatastoreVersionError


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
        event2 = {"message": "a" * 150}
        ds.import_event("test_index", event2)

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
            if len(body) > 4:
                raise TransportError(413, "Request Entity Too Large", "")
            return {"errors": False, "items": []}

        mock_es_instance.bulk.side_effect = bulk_side_effect

        for i in range(4):
            ds.import_event("test_index", {"msg": i})

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

        ds.import_event("test_index", {"msg": "too big"})

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

    @mock.patch("timesketch.lib.datastores.opensearch.OpenSearch")
    def test_get_wildcard_fields(self, mock_client):
        """Test get_wildcard_fields mapping parser logic."""
        ds = OpenSearchDataStore(host="127.0.0.1", port=9200)
        mock_es = mock_client.return_value
        ds.client = mock_es

        mock_mappings = {
            "idx_1": {
                "mappings": {
                    "properties": {
                        "msg": {
                            "type": "text",
                            "fields": {
                                "keyword": {"type": "keyword"},
                                "wildcard": {"type": "wildcard"},
                            },
                        },
                        "xml": {"type": "wildcard"},
                        "nested_obj": {
                            "properties": {
                                "sub_field": {
                                    "type": "text",
                                    "fields": {"wildcard": {"type": "wildcard"}},
                                }
                            }
                        },
                        "non_wildcard": {
                            "type": "text",
                            "fields": {"keyword": {"type": "keyword"}},
                        },
                    }
                }
            }
        }
        mock_es.indices.get_mapping.return_value = mock_mappings

        fields = ds.get_wildcard_fields(["idx_1"])
        self.assertCountEqual(fields, ["msg", "xml", "nested_obj.sub_field"])

        # Test with pre-fetched mappings (should not call mock_es.indices.get_mapping)
        mock_es.indices.get_mapping.reset_mock()
        fields_prefetched = ds.get_wildcard_fields(["idx_1"], mappings=mock_mappings)
        self.assertCountEqual(fields_prefetched, ["msg", "xml", "nested_obj.sub_field"])
        mock_es.indices.get_mapping.assert_not_called()

    @mock.patch("timesketch.lib.datastores.opensearch.OpenSearch")
    def test_build_wildcard_query_dsl_global_search(self, mock_client):
        """Test global wildcard query dsl generation."""
        mock_es = mock_client.return_value
        mock_es.info.return_value = {"version": {"number": "7.0.0"}}
        ds = OpenSearchDataStore(host="127.0.0.1", port=9200)
        wildcard_fields = {"msg", "xml"}

        # 1. Simple global term
        bool_query = ds._build_wildcard_query_dsl("*evil*", wildcard_fields)
        must_clauses = bool_query["must"]
        self.assertEqual(len(must_clauses), 1)
        self.assertEqual(must_clauses[0]["multi_match"]["query"], "*evil*")
        self.assertEqual(must_clauses[0]["multi_match"]["fields"], ["*.wildcard"])

    @mock.patch("timesketch.lib.datastores.opensearch.OpenSearch")
    def test_build_wildcard_query_dsl_field_search(self, mock_client):
        """Test field specific wildcard query dsl generation."""
        mock_es = mock_client.return_value
        mock_es.info.return_value = {"version": {"number": "7.0.0"}}
        ds = OpenSearchDataStore(host="127.0.0.1", port=9200)
        wildcard_fields = {"msg", "xml"}

        # Targeted field mapped to wildcard
        bool_query = ds._build_wildcard_query_dsl("msg:*evil*", wildcard_fields)
        must_clauses = bool_query["must"]
        self.assertEqual(len(must_clauses), 1)
        self.assertEqual(must_clauses[0]["wildcard"]["msg.wildcard"]["value"], "*evil*")
        self.assertTrue(must_clauses[0]["wildcard"]["msg.wildcard"]["case_insensitive"])

        # Targeted field NOT mapped to wildcard -> raises ValueError
        with self.assertRaises(ValueError) as cm:
            ds._build_wildcard_query_dsl("unknown:*evil*", wildcard_fields)

        self.assertIn(
            "Field 'unknown' does not support wildcard search",
            str(cm.exception),
        )

    @mock.patch("timesketch.lib.datastores.opensearch.OpenSearch")
    def test_build_wildcard_query_dsl_operators(self, mock_client):
        """Test wildcard query dsl boolean logical operators routing."""
        mock_es = mock_client.return_value
        mock_es.info.return_value = {"version": {"number": "7.0.0"}}
        ds = OpenSearchDataStore(host="127.0.0.1", port=9200)
        wildcard_fields = {"msg", "xml"}

        # Query: msg:*evil* NOT xml:*test* OR *backdoor*
        # Correctly evaluated as: (msg:*evil* AND (NOT xml:*test*)) OR *backdoor*
        query = "msg:*evil* NOT xml:*test* OR *backdoor*"
        bool_query = ds._build_wildcard_query_dsl(query, wildcard_fields)

        # The top-level query must be an OR (should)
        self.assertEqual(len(bool_query["should"]), 2)
        self.assertEqual(bool_query["minimum_should_match"], 1)

        # Left branch of OR: msg:*evil* AND NOT xml:*test*
        left_and = bool_query["should"][0]
        self.assertEqual(len(left_and["bool"]["must"]), 2)

        self.assertEqual(
            left_and["bool"]["must"][0]["wildcard"]["msg.wildcard"]["value"],
            "*evil*",
        )

        # NOT xml:*test*
        not_test = left_and["bool"]["must"][1]
        self.assertEqual(
            not_test["bool"]["must_not"][0]["wildcard"]["xml.wildcard"]["value"],
            "*test*",
        )

        # Right branch of OR: *backdoor*
        right_or = bool_query["should"][1]
        self.assertEqual(right_or["multi_match"]["query"], "*backdoor*")

    @mock.patch("timesketch.lib.datastores.opensearch.OpenSearch")
    def test_build_wildcard_query_dsl_parentheses(self, mock_client):
        """Test wildcard query dsl parenthetical grouping routing."""
        mock_es = mock_client.return_value
        mock_es.info.return_value = {"version": {"number": "7.0.0"}}
        ds = OpenSearchDataStore(host="127.0.0.1", port=9200)
        wildcard_fields = {"msg", "xml"}

        # Query: msg:*evil* (xml:*test* OR *backdoor*)
        # Evaluated as: msg:*evil* AND (xml:*test* OR *backdoor*)
        query = "msg:*evil* (xml:*test* OR *backdoor*)"
        bool_query = ds._build_wildcard_query_dsl(query, wildcard_fields)

        # Top-level should be a must (AND)
        self.assertEqual(len(bool_query["must"]), 2)

        # Left operand: msg:*evil*
        self.assertEqual(
            bool_query["must"][0]["wildcard"]["msg.wildcard"]["value"],
            "*evil*",
        )

        # Right operand: (xml:*test* OR *backdoor*)
        right_or = bool_query["must"][1]
        self.assertEqual(len(right_or["bool"]["should"]), 2)
        self.assertEqual(right_or["bool"]["minimum_should_match"], 1)
        self.assertEqual(
            right_or["bool"]["should"][0]["wildcard"]["xml.wildcard"]["value"],
            "*test*",
        )
        self.assertEqual(
            right_or["bool"]["should"][1]["multi_match"]["query"],
            "*backdoor*",
        )

    @mock.patch("timesketch.lib.datastores.opensearch.OpenSearch")
    def test_build_wildcard_query_dsl_invalid_field(self, mock_client):
        """Test that querying an unsupported wildcard field raises ValueError."""
        mock_es = mock_client.return_value
        mock_es.info.return_value = {"version": {"number": "7.0.0"}}
        ds = OpenSearchDataStore(host="127.0.0.1", port=9200)
        wildcard_fields = {"msg", "xml"}

        query = "invalid_field:*evil*"
        with self.assertRaises(ValueError) as cm:
            ds._build_wildcard_query_dsl(query, wildcard_fields)

        self.assertIn(
            "Field 'invalid_field' does not support wildcard search",
            str(cm.exception),
        )

    @mock.patch("timesketch.lib.datastores.opensearch.current_app")
    @mock.patch("timesketch.lib.datastores.opensearch.OpenSearch")
    def test_unsupported_version(self, mock_client, mock_app):
        """Test that initializing OpenSearchDataStore raises error on
        unsupported version."""
        mock_app.config = {"TESTING": False}
        mock_es_instance = mock_client.return_value
        mock_es_instance.info.return_value = {"version": {"number": "2.15.0"}}

        with self.assertRaises(UnsupportedDatastoreVersionError) as cm:

            OpenSearchDataStore(host="127.0.0.1", port=9200)

        self.assertIn(
            "Connected OpenSearch version 2.15.0 is not supported", str(cm.exception)
        )

    @mock.patch("timesketch.lib.datastores.opensearch.current_app")
    @mock.patch("timesketch.lib.datastores.opensearch.OpenSearch")
    def test_supported_version(self, mock_client, mock_app):
        """Test that initializing OpenSearchDataStore succeeds on supported version."""
        mock_app.config = {"TESTING": False}
        mock_es_instance = mock_client.return_value
        mock_es_instance.info.return_value = {"version": {"number": "2.19.5"}}

        ds = OpenSearchDataStore(host="127.0.0.1", port=9200)
        self.assertEqual(ds.version, "2.19.5")
