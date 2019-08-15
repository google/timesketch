"""Tests for TimestompPlugin."""
from __future__ import unicode_literals

import mock

from timesketch.lib.analyzers import timestomp
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
    def __init__(self, name, std_info_timestamp, fn_timestamps,
                 expected_si_diffs, expected_fn_diffs, is_timestomp):
        self.name = name
        ref = 7357
        ts_desc = "TEST"
        std_event = MockEvent()
        file_names = [(MockEvent(), ts) for ts in fn_timestamps]

        self.file_info = timestomp.FileInfo(ref, ts_desc, std_event,
                                            std_info_timestamp, file_names)
        self.expected_fn_diffs = expected_fn_diffs
        self.expected_si_diffs = expected_si_diffs

        self.is_timestomp = is_timestomp

class TestTimestompPlugin(BaseTest):
    """Tests the functionality of the analyzer."""

    #def __init__(self, *args, **kwargs):
    #    super(TestTimestompPlugin, self).__init__(*args, **kwargs)

    @mock.patch(
        u'timesketch.lib.analyzers.interface.ElasticsearchDataStore',
        MockDataStore)
    def test_handle_timestomp(self):
        analyzer = timestomp.TimestompSketchPlugin('test_handle_timestomp', 1)

        test_cases = [
            FileInfoTestCase("0", 1000000000000, [1000000000000],None, [None], False)
        ]

        for tc in test_cases:
            ret = analyzer.handle_timestomp(tc.file_info)

            std_diffs = tc.file_info.std_info_event.source.get('time_deltas')
            fn_diffs = [event.source.get('time_delta') for event, _ in
                        tc.file_info.file_names]

            self.assertEqual(ret, tc.is_timestomp)
            self.assertEqual(std_diffs, tc.expected_si_diffs)
            self.assertEqual(fn_diffs, tc.expected_fn_diffs)


    # Mock the Elasticsearch datastore.
    @mock.patch(
        u'timesketch.lib.analyzers.interface.ElasticsearchDataStore',
        MockDataStore)
    def test_analyzer(self):
        """Test analyzer."""
        # TODO: Write actual tests here.
        self.assertEqual(True, True)
