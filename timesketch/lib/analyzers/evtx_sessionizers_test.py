"""Tests for WinEVTXSessionizerSketchPlugin, LogonSessionizerSketchPludin and
UnlockSessionizerSketchPlugin"""

from __future__ import unicode_literals

import unittest
import copy
import mock

from timesketch.lib.analyzers.evtx_sessionizers import \
    LogonSessionizerSketchPlugin
from timesketch.lib.analyzers.evtx_sessionizers import \
    UnlockSessionizerSketchPlugin

from timesketch.lib.analyzers.interface import Event
from timesketch.lib.testlib import BaseTest
from timesketch.lib.testlib import MockDataStore
from timesketch.models.user import User
from timesketch.models.sketch import Sketch

xml_string1 = '<Event xmlns="http://schemas.microsoft.com/win/2004/08/events' \
    '/event"><EventData><Data Name="TargetUserName">USER_1</Data>' \
    '<Data Name="TargetLogonId">0x0000000000000001</Data></EventData></Event>'

xml_string2 = '<Event xmlns="http://schemas.microsoft.com/win/2004/08/events' \
    '/event"><EventData><Data Name="TargetUserName">USER_2</Data>' \
    '<Data Name="TargetLogonId">0x0000000000000002</Data></EventData></Event>'

xml_string3 = '<Event xmlns="http://schemas.microsoft.com/win/2004/08/events' \
    '/event"><EventData><Data Name="TargetUserName">USER_3</Data>' \
    '<Data Name="TargetLogonId">0x0000000000000003</Data></EventData></Event>'

