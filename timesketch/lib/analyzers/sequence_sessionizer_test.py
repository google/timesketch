"""Tests for SequenceSessionizerSketchPlugin."""

from __future__ import unicode_literals

import mock

from timesketch.lib.analyzers.psexec_sessionizers import (
    DestPsexecSessionizerSketchPlugin,
)
from timesketch.lib.analyzers.sequence_sessionizer import (
    SequenceSessionizerSketchPlugin,
)
from timesketch.lib.testlib import BaseTest
from timesketch.lib.testlib import MockDataStore
from timesketch.lib.analyzers.base_sessionizer_test import _create_eventObj


class ManyEventsSequenceSessionizer(SequenceSessionizerSketchPlugin):
    """Mock sequence sessionizer class with many events in the event_seq."""

    session_type = "many_events_seq_sessionizer"
    max_time_diff_micros = 100
    return_fields = ["hostname", "source_short", "timestamp"]
    event_seq = [
        {"hostname": "host", "source_short": "FILE"},
        {"hostname": "host", "source_short": "WEBHIST"},
    ]


class OneEventSequenceSessionizer(SequenceSessionizerSketchPlugin):
    """Mock sequence sessionizer class with one event in the event_seq."""

    session_type = "one_event_seq_sessionizer"
    max_time_diff_micros = 100
    event_seq = [{"hostname": "host", "source_short": "FILE"}]
    return_fields = ["hostname", "source_short", "timestamp"]


# Invalid sequence sessionizers.
class NoneSeqSequenceSessionizer(SequenceSessionizerSketchPlugin):
    """Invalid sequence sessionizer. event_seq should not be None, everything
    else is valid."""

    session_type = "valid_name"
    event_seq = None
    return_fields = ["timestamp"]


class EmptySeqSequenceSessionizer(SequenceSessionizerSketchPlugin):
    """Invalid sequence sessionizer. event_seq should not be [], everything else
    is valid."""

    session_type = "valid_name"
    event_seq = []
    return_fields = ["timestamp"]


class NoTimestampSequenceSessionizer(SequenceSessionizerSketchPlugin):
    """Invalid sequence sessionizer. return_fields should include 'timestamp',
    everything else is valid."""

    session_type = "valid_name"
    event_seq = [{"hostname": "host", "source_short": "FILE"}]
    return_fields = ["hostname", "source_short"]


class MissingAttrSequenceSessionizer(SequenceSessionizerSketchPlugin):
    """Invalid sequence sessionizer. return_fields doesn't includes all needed
    attributes, everything else is valid."""

    session_type = "valid_name"
    event_seq = [{"hostname": "host", "source_short": "FILE"}]
    return_fields = ["timestamp"]


class NoneSessionTypeSequenceSessionizer(SequenceSessionizerSketchPlugin):
    """Invalid sequence sessionizer. session_type should not be None, everything
    else is valid."""

    session_type = None
    event_seq = [{"hostname": "host", "source_short": "FILE"}]
    return_fields = ["timestamp", "hostname", "source_short"]


class EmptyStrSessionTypeSequenceSessionizer(SequenceSessionizerSketchPlugin):
    """Invalid sequence sessionizer. session_type should not be empty string,
    everything else is valid."""

    session_type = ""
    event_seq = [{"hostname": "host", "source_short": "FILE"}]
    return_fields = ["timestamp", "hostname", "source_short"]


