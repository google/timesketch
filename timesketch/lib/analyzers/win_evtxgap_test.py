"""Tests for EvtxGapPlugin."""

from __future__ import unicode_literals

import unittest
import mock

from timesketch.lib.analyzers import win_evtxgap
from timesketch.lib.testlib import BaseTest
from timesketch.lib.testlib import MockDataStore


class TestEvtxGapPlugin(BaseTest):
    """Tests the functionality of the analyzer."""

    @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    def setUp(self):
        super().setUp()
        self.analyzer = win_evtxgap.EvtxGapPlugin("test_index", 1)

    def test_get_range(self):
        """Test the get range function."""
        test_range = [1, 2, 4, 5, 6, 7, 12, 13, 14]
        all_range = list(range(0, 17))

        ranges = list(win_evtxgap.get_range(test_range, all_range))
        expected_ranges = set([(1, 2), (4, 7), (12, 14)])
        self.assertSetEqual(expected_ranges, set(ranges))

        test_range = [0, 3, 4, 5, 6, 7]
        all_range = list(range(0, 17))

        ranges = list(win_evtxgap.get_range(test_range, all_range))
        expected_ranges = set([(0, 0), (3, 7)])
        self.assertSetEqual(expected_ranges, set(ranges))

        test_range = [0, 3, 4, 5, 6, 7]
        all_range = list(range(0, 5))

        with self.assertRaises(IndexError):
            _ = list(win_evtxgap.get_range(test_range, all_range))

        test_range = [0, 3, 4, 5, 6, 7]
        all_range = list(range(2, 50))

        ranges = list(win_evtxgap.get_range(test_range, all_range))
        self.assertSetEqual(set(), set(ranges))


if __name__ == "__main__":
    unittest.main()
