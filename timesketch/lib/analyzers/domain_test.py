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
    def test_get_domain_from_url(self):
        """Test get_domain_from_url function."""
        analyzer = domain.DomainSketchPlugin('test_index', 1)
        url = 'http://example.com/?foo=bar'
        # pylint: disable=protected-access
        _domain = analyzer._get_domain_from_url(url)
        self.assertEquals(_domain, 'example.com')
