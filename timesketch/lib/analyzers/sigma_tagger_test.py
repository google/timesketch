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
        self.test_index = "test_index"

    # Mock the OpenSearch datastore.
    @mock.patch(
        "timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore
    )
    def test_analyzer(self):
        """Test analyzer."""

        _ = sigma_tagger.RulesSigmaPlugin(
            sketch_id=1, index_name=self.test_index
        )

    def test_get_kwargs(self):
        analyzer_init = sigma_tagger.RulesSigmaPlugin(
            sketch_id=1, index_name=self.test_index
        )
        rules = analyzer_init.get_kwargs()
        self.assertIsNotNone(rules)
        self.assertGreaterEqual(len(rules), 1)
        self.assertIn("zmap", rules[0]['rule'].get("es_query"))
        self.assertIn("b793", rules[0]['rule'].get("id"))
        self.assertEqual(rules[0]['rule'].get("ts_use_in_analyzer"), True)
