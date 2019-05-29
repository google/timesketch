"""Index analyzer plugin for threatintel."""
from __future__ import unicode_literals

from flask import current_app
import requests

from timesketch.lib.analyzers import interface
from timesketch.lib.analyzers import manager
from timesketch.lib import emojis


def build_query_for_indicators(indicators):
    """Builds an ElasticSearch query for Yeti indicator patterns.

    Prepends and appends .* to the regex to be able to search within a field.

    Returns:
      The resulting ES query string.
    """
    query = []
    for domain in indicators:
        query.append('domain:/.*{0:s}.*/'.format(domain['pattern']))
    return ' OR '.join(query)


class YetiIndicators(interface.BaseSketchAnalyzer):
    """Index analyzer for Yeti threat intel indicators."""

    NAME = 'yetiindicators'
    DEPENDENCIES = frozenset(['domain'])

    def __init__(self, index_name, sketch_id):
        """Initialize the Index Analyzer.

        Args:
            index_name: Elasticsearch index name
        """
        super(YetiIndicators, self).__init__(index_name, sketch_id)
        self.intel = {}
        self.yeti_api_root = current_app.config.get('YETI_API_ROOT')
        self.yeti_api_key = current_app.config.get('YETI_API_KEY')
        self.yeti_indicator_labels = current_app.config.get(
            'YETI_INDICATOR_LABELS', [])

    def get_bad_domain_indicators(self, entity_id):
        """Retrieves a list of indicators associated to a given entity.

        Args:
          entity_id (str): STIX ID of the entity to get associated inticators
                from. (typically an Intrusion Set)

        Returns:
          A list of JSON objects describing a Yeti Indicator.
        """
        results = requests.post(
            self.yeti_api_root + '/entities/{0:s}/neighbors/'.format(entity_id),
            headers={'X-Yeti-API': self.yeti_api_key},
        )
        if results.status_code != 200:
            return []
        domain_indicators = []
        for neighbor in results.json().get('vertices', {}).values():
            if neighbor['type'] == 'x-regex' and \
                set(self.yeti_indicator_labels) <= set(neighbor['labels']):
                domain_indicators.append(neighbor)

        return domain_indicators

    def get_intrusion_sets(self):
        """Populates the intel attribute with data from Yeti.

        Retrieved intel consists of Intrusion sets and associated Indicators.
        """
        search_query = {'name': '', 'type': 'intrusion-set'}
        results = requests.post(
            self.yeti_api_root + '/entities/filter/',
            json={'name': '', 'type': 'intrusion-set'},
            headers={'X-Yeti-API': self.yeti_api_key},
        )
        if results.status_code != 200:
            return
        self.intel = {item['id']: item for item in results.json()}
        for _id in self.intel:
            self.intel[_id]['indicators'] = self.get_bad_domain_indicators(_id)

    def run(self):
        """Entry point for the analyzer.

        Returns:
            String with summary of the analyzer result
        """

        self.get_intrusion_sets()
        actors_found = []
        for intrusion_set in self.intel.values():
            if not intrusion_set['indicators']:
                continue

            found = False

            for indicator in intrusion_set['indicators']:
                query = build_query_for_indicators([indicator])

                events = self.event_stream(query_string=query,
                                           return_fields=[])

                name = intrusion_set['name']
                for event in events:
                    found = True
                    event.add_emojis([emojis.get_emoji('SKULL')])
                    event.add_tags([name])
                    event.commit()
                    event.add_comment(
                        'Indicator "{0:s}" found for actor "{1:s}"'.format(
                            indicator['name'], name))

            if found:
                actors_found.append(name)
                self.sketch.add_view(
                    'Domain activity for actor {0:s}'.format(name),
                    self.NAME,
                    query_string=query)

        if actors_found:
            return '{0:d} actors were found! [{1:s}]'.format(
                len(actors_found), ', '.join(actors_found))
        return 'No indicators were found in the timeline.'


manager.AnalysisManager.register_analyzer(YetiIndicators)
