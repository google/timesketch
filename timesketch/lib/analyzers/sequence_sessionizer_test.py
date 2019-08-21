"""Tests for SequenceSessionizerSketchPlugin."""

from __future__ import unicode_literals

import copy

import mock

from timesketch.lib.analyzers.sequence_sessionizer \
import SequenceSessionizerSketchPlugin
from timesketch.lib.testlib import BaseTest
from timesketch.lib.testlib import MockDataStore
from timesketch.lib.analyzers.interface import Event
from timesketch.models.user import User
from timesketch.models.sketch import Sketch


class ManyEventsSequenceSessionizer(SequenceSessionizerSketchPlugin):
    session_type = 'mock_seq_sessionizer'
    max_time_diff_micros = 100
    return_fields = ['hostname', 'source_short', 'timestamp']
    event_seq = [{
        'hostname': 'host',
        'source_short': 'FILE'
    }, {
        'hostname': 'host',
        'source_short': 'WEBHIST'
    }]

class OneEventSequenceSessionizer(SequenceSessionizerSketchPlugin):
    max_time_diff_micros = 100
    session_type = 'one_event_seq_sessionizer'
    event_seq = [{'hostname': 'host', 'source_short': 'FILE'}]
    return_fields = ['hostname', 'source_short', 'timestamp']


# Invalid sequence sessionizers.
class NoneSessionTypeSequenceSessionizer(SequenceSessionizerSketchPlugin):
    session_type = 'name'
    event_seq = [{'hostname': 'host', 'source_short': 'FILE'}]
    return_fields = ['timestamp', 'source_short']


class NoneSeqSequenceSessionizer(SequenceSessionizerSketchPlugin):
    session_type = 'valid_name'
    return_fields = ['timestamp', 'source_short']


class EmptySeqSequenceSessionizer(SequenceSessionizerSketchPlugin):
    event_seq = []
    session_type = 'valid_name'
    return_fields = ['timestamp', 'source_short']


class NoTimestampSequenceSessionizer(SequenceSessionizerSketchPlugin):
    session_type = 'valid_name'
    event_seq = [{'hostname': 'host', 'source_short': 'FILE'}]
    return_fields = ['source_short']


class NoReturnAttrSequenceSessionizer(SequenceSessionizerSketchPlugin):
    session_type = 'valid_name'
    event_seq = [{'hostname': 'host', 'source_short': 'FILE'}]
    return_fields = ['timestamp']


# List of dictionaries with attributes for mock events.
one_session_args = [{
    'hostname': 'host',
    'source_short': 'FILE'
}, {
    'hostname': 'host',
    'source_short': 'WEBHIST'
}]

two_sessions_args = [{
    'hostname': 'host',
    'source_short': 'FILE'
}, {
    'hostname': 'host',
    'source_short': 'WEBHIST'
}, {
    'hostname': 'host',
    'source_short': 'FILE'
}, {
    'hostname': 'host',
    'source_short': 'WEBHIST'
}]

one_event_seq_args = [{'hostname': 'host', 'source_short': 'FILE'}]


