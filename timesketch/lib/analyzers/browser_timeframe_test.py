"""Tests for BrowserTimeframePlugin."""

from __future__ import unicode_literals

import numpy as np
import pandas as pd

from timesketch.lib.analyzers import browser_timeframe
from timesketch.lib.testlib import BaseTest


class TestBrowserTimeframePlugin(BaseTest):
    """Tests the functionality of the analyzer."""

    def test_get_list_of_consecutive_sequences(self):
        """Test the get_list_of_consecutive_sequences function."""
        hours = [0, 1, 2, 3, 9, 10, 11, 12, 13, 14]
        runs = browser_timeframe.get_list_of_consecutive_sequences(hours)

        self.assertEqual(len(runs), 2)

        first_run = runs[0]
        self.assertEqual(first_run[0], 0)
        self.assertEqual(first_run[1], 3)

        second_run = runs[1]
        self.assertEqual(second_run[0], 9)
        self.assertEqual(second_run[1], 14)

        hours = [0, 2, 3, 9, 10, 12, 14]
        runs = browser_timeframe.get_list_of_consecutive_sequences(hours)
        self.assertEqual(len(runs), 5)

    def test_fix_gap_in_list(self):
        """Test the fix_gap_in_list function."""
        hours = [0, 6, 10, 11, 13, 14]
        fixed_hours = browser_timeframe.fix_gap_in_list(hours)

        self.assertEqual(fixed_hours, [0, 10, 11, 12, 13, 14])

    def test_get_active_hours(self):
        """Test get_active_hours function."""
        date_array = np.random.randn(500)
        hours = [
            np.repeat(0, 80),
            np.repeat(1, 50),
            np.repeat(4, 10),
            np.repeat(7, 8),
            np.repeat(12, 12),
            np.repeat(18, 40),
            np.repeat(19, 50),
            np.repeat(20, 10),
            np.repeat(21, 90),
            np.repeat(22, 50),
            np.repeat(23, 100),
        ]

        data_frame = pd.DataFrame(
            {"hour": np.concatenate(hours), "datetime": date_array}
        )

        expected_hours = [0, 1, 18, 19, 20, 21, 22, 23]
        active_hours, _, _ = browser_timeframe.get_active_hours(data_frame)
        self.assertEqual(active_hours, expected_hours)
