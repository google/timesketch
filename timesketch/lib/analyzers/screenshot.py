"""Sketch analyzer plugin for screenshot."""
from __future__ import unicode_literals

from timesketch.lib import emojis
from timesketch.lib.analyzers import interface
from timesketch.lib.analyzers import manager


class ScreenshotSketchPlugin(interface.BaseAnalyzer):
    """Sketch analyzer for Screenshot."""

    NAME = 'screenshot'
    DISPLAY_NAME = 'screenshot'
    DESCRIPTION = 'TODO: screenshot description'

    DEPENDENCIES = frozenset()

    def __init__(self, index_name, sketch_id):
        """Initialize The Sketch Analyzer.

        Args:
            index_name: Elasticsearch index name
            sketch_id: Sketch ID
        """
        self.index_name = index_name
        super(ScreenshotSketchPlugin, self).__init__(index_name, sketch_id)

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
        # Swap for self.event_pandas to get pandas back instead of events.
        events = self.event_stream(
            query_string=query, return_fields=return_fields)

        # TODO: If an emoji is needed fetch it here.
        # my_emoji = emojis.get_emoji('emoji_name')

        # TODO: Add analyzer logic here.
        # Methods available to use for sketch analyzers:
        # sketch.get_all_indices()
        # (If you add a view, please make sure the analyzer has results before
        # adding the view.)
        # view = self.sketch.add_view(
        #     view_name=name, analyzer_name=self.NAME,
        #     query_string=query_string, query_filter={})
        # event.add_attributes({'foo': 'bar'})
        # event.add_tags(['tag_name'])
        # event.add_label('label')
        # event.add_star()
        # event.add_comment('comment')
        # event.add_emojis([my_emoji])
        # event.add_human_readable('human readable text', self.NAME)
        # Remember you'll need to add event.commit() once all changes to the
        # event have been completed.
        # You can also add a story.
        # story = self.sketch.add_story(title='Story from analyzer')
        # story.add_text('## This is a markdown title')
        # story.add_view(view)
        # story.add_text('This is another paragraph')
        for event in events:
            pass

        # TODO: Return a summary from the analyzer.
        return 'String to be returned'


manager.AnalysisManager.register_analyzer(ScreenshotSketchPlugin)
"""Sketch analyzer plugin for screenshot."""
from __future__ import unicode_literals

from timesketch.lib import emojis
from timesketch.lib.analyzers import interface
from timesketch.lib.analyzers import manager


class ScreenshotSketchPlugin(interface.BaseAnalyzer):
    """Sketch analyzer for Screenshot."""

    NAME = 'screenshot'
    DISPLAY_NAME = 'screenshot'
    DESCRIPTION = 'TODO: screenshot description'

    DEPENDENCIES = frozenset()

    def __init__(self, index_name, sketch_id):
        """Initialize The Sketch Analyzer.

        Args:
            index_name: Elasticsearch index name
            sketch_id: Sketch ID
        """
        self.index_name = index_name
        super(ScreenshotSketchPlugin, self).__init__(index_name, sketch_id)

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
        # Swap for self.event_pandas to get pandas back instead of events.
        events = self.event_stream(
            query_string=query, return_fields=return_fields)

        # TODO: If an emoji is needed fetch it here.
        # my_emoji = emojis.get_emoji('emoji_name')

        # TODO: Add analyzer logic here.
        # Methods available to use for sketch analyzers:
        # sketch.get_all_indices()
        # (If you add a view, please make sure the analyzer has results before
        # adding the view.)
        # view = self.sketch.add_view(
        #     view_name=name, analyzer_name=self.NAME,
        #     query_string=query_string, query_filter={})
        # event.add_attributes({'foo': 'bar'})
        # event.add_tags(['tag_name'])
        # event.add_label('label')
        # event.add_star()
        # event.add_comment('comment')
        # event.add_emojis([my_emoji])
        # event.add_human_readable('human readable text', self.NAME)
        # Remember you'll need to add event.commit() once all changes to the
        # event have been completed.
        # You can also add a story.
        # story = self.sketch.add_story(title='Story from analyzer')
        # story.add_text('## This is a markdown title')
        # story.add_view(view)
        # story.add_text('This is another paragraph')
        for event in events:
            pass

        # TODO: Return a summary from the analyzer.
        return 'String to be returned'


manager.AnalysisManager.register_analyzer(ScreenshotSketchPlugin)
