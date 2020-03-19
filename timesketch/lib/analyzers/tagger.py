"""Analyzer plugin for tagging."""
from timesketch.lib import emojis
from timesketch.lib.analyzers import interface
from timesketch.lib.analyzers import manager


class TaggerSketchPlugin(interface.BaseSketchAnalyzer):
    """Sketch analyzer for tagging events."""

    NAME = 'tagger'
    CONFIG_FILE = 'tags.yaml'

    def __init__(self, index_name, sketch_id, config=None):
        """Initialize The Sketch Analyzer.

        Args:
            index_name: Elasticsearch index name
            sketch_id: Sketch ID
            config: Optional dict that contains the configuration for the
                analyzer. If not provided, the default YAML file will be used.
        """
        self.index_name = index_name
        self._config = config
        super(TaggerSketchPlugin, self).__init__(index_name, sketch_id)

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
            if tag_result:
                tag_results.append(tag_result)

        return ', '.join(tag_results)

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
        create_view = config.get('create_view', False)
        view_name = config.get('view_name', name)
        tags = config.get('tags', [])
        emoji_names = config.get('emojis', [])
        emojis_to_add = [emojis.get_emoji(x) for x in emoji_names]

        event_counter = 0
        events = self.event_stream(query_string=query, query_dsl=query_dsl)

        for event in events:
            event_counter += 1
            event.add_tags(tags)
            event.add_emojis(emojis_to_add)

            # Commit the event to the datastore.
            event.commit()

        if create_view and event_counter:
            self.sketch.add_view(
                view_name, self.NAME, query_string=query, query_dsl=query_dsl)

        return '{0:d} events tagged for [{1:s}]'.format(event_counter, name)


manager.AnalysisManager.register_analyzer(TaggerSketchPlugin)
