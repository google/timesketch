"""Tests for DomainsPlugin."""
from __future__ import unicode_literals

from flask import current_app
import mock

from datasketch.minhash import MinHash

from timesketch.lib.analyzers import domains
from timesketch.lib.testlib import BaseTest
from timesketch.lib.testlib import MockDataStore


class TestDomainsPlugin(BaseTest):
    """Tests the functionality of the analyzer."""

    def __init__(self, *args, **kwargs):
        super(TestDomainsPlugin, self).__init__(*args, **kwargs)

    def setUp(self):
        """Set up the tests."""
        super(TestDomainsPlugin, self).setUp()
        current_app.config['DOMAIN_ANALYZER_WATCHED_DOMAINS'] = ['foobar.com']
        current_app.config['DOMAIN_ANALYZER_WATCHED_DOMAINS_THRESHOLD'] = 10
        current_app.config[
            'DOMAIN_ANALYZER_WATCHED_DOMAINS_SCORE_THRESHOLD'] = 0.75
        current_app.config[
            'DOMAIN_ANALYZER_WHITELISTED_DOMAINS'] = [
                'ytimg.com', 'gstatic.com', 'yimg.com',
                'akamaized.net', 'akamaihd.net', 's-microsoft.com']

        self.analyzer = domains.DomainsSketchPlugin('test_index', 1)

    # Mock the Elasticsearch datastore.
    @mock.patch(
        u'timesketch.lib.analyzers.interface.ElasticsearchDataStore',
        MockDataStore)
    def test_minhash(self):
        """Test minhash function."""
        domain = 'www.mbl.is'
        # pylint: disable=protected-access
        minhash = self.analyzer._get_minhash_from_domain(domain)

        self.assertIsInstance(minhash, MinHash)

        another_domain = 'mbl.is'
        minhash2 = self.analyzer._get_minhash_from_domain(another_domain)

        self.assertEqual(minhash.jaccard(minhash2), 1.0)

    # Mock the Elasticsearch datastore.
    @mock.patch(
        u'timesketch.lib.analyzers.interface.ElasticsearchDataStore',
        MockDataStore)
    def test_get_similar_domains(self):
        """Test get_similar_domains function."""
        domain = 'mbl.is'
        minhash = self.analyzer._get_minhash_from_domain(domain)
        domains = {domain: minhash}

        similar = self.analyzer._get_similar_domains('www.mbi.is', domains)

        self.assertEquals(len(similar), 1)

        similar = self.analyzer._get_similar_domains('www.google.com', domains)
        self.assertEquals(len(similar), 0)


    # Mock the Elasticsearch datastore.
    @mock.patch(
        u'timesketch.lib.analyzers.interface.ElasticsearchDataStore',
        MockDataStore)
    def test_get_tld(self):
        """Test get_tld function."""
        domain = 'this.is.a.subdomain.evil.com'
        tld = self.analyzer._get_tld(domain)
        self.assertEquals(tld, 'evil.com')

        domain = 'a'
        tld = self.analyzer._get_tld(domain)
        self.assertEquals(tld, 'a')

        domain = 'foo.com'
        tld = self.analyzer._get_tld(domain)
        self.assertEquals(tld, 'foo.com')


    # Mock the Elasticsearch datastore.
    @mock.patch(
        u'timesketch.lib.analyzers.interface.ElasticsearchDataStore',
        MockDataStore)
    def test_strip_www(self):
        """Test strip_www function."""
        domain = 'www.mbl.is'
        stripped = self.analyzer._strip_www(domain)
        self.assertEquals(stripped, 'mbl.is')

        domain = 'mbl.is'
        stripped = self.analyzer._strip_www(domain)
        self.assertEquals(stripped, domain)
