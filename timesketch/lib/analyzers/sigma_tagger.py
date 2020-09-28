"""Index analyzer plugin for sigma."""
from __future__ import unicode_literals

import logging
import os
import time
import codecs
import elasticsearch

from sigma.backends import elasticsearch as sigma_elasticsearch
import sigma.configuration as sigma_configuration
from sigma.parser import collection as sigma_collection
from timesketch.lib.analyzers import utils

from timesketch.lib.analyzers import interface
from timesketch.lib.analyzers import manager


logger = logging.getLogger('timesketch.analyzers.sigma_tagger')


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
        logger.debug('[sigma] Loading config from {0!s}'.format(
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
        tagged_events_counter = 0
        events = self.event_stream(
            query_string=query, return_fields=return_fields)
        for event in events:
            event.add_tags(['sigma_{0:s}'.format(tag_name)])
            event.commit()
            tagged_events_counter += 1
        return tagged_events_counter

    def run(self):
        """Entry point for the analyzer.

        Returns:
            String with summary of the analyzer result.
        """
        sigma_backend = sigma_elasticsearch.ElasticsearchQuerystringBackend(
            self.sigma_config, {})
        tags_applied = {}

        sigma_rule_counter = 0

        rules_path = os.path.join(os.path.dirname(__file__), self._RULES_PATH)


        for dirpath, dirnames, files in os.walk(rules_path):

            if 'deprecated' in dirnames:
                dirnames.remove('deprecated')

            for rule_filename in files:
                if rule_filename.lower().endswith('yml'):

                    # if a sub dir is found, append it to be scanned for rules
                    if os.path.isdir(os.path.join(rules_path, rule_filename)):
                        logger.error(
                            'this is a directory, skipping: {0:s}'.format(
                                rule_filename))
                        continue

                    tag_name, _ = rule_filename.rsplit('.')
                    tags_applied[tag_name] = 0
                    rule_file_path = os.path.join(dirpath, rule_filename)
                    rule_file_path = os.path.abspath(rule_file_path)
                    logger.info('[sigma] Reading rules from {0!s}'.format(
                        rule_file_path))
                    with codecs.open(rule_file_path, 'r', encoding='utf-8',
                                     errors='replace') as rule_file:
                        try:
                            rule_file_content = rule_file.read()
                            parser = sigma_collection.SigmaCollectionParser(
                                rule_file_content, self.sigma_config, None)
                            parsed_sigma_rules = parser.generate(sigma_backend)
                        except NotImplementedError as exception:
                            logger.error(
                                'Error generating rule in file {0:s}: {1!s}'
                                .format(rule_file_path, exception))
                            continue

                        for sigma_rule in parsed_sigma_rules:
                            try:
                                sigma_rule_counter += 1
                                # TODO Investigate how to handle .keyword
                                # fields in Sigma.
                                # https://github.com/google/timesketch/issues/1199#issuecomment-639475885
                                sigma_rule = sigma_rule\
                                    .replace(".keyword:", ":")
                                logger.info(
                                    '[sigma] Generated query {0:s}'
                                    .format(sigma_rule))
                                tagged_events_counter = self.run_sigma_rule(
                                    sigma_rule, tag_name)
                                tags_applied[tag_name] += tagged_events_counter
                            except elasticsearch.TransportError as e:
                                logger.error(
                                    'Timeout generating rule in file {0:s}: '
                                    '{1!s} waiting for 10 seconds'.format(
                                        rule_file_path, e), exc_info=True)
                                time.sleep(10) # waiting 10 seconds

        total_tagged_events = sum(tags_applied.values())
        output_string = 'Applied {0:d} tags\n'.format(total_tagged_events)
        for tag_name, tagged_events_counter in tags_applied.items():
            output_string += '* {0:s}: {1:d}\n'.format(
                tag_name, tagged_events_counter)

        if sigma_rule_counter > 0:
            view = self.sketch.add_view(
                view_name='Sigma Rule matches', analyzer_name=self.NAME,
                query_string='tag:"sigma*"')
            agg_params = {
                'field': 'tag',
                'limit': 20,
            }
            agg_obj = self.sketch.add_aggregation(
                name='Top 20 Sigma tags', agg_name='field_bucket',
                agg_params=agg_params, view_id=view.id, chart_type='hbarchart',
                description='Created by the Sigma analyzer')


            story = self.sketch.add_story("Sigma Rule hits")
            story.add_text(
                utils.SIGMA_STORY_HEADER, skip_if_exists=True)

            story.add_text(
                '## Sigma Analyzer.\n\nThe Sigma '
                'analyzer takes Events and matches them with Sigma rules.'
                'In this timeline the analyzer discovered {0:d} '
                'Sigma tags.\n\nThis is a summary of '
                'it\'s findings.'.format(sigma_rule_counter))
            story.add_text(
                'The top 20 most commonly discovered tags were:')
            story.add_aggregation(agg_obj)
            story.add_text(
                'And an overview of all the discovered search terms:')
            story.add_view(view)


        return output_string

class RulesSigmaPlugin(SigmaPlugin):
    """Sigma plugin to run rules."""

    _RULES_PATH = '../../../data/sigma/rules/'

    NAME = 'sigma'

manager.AnalysisManager.register_analyzer(RulesSigmaPlugin)
