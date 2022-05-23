"""Sessionizing sketch analyzer plugin."""

from __future__ import unicode_literals

from timesketch.lib.analyzers import interface
from timesketch.lib.analyzers import manager


class SessionizerSketchPlugin(interface.BaseAnalyzer):
    """Sessionizing analyzer.

    All events in sketch with id sketch_id
    are grouped in sessions based on the time difference between them. Two
    consecutive events are in the same session if the time difference between
    them is less or equal then max_time_diff_micros.

    Attributes:
        NAME (str): The name of the sessionizer.
        max_time_diff_micros (int): The maximum time difference between two
            events in the same session, in microseconds.
        query (str): The OpenSearch query string query identifying the
            events to be sessionized.
        session_type (str): Used to label the events that are sessionized.
    """

    NAME = "sessionizer"
    DISPLAY_NAME = "Time based sessions"
    DESCRIPTION = (
        "Events are grouped in sessions based on the time difference" " between them"
    )

    # TODO max_time_diff_micros should be configurable
    max_time_diff_micros = 300000000
    query = "*"
    session_type = "all_events"

    def run(self):
        """Entry point for the analyzer. Allocates each event a session_id
        attribute.
        Returns:
            String containing the number of sessions created.
        """
        return_fields = ["timestamp"]

        # event_stream returns an ordered generator of events (by time)
        # therefore no further sorting is needed.
        events = self.event_stream(query_string=self.query, return_fields=return_fields)
        session_num = 0

        try:
            first_event = next(events)
            last_timestamp = first_event.source.get("timestamp")
            session_num = 1
            self.annotateEvent(first_event, session_num)

            for event in events:
                curr_timestamp = event.source.get("timestamp")
                if curr_timestamp - last_timestamp > self.max_time_diff_micros:
                    session_num += 1
                self.annotateEvent(event, session_num)
                last_timestamp = curr_timestamp

        except StopIteration:
            pass

        return "Sessionizing completed, number of session created:" " {0:d}".format(
            session_num
        )

    def annotateEvent(self, event, session_num):
        """Annotate an event with a session ID. Store IDs as dictionary entries
        corresponding to the type of session.
        Args:
            event: The event to annotate.
            session_num: The session ID.
        """
        current_attr = event.source.get("session_id")
        if current_attr is None:
            event.add_attributes({"session_id": {self.session_type: session_num}})
        else:
            current_attr[self.session_type] = session_num
            event.add_attributes({"session_id": current_attr})

        event.commit()


manager.AnalysisManager.register_analyzer(SessionizerSketchPlugin)
