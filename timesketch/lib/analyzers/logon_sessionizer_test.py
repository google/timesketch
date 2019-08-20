"""Tests for LogonSessionizerSketchPlugin"""

from __future__ import unicode_literals

import unittest
import mock

from timesketch.lib.analyzers.logon_sessionizer import \
    LogonSessionizerSketchPlugin
from timesketch.lib.analyzers.base_sessionizer_test import _create_eventObj
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

class TestLogonSessionizerPlugin(BaseTest):
    """Tests for the logon sessionizer analyzer."""
    analyzer_class = LogonSessionizerSketchPlugin

    @mock.patch('timesketch.lib.analyzers.interface.ElasticsearchDataStore',
                MockDataStore)
    def test_one_session(self):
        """Test the behaviour of the analyzer given one login and one logout
        event."""
        with mock.patch.object(
                self.analyzer_class,
                'event_stream',
                return_value=_create_mock_event(
                    0,
                    2,
                    source_attrs=[{'xml_string': xml_string1,
                                   'event_identifier': 4624},
                                  {'xml_string': xml_string1,
                                   'event_identifier': 4634}])):
            index = 'test_index'
            sketch_id = 1
            analyzer = self.analyzer_class(index, sketch_id)
            message = analyzer.run()
            self.assertEqual(
                message,
                'Sessionizing completed, number of sessions created: 1')

            ds = MockDataStore('test', 0)
            event1 = (ds.get_event('test_index', '0', stored_events=True))
            self.assertEqual(event1['_source']['session_id']['logon_session'],
                             ['0 (USER_1)'])
            event2 = (ds.get_event('test_index', '1', stored_events=True))
            self.assertEqual(event2['_source']['session_id']['logon_session'],
                             ['0 (USER_1)'])

    @mock.patch('timesketch.lib.analyzers.interface.ElasticsearchDataStore',
                MockDataStore)
    def test_multiple_sessions(self):
        """Test multiple sessions are allocated correctly, with some login /
        logout events nested."""
        with mock.patch.object(
                self.analyzer_class,
                'event_stream',
                return_value=_create_mock_event(
                    2,
                    6,
                    source_attrs=[{'xml_string': xml_string1,
                                   'event_identifier':4624},
                                  {'xml_string': xml_string1,
                                   'event_identifier':4634},
                                  {'xml_string': xml_string2,
                                   'event_identifier':4624},
                                  {'xml_string': xml_string3,
                                   'event_identifier':4624},
                                  {'xml_string': xml_string2,
                                   'event_identifier':4634},
                                  {'xml_string': xml_string3,
                                   'event_identifier':4634}])):
            index = 'test_index'
            sketch_id = 1
            analyzer = self.analyzer_class(index, sketch_id)
            message = analyzer.run()
            self.assertEqual(
                message,
                'Sessionizing completed, number of sessions created: 3')

            ds = MockDataStore('test', 0)

            #session 0
            event1 = (ds.get_event('test_index', '2', stored_events=True))
            self.assertEqual(event1['_source']['session_id']['logon_session'],
                             ['0 (USER_1)'])
            event2 = (ds.get_event('test_index', '3', stored_events=True))
            self.assertEqual(event2['_source']['session_id']['logon_session'],
                             ['0 (USER_1)'])

            #session 1
            event3 = (ds.get_event('test_index', '4', stored_events=True))
            self.assertEqual(event3['_source']['session_id']['logon_session'],
                             ['1 (USER_2)'])
            event5 = (ds.get_event('test_index', '6', stored_events=True))
            self.assertEqual(event5['_source']['session_id']['logon_session'],
                             ['1 (USER_2)'])

            #session 2
            event4 = (ds.get_event('test_index', '5', stored_events=True))
            self.assertEqual(event4['_source']['session_id']['logon_session'],
                             ['2 (USER_3)'])
            event6 = (ds.get_event('test_index', '7', stored_events=True))
            self.assertEqual(event6['_source']['session_id']['logon_session'],
                             ['2 (USER_3)'])

    @mock.patch('timesketch.lib.analyzers.interface.ElasticsearchDataStore',
                MockDataStore)
    def test_startup(self):
        """Test the behaviour of the analyzer with an event stream containing
        a startup event."""
        with mock.patch.object(
                self.analyzer_class,
                'event_stream',
                return_value=_create_mock_event(
                    8,
                    4,
                    source_attrs=[{'xml_string': xml_string1,
                                   'event_identifier': 4624},
                                  {'xml_string': xml_string2,
                                   'event_identifier': 4624},
                                  {'event_identifier': 6005},
                                  {'xml_string': xml_string1,
                                   'event_identifier': 4634}])):
            index = 'test_index'
            sketch_id = 1
            analyzer = self.analyzer_class(index, sketch_id)
            message = analyzer.run()
            self.assertEqual(
                message,
                'Sessionizing completed, number of sessions created: 2')

            ds = MockDataStore('test', 0)
            event1 = (ds.get_event('test_index', '8', stored_events=True))
            self.assertEqual(event1['_source']['session_id']['logon_session'],
                             ['0 (USER_1)'])
            event2 = (ds.get_event('test_index', '9', stored_events=True))
            self.assertEqual(event2['_source']['session_id']['logon_session'],
                             ['1 (USER_2)'])
            event3 = (ds.get_event('test_index', '10', stored_events=True))
            self.assertEqual(set(event3['_source']['session_id']
                                 ['logon_session']),
                             set(['0 (USER_1)', '1 (USER_2)']))
            event4 = (ds.get_event('test_index', '11', stored_events=True))
            self.assertTrue(event4['_source'].get('session_id') is None or
                            event4['_source']['session_id'].get(
                                'logon_session') is None)

    @mock.patch('timesketch.lib.analyzers.interface.ElasticsearchDataStore',
                MockDataStore)
    def test_no_logout(self):
        """Test the behaviour of the analyzer given a login event without a
        corresponding logout event. The login event is allocated its own
        session. Non-corresponding logout events are ignored."""
        with mock.patch.object(
                self.analyzer_class,
                'event_stream',
                return_value=_create_mock_event(
                    12,
                    2,
                    source_attrs=[{'xml_string': xml_string1,
                                   'event_identifier':4624},
                                  {'xml_string': xml_string2,
                                   'event_identifier':4634}])):
            index = 'test_index'
            sketch_id = 1
            analyzer = self.analyzer_class(index, sketch_id)
            message = analyzer.run()
            self.assertEqual(
                message,
                'Sessionizing completed, number of sessions created: 1')

            ds = MockDataStore('test', 0)
            event1 = (ds.get_event('test_index', '12', stored_events=True))
            self.assertEqual(event1['_source']['session_id']['logon_session'],
                             ['0 (USER_1)'])
            event2 = (ds.get_event('test_index', '13', stored_events=True))
            self.assertTrue(event2['_source'].get('session_id') is None or
                            event2['_source']['session_id'].get(
                                'logon_session') is None)

    @mock.patch('timesketch.lib.analyzers.interface.ElasticsearchDataStore',
                MockDataStore)
    def test_logout_before_login(self):
        """Test the behaviour of the analyzer when a logout event occurs
        before a login event with the same logon ID (a common case for SYSTEM
        logons). The logout event is ignored, and the remaining event stream
        processed normally."""
        with mock.patch.object(
                self.analyzer_class,
                'event_stream',
                return_value=_create_mock_event(
                    14,
                    3,
                    source_attrs=[{'xml_string': xml_string1,
                                   'event_identifier':4634},
                                  {'xml_string': xml_string1,
                                   'event_identifier':4624},
                                  {'xml_string': xml_string1,
                                   'event_identifier':4634}])):
            index = 'test_index'
            sketch_id = 1
            analyzer = self.analyzer_class(index, sketch_id)
            message = analyzer.run()
            self.assertEqual(
                message,
                'Sessionizing completed, number of sessions created: 1')

            ds = MockDataStore('test', 0)
            event1 = (ds.get_event('test_index', '14', stored_events=True))
            self.assertTrue(event1['_source'].get('session_id') is None or
                            event1['_source']['session_id'].get(
                                'logon_session') is None)
            event2 = (ds.get_event('test_index', '15', stored_events=True))
            self.assertEqual(event2['_source']['session_id']['logon_session'],
                             ['0 (USER_1)'])
            event3 = (ds.get_event('test_index', '16', stored_events=True))
            self.assertEqual(event3['_source']['session_id']['logon_session'],
                             ['0 (USER_1)'])

    @mock.patch('timesketch.lib.analyzers.interface.ElasticsearchDataStore',
                MockDataStore)
    def test_identical_logins(self):
        """Test the behaviour of the analyzer given multiple logins with the
        same logon ID before a corresponding logout. Each login is allocated
        its own session, with the logout allocated to the most recent login."""
        with mock.patch.object(
                self.analyzer_class,
                'event_stream',
                return_value=_create_mock_event(
                    17,
                    3,
                    source_attrs=[{'xml_string': xml_string1,
                                   'event_identifier':4624},
                                  {'xml_string': xml_string1,
                                   'event_identifier':4624},
                                  {'xml_string': xml_string1,
                                   'event_identifier':4634}])):
            index = 'test_index'
            sketch_id = 1
            analyzer = self.analyzer_class(index, sketch_id)
            message = analyzer.run()
            self.assertEqual(
                message,
                'Sessionizing completed, number of sessions created: 2')

            ds = MockDataStore('test', 0)
            event1 = (ds.get_event('test_index', '17', stored_events=True))
            self.assertEqual(event1['_source']['session_id']['logon_session'],
                             ['0 (USER_1)'])
            event2 = (ds.get_event('test_index', '18', stored_events=True))
            self.assertEqual(event2['_source']['session_id']['logon_session'],
                             ['1 (USER_1)'])
            event3 = (ds.get_event('test_index', '19', stored_events=True))
            self.assertEqual(event3['_source']['session_id']['logon_session'],
                             ['1 (USER_1)'])

    @mock.patch('timesketch.lib.analyzers.interface.ElasticsearchDataStore',
                MockDataStore)
    def test_identical_logouts(self):
        """Test the behaviour of the analyzer given multiple logouts with the
        same logon ID after a corresponding login. The first logout is
        allocated to the session, and the other(s) ignored."""
        with mock.patch.object(
                self.analyzer_class,
                'event_stream',
                return_value=_create_mock_event(
                    20,
                    3,
                    source_attrs=[{'xml_string': xml_string1,
                                   'event_identifier':4624},
                                  {'xml_string': xml_string1,
                                   'event_identifier':4634},
                                  {'xml_string': xml_string1,
                                   'event_identifier':4634}])):
            index = 'test_index'
            sketch_id = 1
            analyzer = self.analyzer_class(index, sketch_id)
            message = analyzer.run()
            self.assertEqual(
                message,
                'Sessionizing completed, number of sessions created: 1')

            ds = MockDataStore('test', 0)
            event1 = (ds.get_event('test_index', '20', stored_events=True))
            self.assertEqual(event1['_source']['session_id']['logon_session'],
                             ['0 (USER_1)'])
            event2 = (ds.get_event('test_index', '21', stored_events=True))
            self.assertEqual(event2['_source']['session_id']['logon_session'],
                             ['0 (USER_1)'])
            event3 = (ds.get_event('test_index', '22', stored_events=True))
            self.assertTrue(event3['_source'].get('session_id') is None or
                            event3['_source']['session_id'].get(
                                'logon_session') is None)

    @mock.patch('timesketch.lib.analyzers.interface.ElasticsearchDataStore',
                MockDataStore)
    def test_zero_events(self):
        """Test the behaviour of the analyzer given an empty event stream."""
        with mock.patch.object(self.analyzer_class, 'event_stream',
                               return_value=_create_mock_event(23, 0)):
            index = 'test_index'
            sketch_id = 1
            analyzer = self.analyzer_class(index, sketch_id)
            message = analyzer.run()
            self.assertEqual(
                message,
                'Sessionizing completed, number of sessions created: 0')

def _create_mock_event(event_id, quantity, time_diffs=None,
                       source_attrs=None):
    """
    Returns an instance of Event, based on the MockDataStore event_dict
    example.

    Args:
        event_id: Desired ID for the first Event (to then be incremented).
        quantity: The number of Events to be generated.
        time_diffs: A list of time differences between the generated
        Events.
        source_attrs: A list of attributes to be added to the source attribute
        of the Events.
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

    #similarly for source_attrs
    if source_attrs is None:
        source_attrs = [None] * quantity
    else:
        if quantity - len(source_attrs) > 0:
            source_attrs.extend([source_attrs[-1]] *
                                (quantity - len(source_attrs)))

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
                                    event_timestamp, source_attrs[i])
        yield eventObj

        event_timestamp += abs(time_diffs[i])
        event_id += 1

if __name__ == '__main__':
    unittest.main()