class TestWinEXTXSessionizerPlugin(BaseTest):
    """Tests for Windows EVTX log sessionizers listed in analyzer_classes. New
    sessionizer classes should be added in analyzer_classes, if applicable.

     Attributes:
        analyzer_classes: A list of dictionaries representing analyzer classes
        to test.
    """
    analyzer_classes = [
        {"class": LogonSessionizerSketchPlugin,
         "start_event_id": 4624,
         "end_event_id": 4634},

        {"class": UnlockSessionizerSketchPlugin,
         "start_event_id": 4801,
         "end_event_id": 4800}
    ]

    @mock.patch('timesketch.lib.analyzers.interface.ElasticsearchDataStore',
                MockDataStore)
    def test_get_event_data(self):
        """Test getEventData returns the correct values."""
        user = User('test_user')
        sketch = Sketch('test_sketch', 'description', user)
        label = sketch.Label(label='Test label', user=user)
        sketch.labels.append(label)

        index = 'test_index'
        sketch_id = 1

        for analyzer_class in self.analyzer_classes:
            analyzer = analyzer_class['class'](index, sketch_id)
            datastore = analyzer.datastore
            event_dict = copy.deepcopy(MockDataStore.event_dict)
            event_dict['_source'].update({'xml_string': xml_string1})
            event_obj = Event(event_dict, datastore, sketch)

            username = analyzer.getEventData(event_obj, 'TargetUserName')
            logon_id = analyzer.getEventData(event_obj, 'TargetLogonId')

            self.assertEqual(username, 'USER_1')
            self.assertEqual(logon_id, '0x0000000000000001')

    @mock.patch('timesketch.lib.analyzers.interface.ElasticsearchDataStore',
                MockDataStore)
    def test_one_session(self):
        """Test the behaviour of the analyzer given one start and one end
        event."""
        index = 'test_index'
        sketch_id = 1

        for analyzer_class in self.analyzer_classes:
            analyzer = analyzer_class['class'](index, sketch_id)
            analyzer.datastore.client = mock.Mock()
            datastore = analyzer.datastore

            _create_mock_event(
                datastore,
                0,
                2,
                source_attrs=[{'xml_string': xml_string1,
                               'event_identifier':
                               analyzer_class['start_event_id']},
                              {'xml_string': xml_string1,
                               'event_identifier':
                               analyzer_class['end_event_id']}])

            message = analyzer.run()
            self.assertEqual(
                message,
                'Sessionizing completed, number of sessions created: 1')

            # pylint: disable=unexpected-keyword-arg
            event1 = (datastore.get_event('test_index',
                                          '0',
                                          stored_events=True))
            self.assertEqual(event1['_source']['session_id']
                             [analyzer.session_type], ['0 (USER_1)'])
            event2 = (datastore.get_event('test_index',
                                          '1',
                                          stored_events=True))
            self.assertEqual(event2['_source']['session_id']
                             [analyzer.session_type], ['0 (USER_1)'])

    @mock.patch('timesketch.lib.analyzers.interface.ElasticsearchDataStore',
                MockDataStore)
    def test_multiple_sessions(self):
        """Test multiple sessions are allocated correctly."""
        index = 'test_index'
        sketch_id = 1

        for analyzer_class in self.analyzer_classes:
            analyzer = analyzer_class['class'](index, sketch_id)
            analyzer.datastore.client = mock.Mock()
            datastore = analyzer.datastore

            _create_mock_event(
                datastore,
                2,
                6,
                source_attrs=[{'xml_string': xml_string1,
                               'event_identifier':
                               analyzer_class['start_event_id']},
                              {'xml_string': xml_string1,
                               'event_identifier':
                               analyzer_class['end_event_id']},
                              {'xml_string': xml_string2,
                               'event_identifier':
                               analyzer_class['start_event_id']},
                              {'xml_string': xml_string3,
                               'event_identifier':
                               analyzer_class['start_event_id']},
                              {'xml_string': xml_string2,
                               'event_identifier':
                               analyzer_class['end_event_id']},
                              {'xml_string': xml_string3,
                               'event_identifier':
                               analyzer_class['end_event_id']}])

            message = analyzer.run()
            self.assertEqual(
                message,
                'Sessionizing completed, number of sessions created: 3')

            # pylint: disable=unexpected-keyword-arg

            #session 0
            event1 = (datastore.get_event('test_index',
                                          '2',
                                          stored_events=True))
            self.assertEqual(event1['_source']['session_id']
                             [analyzer.session_type], ['0 (USER_1)'])
            event2 = (datastore.get_event('test_index',
                                          '3',
                                          stored_events=True))
            self.assertEqual(event2['_source']['session_id']
                             [analyzer.session_type], ['0 (USER_1)'])

            #session 1
            event3 = (datastore.get_event('test_index',
                                          '4',
                                          stored_events=True))
            self.assertEqual(event3['_source']['session_id']
                             [analyzer.session_type], ['1 (USER_2)'])
            event5 = (datastore.get_event('test_index',
                                          '6',
                                          stored_events=True))
            self.assertEqual(event5['_source']['session_id']
                             [analyzer.session_type], ['1 (USER_2)'])

            #session 2
            event4 = (datastore.get_event('test_index',
                                          '5',
                                          stored_events=True))
            self.assertEqual(event4['_source']['session_id']
                             [analyzer.session_type], ['2 (USER_3)'])
            event6 = (datastore.get_event('test_index',
                                          '7',
                                          stored_events=True))
            self.assertEqual(event6['_source']['session_id']
                             [analyzer.session_type], ['2 (USER_3)'])

    @mock.patch('timesketch.lib.analyzers.interface.ElasticsearchDataStore',
                MockDataStore)
    def test_startup(self):
        """Test the behaviour of the analyzer with an event stream containing
        a startup event."""
        index = 'test_index'
        sketch_id = 1

        for analyzer_class in self.analyzer_classes:
            analyzer = analyzer_class['class'](index, sketch_id)
            analyzer.datastore.client = mock.Mock()
            datastore = analyzer.datastore

            _create_mock_event(
                datastore,
                8,
                4,
                source_attrs=[{'xml_string': xml_string1,
                               'event_identifier':
                               analyzer_class['start_event_id']},
                              {'xml_string': xml_string2,
                               'event_identifier':
                               analyzer_class['start_event_id']},
                              {'event_identifier': 6005},
                              {'xml_string': xml_string1,
                               'event_identifier':
                               analyzer_class['end_event_id']}])

            message = analyzer.run()
            self.assertEqual(
                message,
                'Sessionizing completed, number of sessions created: 2')

            # pylint: disable=unexpected-keyword-arg
            event1 = (datastore.get_event('test_index',
                                          '8',
                                          stored_events=True))
            self.assertEqual(event1['_source']['session_id']
                             [analyzer.session_type], ['0 (USER_1)'])
            event2 = (datastore.get_event('test_index',
                                          '9',
                                          stored_events=True))
            self.assertEqual(event2['_source']['session_id']
                             [analyzer.session_type], ['1 (USER_2)'])
            event3 = (datastore.get_event('test_index',
                                          '10',
                                          stored_events=True))
            self.assertEqual(set(event3['_source']['session_id']
                                 [analyzer.session_type]),
                             set(['0 (USER_1)', '1 (USER_2)']))
            event4 = (datastore.get_event('test_index',
                                          '11',
                                          stored_events=True))
            self.assertTrue(event4['_source'].get('session_id') is None or
                            event4['_source']['session_id'].get(
                                analyzer.session_type) is None)

    @mock.patch('timesketch.lib.analyzers.interface.ElasticsearchDataStore',
                MockDataStore)
    def test_no_end(self):
        """Test the behaviour of the analyzer given a start event without a
        corresponding end event. The start event is allocated its own session.
        Non-corresponding end events are ignored."""
        index = 'test_index'
        sketch_id = 1

        for analyzer_class in self.analyzer_classes:
            analyzer = analyzer_class['class'](index, sketch_id)
            analyzer.datastore.client = mock.Mock()
            datastore = analyzer.datastore

            _create_mock_event(
                datastore,
                12,
                2,
                source_attrs=[{'xml_string': xml_string1,
                               'event_identifier':
                               analyzer_class['start_event_id']},
                              {'xml_string': xml_string2,
                               'event_identifier':
                               analyzer_class['end_event_id']}])

            message = analyzer.run()
            self.assertEqual(
                message,
                'Sessionizing completed, number of sessions created: 1')

            # pylint: disable=unexpected-keyword-arg
            event1 = (datastore.get_event('test_index',
                                          '12',
                                          stored_events=True))
            self.assertEqual(event1['_source']['session_id']
                             [analyzer.session_type], ['0 (USER_1)'])
            event2 = (datastore.get_event('test_index',
                                          '13',
                                          stored_events=True))
            self.assertTrue(event2['_source'].get('session_id') is None or
                            event2['_source']['session_id'].get(
                                analyzer.session_type) is None)

    @mock.patch('timesketch.lib.analyzers.interface.ElasticsearchDataStore',
                MockDataStore)
    def test_end_before_start(self):
        """Test the behaviour of the analyzer when an end event occurs
        before a start event with the same logon ID. The end event is ignored,
        and the remaining event stream processed normally."""
        index = 'test_index'
        sketch_id = 1

        for analyzer_class in self.analyzer_classes:
            analyzer = analyzer_class['class'](index, sketch_id)
            analyzer.datastore.client = mock.Mock()
            datastore = analyzer.datastore

            _create_mock_event(
                datastore,
                14,
                3,
                source_attrs=[{'xml_string': xml_string1,
                               'event_identifier':
                               analyzer_class['end_event_id']},
                              {'xml_string': xml_string1,
                               'event_identifier':
                               analyzer_class['start_event_id']},
                              {'xml_string': xml_string1,
                               'event_identifier':
                               analyzer_class['end_event_id']}])

            message = analyzer.run()
            self.assertEqual(
                message,
                'Sessionizing completed, number of sessions created: 1')

            # pylint: disable=unexpected-keyword-arg
            event1 = (datastore.get_event('test_index',
                                          '14',
                                          stored_events=True))
            self.assertTrue(event1['_source'].get('session_id') is None or
                            event1['_source']['session_id'].get(
                                analyzer.session_type) is None)
            event2 = (datastore.get_event('test_index',
                                          '15',
                                          stored_events=True))
            self.assertEqual(event2['_source']['session_id']
                             [analyzer.session_type], ['0 (USER_1)'])
            event3 = (datastore.get_event('test_index',
                                          '16',
                                          stored_events=True))
            self.assertEqual(event3['_source']['session_id']
                             [analyzer.session_type], ['0 (USER_1)'])

    @mock.patch('timesketch.lib.analyzers.interface.ElasticsearchDataStore',
                MockDataStore)
    def test_identical_start_events(self):
        """Test the behaviour of the analyzer given multiple start events with
        the same logon ID before a corresponding end event. Each start event is
        allocated its own session, with the end event allocated to the most
        recent start event."""
        index = 'test_index'
        sketch_id = 1

        for analyzer_class in self.analyzer_classes:
            analyzer = analyzer_class['class'](index, sketch_id)
            analyzer.datastore.client = mock.Mock()
            datastore = analyzer.datastore

            _create_mock_event(
                datastore,
                17,
                3,
                source_attrs=[{'xml_string': xml_string1,
                               'event_identifier':
                               analyzer_class['start_event_id']},
                              {'xml_string': xml_string1,
                               'event_identifier':
                               analyzer_class['start_event_id']},
                              {'xml_string': xml_string1,
                               'event_identifier':
                               analyzer_class['end_event_id']}])

            message = analyzer.run()
            self.assertEqual(
                message,
                'Sessionizing completed, number of sessions created: 2')

            # pylint: disable=unexpected-keyword-arg
            event1 = (datastore.get_event('test_index',
                                          '17',
                                          stored_events=True))
            self.assertEqual(event1['_source']['session_id']
                             [analyzer.session_type], ['0 (USER_1)'])
            event2 = (datastore.get_event('test_index',
                                          '18',
                                          stored_events=True))
            self.assertEqual(event2['_source']['session_id']
                             [analyzer.session_type], ['1 (USER_1)'])
            event3 = (datastore.get_event('test_index',
                                          '19',
                                          stored_events=True))
            self.assertEqual(event3['_source']['session_id']
                             [analyzer.session_type], ['1 (USER_1)'])

    @mock.patch('timesketch.lib.analyzers.interface.ElasticsearchDataStore',
                MockDataStore)
    def test_identical_end_events(self):
        """Test the behaviour of the analyzer given multiple end events with
        the same logon ID after a corresponding start event. The first end
        event is allocated to the session, and the other(s) ignored."""
        index = 'test_index'
        sketch_id = 1

        for analyzer_class in self.analyzer_classes:
            analyzer = analyzer_class['class'](index, sketch_id)
            analyzer.datastore.client = mock.Mock()
            datastore = analyzer.datastore

            _create_mock_event(
                datastore,
                20,
                3,
                source_attrs=[{'xml_string': xml_string1,
                               'event_identifier':
                               analyzer_class['start_event_id']},
                              {'xml_string': xml_string1,
                               'event_identifier':
                               analyzer_class['end_event_id']},
                              {'xml_string': xml_string1,
                               'event_identifier':
                               analyzer_class['end_event_id']}])

            message = analyzer.run()
            self.assertEqual(
                message,
                'Sessionizing completed, number of sessions created: 1')

            # pylint: disable=unexpected-keyword-arg
            event1 = (datastore.get_event('test_index',
                                          '20',
                                          stored_events=True))
            self.assertEqual(event1['_source']['session_id']
                             [analyzer.session_type], ['0 (USER_1)'])
            event2 = (datastore.get_event('test_index',
                                          '21',
                                          stored_events=True))
            self.assertEqual(event2['_source']['session_id']
                             [analyzer.session_type], ['0 (USER_1)'])
            event3 = (datastore.get_event('test_index',
                                          '22',
                                          stored_events=True))
            self.assertTrue(event3['_source'].get('session_id') is None or
                            event3['_source']['session_id'].get(
                                analyzer.session_type) is None)

    @mock.patch('timesketch.lib.analyzers.interface.ElasticsearchDataStore',
                MockDataStore)
    def test_zero_events(self):
        """Test the behaviour of the analyzer given an empty event stream."""
        index = 'test_index'
        sketch_id = 1

        for analyzer_class in self.analyzer_classes:
            analyzer = analyzer_class['class'](index, sketch_id)
            analyzer.datastore.client = mock.Mock()
            datastore = analyzer.datastore

            _create_mock_event(datastore, 23, 0)

            message = analyzer.run()
            self.assertEqual(
                message,
                'Sessionizing completed, number of sessions created: 0')

