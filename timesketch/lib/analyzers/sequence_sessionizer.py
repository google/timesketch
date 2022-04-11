"""Sequenced activity sessionizing sketch analyzer plugin."""

from __future__ import unicode_literals

from timesketch.lib.analyzers import sessionizer


class SequenceSessionizerSketchPlugin(sessionizer.SessionizerSketchPlugin):
    """Base class for specialized sequenced activity sessionizings
    sketch plugins.

    Attributes:
        event_seq: List of dictionaries of attributes describing the events.
        event_storage: List of events.
        num_event_to_find: Number that shows which event from the sequence
            should be matched.
        recording: Shows if currently are finded and stored events that match
            the specified sequence of events.
        session_num: Counter for the number of sessions.
    """

    event_seq = []
    event_storage = []
    num_event_to_find = 0
    recording = False
    return_fields = ["timestamp"]
    session_num = 0
    session_type = None

    def run(self):
        """Entry point for the analyzer.

        Allocates each event between the first event of the event_seq and the
        last event of the event_seq an session_type attribute with a value
        session_num.

        Returns:
            String containing the name of the event sequence and the
            number of sessions created.
        """
        if self.session_type is None or self.session_type == "":
            raise ValueError("No session_type provided.")
        if self.event_seq is None or self.event_seq == []:
            raise ValueError("No event_seq provided.")
        # If return_fields in None, then all attributes are provided.
        if self.return_fields is not None:
            self.build_return_fields()

        # event_stream returns an ordered generator of events (by time)
        # therefore no further sorting is needed.
        events = self.event_stream(
            query_string=self.query, return_fields=self.return_fields
        )

        last_timestamp = None
        for event in events:
            curr_timestamp = event.source.get("timestamp")
            if last_timestamp and (
                curr_timestamp - last_timestamp > self.max_time_diff_micros
            ):
                self.flush_events(drop=True)
            self.process_event(event)
            last_timestamp = curr_timestamp

        self.sketch.add_view(
            "Session view",
            self.NAME,
            query_string="session_id.{0:s}:*".format(self.session_type),
        )

        return (
            "Sessionizing completed, number of {0:s} sessions created:"
            " {1:d}".format(self.session_type, self.session_num)
        )

    def process_event(self, event):
        """Process event depending on if the event is significant for the
        searched event sequence.

        Event is significant if it matches the current event in the event_seq
        or if in the timeline it is between two consistent events from the
        event_seq.

        Args:
            event: Event to process.
        """
        if self.match_event(event):
            self.recording = True
            self.event_storage.append(event)
            self.num_event_to_find += 1

            if self.num_event_to_find == len(self.event_seq):
                self.flush_events()
            return

        if self.recording:
            self.event_storage.append(event)

    def flush_events(self, drop=False):
        """Annotates or clears events in event_storage according to the flag
        drop and resets session recording state.

        Args:
            drop: If True, the stored events will not be committed to the
                database.
        """
        if not drop:
            self.session_num += 1
            for event in self.event_storage:
                self.annotateEvent(event, self.session_num)

        self.recording = False
        self.num_event_to_find = 0
        self.event_storage = []

    def match_event(self, event):
        """Compare event with the event to search for in the event sequence.

        Args:
            event: Event to compare with the one in the event sequence.

        Returns:
            If event matches the event to search for in the event sequence.
        """
        event_to_match = self.event_seq[self.num_event_to_find]

        for key, value in event_to_match.items():
            if key not in event.source.keys():
                return False
            if value not in event.source.get(key):
                return False
        return True

    def build_return_fields(self):
        """Add missing fields to return_fields. Additional fields are not
        removed."""
        if "timestamp" not in self.return_fields:
            self.return_fields.append("timestamp")
        for event in self.event_seq:
            self.return_fields.extend(event)
        self.return_fields = list(set(self.return_fields))
