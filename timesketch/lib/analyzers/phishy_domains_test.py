"""Tests for DomainsPlugin."""

from __future__ import unicode_literals

import mock

from flask import current_app
from datasketch.minhash import MinHash

from timesketch.lib.analyzers import phishy_domains
from timesketch.lib.testlib import BaseTest
from timesketch.lib.testlib import MockDataStore


class TestDomainsPlugin(BaseTest):
    """Tests the functionality of the analyzer."""

    def setUp(self):
        """Set up the tests."""
        super().setUp()
        current_app.config["DOMAIN_ANALYZER_WATCHED_DOMAINS"] = ["foobar.com"]
        current_app.config["DOMAIN_ANALYZER_WATCHED_DOMAINS_THRESHOLD"] = 10
        current_app.config["DOMAIN_ANALYZER_WATCHED_DOMAINS_SCORE_THRESHOLD"] = 0.75
        current_app.config["DOMAIN_ANALYZER_WHITELISTED_DOMAINS"] = [
            "ytimg.com",
            "gstatic.com",
            "yimg.com",
            "akamaized.net",
            "akamaihd.net",
            "s-microsoft.com",
        ]

    # Mock the OpenSearch datastore.
    @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    def test_minhash(self):
        """Test minhash function."""
        analyzer = phishy_domains.PhishyDomainsSketchPlugin("test_index", 1)
        domain = "www.mbl.is"
        # pylint: disable=protected-access
        minhash = analyzer._get_minhash_from_domain(domain)

        self.assertIsInstance(minhash, MinHash)

        another_domain = "mbl.is"
        # pylint: disable=protected-access
        minhash2 = analyzer._get_minhash_from_domain(another_domain)

        self.assertEqual(minhash.jaccard(minhash2), 0.546875)

    # Mock the OpenSearch datastore.
    @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    def test_get_similar_domains(self):
        """Test get_similar_domains function."""
        analyzer = phishy_domains.PhishyDomainsSketchPlugin("test_index", 1)
        domain = "login.stortmbl.is"
        # pylint: disable=protected-access
        minhash = analyzer._get_minhash_from_domain(domain)
        domain_dict = {domain: {"hash": minhash, "depth": 3}}

        # pylint: disable=protected-access
        similar = analyzer._get_similar_domains("login.stortmbi.is", domain_dict)
        self.assertEqual(len(similar), 1)

        # pylint: disable=protected-access
        similar = analyzer._get_similar_domains("www.google.com", domain_dict)
        self.assertEqual(len(similar), 0)
