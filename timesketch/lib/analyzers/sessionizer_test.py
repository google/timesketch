"""Tests for SessionizerSketchPlugin."""

from __future__ import unicode_literals

import unittest
import copy

import mock

from timesketch.lib.analyzers import sessionizer
from timesketch.lib.analyzers.sessionizer import SessionizerSketchPlugin
from timesketch.lib.testlib import BaseTest
from timesketch.lib.testlib import MockDataStore
from timesketch.lib.analyzers.interface import Event
from timesketch.models.user import User
from timesketch.models.sketch import Sketch


class TestSessionizerPlugin(BaseTest):
    """Tests the functionality of the sessionizing sketch analyzer."""
    @mock.patch('timesketch.lib.analyzers.interface.ElasticsearchDataStore',
                MockDataStore)
    def test_analyzer(self):
        """Test basic analyzer functionality."""
        index = 'test_index'
        sketch_id = 1
        analyser = sessionizer.SessionizerSketchPlugin(index, sketch_id)
        self.assertIsInstance(analyser, SessionizerSketchPlugin)
        self.assertEqual(index, analyser.index_name)
        self.assertEqual(sketch_id, analyser.sketch.id)

    @mock.patch('timesketch.lib.analyzers.interface.ElasticsearchDataStore',
                MockDataStore)
    def test_same_session(self):
        """Test multiple events in the same session are allocated correctly."""
        with mock.patch.object(SessionizerSketchPlugin,
                               'event_stream',
                               return_value=_create_mock_event(
                                   0, 2, time_diffs=[200])):
            index = 'test_index'
            sketch_id = 1
            analyser = sessionizer.SessionizerSketchPlugin(index, sketch_id)
            message = analyser.run()
            self.assertEqual(
                message,
                'Sessionizing completed, number of session created: 1')

            ds = MockDataStore('test', 0)
            event1 = (ds.get_event('test_index', '0', stored_events=True))
            self.assertEqual(event1['_source']['session_number'], 1)
            # checking event with id '101' as 100 events have been inserted
            # as 'padding' (see _create_mock_event())
            event2 = (ds.get_event('test_index', '101', stored_events=True))
            self.assertEqual(event2['_source']['session_number'], 1)

    @mock.patch('timesketch.lib.analyzers.interface.ElasticsearchDataStore',
                MockDataStore)
    def test_diff_session(self):
        """Test multiple events in different sessions are allocated
        correctly."""
        with mock.patch.object(SessionizerSketchPlugin,
                               'event_stream',
                               return_value=_create_mock_event(
                                   0, 2, time_diffs=[400000000])):
            index = 'test_index'
            sketch_id = 1
            analyser = sessionizer.SessionizerSketchPlugin(index, sketch_id)
            message = analyser.run()
            self.assertEqual(
                message,
                'Sessionizing completed, number of session created: 2')

            ds = MockDataStore('test', 0)
            event1 = (ds.get_event('test_index', '0', stored_events=True))
            self.assertEqual(event1['_source']['session_number'], 1)

            event2 = (ds.get_event('test_index', '101', stored_events=True))
            self.assertEqual(event2['_source']['session_number'], 2)
            self.check_surrounding_events([101])

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
            analyser = sessionizer.SessionizerSketchPlugin(index, sketch_id)
            message = analyser.run()
            self.assertEqual(
                message,
                'Sessionizing completed, number of session created: 2')

            ds = MockDataStore('test', 0)
            event1 = (ds.get_event('test_index', '0', stored_events=True))
            self.assertEqual(event1['_source']['session_number'], 1)
            event2 = (ds.get_event('test_index', '101', stored_events=True))
            self.assertEqual(event2['_source']['session_number'], 1)
            event3 = (ds.get_event('test_index', '202', stored_events=True))
            self.assertEqual(event3['_source']['session_number'], 2)
            self.check_surrounding_events([202])

    @mock.patch('timesketch.lib.analyzers.interface.ElasticsearchDataStore',
                MockDataStore)
    def test_edge_time_diff(self):
        """Test events with the edge time difference between them are
        allocated correctly."""
        with mock.patch.object(SessionizerSketchPlugin,
                               'event_stream',
                               return_value=_create_mock_event(
                                   0, 2, time_diffs=[300000000])):
            index = 'test_index'
            sketch_id = 1
            analyser = sessionizer.SessionizerSketchPlugin(index, sketch_id)
            message = analyser.run()
            self.assertEqual(
                message,
                'Sessionizing completed, number of session created: 1')

            ds = MockDataStore('test', 0)
            event1 = (ds.get_event('test_index', '0', stored_events=True))
            self.assertEqual(event1['_source']['session_number'], 1)
            event2 = (ds.get_event('test_index', '101', stored_events=True))
            self.assertEqual(event2['_source']['session_number'], 1)

    @mock.patch('timesketch.lib.analyzers.interface.ElasticsearchDataStore',
                MockDataStore)
    def test_zero_time_diff(self):
        """Test events with no time difference between them are allocated
        correctly."""
        with mock.patch.object(SessionizerSketchPlugin,
                               'event_stream',
                               return_value=_create_mock_event(0, 2,
                                                               time_diffs=[0])):
            index = 'test_index'
            sketch_id = 1
            analyser = sessionizer.SessionizerSketchPlugin(index, sketch_id)
            message = analyser.run()
            self.assertEqual(
                message,
                'Sessionizing completed, number of session created: 1')

            ds = MockDataStore('test', 0)
            event1 = (ds.get_event('test_index', '0', stored_events=True))
            self.assertEqual(event1['_source']['session_number'], 1)
            event1 = (ds.get_event('test_index', '100', stored_events=True))
            self.assertEqual(event1['_source']['session_number'], 1)
            event2 = (ds.get_event('test_index', '101', stored_events=True))
            self.assertEqual(event2['_source']['session_number'], 1)

    @mock.patch('timesketch.lib.analyzers.interface.ElasticsearchDataStore',
                MockDataStore)
    def test_zero_events(self):
        """Test the behaviour of the sessionizer when given zero events."""
        with mock.patch.object(SessionizerSketchPlugin,
                               'event_stream',
                               return_value=_create_mock_event(0, 0)):
            index = 'test_index'
            sketch_id = 1
            analyser = sessionizer.SessionizerSketchPlugin(index, sketch_id)
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
            analyser = sessionizer.SessionizerSketchPlugin(index, sketch_id)
            message = analyser.run()
            self.assertEqual(
                message,
                'Sessionizing completed, number of session created: 1')
            ds = MockDataStore('test', 0)
            event1 = (ds.get_event('test_index', '0', stored_events=True))
            self.assertEqual(event1['_source']['session_number'], 1)

    def check_surrounding_events(self, threshold_ids):
        """Checks that the events surrounding the first event in a new session
        are allocated correctly.

        Args:
            threshold_ids: a list of IDs of the first events in the sessions.
        """
        ds = MockDataStore('test', 0)
        session_no = 1
        last_id = threshold_ids[-1]

        for threshold_id in threshold_ids:
            if threshold_id != 0:
                # check previous event is in the previous session
                event = (ds.get_event('test_index', str(threshold_id - 1),
                                      stored_events=True))
                self.assertEqual(event['_source']['session_number'],
                                 session_no)

            if threshold_id != last_id:
                # check next event is in the same session (as the event with
                # threshold id)
                session_no += 1
                event = (ds.get_event('test_index', str(threshold_id + 1),
                                      stored_events=True))
                self.assertEqual(event['_source']['session_number'],
                                 session_no)


