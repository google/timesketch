"""Tests for SessionizerSketchPlugin."""

from __future__ import unicode_literals

import unittest
import mock

from timesketch.lib.analyzers.sessionizer import SessionizerSketchPlugin
from timesketch.lib.analyzers.base_sessionizer_test import BaseSessionizerTest
from timesketch.lib.analyzers.base_sessionizer_test import _create_mock_event
from timesketch.lib.testlib import BaseTest
from timesketch.lib.testlib import MockDataStore

class TestSessionizerPlugin(BaseTest, BaseSessionizerTest):
    """Tests the functionality of the sessionizing sketch analyzer, focusing
    on edge cases."""
    analyzer_class = SessionizerSketchPlugin

    @mock.patch('timesketch.lib.analyzers.interface.ElasticsearchDataStore',
                MockDataStore)
    def test_multiple_sessions(self):
        """Test multiple events, two of which are in the same session and
        one in a different session."""
        with mock.patch.object(SessionizerSketchPlugin,
                               'event_stream',
                               return_value=_create_mock_event(
                                   0, 3, time_diffs=[3000, 400000000])):
            index = 'test_index'
            sketch_id = 1
            analyser = SessionizerSketchPlugin(index, sketch_id)
            message = analyser.run()
            self.assertEqual(
                message,
                'Sessionizing completed, number of session created: 2')

            ds = MockDataStore('test', 0)
            event1 = (ds.get_event('test_index', '0', stored_events=True))
            self.assertEqual(event1['_source']['session_id'],
                             {'all_events': 1})
            event2 = (ds.get_event('test_index', '101', stored_events=True))
            self.assertEqual(event2['_source']['session_id'],
                             {'all_events': 1})
            event3 = (ds.get_event('test_index', '202', stored_events=True))
            self.assertEqual(event3['_source']['session_id'],
                             {'all_events': 2})
            self._check_surrounding_events([202], 'all_events')

    @mock.patch('timesketch.lib.analyzers.interface.ElasticsearchDataStore',
                MockDataStore)
    def test_zero_time_diff(self):
        """Test events with no time difference between them are allocated
        correctly."""
        with mock.patch.object(SessionizerSketchPlugin,
                               'event_stream',
                               return_value=_create_mock_event(
                                   0, 2, time_diffs=[0])):
            index = 'test_index'
            sketch_id = 1
            analyser = SessionizerSketchPlugin(index, sketch_id)
            message = analyser.run()
            self.assertEqual(
                message,
                'Sessionizing completed, number of session created: 1')

            ds = MockDataStore('test', 0)
            event1 = (ds.get_event('test_index', '0', stored_events=True))
            self.assertEqual(event1['_source']['session_id'],
                             {'all_events': 1})
            event1 = (ds.get_event('test_index', '100', stored_events=True))
            self.assertEqual(event1['_source']['session_id'],
                             {'all_events': 1})
            event2 = (ds.get_event('test_index', '101', stored_events=True))
            self.assertEqual(event2['_source']['session_id'],
                             {'all_events': 1})

    @mock.patch('timesketch.lib.analyzers.interface.ElasticsearchDataStore',
                MockDataStore)
    def test_zero_events(self):
        """Test the behaviour of the sessionizer when given zero events."""
        with mock.patch.object(SessionizerSketchPlugin,
                               'event_stream',
                               return_value=_create_mock_event(0, 0)):
            index = 'test_index'
            sketch_id = 1
            analyser = SessionizerSketchPlugin(index, sketch_id)
            message = analyser.run()
            self.assertEqual(
                message,
                'Sessionizing completed, number of session created: 0')

    @mock.patch('timesketch.lib.analyzers.interface.ElasticsearchDataStore',
                MockDataStore)
    def test_one_event(self):
        """Test the behaviour of the sessionizer when given one event."""
        with mock.patch.object(SessionizerSketchPlugin,
                               'event_stream',
                               return_value=_create_mock_event(0, 1)):
            index = 'test_index'
            sketch_id = 1
            analyser = SessionizerSketchPlugin(index, sketch_id)
            message = analyser.run()
            self.assertEqual(
                message,
                'Sessionizing completed, number of session created: 1')
            ds = MockDataStore('test', 0)
            event1 = (ds.get_event('test_index', '0', stored_events=True))
            self.assertEqual(event1['_source']['session_id'],
                             {'all_events': 1})


if __name__ == '__main__':
    unittest.main()
