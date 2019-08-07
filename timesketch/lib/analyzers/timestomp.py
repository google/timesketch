"""Sketch analyzer plugin for timestomp."""
from __future__ import unicode_literals

from timesketch.lib.analyzers import interface
from timesketch.lib.analyzers import manager

class FileInfo(object):
    def __init__(self, si_events=None, si_timestamps=None,
                 fn_events=None, fn_timestamps=None):
        if si_events:
            self.si_events = si_events
        else:
            self.si_events = []
        if si_timestamps:
            self.si_timestamps = si_timestamps
        else:
            self.si_timestamps = []
        if fn_events:
            self.fn_events = fn_events
        else:
            self.fn_events = []
        if fn_timestamps:
            self.fn_timestamps = fn_timestamps
        else:
            self.fn_timestamps = []

class TimestompSketchPlugin(interface.BaseSketchAnalyzer):
    """Sketch analyzer for Timestomp."""

    NAME = 'timestomp'
    MARGIN = 6000000000

    def __init__(self, index_name, sketch_id):
        """Initialize The Sketch Analyzer.

        Args:
            index_name: Elasticsearch index name
            sketch_id: Sketch ID
        """
        self.index_name = index_name
        super(TimestompSketchPlugin, self).__init__(index_name, sketch_id)


# TODO: Find better name for this method.
    def handle_timestomp(self, file_info):
        """Compares timestamps and adds diffs to events.

        Args:
            file_info: FileInfo object for event to look at.

        Returns:
            Boolean, true if timestomping was detected.

        """
        if (len(set(file_info.si_timestamps)) != 1
                or not file_info.fn_timestamps):
            return False

        suspicious = True
        for i in range(len(file_info.fn_timestamps)):
            diff = abs(file_info.fn_timestamps[i]
                       - file_info.si_timestamps[0])
            file_info.fn_events[i].add_attributes({'time_delta': diff})
            file_info.fn_events[i].add_label("timestomped")
            if diff <= self.MARGIN:
                suspicious = False
                file_info.diff = 0
                break

        if suspicious:
            for fn_event in file_info.fn_events:
                fn_event.commit()

            # TODO: Decide if we want to flag std_info events
            for si_event in file_info.si_events:
                si_event.add_attributes({'timestomped': True})
                si_event.commit()

        return suspicious

    def run(self):
        """Entry point for the analyzer.

        Returns:
            String with summary of the analyzer result
        """
        query = 'attribute_type:48 OR attribute_type:16'

        return_fields = ['attribute_type', 'timestamp_desc',
                         'file_reference', 'timestamp']

        # Dict timstamp_type + "&" + file_ref -> FileInfo
        file_infos = dict()
        # Margin of deviation allowed between.

        # Generator of events based on your query.
        events = self.event_stream(
            query_string=query, return_fields=return_fields)

        for event in events:
            attribute_type = event.source.get('attribute_type')
            file_ref = event.source.get('file_reference')
            timestamp_type = event.source.get('timestamp_desc')
            timestamp = event.source.get('timestamp')

            if not attribute_type or not timestamp_type:
                continue

            if not attribute_type in (16, 48):
                continue

            key = timestamp_type + "&" + str(file_ref)

            if not key in file_infos:
                file_infos[key] = FileInfo()

                file_info = file_infos[key]

            if attribute_type == 16:
                file_info.si_events.append(event)
                file_info.si_timestamps.append(timestamp)

            if attribute_type == 48:
                file_info.fn_events.append(event)
                file_info.fn_timestamps.append(timestamp)

        timestomps = 0
        for file_info in file_infos.values():
            if self.handle_timestomp(file_info):
                timestomps = timestomps + 1


        if timestomps > 0:
            self.sketch.add_view(
                view_name='Timestomp', analyzer_name=self.NAME,
                query_string='_exists_:time_delta')


        return ('Timestomp Analyzer completed, found {0:d} timestomped events'
                .format(timestomps))


manager.AnalysisManager.register_analyzer(TimestompSketchPlugin)
