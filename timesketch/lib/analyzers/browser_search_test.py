"""Tests for BrowserSearchPlugin."""

from __future__ import unicode_literals

import mock

from timesketch.lib.analyzers import browser_search
from timesketch.lib.testlib import BaseTest
from timesketch.lib.testlib import MockDataStore


class TestBrowserSearchPlugin(BaseTest):
    """Tests the functionality of the analyzer."""

    # Mock the OpenSearch datastore.
    @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    def test_url_extraction(self):
        """Test the browser search analyzer."""
        analyzer = browser_search.BrowserSearchSketchPlugin("test_index", 1)

        # Need to access protected members for testing purposes.
        # pylint: disable=protected-access
        bing_search = "https://www.bing.com/search?q=foobar+stuff&f=en"
        bing_result = analyzer._extract_search_query_from_url(bing_search, "q")
        self.assertEqual(bing_result, "foobar stuff")

        github_search = "https://github.com/search?q=foobar&another=true"
        github_result = analyzer._extract_search_query_from_url(github_search, "q")
        self.assertEqual(github_result, "foobar")

        drive_search = (
            "https://drive.google.com/drive/search?q=my%20secret%20stuff&ln=en"
        )
        drive_result = analyzer._extract_search_query_from_url(drive_search, "q")
        self.assertEqual(drive_result, "my secret stuff")

        google_search = "https://subsite.google.is/search?q=my%20secret%20stuff&ln=en"
        google_result = analyzer._extract_search_query_from_url(google_search, "q")
        self.assertEqual(google_result, "my secret stuff")
        google_search = "https://google.com/search?q=my%20secret%20stuff&ln=en"
        google_result = analyzer._extract_search_query_from_url(google_search, "q")
        self.assertEqual(google_result, "my secret stuff")

        sites_search = (
            "https://sites.google.com/site/mydomain/system/app/pages/"
            "meta/search?q=my%20secret%20stuff&ln=en"
        )
        sites_result = analyzer._extract_search_query_from_url(sites_search, "q")
        self.assertEqual(sites_result, "my secret stuff")

        duck_search = "https://duckduckgo.com/?q=foobar+stuff&f=en"
        duck_result = analyzer._extract_search_query_from_url(duck_search, "q")
        self.assertEqual(duck_result, "foobar stuff")

        duck_search = "https://duckduckgo.com/?q=from%3Ame%40stuff.com&f=en"
        duck_result = analyzer._extract_search_query_from_url(duck_search, "q")
        self.assertEqual(duck_result, "from:me@stuff.com")

        group_search = (
            "https://groups.google.com/a/mydomain/forum/#!search/secret/somestuff"
        )
        group_result = analyzer._extract_urlpart_search_query(group_search)
        self.assertEqual(group_result, "secret")
