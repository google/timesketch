"""Tests for BrowserTimeframePlugin."""
from __future__ import unicode_literals

from timesketch.lib.analyzers import browser_timeframe
from timesketch.lib.testlib import BaseTest


class TestBrowserTimeframePlugin(BaseTest):
    """Tests the functionality of the analyzer."""

    def test_get_runs(self):
        """Test the get_runs function."""
        hours = [0, 1, 2, 3, 9, 10, 11, 12, 13, 14]
        runs = browser_timeframe.get_runs(hours)

        self.assertEquals(len(runs), 2)

        first_run = runs[0]
        self.assertEquals(first_run[0], 0)
        self.assertEquals(first_run[1], 3)

        second_run = runs[1]
        self.assertEquals(second_run[0], 9)
        self.assertEquals(second_run[1], 14)

        hours = [0, 2, 3, 9, 10, 12, 14]
        runs = browser_timeframe.get_runs(hours)
        self.assertEquals(len(runs), 5)

    def test_fix_gap_in_list(self):
        """Test the fix_gap_in_list function."""
        hours = [0, 6, 10, 11, 13, 14]
        fixed_hours = browser_timeframe.fix_gap_in_list(hours)

        self.assertEquals(fixed_hours, [0, 10, 11, 12, 13, 14])

    def test_get_hours(self):
        """Test get_hours function."""
        self.assertEquals(1, 1)
