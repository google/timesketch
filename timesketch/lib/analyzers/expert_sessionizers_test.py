"""Tests for expert sessionizers."""

from __future__ import unicode_literals

import unittest
import mock

from timesketch.lib.analyzers.expert_sessionizers import (
    WebActivitySessionizerSketchPlugin,
)
from timesketch.lib.analyzers.expert_sessionizers import (
    SSHBruteforceSessionizerSketchPlugin,
)
from timesketch.lib.analyzers.base_sessionizer_test import _create_mock_event
from timesketch.lib.testlib import BaseTest
from timesketch.lib.testlib import MockDataStore


class TestWebActivitySessionizerPlugin(BaseTest):
    """Tests the functionality of the web activity sessionizing sketch
    analyzer."""

    @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    def test_event_type(self):
        """Test the mocking of events returns an event stream that matches the
        query for the analyzer."""
        index = "test_index"
        sketch_id = 1
        analyzer = WebActivitySessionizerSketchPlugin(index, sketch_id)
        analyzer.datastore.client = mock.Mock()
        datastore = analyzer.datastore

        _create_mock_event(datastore, 0, 2, source_attrs={"source_short": "WEBHIST"})

        message = analyzer.run()
        self.assertEqual(
            message, "Sessionizing completed, number of session created: 1"
        )

        event1 = datastore.event_store["0"]
        self.assertEqual(event1["_source"]["source_short"], "WEBHIST")
        self.assertEqual(event1["_source"]["session_id"], {analyzer.session_type: 1})
        event2 = datastore.event_store["101"]
        self.assertEqual(event2["_source"]["source_short"], "WEBHIST")
        self.assertEqual(event2["_source"]["session_id"], {analyzer.session_type: 1})


class TestSSHBruteforceSessionizerPlugin(BaseTest):
    """Tests the functionality of the SSH bruteforce attack sessionizing sketch
    analyzer."""

    @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    def test_event_type(self):
        """Test the mocking of events returns an event stream that matches the
        query for the analyzer."""
        index = "test_index"
        sketch_id = 1
        analyzer = SSHBruteforceSessionizerSketchPlugin(index, sketch_id)
        analyzer.datastore.client = mock.Mock()
        datastore = analyzer.datastore

        _create_mock_event(
            datastore,
            0,
            2,
            source_attrs={
                "reporter": "sshd",
                "message": "[sshd] [0]: Invalid user " "NoSuchUser from 0.0.0.0 port 0",
            },
        )

        message = analyzer.run()
        self.assertEqual(
            message, "Sessionizing completed, number of session created: 1"
        )

        test_message = "[sshd] [0]: Invalid user NoSuchUser from 0.0.0.0 " "port 0"
        # pylint: disable=unexpected-keyword-arg
        event1 = datastore.event_store["0"]
        self.assertEqual(event1["_source"]["reporter"], "sshd")
        self.assertEqual(event1["_source"]["message"], test_message)
        self.assertEqual(event1["_source"]["session_id"], {analyzer.session_type: 1})

        event2 = datastore.event_store["1"]
        self.assertEqual(event2["_source"]["reporter"], "sshd")
        self.assertEqual(event2["_source"]["message"], test_message)
        self.assertEqual(event2["_source"]["session_id"], {analyzer.session_type: 1})


if __name__ == "__main__":
    unittest.main()
