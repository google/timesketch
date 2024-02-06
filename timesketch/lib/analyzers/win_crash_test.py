"""Tests for WinCrashPlugin."""

from __future__ import unicode_literals

import unittest
import mock

from timesketch.lib.analyzers import win_crash
from timesketch.lib.testlib import BaseTest
from timesketch.lib.testlib import MockDataStore


class TestWinCrashPlugin(BaseTest):
    """Tests the functionality of the analyzer."""

    @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    def setUp(self):
        super().setUp()
        self.analyzer = win_crash.WinCrashSketchPlugin("test_index", 1)

    def test_formulate_query(self):
        """Test generator of OpenSearch queries"""
        template = {
            "Event - App Error": (
                'data_type:"windows:evtx:record"',
                'event_level:"2"',
            ),
            "File - WER Report": (
                'data_type:"fs:stat"',
                'filename:"/Microsoft/Windows/WER/"',
            ),
            "Registry - Crash Reporting": (
                'data_type:"windows:registry:key_value"',
                r'key_path:"\\Control\\CrashControl"',
            ),
        }
        expected_query = (
            (
                '(data_type:"windows:evtx:record" AND event_level:"2")'
                ' OR (data_type:"fs:stat" AND filename:"/Microsoft/Windows/WER/")'
                ' OR (data_type:"windows:registry:key_value" AND '
                'key_path:"\\\\Control\\\\CrashControl")'
            )
            .replace("(", "")
            .replace(")", "")
        )

        # To prevent flakiness we break up the query into a set.
        expected_set = set(expected_query.split())

        formulated_query = self.analyzer.formulate_query(template)
        formulated_set = set(formulated_query.replace("(", "").replace(")", "").split())

        self.assertSetEqual(expected_set, formulated_set)

    def test_extract_filename(self):
        """Test generator of filename extraction regex"""
        string_list = (
            "\\WER\\ReportQueue\\AppCrash_notepad.exe_8d163e29d3960561ca2e972"
            "3640cd8fff5c2ad5_cab_0a5810ac\\Report.wer",
            "/WER/ReportQueue/NonCritical_notepad.exe_d473a376adfb18a7b165c5e"
            "3c26de43cd8bccb_cab_07fd2620",
            "/WER/ReportQueue/NonCritical_x64_d473a376adfb18a7b165c5e3c26de43"
            "cd8bccb_cab_07fd2620",
            "Strings: ['iexplore.exe', '8.0.7601.17514'",
        )
        expected_list = ("notepad.exe", "notepad.exe", "", "iexplore.exe")

        for i, s in enumerate(string_list):
            self.assertEqual(self.analyzer.extract_filename(s), expected_list[i])

    def test_mark_as_crash(self):
        mock_event = mock.Mock()
        filename = "sample_filename.exe"
        self.analyzer.mark_as_crash(mock_event, filename)
        mock_event.add_attributes.assert_called_once_with({"crash_app": filename})
        mock_event.add_tags.assert_called_once_with(["win_crash"])

        mock_event = mock.Mock()
        self.analyzer.mark_as_crash(mock_event, None)
        mock_event.add_attributes.assert_not_called()
        mock_event.add_tags.assert_called_once_with(["win_crash"])


if __name__ == "__main__":
    unittest.main()
