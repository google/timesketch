"""Tests for SigmaPlugin."""
from __future__ import unicode_literals

import mock

from timesketch.lib.analyzers import sigma_tagger
from timesketch.lib.testlib import BaseTest
from timesketch.lib.testlib import MockDataStore


class TestSigmaPlugin(BaseTest):
    """Tests the functionality of the analyzer."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.test_index = 'test_index'


    # Mock the OpenSearch datastore.
    @mock.patch(
        'timesketch.lib.analyzers.interface.OpenSearchDataStore',
        MockDataStore)
    def test_analyzer(self):
        """Test analyzer."""
        # TODO: Add more tests

        _ = sigma_tagger.RulesSigmaPlugin(
            sketch_id=1, index_name=self.test_index)
