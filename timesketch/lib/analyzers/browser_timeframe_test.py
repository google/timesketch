"""Tests for BrowserTimeframePlugin."""
from __future__ import unicode_literals

import mock

from timesketch.lib.analyzers import browser_timeframe
from timesketch.lib.testlib import BaseTest
from timesketch.lib.testlib import MockDataStore


class TestBrowserTimeframePlugin(BaseTest):
    """Tests the functionality of the analyzer."""

    def __init__(self, *args, **kwargs):
        super(TestBrowserTimeframePlugin, self).__init__(*args, **kwargs)

    # Mock the Elasticsearch datastore.
    @mock.patch(
        u'timesketch.lib.analyzers.interface.ElasticsearchDataStore',
        MockDataStore)
    def test_analyzer(self):
        """Test analyzer."""
        # TODO: Write actual tests here.
        self.assertIsEqual(True, False)
