"""Tests for ThreatintelPlugin."""
from __future__ import unicode_literals

import mock

from timesketch.lib.analyzers import yetiindicators
from timesketch.lib.testlib import BaseTest
from timesketch.lib.testlib import MockDataStore

MOCK_YETI_INDICATORS = [{
    "created": "2019-05-28T15:48:12.642Z",
    "id": "x-regex--6ebc9344-0000-4d65-8bdd-b6dddf613068",
    "labels": ["domain"],
    "modified": "2019-05-29T11:08:01.290Z",
    "name": "Obvious Fancy Bear c2",
    "pattern": "help.notphishy.com",
    "type": "x-regex",
    "valid_from": "2019-05-01T15:47:00Z"
}, {
    "created": "2019-05-28T15:48:12.642Z",
    "id": "x-regex--6ebc9344-1111-4d65-8bdd-b6dddf613068",
    "labels": ["domain"],
    "modified": "2019-05-29T11:08:01.290Z",
    "name": "Secret Fancy Bear c2",
    "pattern": "help.verylegit(.com|.net)",
    "type": "x-regex",
    "valid_from": "2019-05-01T15:47:00Z"
}]


class TestThreatintelPlugin(BaseTest):
    """Tests the functionality of the analyzer."""

    # Mock the Elasticsearch datastore.
    @mock.patch('timesketch.lib.analyzers.interface.ElasticsearchDataStore',
                MockDataStore)
    def test_build_query_for_indicators(self):
        """Test that ES queries for indicators are correctly built."""
        query = yetiindicators.build_query_for_indicators(MOCK_YETI_INDICATORS)
        # pylint: disable=line-too-long
        self.assertEqual(
            query,
            'domain:/.*help.notphishy.com.*/ OR domain:/.*help.verylegit(.com|.net).*/'
        )
