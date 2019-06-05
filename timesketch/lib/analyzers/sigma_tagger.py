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

    CONFIG_FILE = 'sigma.yaml'


    def __init__(self, index_name):
        """Initialize the Index Analyzer.

        Args:
            index_name: Elasticsearch index name
        """
        super(SigmaPlugin, self).__init__(index_name)

    def run_sigma_rule(self, query, tag_name):
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
            String with summary of the analyzer result
        """
        with open('/Users/onager/code/timesketch/es_config.yaml', 'r') as sigma_config_file:
            sigma_config = sigma_config_file.read()
            sigma_config = sigma_configuration.SigmaConfiguration(sigma_config)

        sigma_backend = sigma_elasticsearch.ElasticsearchQuerystringBackend(sigma_config, {})

        rules_path = '/Users/onager/code/sigma/rules/linux'
        for rule_filename in os.listdir(rules_path):
            tag_name, _ = rule_filename.rsplit('.')
            full_path = os.path.join(rules_path, rule_filename)
            with open(full_path, 'r') as rule_file_content:
                query = rule_file_content.read()
                parser = sigma_collection.SigmaCollectionParser(query, sigma_config, None)
                results = parser.generate(sigma_backend)
                for result in results:
                    print(result)
                # self.run_sigma_rule(query, tag_name)


manager.AnalysisManager.register_analyzer(SigmaPlugin)
