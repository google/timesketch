"""Tests for DomainPlugin."""

from __future__ import unicode_literals

import mock

from timesketch.lib.analyzers import domain
from timesketch.lib.testlib import BaseTest
from timesketch.lib.testlib import MockDataStore


class TestDomainPlugin(BaseTest):
    """Tests the functionality of the analyzer."""

    # Mock the OpenSearch datastore.
    @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    def test_domain_analyzer_class(self):
        """Test core functionality of the analyzer class."""
        index_name = "test"
        sketch_id = 1
        analyzer = domain.DomainSketchPlugin(index_name, sketch_id)
        self.assertEqual(analyzer.index_name, index_name)
        self.assertEqual(analyzer.sketch.id, sketch_id)
