"""Tests for BigQueryMatcher Plugin."""

import sys
import copy
import mock

from timesketch.lib.testlib import MockDataStore

from timesketch.lib.emojis import EMOJI_MAP
from timesketch.lib.analyzers.contrib import bigquery_matcher
from timesketch.lib.testlib import BaseTest


class TestBigQueryMatcherPlugin(BaseTest):
    """Tests the functionality of the analyzer."""

    _TEST_EMOJI = "SKULL"
    _TEST_TAG = "test-tag"
    # Skip the tests if bigquery is not imported.
    # pylint: disable=simplifiable-if-expression
    __test__ = True if "google.cloud.bigquery" in sys.modules else False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.test_index = "test_index"

    def setUp(self):
        """Set up the tests."""
        super().setUp()
        self.config = {}
        self.config["event_field_name"] = "field_name"
        self.config["bq_query"] = "test_query"
        self.config["bq_project"] = "test_project"
        self.config["tags"] = [self._TEST_TAG]
        self.config["emojis"] = [self._TEST_EMOJI]

    @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    @mock.patch("google.cloud.bigquery.Client")
    def test_match_single_entry(self, mock_bq):
        """Test that an entry is tagged correctly if it matches a row in BQ."""
        analyzer = bigquery_matcher.BigQueryMatcherPlugin(
            sketch_id=1, index_name=self.test_index
        )

        analyzer.datastore.client = mock.Mock()
        datastore = analyzer.datastore
        test_value = "12345"
        mock_bq().query.return_value = [[test_value]]
        _add_event_to_datastore(datastore, 0, {"field_name": test_value})

        analyzer.matcher("test_name", self.config)
        self.assertEqual(
            EMOJI_MAP[self._TEST_EMOJI].code, analyzer.emoji_events["0"]["emojis"][0]
        )
        self.assertEqual(self._TEST_TAG, analyzer.tagged_events["0"]["tags"][0])

    @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    @mock.patch("google.cloud.bigquery.Client")
    def test_no_match_single_entry(self, mock_bq):
        """Test that an entry is not tagged if it has no match in BQ."""
        analyzer = bigquery_matcher.BigQueryMatcherPlugin(
            sketch_id=1, index_name=self.test_index
        )

        analyzer.datastore.client = mock.Mock()
        datastore = analyzer.datastore
        mock_bq().query.return_value = []
        _add_event_to_datastore(datastore, 0, {"field_name": "not-in-bigquery"})

        analyzer.matcher("test_name", self.config)
        self.assertFalse(analyzer.emoji_events)
        self.assertFalse(analyzer.tagged_events)

    @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    @mock.patch("google.cloud.bigquery.Client")
    def test_query_batching(self, mock_bq):
        """Test that queries are batched correctly."""
        analyzer = bigquery_matcher.BigQueryMatcherPlugin(
            sketch_id=1, index_name=self.test_index
        )

        analyzer.datastore.client = mock.Mock()
        datastore = analyzer.datastore
        mock_bq().query.return_value = []
        # Need to access protected members for testing purposes.
        # pylint: disable=protected-access
        for i in range(analyzer._BQ_BATCH_SIZE + 1):
            _add_event_to_datastore(datastore, i, {"field_name": str(i)})

        analyzer.matcher("test_name", self.config)
        self.assertEqual(mock_bq().query.call_count, 2)


def _add_event_to_datastore(datastore, event_id, attributes_dict):
    event = copy.deepcopy(MockDataStore.event_dict)
    event["_source"].update(attributes_dict)
    datastore.import_event("test_index", "test_event", event["_source"], str(event_id))
