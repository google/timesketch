"""Sequenced activity sessionizing sketch analyzer plugin."""

from __future__ import unicode_literals

from timesketch.lib.analyzers import sessionizer


class SequenceSessionizerSketchPlugin(
        sessionizer.SessionizerSketchPlugin):
    """Base class for specialized sequenced activity sessionizings
    sketch plugins.

    Attributes:
        event_seq_name: The name of the event sequence.
        event_seq: List of dictionaries of attributes describing the events.
        event_storage: List of events.
        num_event_to_find: Number that shows which event from the sequence
            should be matched.
        recording: Shows if currently are finded and stored events that match
            the specified sequence of events.
        return_fields: List of name of event attributes, should be specified in
            the inheriting sessionizers. It must contains 'timestamp'.
        session_num: Counter for the number of sessions.
    """
    event_seq_name = None
    event_seq = None
    event_storage = []
    num_event_to_find = 0
    recording = False
    return_fields = ['timestamp']
    session_num = 0

    def run(self):
        """Entry point for the analyzer.

        Allocates each event between the first event of the event_seq and the
        last event of the event_seq an event_seq_name attribute and a
        session_num.

        Returns:
            String containing the name of the event sequence and the
            number of sessions created.
        """
        if self.event_seq_name is None:
            raise RuntimeError('No event_seq_name provided.')
        if self.event_seq is None or self.event_seq == []:
            raise RuntimeError('No event_seq provided.')
        # If return_fields in none, then all attributes are provided.
        if self.return_fields is not None:
            if 'timestamp' not in self.return_fields:
                raise RuntimeError('No "timestamp" in return_fields.')
            if len(self.return_fields) <= 1:
                raise RuntimeError('No return_fields provided.')

        # event_stream returns an ordered generator of events (by time)
        # therefore no further sorting is needed.
        events = self.event_stream(query_string=self.query,
                                   return_fields=self.return_fields)

        last_timestamp = 0

        try:
            first_event = next(events)
            last_timestamp = first_event.source.get('timestamp')
            self.process_event(first_event)

            for event in events:
                curr_timestamp = event.source.get('timestamp')
                if curr_timestamp - last_timestamp > self.max_time_diff_micros:
                    self.flush_events(drop=True)

                self.process_event(event)
                last_timestamp = curr_timestamp
        except StopIteration:
            pass

        self.query = self.get_query_string()

        self.sketch.add_view('Session view', self.NAME, query_string=self.query)

        return ('Sessionizing completed, number of {0:s} session created:'
                ' {1:d}'.format(self.event_seq_name, self.session_num))

    def annotateEvent(self, event, session_num):
        """Add an event_seq_name attribute with a session_num to event.

        Args:
            event: Event to annotate.
            session_num: Session number for the event.
        """
        event.add_attributes({self.event_seq_name: session_num})
        event.commit()

    def process_event(self, event):
        """Process event depending on if the event is significant for the
        searched event sequence.

        Event is significant if it matches the current
        event in the event_seq or if in the timeline it is between two
        consistent events from the event_seq.

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
            drop: Indicator if the stored events should not be commited.
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
            If event matches the event to search for in the event
        sequence.
        """
        event_to_match = self.event_seq[self.num_event_to_find]

        for key, value in event_to_match.items():
            if value != event.source.get(key):
                return False
        return True

    def get_query_string(self):
        """Generate query string for all events allocated with event_seq_name
        attribute.

        Returns:
            Query string for Elasticsearch.
        """
        query_string = self.event_seq_name + ':*'
        return query_string
