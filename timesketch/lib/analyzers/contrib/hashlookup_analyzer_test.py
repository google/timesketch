"""Test for Hashlookup"""

import copy
import mock

from flask import current_app

from timesketch.lib.analyzers.contrib import hashlookup_analyzer
from timesketch.lib.testlib import BaseTest
from timesketch.lib.testlib import MockDataStore

SHA256_HASH = "ac7233de5daa4ab262e2e751028f56a7e9d5b9e724624c1d55e8b070d8c3cd09"
SHA256_N_HASH = "bc7233de5daa4ab262e2e751028f56a7e9d5b9e724624c1d55e8b070d8c3cd09"
MATCHING_HASH = {"sha256_hash": SHA256_HASH}
NO_MATCHING_HASH = {"sha256_hash": SHA256_N_HASH}


class TestHashlookup(BaseTest):
    """Tests the functionality of the analyzer."""

    def setUp(self):
        super().setUp()
        current_app.config["HASHLOOKUP_URL"] = "https://test.com/"

    @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    @mock.patch("requests.get")
    def test_hash_match(self, mock_requests_get):
        """Test match"""
        analyzer = hashlookup_analyzer.HashlookupAnalyzer("test_index", 1)
        analyzer.hashlookup_url = "https://test.com/"
        analyzer.datastore.client = mock.Mock()
        mock_requests_get.return_value.status_code = 200
        mock_requests_get.return_value.json.return_value = {"FileName": "test.txt"}

        event = copy.deepcopy(MockDataStore.event_dict)
        event["_source"].update(MATCHING_HASH)
        analyzer.datastore.import_event("test_index", event["_source"], "0")

        message = analyzer.run()
        self.assertEqual(
            message,
            ("Hashlookup Matches: 1"),
        )
        url = f"https://test.com/sha256/{SHA256_HASH}"
        mock_requests_get.assert_called_with(url)

    @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    @mock.patch("requests.get")
    def test_hash_nomatch(self, mock_requests_get):
        """Test no match"""
        analyzer = hashlookup_analyzer.HashlookupAnalyzer("test_index", 1)
        analyzer.hashlookup_url = "https://test.com/"
        analyzer.datastore.client = mock.Mock()
        mock_requests_get.return_value.status_code = 404
        mock_requests_get.return_value.json.return_value = []

        event = copy.deepcopy(MockDataStore.event_dict)
        event["_source"].update(NO_MATCHING_HASH)
        analyzer.datastore.import_event("test_index", event["_source"], "0")

        message = analyzer.run()
        self.assertEqual(
            message,
            ("Hashlookup Matches: 0"),
        )
        url = f"https://test.com/sha256/{SHA256_N_HASH}"
        mock_requests_get.assert_called_with(url)
