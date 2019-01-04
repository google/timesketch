"""Sketch analyzer plugin for domain."""
from __future__ import unicode_literals

import collections

from timesketch.lib import emojis
from timesketch.lib.analyzers import interface
from timesketch.lib.analyzers import manager
from timesketch.lib.analyzers import utils


class DomainSketchPlugin(interface.BaseSketchAnalyzer):
    """Sketch analyzer for Domain."""

    NAME = 'domain'

    DEPENDENCIES = frozenset()

    def __init__(self, index_name, sketch_id):
        """Initialize The Sketch Analyzer.

        Args:
            index_name: Elasticsearch index name
            sketch_id: Sketch ID
        """
        self.index_name = index_name
        super(DomainSketchPlugin, self).__init__(index_name, sketch_id)

    def run(self):
        """Entry point for the analyzer.

        Returns:
            String with summary of the analyzer result
        """
        query = (
            '{"query": { "bool": { "should": [ '
            '{ "exists" : { "field" : "url" }}, '
            '{ "exists" : { "field" : "domain" }} ] } } }')

        return_fields = ['domain', 'url']

        events = self.event_stream(
            '', query_dsl=query, return_fields=return_fields)

        domains = {}
        domain_counter = collections.Counter()
        tld_counter = collections.Counter()

        for event in events:
            domain = event.source.get('domain')

            if not domain:
                url = event.source.get('url')
                if not url:
                    continue
                domain = utils.get_domain_from_url(url)
                event.add_attributes({'domain': domain})

            if not domain:
                continue

            domain_counter[domain] += 1
            domains.setdefault(domain, [])
            domains[domain].append(event)

            tld = '.'.join(domain.split('.')[-2:])
            tld_counter[tld] += 1

        satellite_emoji = emojis.get_emoji('SATELLITE')
        for domain, count in domain_counter.iteritems():
            emojis_to_add = [satellite_emoji]
            text = '{0:s} seen {1:d} times'.format(domain, count)

            for event in domains.get(domain, []):
                event.add_emojis(emojis_to_add)
                event.add_human_readable(text, self.NAME, append=False)
                event.add_attributes({'domain_count': count})

        return (
            '{0:d} domains discovered with {1:d} TLDs.').format(
                len(domains), len(tld_counter))


manager.AnalysisManager.register_analyzer(DomainSketchPlugin)
