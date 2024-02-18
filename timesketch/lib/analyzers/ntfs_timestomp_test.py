"""Tests for NtfsTimestompPlugin."""

from __future__ import unicode_literals

import mock

from timesketch.lib.analyzers import ntfs_timestomp
from timesketch.lib.testlib import BaseTest
from timesketch.lib.testlib import MockDataStore


class MockEvent(object):
    def __init__(self, source=None):
        if source:
            self.source = source
        else:
            self.source = {}
        self.label = ""

    def add_attributes(self, attributes):
        self.source = dict(self.source, **attributes)

    def add_label(self, label):
        self.label = label

    def commit(self):
        pass


class FileInfoTestCase(object):
    def __init__(
        self,
        name,
        std_info_timestamp,
        fn_timestamps,
        expected_si_diffs,
        expected_fn_diffs,
        is_timestomp,
    ):
        self.name = name
        ref = 7357
        ts_desc = "TEST"
        std_event = MockEvent()
        file_names = [(MockEvent(), ts) for ts in fn_timestamps]

        self.file_info = ntfs_timestomp.FileInfo(
            ref, ts_desc, std_event, std_info_timestamp, file_names
        )
        self.expected_fn_diffs = expected_fn_diffs
        self.expected_si_diffs = expected_si_diffs

        self.is_timestomp = is_timestomp


class TestNtfsTimestompPlugin(BaseTest):
    """Tests the functionality of the analyzer."""

    @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    def test_is_suspicious(self):
        """Test is_suspicious method."""
        analyzer = ntfs_timestomp.NtfsTimestompSketchPlugin("is_suspicious", 1)

        test_cases = [
            FileInfoTestCase(
                "no timestomp", 1000000000000, [1000000000000], None, [None], False
            ),
            FileInfoTestCase(
                "multiple file_names and all of them are timestomped",
                0,
                [6000000000, 7000000000, 8000000000],
                [6000000000, 7000000000, 8000000000],
                [6000000000, 7000000000, 8000000000],
                True,
            ),
            FileInfoTestCase(
                "one of the file_names matches exactly",
                0,
                [0, 7000000000, 8000000000],
                None,
                [None, None, None],
                False,
            ),
            FileInfoTestCase(
                "file_name is within threshold",
                0,
                [analyzer.threshold, 7000000000, 8000000000],
                None,
                [None, None, None],
                False,
            ),
            FileInfoTestCase(
                "file_name is within threshold",
                0,
                [600000000, 7000000000, 8000000000],
                None,
                [None, None, None],
                False,
            ),
        ]

        for tc in test_cases:
            ret = analyzer.is_suspicious(tc.file_info)

            std_diffs = tc.file_info.std_info_event.source.get("time_deltas")
            fn_diffs = [
                event.source.get("time_delta") for event, _ in tc.file_info.file_names
            ]

            self.assertEqual(ret, tc.is_timestomp)
            self.assertEqual(std_diffs, tc.expected_si_diffs)
            self.assertEqual(fn_diffs, tc.expected_fn_diffs)

    # Mock the OpenSearch datastore.
    @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    def test_analyzer(self):
        """Test analyzer."""
        # TODO: Write actual tests here.
        self.assertEqual(True, True)
