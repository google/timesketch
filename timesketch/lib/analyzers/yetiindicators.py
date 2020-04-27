"""Index analyzer plugin for Yeti indicators."""
from __future__ import unicode_literals

import re

from flask import current_app
import requests

from timesketch.lib.analyzers import interface
from timesketch.lib.analyzers import manager
from timesketch.lib import emojis


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

    def get_neighbors(self, entity_id):
        """Retrieves a list of neighbors associated to a given entity.

        Args:
          entity_id (str): STIX ID of the entity to get associated inticators
                from. (typically an Intrusion Set or an Incident)

        Returns:
          A list of JSON objects describing a Yeti object.
        """
        results = requests.post(
            self.yeti_api_root + '/entities/{0:s}/neighbors/'.format(entity_id),
            headers={'X-Yeti-API': self.yeti_api_key},
        )
        if results.status_code != 200:
            return []
        neighbors = []
        for neighbor in results.json().get('vertices', {}).values():
            neighbors.append(neighbor)

        return neighbors

    def get_indicators(self, indicator_type):
        """Populates the intel attribute with entities from Yeti."""
        results = requests.post(
            self.yeti_api_root + '/indicators/filter/',
            json={'name': '', 'type': indicator_type},
            headers={'X-Yeti-API': self.yeti_api_key},
        )
        if results.status_code != 200:
            return
        self.intel = {item['id']: item for item in results.json()}
        for item in results.json():
            item['compiled_regexp'] = re.compile(item['pattern'])
            self.intel[item['id']] = item

    def mark_event(self, indicator, event, neighbors):
        """Anotate an event with data from indicators and neighbors.

        Tags with skull emoji, adds a comment to the event.
        """
        event.add_emojis([emojis.get_emoji('SKULL')])
        event.add_tags([n['name'] for n in neighbors])
        event.commit()

        msg = 'Indicator match: "{0:s}" ({1:s})\n'.format(
            indicator['name'], indicator['id'])
        msg += 'Related entities: {0!s}'.format(
            [n['name'] for n in neighbors])
        event.add_comment(msg)
        event.commit()

    def run(self):
        """Entry point for the analyzer.

        Returns:
            String with summary of the analyzer result
        """
        if not self.yeti_api_root or not self.yeti_api_key:
            return 'No Yeti configuration settings found, aborting.'

        self.get_indicators('x-regex')

        entities_found = set()

        events = self.event_stream(query_string='*',
                                   return_fields=['message'])
        total_matches = 0
        matching_indicators = set()
        for event in events:
            for _id, indicator in self.intel.items():
                regexp = indicator['compiled_regexp']
                if regexp.search(event.source['message']):
                    total_matches += 1
                    matching_indicators.add(indicator['id'])
                    neighbors = self.get_neighbors(indicator['id'])
                    self.mark_event(indicator, event, neighbors)
                    for n in neighbors:
                        entities_found.add('{0:s}:{1:s}'.format(
                            n['name'], n['type']
                        ))

        if not total_matches:
            return 'No indicators were found in the timeline.'

        for entity in entities_found:
            name, _type = entity.split(':')
            self.sketch.add_view(
                'Indicator matches for {0:s} ({1:s})'.format(name, _type),
                self.NAME,
                query_string='tag:"{0:s}"'.format(name))
        return '{0:d} events matched {1:d} indicators. [{2:s}]'.format(
            total_matches, len(matching_indicators), ', '.join(entities_found))


manager.AnalysisManager.register_analyzer(YetiIndicators)
