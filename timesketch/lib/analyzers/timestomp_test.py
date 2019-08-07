"""Tests for TimestompPlugin."""
from __future__ import unicode_literals

import mock

from timesketch.lib.analyzers import timestomp as ts
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

class TestTimestompPlugin(BaseTest):
    """Tests the functionality of the analyzer."""

    def __init__(self, *args, **kwargs):
        super(TestTimestompPlugin, self).__init__(*args, **kwargs)

    # TODO: like in timestomp.py, find better name and replace.
    # Mock the Elasticsearch datastore.
    @mock.patch(
        u'timesketch.lib.analyzers.interface.ElasticsearchDataStore',
        MockDataStore)
    def test_handle_timestomp(self):
        analyzer = ts.TimestompSketchPlugin('timestomp_test_handle_timestomp', 1)
        test_cases = [
            (ts.FileInfo(si_events=[MockEvent()],si_timestamps=[6000000001],fn_events=[MockEvent()],fn_timestamps=[0]), True)
        ]

        for test_case in test_cases:
          self.assertEqual(analyzer.handle_timestomp(test_case[0]), test_case[1])


    # Mock the Elasticsearch datastore.
    @mock.patch(
        u'timesketch.lib.analyzers.interface.ElasticsearchDataStore',
        MockDataStore)
    def test_analyzer(self):
        """Test analyzer."""
        # TODO: Write actual tests here.
        self.assertEqual(True, True)
