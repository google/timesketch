"""Tests for SessionizerSketchPlugin."""

from __future__ import unicode_literals

import unittest
import mock

from timesketch.lib.analyzers.sessionizer import SessionizerSketchPlugin
from timesketch.lib.analyzers.base_sessionizer_test import _create_mock_event
from timesketch.lib.analyzers.base_sessionizer_test import check_surrounding_events
from timesketch.lib.testlib import BaseTest
from timesketch.lib.testlib import MockDataStore


class TestSessionizerPlugin(BaseTest):
    """Tests the functionality of the sessionizing sketch analyzer, focusing
    on edge cases."""

    @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    def test_multiple_sessions(self):
        """Test multiple events, two of which are in the same session and
        one in a different session."""

        index = "test_index"
        sketch_id = 1
        analyzer = SessionizerSketchPlugin(index, sketch_id)
        analyzer.datastore.client = mock.Mock()
        datastore = analyzer.datastore

        _create_mock_event(datastore, 0, 3, time_diffs=[3000, 400000000])

        message = analyzer.run()
        self.assertEqual(
            message, "Sessionizing completed, number of session created: 2"
        )

        event1 = datastore.event_store["0"]
        self.assertEqual(event1["_source"]["session_id"], {"all_events": 1})
        event2 = datastore.event_store["101"]
        self.assertEqual(event2["_source"]["session_id"], {"all_events": 1})
        event3 = datastore.event_store["202"]
        self.assertEqual(event3["_source"]["session_id"], {"all_events": 2})
        check_surrounding_events(self, datastore, [202], "all_events")

    @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    def test_zero_time_diff(self):
        """Test events with no time difference between them are allocated
        correctly."""
        index = "test_index"
        sketch_id = 1
        analyzer = SessionizerSketchPlugin(index, sketch_id)
        analyzer.datastore.client = mock.Mock()
        datastore = analyzer.datastore

        _create_mock_event(datastore, 0, 2, time_diffs=[0])

        message = analyzer.run()
        self.assertEqual(
            message, "Sessionizing completed, number of session created: 1"
        )

        event1 = datastore.event_store["0"]
        self.assertEqual(event1["_source"]["session_id"], {"all_events": 1})
        event2 = datastore.event_store["100"]
        self.assertEqual(event2["_source"]["session_id"], {"all_events": 1})
        event3 = datastore.event_store["101"]
        self.assertEqual(event3["_source"]["session_id"], {"all_events": 1})

    @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    def test_zero_events(self):
        """Test the behaviour of the sessionizer when given zero events."""
        index = "test_index"
        sketch_id = 1
        analyzer = SessionizerSketchPlugin(index, sketch_id)
        analyzer.datastore.client = mock.Mock()
        datastore = analyzer.datastore

        _create_mock_event(datastore, 0, 0)

        message = analyzer.run()
        self.assertEqual(
            message, "Sessionizing completed, number of session created: 0"
        )

    @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    def test_one_event(self):
        """Test the behaviour of the sessionizer when given one event."""
        index = "test_index"
        sketch_id = 1
        analyzer = SessionizerSketchPlugin(index, sketch_id)
        analyzer.datastore.client = mock.Mock()
        datastore = analyzer.datastore

        _create_mock_event(datastore, 0, 1)

        message = analyzer.run()
        self.assertEqual(
            message, "Sessionizing completed, number of session created: 1"
        )

        event1 = datastore.event_store["0"]
        self.assertEqual(event1["_source"]["session_id"], {"all_events": 1})


if __name__ == "__main__":
    unittest.main()
