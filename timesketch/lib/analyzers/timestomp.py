"""Sketch analyzer plugin for timestomp."""
from __future__ import unicode_literals

from timesketch.lib import emojis
from timesketch.lib.analyzers import interface
from timesketch.lib.analyzers import manager


class TimestompSketchPlugin(interface.BaseSketchAnalyzer):
    """Sketch analyzer for Timestomp."""

    NAME = 'timestomp'
    class FileAccessInfo:
        def __init__(self, file_reference, timestamp_type):
            self.file_ref = file_reference
            self.timestamp_type = timestamp_type

            self.si_events = []
            self.fn_events = []

            self.si_timestamps = []
            self.fn_timestamps = []
            self.suspicious = False
            self.diff = 0

            self.name = ""

    def __init__(self, index_name, sketch_id):
        """Initialize The Sketch Analyzer.

        Args:
            index_name: Elasticsearch index name
            sketch_id: Sketch ID
        """
        self.index_name = index_name
        super(TimestompSketchPlugin, self).__init__(index_name, sketch_id)

    def run(self):
        """Entry point for the analyzer.

        Returns:
            String with summary of the analyzer result
        """
        query = 'attribute_type:48 OR attribute_type:16'

        return_fields = ['attribute_type', 'timestamp_desc',
                         'file_reference', 'timestamp', 'name']

        # Dict timstamp_type + "&" + file_ref -> FileAccessInfo
        file_infos = dict()
        # Margin of deviation allowed between.
        margin = 6_000_000_000

        # Generator of events based on your query.
        events = self.event_stream(
            query_string=query, return_fields=return_fields)

        # TODO: If an emoji is needed fetch it here.
        # my_emoji = emojis.get_emoji('emoji_name')

        # TODO: Add analyzer logic here.
        # Methods available to use for sketch analyzers:
        # sketch.get_all_indices()
        # sketch.add_view(name, query_string, query_filter={})
        # event.add_attributes({'foo': 'bar'})
        # event.add_tags(['tag_name'])
        # event_add_label('label')
        # event.add_star()
        # event.add_comment('comment')
        # event.add_emojis([my_emoji])
        # event.add_human_readable('human readable text', self.NAME)
        x = 0
        for event in events:
            event.add_attributes({'sally': 'up'})
            event.commit()
#            attribute_type = event.source.get('attribute_type')
#            file_ref = event.source.get('file_reference')
#            timestamp_type = event.source.get('timestamp_desc')
#            timestamp = event.source.get('timestamp')
#            name = event.source.get('name')
#
#            if not attribute_type or not timestamp_type:
#                continue
#
#            if not (attribute_type == 16 or attribute_type == 48):
#                continue
#
#            key = timestamp_type + "&" + str(file_ref)
#
#            if not key in file_infos:
#                file_infos[key] = TimestompSketchPlugin.FileAccessInfo(
#                  file_ref, timestamp_type)
#
#            file_info = file_infos[key]
#
#            if attribute_type == 16:
#                file_info.si_events.append(event)
#                file_info.si_timestamps.append(timestamp)
#
#            if attribute_type == 48:
#                file_info.name = name
#                file_info.fn_events.append(event)
#                file_info.fn_timestamps.append(timestamp)
#
#        # STEP 2: Flag all suspicious events.
#        for file_info in file_infos.values():
#            if (len(set(file_info.si_timestamps)) != 1 or len(file_info.fn_timestamps) < 1):
#                continue
#
#            suspicious = True
#            for i in range(len(file_info.fn_timestamps)):
#                diff = abs(file_info.fn_timestamps[i] - file_info.si_timestamps[0])
#                file_info.fn_events[i].add_attributes({'time_delta': diff})
#                if diff <= margin:
#                    suspicious = False
#                    file_info.diff = 0
#                    break
#            if suspicious:
#                for fn_event in file_info.fn_events:
#                    fn_event.commit()
#                for si_event in file_info.si_events:
#                    si_event.add_attributes({'timestomped': True})
#                    si_event.commit()


        # TODO: Return a summary from the analyzer.
        return 'String to be returned'


manager.AnalysisManager.register_analyzer(TimestompSketchPlugin)
