"""Sketch analyzer plugin for feature extraction."""
from __future__ import unicode_literals

import logging
import os
import re
import yaml

from timesketch.lib import emojis
from timesketch.lib.analyzers import interface
from timesketch.lib.analyzers import manager


class FeatureExtractionSketchPlugin(interface.BaseSketchAnalyzer):
    """Sketch analyzer for FeatureExtraction."""

    NAME = 'feature_extraction'

    CONFIG_FILE = interface.get_config('features.yaml')

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
        if not os.path.isfile(self.CONFIG_FILE):
            return 'Unable to read config file, no features extracted.'

        with open(self.CONFIG_FILE, 'r') as fh:
            try:
                config = yaml.safe_load(fh)
            except yaml.parser.ParserError as exception:
                logging.warning((
                    'Unable to read in YAML config file, '
                    'with error: {0:s}').format(exception))
                return 'No results, unable to parse config file.'

        return_strings = []
        for name, feature_config in config.iteritems():
            feature_string = self.extract_feature(name, feature_config)
            if feature_string:
                return_strings.append(feature_string)

        return ', '.join(return_strings)

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
        try:
            expression = re.compile(expression_string)
        except re.error as exception:
            logging.warning((
                'Regular expression failed to compile, with '
                'error: {0:s}').format(exception))
            return

        emoji_names = config.get('emojis', [])
        emojis_to_add = [emoji.get_emoji(x) for x in emoji_names]

        return_fields = [attribute]

        events = self.event_stream(
            query_string=query, query_dsl=query_dsl,
            return_fields=return_fields)

        event_counter = 0
        for event in events:
            attribute_field = event.source.get(attribute)
            if isinstance(attribute_field, (str, unicode)):
                attribute_value = attribute_field.lower()
            elif isinstance(attribute_field, (list, tuple)):
                attribute_value = ','.join(attribute_field)
            elif isinstance(attribute_field, (int, float)):
                attribute_value = attribute_field
            else:
                attribute_value = None

            if not attribute_value:
                continue

            result = expression.findall(attribute_value)
            if not result:
                continue

            event_counter += 1
            event.add_attributes({store_as: result[0]})
            if emojis_to_add:
                event.add_emojis(emojis_to_add)

            if tags:
                event.add_tags(tags)

        create_view = config.get('create_view', False)
        if create_view and event_counter:
            if query:
                query_string = query
            else:
                query_string = query_dsl
            self.sketch.add_view(name, query_string)

        return 'Feature extraction [{0:s}] extracted {1:d} features.'.format(
            name, event_counter)


manager.AnalysisManager.register_analyzer(FeatureExtractionSketchPlugin)
