"""Sessionizing sketch analyzer plugin."""

from __future__ import unicode_literals

from timesketch.lib.analyzers import interface
from timesketch.lib.analyzers import manager


class SessionizerSketchPlugin(interface.BaseSketchAnalyzer):
    """Sessionizing sketch analyser. All events in sketch with id sketch_id
    are grouped in sessions based on the time difference between them. Two
    consecutive events are in the same session if the time difference between
    them is less or equal then max_time_diff_micros"""

    NAME = 'sessionizer'
    max_time_diff_micros = 300000000

    def __init__(self, index_name, sketch_id):
        """Initialize the sessionizing Sketch Analyzer.

        Args:
            index_name: Elasticsearch index name
            sketch_id: Sketch ID
        """
        self.index_name = index_name
        super(SessionizerSketchPlugin, self).__init__(index_name, sketch_id)

    def run(self):
        """Entry point for the analyzer. Allocates each event a session_number
        attribute.

        Returns:
            String containing the number of sessions created.
        """
        query = '*'
        return_fields = ['timestamp']

        # event_stream returns an ordered generator of events (by time)
        # therefore no further sorting is needed.
        events = self.event_stream(query_string=query,
                                   return_fields=return_fields)
        session_num = 0

        try:
            first_event = next(events)
            last_timestamp = first_event.source.get('timestamp')
            session_num = 1
            first_event.add_attributes({'session_number': session_num})
            first_event.commit()

            for event in events:
                curr_timestamp = event.source.get('timestamp')
                if curr_timestamp - last_timestamp > self.max_time_diff_micros:
                    session_num += 1
                event.add_attributes({'session_number': session_num})
                event.commit()

                last_timestamp = curr_timestamp

            self.sketch.add_view('Session view', 'sessionizer')
        except StopIteration:
            pass

        return ('Sessionizing completed, number of session created:'
                ' {0:d}'.format(session_num))


manager.AnalysisManager.register_analyzer(SessionizerSketchPlugin)