class TestValidSequenceSessionizerPlugin(BaseTest):
    """Tests the validation functionality of the sequence sessionizing sketch
    analyzer."""

    @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    def test_event_seq_none(self):
        """Test event_seq is not None."""
        index = "test_index"
        sketch_id = 1
        sessionizer = NoneSeqSequenceSessionizer(index, sketch_id)

        with self.assertRaises(ValueError):
            sessionizer.run()

    @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    def test_event_seq_empty(self):
        """Test event_seq is not empty."""
        index = "test_index"
        sketch_id = 1
        sessionizer = EmptySeqSequenceSessionizer(index, sketch_id)

        with self.assertRaises(ValueError):
            sessionizer.run()

    @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    def test_no_timestamp(self):
        """Test missing timestamp attribute is added in return_fields.
        The sessionizer should be validated automatically when calling
        sessionizer.run()."""
        index = "test_index"
        sketch_id = 1
        sessionizer = NoTimestampSequenceSessionizer(index, sketch_id)
        sessionizer.datastore.client = mock.Mock()
        datastore = sessionizer.datastore

        _create_mock_event(datastore, 0, 0, [], [0])

        self.assertNotIn("timestamp", sessionizer.return_fields)
        sessionizer.run()
        self.assertIn("timestamp", sessionizer.return_fields)

    @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    def test_missing_attr(self):
        """Test missing attributes added in return_fields.
        The sessionizer should be validated automatically when calling
        sessionizer.run()."""
        index = "test_index"
        sketch_id = 1
        sessionizer = MissingAttrSequenceSessionizer(index, sketch_id)
        sessionizer.datastore.client = mock.Mock()
        datastore = sessionizer.datastore

        _create_mock_event(datastore, 0, 0, [], [0])

        for event in sessionizer.event_seq:
            for attr in event:
                self.assertNotIn(attr, sessionizer.return_fields)
        sessionizer.run()
        for event in sessionizer.event_seq:
            for attr in event:
                self.assertIn(attr, sessionizer.return_fields)

    @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    def test_session_type_none(self):
        """Test session_type is not None."""
        index = "test_index"
        sketch_id = 1
        sessionizer = NoneSessionTypeSequenceSessionizer(index, sketch_id)

        with self.assertRaises(ValueError):
            sessionizer.run()

    @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    def test_session_type_empty_str(self):
        """Test session_type is not empty string."""
        index = "test_index"
        sketch_id = 1
        sessionizer = EmptyStrSessionTypeSequenceSessionizer(index, sketch_id)

        with self.assertRaises(ValueError):
            sessionizer.run()


