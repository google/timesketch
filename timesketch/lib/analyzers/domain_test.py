"""Tests for DomainPlugin."""
from __future__ import unicode_literals

import mock

from timesketch.lib.analyzers import domain
from timesketch.lib.testlib import BaseTest
from timesketch.lib.testlib import MockDataStore


class TestDomainPlugin(BaseTest):
    """Tests the functionality of the analyzer."""

    def __init__(self, *args, **kwargs):
        super(TestDomainPlugin, self).__init__(*args, **kwargs)

    # Mock the Elasticsearch datastore.
    @mock.patch(
        u'timesketch.lib.analyzers.interface.ElasticsearchDataStore',
        MockDataStore)
    def test_domain_analyzer_class(self):
        """Test core functionality of the analyzer class."""
        index_name = 'test'
        sketch_id = 1
        analyzer = domain.DomainSketchPlugin(index_name, sketch_id)
        self.assertEquals(analyzer.index_name, index_name)
        self.assertEquals(analyzer.sketch.id, sketch_id)