class TestSequenceSessionizerPlugin(BaseTest):
    """Tests the functionality of the sequence sessionizing sketch analyzer."""
    @mock.patch('timesketch.lib.analyzers.interface.ElasticsearchDataStore',
                MockDataStore)
    def test_session_type_none(self):
        """Test session_type is not None."""
        index = 'test_index'
        sketch_id = 1
        self.assertRaises(RuntimeError, sessionizer=\
            NoneSessionTypeSequenceSessionizer(index, sketch_id))

    @mock.patch('timesketch.lib.analyzers.interface.ElasticsearchDataStore',
                MockDataStore)
    def test_event_seq_none(self):
        """Test event_seq is not None."""
        index = 'test_index'
        sketch_id = 1
        self.assertRaises(RuntimeError, sessionizer=\
            NoneSeqSequenceSessionizer(index, sketch_id))

    @mock.patch('timesketch.lib.analyzers.interface.ElasticsearchDataStore',
                MockDataStore)
    def test_event_seq_empty(self):
        """Test event_seq is not empty."""
        index = 'test_index'
        sketch_id = 1
        self.assertRaises(RuntimeError, sessionizer=\
            EmptySeqSequenceSessionizer(index, sketch_id))

    @mock.patch('timesketch.lib.analyzers.interface.ElasticsearchDataStore',
                MockDataStore)
    def test_no_timestamp(self):
        """Test return_fields includes timestamp."""
        index = 'test_index'
        sketch_id = 1
        self.assertRaises(RuntimeError, sessionizer=\
            NoTimestampSequenceSessionizer(index, sketch_id))

    @mock.patch('timesketch.lib.analyzers.interface.ElasticsearchDataStore',
                MockDataStore)
    def test_no_return_attr(self):
        """Test in return_fields are specified attributes."""
        index = 'test_index'
        sketch_id = 1
        self.assertRaises(RuntimeError, sessionizer=\
            NoReturnAttrSequenceSessionizer(index, sketch_id))

    @mock.patch('timesketch.lib.analyzers.interface.ElasticsearchDataStore',
                MockDataStore)
    def test_sessionizer(self):
        """Test basic sequence sessionizer functionality."""
        index = 'test_index'
        sketch_id = 1
        sessionizer = ManyEventsSequenceSessionizer(index, sketch_id)
        self.assertIsInstance(sessionizer, SequenceSessionizerSketchPlugin)
        self.assertEqual(index, sessionizer.index_name)
        self.assertEqual(sketch_id, sessionizer.sketch.id)

    @mock.patch('timesketch.lib.analyzers.interface.ElasticsearchDataStore',
                MockDataStore)
    def test_one_session(self):
        """Test one sequence of events is finded and allocated as a session."""
        with mock.patch.object(SequenceSessionizerSketchPlugin,
                               'event_stream',
                               return_value=_create_mock_event(
                                   0, 2, one_session_args, time_diffs=[1])):
            index = 'test_index'
            sketch_id = 1
            sessionizer = ManyEventsSequenceSessionizer(index, sketch_id)
            message = sessionizer.run()
            self.assertEqual(
                message,
                'Sessionizing completed, number of {0:s} session created: 1'.
                format(sessionizer.session_type))

            ds = MockDataStore('test', 0)
            # Events that are not part of the sequence but are between
            # significant events from the event sequence considered as a session
            # are part of the significant events' session.
            for i in range(0, 101):
                event = ds.get_event('test_index', str(i), stored_events=True)
                self.assertEqual(event['_source'][sessionizer.session_type],
                                 1)

    @mock.patch('timesketch.lib.analyzers.interface.ElasticsearchDataStore',
                MockDataStore)
    def test_multiple_sessions(self):
        """Test multiple sessions are finded and allocated correctly."""
        with mock.patch.object(SequenceSessionizerSketchPlugin,
                               'event_stream',
                               return_value=_create_mock_event(
                                   0,
                                   4,
                                   two_sessions_args,
                                   time_diffs=[1, 1, 1])):
            index = 'test_index'
            sketch_id = 1
            sessionizer = ManyEventsSequenceSessionizer(index, sketch_id)
            message = sessionizer.run()
            self.assertEqual(
                message,
                'Sessionizing completed, number of {0:s} session created: 2'.
                format(sessionizer.session_type))

            ds = MockDataStore('test', 0)
            for i in range(0, 100):
                event = ds.get_event('test_index', str(i), stored_events=True)
                self.assertEqual(event['_source'][sessionizer.session_type],
                                 1)
            # Events with id in the range of 101 to 201 are not part of any
            # session.
            for i in range(202, 302):
                event = ds.get_event('test_index', str(i), stored_events=True)
                self.assertEqual(event['_source'][sessionizer.session_type],
                                 2)

    @mock.patch('timesketch.lib.analyzers.interface.ElasticsearchDataStore',
                MockDataStore)
    def test_after_session(self):
        """Test events after the last event of a sequence are not allocated with
        a session number if they are not part from another session."""
        with mock.patch.object(
            SequenceSessionizerSketchPlugin,
            'event_stream',
            return_value=_create_mock_event(0,
                                            4,
                                            two_sessions_args,
                                            time_diffs=[1, 1])):
            index = 'test_index'
            sketch_id = 1
            sessionizer = ManyEventsSequenceSessionizer(index, sketch_id)
            message = sessionizer.run()
            ds = MockDataStore('test', 0)

            self.assertEqual(
                message,
                'Sessionizing completed, number of {0:s} session created: 2'.
                format(sessionizer.session_type))
            # Session 1: events with id from 0 to 101,
            # session 2: events with id from 202 to 303.
            for i in range(102, 201):
                event = ds.get_event('test_index', str(i), stored_events=True)
                self.assertNotIn(sessionizer.session_type, event)

    @mock.patch('timesketch.lib.analyzers.interface.ElasticsearchDataStore',
                MockDataStore)
    def test_edge_time_diff(self):
        """Test events with the edge time difference between them are
        allocated correctly."""
        with mock.patch.object(
            SequenceSessionizerSketchPlugin,
            'event_stream',
            return_value=_create_mock_event(
                0,
                2,
                one_session_args,
                time_diffs=[
                    ManyEventsSequenceSessionizer.max_time_diff_micros
                ])):
            index = 'test_index'
            sketch_id = 1
            sessionizer = ManyEventsSequenceSessionizer(index, sketch_id)
            message = sessionizer.run()
            self.assertEqual(
                message,
                'Sessionizing completed, number of {0:s} session created: 1'.
                format(sessionizer.session_type))

            ds = MockDataStore('test', 0)
            for i in range(0, 101):
                event = ds.get_event('test_index', str(i), stored_events=True)
                self.assertEqual(event['_source'][sessionizer.session_type],
                                 1)

    @mock.patch('timesketch.lib.analyzers.interface.ElasticsearchDataStore',
                MockDataStore)
    def test_above_max_time_diff(self):
        """Test events with max time difference + 1 between them are allocated
        correctly."""
        with mock.patch.object(
            SequenceSessionizerSketchPlugin,
            'event_stream',
            return_value=_create_mock_event(
                0,
                2,
                one_session_args,
                time_diffs=[
                    SequenceSessionizerSketchPlugin.max_time_diff_micros +
                    1
                ])):
            index = 'test_index'
            sketch_id = 1
            sessionizer = ManyEventsSequenceSessionizer(index, sketch_id)
            message = sessionizer.run()
            self.assertEqual(
                message,
                'Sessionizing completed, number of {0:s} session created: 0'.
                format(sessionizer.session_type))

            ds = MockDataStore('test', 0)
            # Events with id 0 and id 101 form the requested sequence, but
            # event with id 100 and 101 have max_time_diff_micros + 1 bewtween
            # them
            for i in range(0, 201):
                event = ds.get_event('test_index', str(i), stored_events=True)
                self.assertNotIn(sessionizer.session_type, event)

    @mock.patch('timesketch.lib.analyzers.interface.ElasticsearchDataStore',
                MockDataStore)
    def test_zero_events(self):
        """Test the behaviour of the sequence sessionizer when given zero
        events."""
        with mock.patch.object(SequenceSessionizerSketchPlugin,
                               'event_stream',
                               return_value=_create_mock_event(0, 0, [], [0])):
            index = 'test_index'
            sketch_id = 1
            sessionizer = ManyEventsSequenceSessionizer(index, sketch_id)
            message = sessionizer.run()
            self.assertEqual(
                message,
                'Sessionizing completed, number of {0:s} session created: 0'.
                format(sessionizer.session_type))

    @mock.patch('timesketch.lib.analyzers.interface.ElasticsearchDataStore',
                MockDataStore)
    def test_one_event_seq(self):
        """Test the behaviour of the seqeunce sessionizer when given a sequence
        of one event."""
        with mock.patch.object(SequenceSessionizerSketchPlugin,
                               'event_stream',
                               return_value=_create_mock_event(
                                   0, 1, one_event_seq_args, [1])):
            index = 'test_index'
            sketch_id = 1
            sessionizer = OneEventSequenceSessionizer(index, sketch_id)
            message = sessionizer.run()
            self.assertEqual(
                message,
                'Sessionizing completed, number of {0:s} session created: 1'.
                format(sessionizer.session_type))

            ds = MockDataStore('test', 0)
            event = ds.get_event('test_index', '0', stored_events=True)
            self.assertEqual(event['_source'][sessionizer.session_type], 1)

            for i in range(1, 100):
                event = ds.get_event('test_index', str(i), stored_events=True)
                self.assertNotIn(sessionizer.session_type, event)


