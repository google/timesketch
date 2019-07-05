"""Index analyzer plugin for sigma."""
from __future__ import unicode_literals
import os

from sigma.backends import elasticsearch as sigma_elasticsearch
import sigma.configuration as sigma_configuration
from sigma.parser import collection as sigma_collection


from timesketch.lib.analyzers import interface
from timesketch.lib.analyzers import manager


class SigmaPlugin(interface.BaseIndexAnalyzer):
    """Index analyzer for Sigma."""

    NAME = 'sigma'

    _CONFIG_FILE = 'sigma_config.yaml'


    def __init__(self, index_name):
        """Initialize the Index Analyzer.

        Args:
            index_name: Elasticsearch index name
        """
        super(SigmaPlugin, self).__init__(index_name)
        sigma_config_path = os.path.join(os.path.dirname(__file__), self._CONFIG_FILE)
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
        sigma_backend = sigma_elasticsearch.ElasticsearchQuerystringBackend(self.sigma_config, {})
        tags_applied = {}

        rules_path = '/path/to/rules/'
        for rule_filename in os.listdir(rules_path):
            tag_name, _ = rule_filename.rsplit('.')
            full_path = os.path.join(rules_path, rule_filename)
            with open(full_path, 'r') as rule_file_content:
                query = rule_file_content.read()
                parser = sigma_collection.SigmaCollectionParser(query, self.sigma_config, None)
                results = parser.generate(sigma_backend)
                for result in results:
                    print(result)
                number_of_tagged_events = self.run_sigma_rule(query, tag_name)
                tags_applied[tag_name] = number_of_tagged_events
        total_tagged_events = sum(tags_applied.values())
        output_string = 'Applied {0:d} tags\n'.format(total_tagged_events)
        for tag_name, number_of_tagged_events in tags_applied:
            output_string += '* {0:s}: {0:d}'.format(tag_name, number_of_tagged_events)
        return output_string


manager.AnalysisManager.register_analyzer(SigmaPlugin)
