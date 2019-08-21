"""Tests common to all sessionizing sketch plugins."""

from __future__ import unicode_literals

import copy
import mock

from timesketch.lib.testlib import MockDataStore
from timesketch.lib.analyzers.interface import Event
from timesketch.models.user import User
from timesketch.models.sketch import Sketch

class BaseSessionizerTest(object):
    """Base class for tests for sessionizers."""
    @mock.patch('timesketch.lib.analyzers.interface.ElasticsearchDataStore',
                MockDataStore)
    def test_analyzer(self):
        """Test basic analyzer functionality."""
        index = 'test_index'
        sketch_id = 1
        analyzer = self.analyzer_class(index, sketch_id)
        self.assertIsInstance(analyzer, self.analyzer_class)
        self.assertEqual(index, analyzer.index_name)
        self.assertEqual(sketch_id, analyzer.sketch.id)

    @mock.patch('timesketch.lib.analyzers.interface.ElasticsearchDataStore',
                MockDataStore)
    def test_same_session(self):
        """Test multiple events in the same session are allocated correctly."""
        with mock.patch.object(
                self.analyzer_class,
                'event_stream',
                return_value=_create_mock_event(
                    0,
                    2,
                    time_diffs=[self.analyzer_class.max_time_diff_micros / 2])):
            index = 'test_index'
            sketch_id = 1
            analyzer = self.analyzer_class(index, sketch_id)
            message = analyzer.run()
            self.assertEqual(
                message,
                'Sessionizing completed, number of session created: 1')

            ds = MockDataStore('test', 0)
            event1 = (ds.get_event('test_index', '0', stored_events=True))
            self.assertEqual(event1['_source']['session_id'],
                             {analyzer.session_type: 1})
            # checking event with id '101' as 100 events have been inserted
            # as 'padding' (see _create_mock_event())
            event2 = (ds.get_event('test_index', '101', stored_events=True))
            self.assertEqual(event2['_source']['session_id'],
                             {analyzer.session_type: 1})

    @mock.patch('timesketch.lib.analyzers.interface.ElasticsearchDataStore',
                MockDataStore)
    def test_diff_session(self):
        """Test multiple events in different sessions are allocated
        correctly."""
        with mock.patch.object(
                self.analyzer_class,
                'event_stream',
                return_value=_create_mock_event(
                    0,
                    2,
                    time_diffs=[
                        self.analyzer_class.max_time_diff_micros +
                        (self.analyzer_class.max_time_diff_micros / 2)])):
            index = 'test_index'
            sketch_id = 1
            analyzer = self.analyzer_class(index, sketch_id)
            message = analyzer.run()
            self.assertEqual(
                message,
                'Sessionizing completed, number of session created: 2')

            ds = MockDataStore('test', 0)
            event1 = (ds.get_event('test_index', '0', stored_events=True))
            self.assertEqual(event1['_source']['session_id'],
                             {analyzer.session_type: 1})

            event2 = (ds.get_event('test_index', '101', stored_events=True))
            self.assertEqual(event2['_source']['session_id'],
                             {analyzer.session_type: 2})
            self._check_surrounding_events([101], analyzer.session_type)

    @mock.patch('timesketch.lib.analyzers.interface.ElasticsearchDataStore',
                MockDataStore)
    def test_edge_time_diff(self):
        """Test events with the edge time difference between them are
        allocated correctly."""
        with mock.patch.object(
                self.analyzer_class,
                'event_stream',
                return_value=_create_mock_event(
                    0,
                    2,
                    time_diffs=[self.analyzer_class.max_time_diff_micros])):
            index = 'test_index'
            sketch_id = 1
            analyzer = self.analyzer_class(index, sketch_id)
            message = analyzer.run()
            self.assertEqual(
                message,
                'Sessionizing completed, number of session created: 1')

            ds = MockDataStore('test', 0)
            event1 = (ds.get_event('test_index', '0', stored_events=True))
            self.assertEqual(event1['_source']['session_id'],
                             {analyzer.session_type: 1})
            event2 = (ds.get_event('test_index', '101', stored_events=True))
            self.assertEqual(event2['_source']['session_id'],
                             {analyzer.session_type: 1})

    def _check_surrounding_events(self, threshold_ids, session_type):
        """Checks that the events surrounding the first event in a new session
        are allocated correctly.

        Args:
            threshold_ids: a list of IDs of the first events in the sessions.
            session_type: a list of IDs of the first events in the sessions.
        """
        ds = MockDataStore('test', 0)
        session_no = 1
        last_id = threshold_ids[-1]

        for threshold_id in threshold_ids:
            if threshold_id != 0:
                # check previous event is in the previous session
                event = (ds.get_event('test_index',
                                      str(threshold_id - 1),
                                      stored_events=True))
                self.assertEqual(event['_source']['session_id'],
                                 {session_type: session_no})

            if threshold_id != last_id:
                # check next event is in the same session (as the event with
                # threshold id)
                session_no += 1
                event = (ds.get_event('test_index',
                                      str(threshold_id + 1),
                                      stored_events=True))
                self.assertEqual(event['_source']['session_id'],
                                 {session_type: session_no})

def _create_mock_event(event_id, quantity, time_diffs=None,
                       source_attrs=None):
    """
    Returns an instance of Event, based on the MockDataStore event_dict
    example.

    Args:
        event_id: Desired ID for the Event.
        quantity: The number of Events to be generated.
        time_diffs: A list of time differences between the generated
        Events.

    Returns:
        A generator of Event objects.
    """

    if not time_diffs:
        time_diffs = [0]
    if quantity < 0:
        quantity = abs(quantity)

    # If the list of time differences is too small to be compatible
    # with the quantity of events, then extend the list with the last
    # value for as many items as necessary.
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
        eventObj = _create_eventObj(ds, sketch, event_template, event_id,
                                    event_timestamp, source_attrs)
        yield eventObj

        # adding extra events after every requested event for better
        # simulation of real timeline data i.e. working with a larger
        # dataset
        for _ in range(100):
            event_timestamp += 1
            event_id += 1
            eventObj = _create_eventObj(ds, sketch, event_template, event_id,
                                        event_timestamp, source_attrs)
            yield eventObj

        event_timestamp += abs(time_diffs[i])
        event_id += 1

def _create_eventObj(ds, sketch, event_template, event_id, ts, source_attrs):
    event = event_template
    event['_id'] = str(event_id)
    event['_source']['timestamp'] = ts
    if source_attrs:
        event['_source'].update(source_attrs)

    eventObj = Event(copy.deepcopy(event), ds, sketch)
    ds.import_event(eventObj.index_name,
                    eventObj.event_type,
                    event_id=eventObj.event_id,
                    event=eventObj.source)
    return eventObj
