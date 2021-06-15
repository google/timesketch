"""Analyzer plugin for tagging."""
import logging

from timesketch.lib import emojis
from timesketch.lib.analyzers import interface
from timesketch.lib.analyzers import manager
from timesketch.lib.analyzers import utils


logger = logging.getLogger('timesketch.analyzers.tagger')


class TaggerSketchPlugin(interface.BaseAnalyzer):
    """Analyzer for tagging events."""

    NAME = 'tagger'
    DISPLAY_NAME = 'Tagger'
    DESCRIPTION = 'Tag events based on pre-defined rules'

    CONFIG_FILE = 'tags.yaml'

    def __init__(self, index_name, sketch_id, timeline_id=None, config=None):
        """Initialize The Sketch Analyzer.

        Args:
            index_name: Elasticsearch index name
            sketch_id: Sketch ID
            timeline_id: The ID of the timeline.
            config: Optional dict that contains the configuration for the
                analyzer. If not provided, the default YAML file will be used.
        """
        self.index_name = index_name
        self._config = config
        super().__init__(index_name, sketch_id, timeline_id=timeline_id)

    def run(self):
        """Entry point for the analyzer.

        Returns:
            String with summary of the analyzer result.
        """
        config = self._config or interface.get_yaml_config(self.CONFIG_FILE)
        if not config:
            return 'Unable to parse the config file.'

        tag_results = []
        for name, tag_config in iter(config.items()):
            tag_result = self.tagger(name, tag_config)
            if tag_result and not tag_result.startswith('0 events tagged'):
                tag_results.append(tag_result)

        if tag_results:
            return ', '.join(tag_results)
        return 'No tags applied'

    def tagger(self, name, config):
        """Tag and add emojis to events.

        Args:
            name: String with the name describing what will be tagged.
            config: A dict that contains the configuration See data/tags.yaml
                for fields and documentation of what needs to be defined.

        Returns:
            String with summary of the analyzer result.
        """
        query = config.get('query_string')
        query_dsl = config.get('query_dsl')
        save_search = config.get('save_search', False)
        # For legacy reasons to support both save_search and
        # create_view parameters.
        if not save_search:
            save_search = config.get('create_view', False)

        search_name = config.get('search_name', None)
        # For legacy reasons to support both search_name and view_name.
        if search_name is None:
            search_name = config.get('view_name', name)

        tags = config.get('tags', [])
        emoji_names = config.get('emojis', [])
        emojis_to_add = [emojis.get_emoji(x) for x in emoji_names]

        expression_string = config.get('regular_expression', '')
        attributes = None
        expression = None
        if expression_string:
            expression = utils.compile_regular_expression(
                expression_string=expression_string,
                expression_flags=config.get('re_flags'))

            attribute = config.get('re_attribute')
            if attribute:
                attributes = [attribute]

        event_counter = 0
        events = self.event_stream(
            query_string=query, query_dsl=query_dsl, return_fields=attributes)

        for event in events:
            if expression:
                value = event.source.get(attributes[0])
                if value:
                    result = expression.findall(value)
                    if not result:
                        # Skip counting this tag since the regular expression
                        # didn't find anything.
                        continue

            event_counter += 1
            event.add_tags(tags)
            event.add_emojis(emojis_to_add)

            # Commit the event to the datastore.
            event.commit()

        if save_search and event_counter:
            self.sketch.add_view(
                search_name, self.NAME, query_string=query, query_dsl=query_dsl)

        return '{0:d} events tagged for [{1:s}]'.format(event_counter, name)


manager.AnalysisManager.register_analyzer(TaggerSketchPlugin)