def _create_mock_event(event_id, quantity, attributes, time_diffs=None):
    """
    Generates list of Event objects, based on the MockDataStore event_dict
    example, the given attributes and the time differences.

    Args:
        event_id: Desired ID for the Event.
        quantity: The number of Events to be generated.
        attributes: A list of dictionaries with attributes for the generated
            events.
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

    # Setup for Event object initialisation.
    ds = MockDataStore('test', 0)
    user = User('test_user')
    sketch = Sketch('test_sketch', 'description', user)
    label = sketch.Label(label='Test label', user=user)
    sketch.labels.append(label)

    event_timestamp = 1410895419859714
    event_template = ds.get_event('test', 'test')

    for i in range(quantity):
        eventObj = create_eventObj(ds, sketch, event_template, event_id,
                                   event_timestamp, attributes[i])
        yield eventObj
        # Adding extra events after every requested event for better simulation
        # of real timeline data i.e. working with a larger dataset.
        for _ in range(100):
            event_timestamp += 1
            event_id += 1
            eventObj = create_eventObj(ds, sketch, event_template, event_id,
                                       event_timestamp)
            yield eventObj

        event_timestamp += abs(time_diffs[i])
        event_id += 1


def create_eventObj(ds,
                    sketch,
                    event_template,
                    event_id,
                    ts,
                    attributes_dict=None):
    """
    Creates Event object based on the given arguments and returns it.

    Args:
        ds: An instance of MockDataStore.
        sketch: A sketch id number.
        event_template: An event source dictionary.
        event_id: An event id number.
        ts: A timestamp for an event.
        attributes_dict: A dictionary with attributes and theirs values.

    Returns:
        An Event object.
    """
    event = copy.deepcopy(event_template)
    event['_id'] = str(event_id)
    event['_source']['timestamp'] = ts
    # If attributes_dict is None, Event object is created based on
    # event_template with no addictional changes.
    if attributes_dict is not None:
        for attribute, value in attributes_dict.items():
            event['_source'][attribute] = value

    eventObj = Event(copy.deepcopy(event), ds, sketch)
    ds.import_event(eventObj.index_name,
                    eventObj.event_type,
                    event_id=eventObj.event_id,
                    event=eventObj.source)
    return eventObj
