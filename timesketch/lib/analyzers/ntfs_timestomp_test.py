"""Tests for NtfsTimestompPlugin."""

from unittest import mock

from timesketch.lib.analyzers import ntfs_timestomp
from timesketch.lib.testlib import BaseTest
from timesketch.lib.testlib import MockDataStore


class MockEvent:
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


class FileInfoTestCase:
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

    @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    def test_is_suspicious_no_std_info(self):
        """Test that FileInfo without a std_info_event is never suspicious."""
        analyzer = ntfs_timestomp.NtfsTimestompSketchPlugin("test", 1)
        file_info = ntfs_timestomp.FileInfo(
            file_reference=1,
            timestamp_desc="Content Modification Time",
            std_info_event=None,
            std_info_timestamp=0,
            file_names=[(MockEvent(), 9000000000)],
        )
        self.assertFalse(analyzer.is_suspicious(file_info))

    @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    def test_is_suspicious_no_file_names(self):
        """Test that FileInfo with no file_names is never suspicious."""
        analyzer = ntfs_timestomp.NtfsTimestompSketchPlugin("test", 1)
        file_info = ntfs_timestomp.FileInfo(
            file_reference=1,
            timestamp_desc="Content Modification Time",
            std_info_event=MockEvent(),
            std_info_timestamp=0,
            file_names=[],
        )
        self.assertFalse(analyzer.is_suspicious(file_info))

    @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    def test_is_suspicious_within_threshold(self):
        """Test that file_names within the threshold are not flagged."""
        analyzer = ntfs_timestomp.NtfsTimestompSketchPlugin("test", 1)
        # threshold is 10 * 60000000 = 600000000 microseconds by default.
        # A diff smaller than the threshold must not trigger detection.
        fn_event = MockEvent()
        file_info = ntfs_timestomp.FileInfo(
            file_reference=1,
            timestamp_desc="Content Modification Time",
            std_info_event=MockEvent(),
            std_info_timestamp=0,
            file_names=[(fn_event, analyzer.threshold - 1)],
        )
        self.assertFalse(analyzer.is_suspicious(file_info))
        # The time_delta attribute must NOT have been set on the file_name event.
        self.assertIsNone(fn_event.source.get("time_delta"))

    @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    def test_is_suspicious_timestomped(self):
        """Test that file_names with differences above the threshold are flagged."""
        analyzer = ntfs_timestomp.NtfsTimestompSketchPlugin("test", 1)
        fn_event = MockEvent()
        si_event = MockEvent()
        large_diff = analyzer.threshold + 1
        file_info = ntfs_timestomp.FileInfo(
            file_reference=1,
            timestamp_desc="Content Modification Time",
            std_info_event=si_event,
            std_info_timestamp=0,
            file_names=[(fn_event, large_diff)],
        )
        self.assertTrue(analyzer.is_suspicious(file_info))
        # The time_delta attribute must be set on every suspicious file_name.
        self.assertEqual(fn_event.source.get("time_delta"), large_diff)
        # The accumulated time_deltas must be stored on the STD_INFO event.
        self.assertEqual(si_event.source.get("time_deltas"), [large_diff])

    @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    def test_is_suspicious_mixed_file_names(self):
        """Test that a single within-threshold file_name prevents detection."""
        analyzer = ntfs_timestomp.NtfsTimestompSketchPlugin("test", 1)
        fn_event_large = MockEvent()
        fn_event_small = MockEvent()
        file_info = ntfs_timestomp.FileInfo(
            file_reference=1,
            timestamp_desc="Content Modification Time",
            std_info_event=MockEvent(),
            std_info_timestamp=0,
            file_names=[
                (fn_event_large, analyzer.threshold + 1),
                (fn_event_small, analyzer.threshold - 1),
            ],
        )
        # One file_name is within threshold — detection must be suppressed.
        self.assertFalse(analyzer.is_suspicious(file_info))
