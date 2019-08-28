"""Tests for expert sessionizers."""

from __future__ import unicode_literals

import unittest
import mock

from timesketch.lib.analyzers.expert_sessionizers import \
    WebActivitySessionizerSketchPlugin
from timesketch.lib.analyzers.expert_sessionizers import \
    SSHBruteforceSessionizerSketchPlugin
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

class TestSSHBruteforceSessionizerPlugin(BaseTest, BaseSessionizerTest):
    """Tests the functionality of the SSH bruteforce attack sessionizing sketch
    analyzer."""
    analyzer_class = SSHBruteforceSessionizerSketchPlugin

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
                    source_attrs={'reporter': 'sshd',
                                  'message': '[sshd] [0]: Invalid user ' \
                                      'NoSuchUser from 0.0.0.0 port 0'})):
            index = 'test_index'
            sketch_id = 1
            analyzer = self.analyzer_class(index, sketch_id)
            message = analyzer.run()
            self.assertEqual(
                message,
                'Sessionizing completed, number of session created: 1')

            ds = MockDataStore('test', 0)
            test_message = '[sshd] [0]: Invalid user NoSuchUser from 0.0.0.0' \
                ' port 0'
            event1 = (ds.get_event('test_index', '0', stored_events=True))
            self.assertEqual(event1['_source']['reporter'], 'sshd')
            self.assertEqual(event1['_source']['message'], test_message)
            self.assertEqual(event1['_source']['session_id'],
                             {analyzer.session_type: 1})

            event2 = (ds.get_event('test_index', '101', stored_events=True))
            self.assertEqual(event2['_source']['reporter'], 'sshd')
            self.assertEqual(event2['_source']['message'], test_message)
            self.assertEqual(event2['_source']['session_id'],
                             {analyzer.session_type: 1})

if __name__ == '__main__':
    unittest.main()
