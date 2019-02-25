"""Tests for PotentialBruteforcePlugin."""
from __future__ import unicode_literals

import mock

from timesketch.lib.analyzers import potential_bruteforce
from timesketch.lib.testlib import BaseTest
from timesketch.lib.testlib import MockDataStore


class TestPotentialBruteforcePlugin(BaseTest):
    """Tests the functionality of the analyzer."""

    def __init__(self, *args, **kwargs):
        super(TestPotentialBruteforcePlugin, self).__init__(*args, **kwargs)

    # Mock the Elasticsearch datastore.
    @mock.patch(
        'timesketch.lib.analyzers.interface.ElasticsearchDataStore',
        MockDataStore)
    def test_bruteforce_analyzer_class(self):
        """Test core functionality of the analyzer class."""
        index_name = 'test'
        sketch_id = 1
        analyzer = domain.PotentialBruteforcePlugin(index_name, sketch_id)
        self.assertEqual(analyzer.index_name, index_name)
        self.assertEqual(analyzer.sketch.id, sketch_id)
