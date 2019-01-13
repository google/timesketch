"""Sketch analyzer plugin for feature extraction."""
from __future__ import unicode_literals

import logging
import re
import yaml

from timesketch.lib import emojis
from timesketch.lib.analyzers import interface
from timesketch.lib.analyzers import manager


class FeatureExtractionSketchPlugin(interface.BaseSketchAnalyzer):
    """Sketch analyzer for FeatureExtraction."""

    NAME = 'feature_extraction'

    def __init__(self, index_name, sketch_id):
        """Initialize The Sketch Analyzer.

        Args:
            index_name: Elasticsearch index name
            sketch_id: Sketch ID
        """
        self.index_name = index_name
        super(FeatureExtractionSketchPlugin, self).__init__(
            index_name, sketch_id)

    def run(self):
        """Entry point for the analyzer.

        Returns:
            String with summary of the analyzer result
        """
        #TODO: Add stuff here.
        # Read config file, for each config, run...
        # for name, config in config_files.iteritems():
        #     self.extract_feature(name, config)

    def extract_feature(self, name, config):
        """Ext..."""
        query = config.get('query_string')
        query_dsl = config.get('query_dsl')
        attribute = config.get('attribute')

        if not attribute:
            logging.warning('No attribute defined.')
            return

        store_as = config.get('store_as')
        if not store_as:
            logging.warning('No attribute defined to store results in.')
            return

        tags = config.get('tags', [])
        expression_string = config.get('re')

        if not expression_string:
            logging.warning('No regular expression defined.')
            return
        expression = re.compile(expression_string)

        create_view = config.get('create_view', False)

        emojis_names = config.get('emojis', [])
        emojis_to_add = [emoji.get_emoji(x) for x in emoji_names]

        return_fields = [attribute]

        events = self.event_stream(
            query_string=query, query_dsl=query_dsl,
            return_fields=return_fields)

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
            attribute_result = event.source.get(attribute)
            # TODO: Apply RE to get results.

        # TODO: Return a summary from the analyzer.
        return 'String to be returned'


manager.AnalysisManager.register_analyzer(FeatureExtractionSketchPlugin)