def _create_mock_event(datastore, event_id, quantity, time_diffs=None,
                       source_attrs=None):
    """
    Loads in the datastore mock events that based on the given arguments.

    Args:
        datastore: An instance of MockDataStore.
        event_id: Desired ID for the first Event (to then be incremented).
        quantity: The number of Events to be generated.
        time_diffs: A list of time differences between the generated
        Events.
        source_attrs: A list of attributes to be added to the source attribute
        of the Events.
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

    #similarly for source_attrs
    if source_attrs is None:
        source_attrs = [None] * quantity
    else:
        if quantity - len(source_attrs) > 0:
            source_attrs.extend([source_attrs[-1]] *
                                (quantity - len(source_attrs)))

    event_timestamp = 1410895419859714

    for i in range(quantity):
        _create_eventObj(datastore, event_id, event_timestamp, source_attrs[i])
        event_timestamp += abs(time_diffs[i])
        event_id += 1

def _create_eventObj(datastore, event_id, ts, source_attrs):
    """Changes MockDataStore.event_dict based on the given arguments and commits
    it to the datastore.
    Args:
        datastore: An instance of MockDataStore.
        event_id: An event id number.
        ts: A timestamp for an event.
        source_attrs: A dictionary with attributes and theirs values.
    """
    event = copy.deepcopy(MockDataStore.event_dict)
    event['_source']['timestamp'] = ts
    if source_attrs:
        event['_source'].update(source_attrs)

    datastore.import_event(event['_index'], event['_type'], event['_source'],
                           str(event_id))

if __name__ == '__main__':
    unittest.main()
