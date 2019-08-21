"""Tests for expert sessionizers."""

from __future__ import unicode_literals

import unittest
import mock

from timesketch.lib.analyzers.expert_sessionizers import \
    WebActivitySessionizerSketchPlugin
from timesketch.lib.analyzers.base_sessionizer_test import BaseSessionizerTest
from timesketch.lib.analyzers.base_sessionizer_test import _create_mock_event
from timesketch.lib.testlib import BaseTest
from timesketch.lib.testlib import MockDataStore

class TestWebActivitySessionizerPlugin(BaseTest, BaseSessionizerTest):
    """Tests the functionality of the web activity sessionizing sketch
    analyzer."""
    analyzer_class = WebActivitySessionizerSketchPlugin

    @mock.patch('timesketch.lib.analyzers.interface.ElasticsearchDataStore',
                MockDataStore)
    def test_event_type(self):
        """Test the mocking of events returns an event stream that matches the
        query for the analyzer."""
        with mock.patch.object(
                self.analyzer_class,
                'event_stream',
                return_value=_create_mock_event(
                    0,
                    2,
                    source_attrs={'source_short': 'WEBHIST'})):
            index = 'test_index'
            sketch_id = 1
            analyzer = self.analyzer_class(index, sketch_id)
            message = analyzer.run()
            self.assertEqual(
                message,
                'Sessionizing completed, number of session created: 1')

            ds = MockDataStore('test', 0)
            event1 = (ds.get_event('test_index', '0', stored_events=True))
            self.assertEqual(event1['_source']['source_short'], 'WEBHIST')
            event2 = (ds.get_event('test_index', '101', stored_events=True))
            self.assertEqual(event2['_source']['source_short'], 'WEBHIST')

if __name__ == '__main__':
    unittest.main()