class TestManyEventsSequenceSessionizerPlugin(BaseTest):
    """Tests base functionality of sequence sessionizing sketch analyzers with
    many events in the even_seq which are listed in seq_sessionizer_classes.

    Attributes:
        seq_sessionizer_classes: A list of sequence sessionizer classes to
            test.
    """

    seq_sessionizer_classes = [
        ManyEventsSequenceSessionizer,
        DestPsexecSessionizerSketchPlugin,
    ]

    @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    def test_sessionizer(self):
        """Test basic sequence sessionizer functionality."""
        index = "test_index"
        sketch_id = 1
        for seq_sessionizer_class in self.seq_sessionizer_classes:
            sessionizer = seq_sessionizer_class(index, sketch_id)
            self.assertIsInstance(sessionizer, seq_sessionizer_class)
            self.assertEqual(index, sessionizer.index_name)
            self.assertEqual(sketch_id, sessionizer.sketch.id)

    @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    def test_one_session(self):
        """Test one sequence of events is finded and allocated as a session."""
        index = "test_index"
        sketch_id = 1
        for seq_sessionizer_class in self.seq_sessionizer_classes:
            sessionizer = seq_sessionizer_class(index, sketch_id)
            sessionizer.datastore.client = mock.Mock()
            datastore = sessionizer.datastore

            _create_mock_event(
                datastore, 0, 2, seq_sessionizer_class.event_seq, time_diffs=[1]
            )

            message = sessionizer.run()
            self.assertEqual(
                message,
                "Sessionizing completed, number of {0:s} sessions created: 1".format(
                    sessionizer.session_type
                ),
            )

            # Events that are not part of the sequence but are between
            # significant events from the event sequence considered as a session
            # are part of the significant events' session.
            for i in range(0, 101):
                event = datastore.event_store[str(i)]
                self.assertEqual(
                    event["_source"]["session_id"][sessionizer.session_type], 1
                )

    @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    def test_multiple_sessions(self):
        """Test multiple sessions are found and allocated correctly."""
        index = "test_index"
        sketch_id = 1
        for seq_sessionizer_class in self.seq_sessionizer_classes:
            sessionizer = seq_sessionizer_class(index, sketch_id)
            sessionizer.datastore.client = mock.Mock()
            datastore = sessionizer.datastore

            _create_mock_event(
                datastore,
                0,
                4,
                seq_sessionizer_class.event_seq + seq_sessionizer_class.event_seq,
                time_diffs=[1, 1, 1],
            )

            message = sessionizer.run()
            self.assertEqual(
                message,
                "Sessionizing completed, number of {0:s} sessions created: 2".format(
                    sessionizer.session_type
                ),
            )

            for i in range(0, 100):
                event = datastore.event_store[str(i)]
                self.assertEqual(
                    event["_source"]["session_id"][sessionizer.session_type], 1
                )
            # Events with id in the range of 101 to 201 are not part of any
            # session.
            for i in range(202, 302):
                event = datastore.event_store[str(i)]
                self.assertEqual(
                    event["_source"]["session_id"][sessionizer.session_type], 2
                )

    @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    def test_after_session(self):
        """Test events after the last event of a sequence are not allocated with
        a session number if they are not part from another session."""
        index = "test_index"
        sketch_id = 1
        for seq_sessionizer_class in self.seq_sessionizer_classes:
            sessionizer = seq_sessionizer_class(index, sketch_id)
            sessionizer.datastore.client = mock.Mock()
            datastore = sessionizer.datastore

            _create_mock_event(
                datastore,
                0,
                4,
                seq_sessionizer_class.event_seq + seq_sessionizer_class.event_seq,
                time_diffs=[1, 1],
            )

            message = sessionizer.run()
            self.assertEqual(
                message,
                "Sessionizing completed, number of {0:s} sessions created: 2".format(
                    sessionizer.session_type
                ),
            )

            # Session 1: events with id from 0 to 101,
            # session 2: events with id from 202 to 303.
            for i in range(102, 201):
                event = datastore.event_store[str(i)]
                self.assertNotIn("session_id", event["_source"])

    @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    def test_edge_time_diff(self):
        """Test events with the edge time difference between them are
        allocated correctly."""
        index = "test_index"
        sketch_id = 1
        for seq_sessionizer_class in self.seq_sessionizer_classes:
            sessionizer = seq_sessionizer_class(index, sketch_id)
            sessionizer.datastore.client = mock.Mock()
            datastore = sessionizer.datastore

            _create_mock_event(
                datastore,
                0,
                2,
                seq_sessionizer_class.event_seq,
                time_diffs=[seq_sessionizer_class.max_time_diff_micros],
            )

            message = sessionizer.run()
            self.assertEqual(
                message,
                "Sessionizing completed, number of {0:s} sessions created: 1".format(
                    sessionizer.session_type
                ),
            )

            for i in range(0, 101):
                event = datastore.event_store[str(i)]
                self.assertEqual(
                    event["_source"]["session_id"][sessionizer.session_type], 1
                )

    @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    def test_above_max_time_diff(self):
        """Test events with max time difference + 1 between them are allocated
        correctly."""
        index = "test_index"
        sketch_id = 1
        for seq_sessionizer_class in self.seq_sessionizer_classes:
            sessionizer = seq_sessionizer_class(index, sketch_id)
            sessionizer.datastore.client = mock.Mock()
            datastore = sessionizer.datastore

            _create_mock_event(
                datastore,
                0,
                2,
                seq_sessionizer_class.event_seq,
                time_diffs=[seq_sessionizer_class.max_time_diff_micros + 1],
            )

            message = sessionizer.run()
            self.assertEqual(
                message,
                "Sessionizing completed, number of {0:s} sessions created: 0".format(
                    sessionizer.session_type
                ),
            )

            # Events with id 0 and id 101 form the requested sequence, but
            # event with id 100 and 101 have max_time_diff_micros + 1 bewtween
            # them
            for i in range(0, 201):
                event = datastore.event_store[str(i)]
                self.assertNotIn("session_id", event["_source"])

    @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    def test_zero_events(self):
        """Test the behaviour of the sequence sessionizer when given zero
        events."""
        index = "test_index"
        sketch_id = 1
        for seq_sessionizer_class in self.seq_sessionizer_classes:
            sessionizer = seq_sessionizer_class(index, sketch_id)
            sessionizer.datastore.client = mock.Mock()
            datastore = sessionizer.datastore

            _create_mock_event(datastore, 0, 0, [], [0])

            message = sessionizer.run()
            self.assertEqual(
                message,
                "Sessionizing completed, number of {0:s} sessions created: 0".format(
                    sessionizer.session_type
                ),
            )


