"""Tests for expert sessionizers."""

from __future__ import unicode_literals

import mock

from timesketch.lib.analyzers.expert_sessionizers import \
    WebActivitySessionizerSketchPlugin
from timesketch.lib.analyzers.sessionizer_test import _create_mock_event
from timesketch.lib.testlib import BaseTest
from timesketch.lib.testlib import MockDataStore


class TestWebActivitySessionizerPlugin(BaseTest):
    """Tests the functionality of the web activity sessionizing sketch
    analyzer."""
    @mock.patch('timesketch.lib.analyzers.interface.ElasticsearchDataStore',
                MockDataStore)
    def test_analyzer(self):
        """Test basic analyzer functionality."""
        index = 'test_index'
        sketch_id = 1
        analyser = WebActivitySessionizerSketchPlugin(index, sketch_id)
        self.assertIsInstance(analyser, WebActivitySessionizerSketchPlugin)
        self.assertEqual(index, analyser.index_name)
        self.assertEqual(sketch_id, analyser.sketch.id)

    @mock.patch('timesketch.lib.analyzers.interface.ElasticsearchDataStore',
                MockDataStore)
    def test_same_session(self):
        """Test multiple events in the same session are allocated and labelled
        correctly."""
        with mock.patch.object(WebActivitySessionizerSketchPlugin,
                               'event_stream',
                               return_value=_create_mock_event(
                                   0, 2, time_diffs=[200])):
            index = 'test_index'
            sketch_id = 1
            analyser = WebActivitySessionizerSketchPlugin(index, sketch_id)
            message = analyser.run()
            self.assertEqual(
                message,
                'Sessionizing completed, number of session created: 1')

            ds = MockDataStore('test', 0)
            event1 = (ds.get_event('test_index', '0', stored_events=True))
            self.assertEqual(event1['_source']['session_id'],
                             {'web_activity': 1})
            # checking event with id '101' as 100 events have been inserted
            # as 'padding' (see _create_mock_event())
            event2 = (ds.get_event('test_index', '101', stored_events=True))
            self.assertEqual(event2['_source']['session_id'],
                             {'web_activity': 1})

    @mock.patch('timesketch.lib.analyzers.interface.ElasticsearchDataStore',
                MockDataStore)
    def test_diff_sessions(self):
        """Test multiple events in different sesssions are allocated and
        labelled correctly."""
        with mock.patch.object(WebActivitySessionizerSketchPlugin,
                               'event_stream',
                               return_value=_create_mock_event(
                                   0, 2, time_diffs=[1000000000])):
            index = 'test_index'
            sketch_id = 1
            analyser = WebActivitySessionizerSketchPlugin(index, sketch_id)
            message = analyser.run()
            self.assertEqual(
                message,
                'Sessionizing completed, number of session created: 2')

            ds = MockDataStore('test', 0)
            event1 = (ds.get_event('test_index', '0', stored_events=True))
            self.assertEqual(event1['_source']['session_id'],
                             {'web_activity': 1})
            event2 = (ds.get_event('test_index', '101', stored_events=True))
            self.assertEqual(event2['_source']['session_id'],
                             {'web_activity': 2})

    @mock.patch('timesketch.lib.analyzers.interface.ElasticsearchDataStore',
                MockDataStore)
    def test_edge_time_diff(self):
        """Test events with the edge time difference between them are allocated
        correctly."""
        with mock.patch.object(WebActivitySessionizerSketchPlugin,
                               'event_stream',
                               return_value=_create_mock_event(
                                   0, 2, time_diffs=[600000000])):
            index = 'test_index'
            sketch_id = 1
            analyser = WebActivitySessionizerSketchPlugin(index, sketch_id)
            message = analyser.run()
            self.assertEqual(
                message,
                'Sessionizing completed, number of session created: 1')

            ds = MockDataStore('test', 0)
            event1 = (ds.get_event('test_index', '0', stored_events=True))
            self.assertEqual(event1['_source']['session_id'],
                             {'web_activity': 1})
            event2 = (ds.get_event('test_index', '101', stored_events=True))
            self.assertEqual(event2['_source']['session_id'],
                             {'web_activity': 1})
