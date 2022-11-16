import mock

from timesketch.lib.testlib import BaseTest
from timesketch.lib.testlib import MockDataStore

HASHLOOKUP_DB = ["301c9ec7a9aadee4d745e8fd4fa659dafbbcc6b75b9ff491d14cbbdd840814e9", "ac7233de5daa4ab262e2e751028f56a7e9d5b9e724624c1d55e8b070d8c3cd09"]

MATCHING_HASH = {"sha256_hash": "ac7233de5daa4ab262e2e751028f56a7e9d5b9e724624c1d55e8b070d8c3cd09"}

class TestHashlookup(BaseTest):
    """Tests the functionality of the analyzer."""

    def setUp(self):
        super().setUp()

    def hash_match(self):
        cp = 0
        if HASHLOOKUP_DB['sha256_hash'] in MATCHING_HASH:
            cp += 1
        return f"Hash Match: {cp}"

    @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    @mock.patch(
        "timesketch.lib.analyzers.contrib.hashlookup_analyzer." "HashlookupAnalyzer.get_hash_info"
    )
    def test_hash_match(self):
        message = self.attr_match()
        self.assertEqual(
            message,
            ("Hash Match: 1"),
        )

    @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    @mock.patch(
        "timesketch.lib.analyzers.contrib.hashlookup_analyzer." "HashlookupAnalyzer.get_hash_info"
    )
    def test_hash_nomatch(self):
        HASHLOOKUP_DB = {}
        message = self.attr_match()
        self.assertEqual(
            message,
            ("Hash Match: 0"),
        )
