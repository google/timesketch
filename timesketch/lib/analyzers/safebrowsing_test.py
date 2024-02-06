"""Tests for SafeBrowsingSketchPlugin."""

from __future__ import unicode_literals

from collections import OrderedDict

import mock
from httmock import HTTMock, all_requests

from timesketch.lib.analyzers import safebrowsing
from timesketch.lib.testlib import BaseTest, MockDataStore


class TestSafeBrowsingSketchPlugin(BaseTest):
    """Tests the functionality of the analyzer."""

    @mock.patch(
        "timesketch.lib.analyzers.interface.OpenSearchDataStore",
        MockDataStore,
    )
    def test_safebrowsing_analyzer_class(self):
        """Test core functionality of the analyzer class."""
        index_name = "test"
        sketch_id = 1
        analyzer = safebrowsing.SafeBrowsingSketchPlugin(index_name, sketch_id)
        self.assertEqual(analyzer.index_name, index_name)
        self.assertEqual(analyzer.sketch.id, sketch_id)

    @all_requests
    # pylint: disable=unused-argument,missing-docstring
    def safebrowsing_find_mock(self, url, request):
        MOCK_RESULT = {
            "matches": [
                {
                    "threat": {
                        "url": "http://A",
                    },
                    "cacheDuration": "300s",
                    "threatEntryType": "URL",
                    "threatType": "MALWARE",
                    "platformType": "ANY_PLATFORM",
                },
                {
                    "threat": {
                        "url": "https://B",
                    },
                    "cacheDuration": "300s",
                    "threatEntryType": "URL",
                    "threatType": "MALWARE",
                    "platformType": "WINDOWS",
                },
            ],
        }

        return {
            "status_code": 200,
            "content": MOCK_RESULT,
        }

    @mock.patch(
        "timesketch.lib.analyzers.interface.OpenSearchDataStore",
        MockDataStore,
    )
    # pylint: disable=missing-docstring
    def test_do_safebrowsing_lookup(self):
        index_name = "test"
        sketch_id = 1
        analyzer = safebrowsing.SafeBrowsingSketchPlugin(index_name, sketch_id)

        with HTTMock(self.safebrowsing_find_mock):
            EXPECTED_RESULT = {
                "http://A": {
                    "platformType": "ANY_PLATFORM",
                    "threatType": "MALWARE",
                },
                "https://B": {
                    "platformType": "WINDOWS",
                    "threatType": "MALWARE",
                },
            }

            # pylint: disable=protected-access
            actual_result = analyzer._do_safebrowsing_lookup(
                ["http://A", "https://B"],
                [],
                [],
            )

            self.assertEqual(
                OrderedDict(
                    sorted(
                        EXPECTED_RESULT.items(),
                    ),
                ),
                OrderedDict(
                    sorted(
                        actual_result.items(),
                    ),
                ),
            )

    @mock.patch(
        "timesketch.lib.analyzers.interface.OpenSearchDataStore",
        MockDataStore,
    )
    def test_helper_functions(self):
        """Tests the helper functions used by the analyzer."""
        index_name = "test"
        sketch_id = 1
        analyzer = safebrowsing.SafeBrowsingSketchPlugin(index_name, sketch_id)

        HELPERS = [
            self.check_sanitize_url,
            self.check_allowlist,
        ]

        for helper in HELPERS:
            helper(analyzer)

    def check_sanitize_url(self, analyzer):
        URLS = [
            ("http://w.com", "http://w.com"),
            ("https://w.com", "https://w.com"),
            ("Something before@https://w.com", "https://w.com"),
            ("https://w.com and after", "https://w.com"),
            ("nothing", ""),
        ]

        for entry, result in URLS:
            self.assertEqual(
                # pylint: disable=protected-access
                analyzer._sanitize_url(entry),
                result,
            )

    # pylint: disable=missing-docstring
    def check_allowlist(self, analyzer):
        ALLOW_LIST = [
            "lorem-*.com",
            "ipsum.dk",
            "dolo?.co.*",
        ]

        self.assertTrue(
            # pylint: disable=protected-access
            analyzer._is_url_allowlisted(
                "lorem-ipsum.com",
                ALLOW_LIST,
            ),
        )

        self.assertFalse(
            # pylint: disable=protected-access
            analyzer._is_url_allowlisted(
                "ipsum.com",
                ALLOW_LIST,
            ),
        )

        self.assertTrue(
            # pylint: disable=protected-access
            analyzer._is_url_allowlisted(
                "dolor.co.dk",
                ALLOW_LIST,
            ),
        )

        self.assertFalse(
            # pylint: disable=protected-access
            analyzer._is_url_allowlisted(
                "www.amet.com",
                ALLOW_LIST,
            ),
        )
