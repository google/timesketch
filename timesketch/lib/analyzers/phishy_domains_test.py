"""Tests for DomainsPlugin."""

from unittest import mock

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

    @staticmethod
    def _mock_events(domains):
        """Returns mock events with the given domains."""
        events = []
        for domain in domains:
            event = mock.MagicMock()
            event.source = {"domain": domain}
            events.append(event)
        return events

    # Mock the OpenSearch datastore.
    @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    def test_run_does_not_modify_config(self):
        """Test that a run does not add domains to the configured list."""
        analyzer = phishy_domains.PhishyDomainsSketchPlugin("test_index", 1)
        events = self._mock_events(["first-domain.example", "other.example"])
        with mock.patch.object(analyzer, "event_stream", return_value=events):
            analyzer.run()

        self.assertEqual(
            current_app.config["DOMAIN_ANALYZER_WATCHED_DOMAINS"], ["foobar.com"]
        )

    # Mock the OpenSearch datastore.
    @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    def test_run_does_not_reuse_domains_from_previous_run(self):
        """Test that domains of one run are not watched in a later run."""
        first = phishy_domains.PhishyDomainsSketchPlugin("test_index", 1)
        events = self._mock_events(["first-domain.example"])
        with mock.patch.object(first, "event_stream", return_value=events):
            first.run()

        # The second run has its own top domains, and one rare domain that is
        # only similar to the top domain of the first run. Nothing should match.
        second = phishy_domains.PhishyDomainsSketchPlugin("test_index", 2)
        frequent = [f"frequent{i:02d}.test" for i in range(10)]
        events = self._mock_events(frequent * 2 + ["first-d0main.example"])
        with mock.patch.object(second, "event_stream", return_value=events):
            result = second.run()

        self.assertEqual(result, "0 potentially phishy domains discovered.")
        for event in events:
            event.add_tags.assert_called_once_with([])
