"""Tests for EvtxGapPlugin."""

import unittest
from unittest import mock

import pandas as pd

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
        expected_ranges = {(1, 2), (4, 7), (12, 14)}
        self.assertSetEqual(expected_ranges, set(ranges))

        test_range = [0, 3, 4, 5, 6, 7]
        all_range = list(range(0, 17))

        ranges = list(win_evtxgap.get_range(test_range, all_range))
        expected_ranges = {(0, 0), (3, 7)}
        self.assertSetEqual(expected_ranges, set(ranges))

        test_range = [0, 3, 4, 5, 6, 7]
        all_range = list(range(0, 5))

        with self.assertRaises(IndexError):
            _ = list(win_evtxgap.get_range(test_range, all_range))

        test_range = [0, 3, 4, 5, 6, 7]
        all_range = list(range(2, 50))

        ranges = list(win_evtxgap.get_range(test_range, all_range))
        self.assertSetEqual(set(), set(ranges))

    def test_run_with_missing_days(self):
        """Test run() fills missing days into the per-day aggregation."""
        event_frame = pd.DataFrame(
            [
                {
                    "datetime": "2020-01-01T10:00:00",
                    "timestamp": 1577872800000000,
                    "record_number": 1,
                    "source_name": "Security",
                },
                {
                    "datetime": "2020-01-01T11:00:00",
                    "timestamp": 1577876400000000,
                    "record_number": 2,
                    "source_name": "Security",
                },
                {
                    "datetime": "2020-01-03T10:00:00",
                    "timestamp": 1578045600000000,
                    "record_number": 5,
                    "source_name": "Security",
                },
            ]
        )
        self.analyzer.sketch = mock.MagicMock(id=1)
        self.analyzer.timeline_name = "test"
        self.analyzer.event_pandas = mock.MagicMock(return_value=event_frame)

        result = self.analyzer.run()

        self.assertIn("Gaps were detected", result)
        manual_feed = [
            call.kwargs["agg_params"]
            for call in self.analyzer.sketch.add_aggregation.call_args_list
            if call.kwargs.get("agg_name") == "manual_feed"
        ]
        self.assertEqual(len(manual_feed), 1)
        days = {row["day"]: row["count"] for row in manual_feed[0]["data"]}
        self.assertEqual(days, {"20200101": 2, "20200102": 0, "20200103": 1})


if __name__ == "__main__":
    unittest.main()
