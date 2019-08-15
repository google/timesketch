"""Sketch analyzer plugin for timestomp."""
from __future__ import unicode_literals

from flask import current_app

from timesketch.lib.analyzers import interface
from timesketch.lib.analyzers import manager

class FileInfo(object):
    def __init__(self, file_reference=None, timestamp_desc=None,
                 std_info_event=None, std_info_timestamp=None, file_names=None):
        self.file_reference = file_reference
        self.timestamp_desc = timestamp_desc
        self.std_info_event = std_info_event
        self.std_info_timestamp = std_info_timestamp
        if file_names:
            self.file_names = file_names
        else:
            self.file_names = []

class TimestompSketchPlugin(interface.BaseSketchAnalyzer):
    """Sketch analyzer for Timestomp."""

    NAME = 'timestomp'

    def __init__(self, index_name, sketch_id):
        """Initialize The Sketch Analyzer.

        Args:
            index_name: Elasticsearch index name
            sketch_id: Sketch ID
        """
        self.index_name = index_name
        self.threshold = current_app.config.get(
            'TIMESTOMP_ANALYZER_THRESHOLD', 10) * 60000000
        super(TimestompSketchPlugin, self).__init__(index_name, sketch_id)

    def handle_timestomp(self, file_info):
        """Compares timestamps and adds diffs to events.

        Args:
            file_info: FileInfo object for event to look at.

        Returns:
            Boolean, true if timestomping was detected.

        """
        if not file_info.std_info_event or not file_info.file_names:
            return False

        suspicious = True
        diffs = []

        for fn in file_info.file_names:
            diff = fn[1] - file_info.std_info_timestamp
            diffs.append(diff)

            if abs(diff) > self.threshold:
                fn[0].add_attributes({'time_delta': diff})
            else:
                suspicious = False
                break

        if suspicious:
            for fn in file_info.file_names:
                fn[0].commit()

            file_info.std_info_event.add_attributes({'time_deltas': diffs})
            file_info.std_info_event.commit()

        return suspicious

    def run(self):
        """Entry point for the analyzer.

        Returns:
            String with summary of the analyzer result
        """

        query = 'attribute_type:48 OR attribute_type:16'

        return_fields = ['attribute_type', 'timestamp_desc',
                         'file_reference', 'timestamp']


        # Generator of events based on your query.
        events = self.event_stream(
            query_string=query, return_fields=return_fields)

        # Dict timstamp_type + "&" + file_ref -> FileInfo
        file_infos = dict()

        for event in events:
            attribute_type = event.source.get('attribute_type')
            file_ref = event.source.get('file_reference')
            timestamp_type = event.source.get('timestamp_desc')
            timestamp = event.source.get('timestamp')

            if not attribute_type or not timestamp_type:
                continue

            if not attribute_type in [16, 48]:
                continue

            key = timestamp_type + "&" + str(file_ref)

            if not key in file_infos:
                file_infos[key] = FileInfo()

            file_info = file_infos[key]
            file_info.file_reference = file_ref
            file_info.timestamp_desc = timestamp_type

            if attribute_type == 16:
                # TODO: Check if std_info is already set (should be one at max)
                file_info.std_info_timestamp = timestamp
                file_info.std_info_event = event

            if attribute_type == 48:
                file_info.file_names.append((event, timestamp))

        timestomps = 0
        for file_info in file_infos.values():
            if self.handle_timestomp(file_info):
                timestomps = timestomps + 1


        if timestomps > 0:
            self.sketch.add_view(
                view_name='Timestomp', analyzer_name=self.NAME,
                query_string='_exists_:time_delta or _exists:time_deltas')


        return ('Timestomp Analyzer completed, found {0:d} timestomped events'
                .format(timestomps))


manager.AnalysisManager.register_analyzer(TimestompSketchPlugin)