class TestOneEventSequenceSessionizerPlugin(BaseTest):
    """Tests base functionality of sequence sessionizing sketch analyzers with
    one event in the even_seq which are listed in seq_sessionizer_classes.

    Attributes:
        seq_sessionizer_classes: A list of sequence sessionizer classes to
            test.
    """

    seq_sessionizer_classes = [OneEventSequenceSessionizer]

    @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    def test_sessionizer(self):
        """Test basic sequence sessionizer functionality."""
        index = "test_index"
        sketch_id = 1
        for seq_sessionizer_class in self.seq_sessionizer_classes:
            sessionizer = seq_sessionizer_class(index, sketch_id)
            self.assertIsInstance(sessionizer, seq_sessionizer_class)
            self.assertEqual(index, sessionizer.index_name)
            self.assertEqual(sketch_id, sessionizer.sketch.id)

    @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    def test_one_session(self):
        """Test one sequence of events is finded and allocated as a session."""
        index = "test_index"
        sketch_id = 1
        for seq_sessionizer_class in self.seq_sessionizer_classes:
            sessionizer = seq_sessionizer_class(index, sketch_id)
            sessionizer.datastore.client = mock.Mock()
            datastore = sessionizer.datastore

            _create_mock_event(datastore, 0, 1, seq_sessionizer_class.event_seq)

            message = sessionizer.run()
            self.assertEqual(
                message,
                "Sessionizing completed, number of {0:s} sessions created: 1".format(
                    sessionizer.session_type
                ),
            )

            # Event with id 0 is the significant for the event_seq event.
            event = datastore.event_store["0"]
            self.assertEqual(
                event["_source"]["session_id"][sessionizer.session_type], 1
            )

    @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    def test_multiple_sessions(self):
        """Test multiple sessions are finded and allocated correctly."""
        index = "test_index"
        sketch_id = 1
        for seq_sessionizer_class in self.seq_sessionizer_classes:
            sessionizer = seq_sessionizer_class(index, sketch_id)
            sessionizer.datastore.client = mock.Mock()
            datastore = sessionizer.datastore

            _create_mock_event(
                datastore,
                0,
                2,
                seq_sessionizer_class.event_seq + seq_sessionizer_class.event_seq,
                time_diffs=[1, 1, 1],
            )

            message = sessionizer.run()
            self.assertEqual(
                message,
                "Sessionizing completed, number of {0:s} sessions created: 2".format(
                    sessionizer.session_type
                ),
            )

            # Session 1: events with id 0.
            event = datastore.event_store["0"]
            self.assertEqual(
                event["_source"]["session_id"][sessionizer.session_type], 1
            )
            # Session 2: events with id 101.
            event = datastore.event_store["101"]
            self.assertEqual(
                event["_source"]["session_id"][sessionizer.session_type], 2
            )

    @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    def test_after_session(self):
        """Test events after the last event of a sequence are not allocated with
        a session number if they are not part from another session."""
        index = "test_index"
        sketch_id = 1
        for seq_sessionizer_class in self.seq_sessionizer_classes:
            sessionizer = seq_sessionizer_class(index, sketch_id)
            sessionizer.datastore.client = mock.Mock()
            datastore = sessionizer.datastore

            _create_mock_event(
                datastore,
                0,
                2,
                seq_sessionizer_class.event_seq + seq_sessionizer_class.event_seq,
                time_diffs=[1, 1],
            )

            message = sessionizer.run()
            self.assertEqual(
                message,
                "Sessionizing completed, number of {0:s} sessions created: 2".format(
                    sessionizer.session_type
                ),
            )

            # Session 1: events with id 0.
            # Session 1: events with id 101.
            for i in range(1, 100):
                event = datastore.event_store[str(i)]
                self.assertNotIn("session_id", event["_source"])

    @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    def test_zero_events(self):
        """Test the behaviour of the sequence sessionizer when given zero
        events."""
        index = "test_index"
        sketch_id = 1
        for seq_sessionizer_class in self.seq_sessionizer_classes:
            sessionizer = seq_sessionizer_class(index, sketch_id)
            sessionizer.datastore.client = mock.Mock()
            datastore = sessionizer.datastore

            _create_mock_event(datastore, 0, 0, [], [0])

            message = sessionizer.run()
            self.assertEqual(
                message,
                "Sessionizing completed, number of {0:s} sessions created: 0".format(
                    sessionizer.session_type
                ),
            )


def _create_mock_event(datastore, event_id, quantity, attributes, time_diffs=None):
    """Loads in the datastore mock events that based on the given arguments.
    Args:
        datastore: An instance of MockDataStore.
        event_id: Desired ID for the Event.
        quantity: The number of Events to be generated.
        attributes: A list of dictionaries with attributes for the generated
            events.
        time_diffs: A list of time differences between the generated Events.
    """

    if not time_diffs:
        time_diffs = [0]
    if quantity < 0:
        quantity = abs(quantity)

    # If the list of time differences is too small to be compatible with the
    # quantity of events, then extend the list with the last value for as many
    # items as necessary.
    if quantity - len(time_diffs) > 0:
        time_diffs.extend(
            [time_diffs[len(time_diffs) - 1]] * (quantity - len(time_diffs))
        )

    event_timestamp = 1410895419859714

    for i in range(quantity):
        _create_eventObj(datastore, event_id, event_timestamp, attributes[i])
        # Adding extra events after every requested event for better simulation
        # of real timeline data i.e. working with a larger dataset.
        for _ in range(100):
            event_timestamp += 1
            event_id += 1
            _create_eventObj(datastore, event_id, event_timestamp)
        event_timestamp += abs(time_diffs[i])
        event_id += 1
