"""Analyzer plugin for tagging."""

from collections.abc import Iterable  # pylint: disable no-name-in-module
import logging

from timesketch.lib import emojis
from timesketch.lib.analyzers import interface
from timesketch.lib.analyzers import manager
from timesketch.lib.analyzers import utils


logger = logging.getLogger("timesketch.analyzers.tagger")


class TaggerSketchPlugin(interface.BaseAnalyzer):
    """Analyzer for tagging events."""

    NAME = "tagger"
    DISPLAY_NAME = "Tagger"
    DESCRIPTION = "Tag events based on pre-defined rules"

    CONFIG_FILE = "tags.yaml"

    MODIFIERS = {"split": lambda x: x.split(), "upper": lambda x: x.upper()}

    def __init__(self, index_name, sketch_id, timeline_id=None, **kwargs):
        """Initialize The Sketch Analyzer.

        Args:
            index_name: OpenSearch index name
            sketch_id: Sketch ID
            timeline_id: The ID of the timeline
        """
        self.index_name = index_name
        self._tag_name = kwargs.get("tag")
        self._tag_config = kwargs.get("tag_config")
        super().__init__(index_name, sketch_id, timeline_id=timeline_id)

    def run(self):
        """Entry point for the analyzer.

        Returns:
            String with summary of the analyzer result.
        """
        return self.tagger(self._tag_name, self._tag_config)

    @staticmethod
    def get_kwargs():
        """Get kwargs for the analyzer.

        Returns:
            List of searches to tag results for.
        """
        tags_config = interface.get_yaml_config("tags.yaml")
        if not tags_config:
            return "Unable to parse the tags config file."

        tags_kwargs = [
            {"tag": tag, "tag_config": config} for tag, config in tags_config.items()
        ]
        return tags_kwargs

    def tagger(self, name, config):
        """Tag and add emojis to events.

        Args:
            name: String with the name describing what will be tagged.
            config: A dict that contains the configuration See data/tags.yaml
                for fields and documentation of what needs to be defined.

        Returns:
            String with summary of the analyzer result.
        """
        query = config.get("query_string")
        query_dsl = config.get("query_dsl")
        save_search = config.get("save_search", False)
        # For legacy reasons to support both save_search and
        # create_view parameters.
        if not save_search:
            save_search = config.get("create_view", False)

        search_name = config.get("search_name", None)
        # For legacy reasons to support both search_name and view_name.
        if search_name is None:
            search_name = config.get("view_name", name)

        tags = set(config.get("tags", []))
        dynamic_tags = {tag[1:] for tag in tags if tag.startswith("$")}
        tags = {tag for tag in tags if not tag.startswith("$")}

        emoji_names = config.get("emojis", [])
        emojis_to_add = [emojis.get_emoji(x) for x in emoji_names]

        expression_string = config.get("regular_expression", "")
        attributes = list(dynamic_tags)
        expression = None
        if expression_string:
            expression = utils.compile_regular_expression(
                expression_string=expression_string,
                expression_flags=config.get("re_flags"),
            )

            attribute = config.get("re_attribute")
            if attribute:
                attributes.append(attribute)

        event_counter = 0
        events = self.event_stream(
            query_string=query, query_dsl=query_dsl, return_fields=attributes
        )

        for event in events:
            if expression:
                value = event.source.get(config.get("re_attribute"))
                if value:
                    result = expression.findall(value)
                    if not result:
                        # Skip counting this tag since the regular expression
                        # didn't find anything.
                        continue

            event_counter += 1
            event.add_tags(tags)

            # Compute dynamic tag values with modifiers.
            dynamic_tag_values = []
            for attribute in dynamic_tags:
                tag_value = event.source.get(attribute)
                for mod in config.get("modifiers", []):
                    if isinstance(tag_value, str):
                        tag_value = self.MODIFIERS[mod](tag_value)
                if isinstance(tag_value, Iterable):
                    dynamic_tag_values.extend(tag_value)
                else:
                    dynamic_tag_values.append(tag_value)
            event.add_tags(dynamic_tag_values)

            event.add_emojis(emojis_to_add)

            # Commit the event to the datastore.
            event.commit()

        if save_search and event_counter:
            self.sketch.add_view(
                search_name, self.NAME, query_string=query, query_dsl=query_dsl
            )
        return "{0:d} events tagged for [{1:s}]".format(event_counter, name)


manager.AnalysisManager.register_analyzer(TaggerSketchPlugin)
