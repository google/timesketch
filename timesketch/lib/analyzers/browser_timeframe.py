"""Sketch analyzer plugin for browser timeframe."""
from __future__ import unicode_literals

from timesketch.lib import emojis
from timesketch.lib.analyzers import interface
from timesketch.lib.analyzers import manager


class BrowserTimeframeSketchPlugin(interface.BaseSketchAnalyzer):
    """Sketch analyzer for BrowserTimeframe."""

    NAME = 'browser_timeframe'

    def __init__(self, index_name, sketch_id):
        """Initialize The Sketch Analyzer.

        Args:
            index_name: Elasticsearch index name
            sketch_id: Sketch ID
        """
        self.index_name = index_name
        super(BrowserTimeframeSketchPlugin, self).__init__(
            index_name, sketch_id)

    def run(self):
        """Entry point for the analyzer.

        Returns:
            String with summary of the analyzer result
        """
        # TODO: Add Elasticsearch query to get the events you need.
        query = ''

        # TODO: Specify what returned fields you need for your analyzer.
        return_fields = ['message']

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
        for event in events:
            pass

        # TODO: Return a summary from the analyzer.
        return 'String to be returned'


manager.AnalysisManager.register_analyzer(BrowserTimeframeSketchPlugin)
