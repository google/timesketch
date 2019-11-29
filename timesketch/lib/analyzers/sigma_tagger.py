"""Index analyzer plugin for sigma."""
from __future__ import unicode_literals

import logging
import os

from sigma.backends import elasticsearch as sigma_elasticsearch
import sigma.configuration as sigma_configuration
from sigma.parser import collection as sigma_collection


from timesketch.lib.analyzers import interface
from timesketch.lib.analyzers import manager


class SigmaPlugin(interface.BaseSketchAnalyzer):
    """Index analyzer for Sigma."""

    NAME = 'sigma'

    _CONFIG_FILE = 'sigma_config.yaml'

    # Path to the directory containing the Sigma Rules to run, relative to
    # this file.
    _RULES_PATH = ''


    def __init__(self, index_name, sketch_id):
        """Initialize the Index Analyzer.

        Args:
            index_name: Elasticsearch index name.
            sketch_id: Sketch ID.
        """
        super(SigmaPlugin, self).__init__(index_name, sketch_id)
        sigma_config_path = interface.get_config_path(self._CONFIG_FILE)
        logging.debug('[sigma] Loading config from {0!s}'.format(
            sigma_config_path))
        with open(sigma_config_path, 'r') as sigma_config_file:
            sigma_config = sigma_config_file.read()
        self.sigma_config = sigma_configuration.SigmaConfiguration(sigma_config)

    def run_sigma_rule(self, query, tag_name):
        """Runs a sigma rule and applies the appropriate tags.

        Args:
            query: elastic search query for events to tag.
            tag_name: tag to apply to matching events.

        Returns:
            int: number of events tagged.
        """
        return_fields = []
        tagged_events = 0
        events = self.event_stream(
            query_string=query, return_fields=return_fields)
        for event in events:
            event.add_tags([tag_name])
            event.commit()
            tagged_events += 1
        return tagged_events

    def run(self):
        """Entry point for the analyzer.

        Returns:
            String with summary of the analyzer result.
        """
        sigma_backend = sigma_elasticsearch.ElasticsearchQuerystringBackend(
            self.sigma_config, {})
        tags_applied = {}

        rules_path = os.path.join(os.path.dirname(__file__), self._RULES_PATH)
        for rule_filename in os.listdir(rules_path):
            tag_name, _ = rule_filename.rsplit('.')
            tags_applied[tag_name] = 0
            rule_file_path = os.path.join(rules_path, rule_filename)
            rule_file_path = os.path.abspath(rule_file_path)
            logging.info('[sigma] Reading rules from {0!s}'.format(
                rule_file_path))
            with open(rule_file_path, 'r') as rule_file:
                rule_file_content = rule_file.read()
                parser = sigma_collection.SigmaCollectionParser(
                    rule_file_content, self.sigma_config, None)
                try:
                    results = parser.generate(sigma_backend)
                except NotImplementedError as exception:
                    logging.error(
                        'Error generating rule in file {0:s}: {1!s}'.format(
                            rule_file_path, exception))
                    continue

                for result in results:
                    logging.info(
                        '[sigma] Generated query {0:s}'.format(result))
                    number_of_tagged_events = self.run_sigma_rule(
                        result, tag_name)
                    tags_applied[tag_name] += number_of_tagged_events

        total_tagged_events = sum(tags_applied.values())
        output_string = 'Applied {0:d} tags\n'.format(total_tagged_events)
        for tag_name, number_of_tagged_events in tags_applied.items():
            output_string += '* {0:s}: {1:d}'.format(
                tag_name, number_of_tagged_events)
        return output_string


class LinuxRulesSigmaPlugin(SigmaPlugin):
    """Sigma plugin to run Linux rules."""

    _RULES_PATH = '../../../data/linux'

    NAME = 'sigma_linux'


manager.AnalysisManager.register_analyzer(LinuxRulesSigmaPlugin)
