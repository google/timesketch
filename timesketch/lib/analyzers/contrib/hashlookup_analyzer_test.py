"""Test for Hashlookup"""

from timesketch.lib.testlib import BaseTest

SHA256_HASH = "ac7233de5daa4ab262e2e751028f56a7e9d5b9e724624c1d55e8b070d8c3cd09"


class TestHashlookup(BaseTest):
    """Tests the functionality of the analyzer."""

    def setUp(self):
        super().setUp()

        self.HASHLOOKUP_DB = [
            "301c9ec7a9aadee4d745e8fd4fa659dafbbcc6b75b9ff491d14cbbdd840814e9",
            "ac7233de5daa4ab262e2e751028f56a7e9d5b9e724624c1d55e8b070d8c3cd09",
        ]
        self.MATCHING_HASH = {"sha256_hash": SHA256_HASH}

    def hash_match(self):
        """Compare Hashlookup reponse and timesketch event"""
        cp = 0
        if self.MATCHING_HASH["sha256_hash"] in self.HASHLOOKUP_DB:
            cp += 1
        return f"Hash Match: {cp}"

    def test_hash_match(self):
        """Test match"""
        message = self.hash_match()
        self.assertEqual(
            message,
            ("Hash Match: 1"),
        )

    def test_hash_nomatch(self):
        """Test no match"""
        self.HASHLOOKUP_DB = []
        message = self.hash_match()
        self.assertEqual(
            message,
            ("Hash Match: 0"),
        )