def _create_mock_event(event_id, quantity, time_diffs=None):
    """
    Returns an instance of Event, based on the MockDataStore event_dict
    example.

    Args:
        event_id: Desired ID for the Event.
        quantity: The number of Events to be generated.
        time_diffs: A list of time differences between the generated Events.

    Returns:
        A generator of Event objects.
    """

    if not time_diffs:
        time_diffs = [0]
    if quantity < 0:
        quantity = abs(quantity)

    # If the list of time differences is too small to be compatible with the
    # quantity of events, then extend the list with the last value for as many
    # items as necessary.
    if quantity - len(time_diffs) > 0:
        time_diffs.extend([time_diffs[len(time_diffs) - 1]] *
                          (quantity - len(time_diffs)))

    # Setup for Event object initialisation
    ds = MockDataStore('test', 0)
    user = User('test_user')
    sketch = Sketch('test_sketch', 'description', user)
    label = sketch.Label(label='Test label', user=user)
    sketch.labels.append(label)

    event_timestamp = 1410895419859714
    event_template = ds.get_event('test', 'test')

    for i in range(quantity):
        eventObj = create_eventObj(ds, sketch, event_template, event_id,
                                   event_timestamp)
        yield eventObj

        # adding extra events after every requested event for better simulation
        # of real timeline data i.e. working with a larger dataset
        for _ in range(100):
            event_timestamp += 1
            event_id += 1
            eventObj = create_eventObj(ds, sketch, event_template, event_id,
                                       event_timestamp)

            yield eventObj

        event_timestamp += abs(time_diffs[i])
        event_id += 1


def create_eventObj(ds, sketch, event_template, event_id, ts):
    event = event_template
    event['_id'] = str(event_id)
    event['_source']['timestamp'] = ts

    eventObj = Event(copy.deepcopy(event), ds, sketch)
    ds.import_event(eventObj.index_name,
                    eventObj.event_type,
                    event_id=eventObj.event_id,
                    event=eventObj.source)
    return eventObj


if __name__ == '__main__':
    unittest.main()
