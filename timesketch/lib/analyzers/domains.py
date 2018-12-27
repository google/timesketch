"""Sketch analyzer plugin for domains."""
from __future__ import unicode_literals

import collections

#from flask import current_app

try:
    from urlparse import urlparse
except ImportError:
    from urllib import parse as urlparse  # pylint: disable=no-name-in-module


from timesketch.lib import emojis
from timesketch.lib import similarity
from timesketch.lib.analyzers import interface
from timesketch.lib.analyzers import manager


class DomainsSketchPlugin(interface.BaseSketchAnalyzer):
    """Sketch analyzer for Domains."""

    NAME = 'domains'

    # Defines how deep into the top level domains the analyzer
    # should look for similarities.
    TOP_DOMAIN_THRESHOLD = 5

    # The minimum jaccard distance for a domain to be considered
    # similar to the top domains.
    TOP_DOMAIN_SCORE_THRESHOLD = 0.33

    # A list of domains to include in the top domain list, by default
    # it's taken from the Alexa top 10 list (as of 2018-12-27).
    TOP_DOMAIN_BASE_LIST = [
        'google.com', 'youtube.com', 'facebook.com', 'baidu.com',
        'wikipedia.org', 'qq.com', 'amazon.com', 'yahoo.com', 'taobao.com',
        'reddit.com']

    def __init__(self, index_name, sketch_id):
        """Initialize The Sketch Analyzer.

        Args:
            index_name: Elasticsearch index name
            sketch_id: Sketch ID
        """
        self.index_name = index_name
        super(DomainsSketchPlugin, self).__init__(index_name, sketch_id)

    def _get_tld(self, domain):
        """Get the top level domain from a domain string.

        Args:
          domain: string with a full domain, eg. www.google.com

        Returns:
          string: TLD or a top level domain extracted from the domain,
              eg: google.com
        """
        return '.'.join(domain.split('.')[-2:])

    def run(self):
        """Entry point for the analyzer.

        Returns:
            String with summary of the analyzer result
        """
        query = (
            '{"query": { "bool": { "should": [ '
            '{ "exists" : { "field" : "url" }}, '
            '{ "exists" : { "field" : "domain" }} ] } } }')

        return_fields = ['domain', 'url', 'message', 'human_readable']

        # Generator of events based on your query.
        events = self.event_stream(
            '', query_dsl=query, return_fields=return_fields)

        domains = {}
        domain_counter = collections.Counter()
        tld_counter = collections.Counter()

        # TODO: Add analyzer logic here.
        # Methods available to use for sketch analyzers:
        # sketch.get_all_indices()
        # sketch.add_view(name, query_string, query_filter={})
        # event.add_attributes({'foo': 'bar'})
        # event.add_tags(['tag_name'])
        # event_add_label('label')
        # event.add_star()
        # event.add_comment('comment')
        for event in events:
            domain = event.source.get('domain')

            if not domain:
                url = event.source.get('url')
                if not url:
                    continue
                domain_parsed = urlparse(url)
                domain_full = domain_parsed.netloc
                domain, _, _ = domain_full.partition(':')
                event.add_attributes({'domain': domain})

            if not domain:
                continue

            domain_counter[domain] += 1
            domains.setdefault(domain, [])
            domains[domain].append(event)

            # Extract the top level domain.
            tld = self._get_tld(domain)
            tld_counter[tld] += 1

        minhashes = {}
        most_common_tlds = [
            x for x, _ in tld_counter.most_common(self.TOP_DOMAIN_THRESHOLD)]

        # THROW AWAY FOR EXPERIMENTAL PURPOSES!!!
        most_common_tlds.append('greendale.xyz')
        top_domain_list = list(
            set().union(self.TOP_DOMAIN_BASE_LIST, most_common_tlds))
        # THROW AWAY FOR EXPERIMENTAL PURPOSES!!!
        print 'Domains inspected: {0:s}'.format(', '.join(top_domain_list))
        top_domains = {}
        potentially_evil_tlds = {}

        for domain in top_domain_list:
            minhash = similarity.minhash_from_text(
                domain, similarity.DEFAULT_PERMUTATIONS, ['\.', '/'])
            top_domains[domain] = minhash

        for domain in tld_counter.iterkeys():
            if domain in top_domain_list:
                continue
            minhash = similarity.minhash_from_text(
                domain, similarity.DEFAULT_PERMUTATIONS, ['\.', '/'])
            # THROW AWAY FOR EXPERIMENTAL PURPOSES!!!
            if 'greendale' in domain or 'grendale' in domain:
                print 'inspecting: {}'.format(domain)

            for top_domain, top_hash in top_domains.iteritems():
                score = top_hash.jaccard(minhash)
                # THROW AWAY FOR EXPERIMENTAL PURPOSES!!!
                if 'greendale' in top_domain and 'grendale' in domain:
                    print 'Inspecting {} and {} = {}'.format(domain, top_domain, score)
                if score > self.TOP_DOMAIN_SCORE_THRESHOLD:
                    # THROW AWAY FOR EXPERIMENTAL PURPOSES!!!
                    print 'BINGO: domain {0:s} similar to {1:s} with score {2}'.format(domain, top_domain, score)
                    potentially_evil_tlds.setdefault(domain, [])
                    potentially_evil_tlds[domain].append(top_domain)

        for domain, count in domain_counter.iteritems():
            if count == 1:
                text = 'Domain: only occurance of domain'
            else:
                text = 'Domain seen: {0:d} times'.format(count)

            tld = self._get_tld(domain)
            if tld in potentially_evil_tlds:
                evil = True
            else:
                evil = False

            for event in domains.get(domain, []):
                emojis_to_add = [emojis.SATELLITE]

                if evil:
                    emojis_to_add.append(emojis.SKULL_CROSSBONE)
                    added_text = 'domain similar to: {0:s}'.format(', '.join(
                        potentially_evil_tlds[tld]))
                    text = '{0:s} - {1:s}'.format(text, added_text)

                event.add_emojis(emojis_to_add)
                event.add_human_readable(text, self.NAME, append=False)
                event.add_attributes({'domain_count': count})

        # THROW AWAY FOR EXPERIMENTAL PURPOSES!!!
        print 'Done with minhashes and count'

        return (
            'Domain extraction ({0:d} domains discovered with {1:d} TLDs) '
            'and {2:d} potentially evil domains discovered.').format(
                len(domains), len(tld_counter), len(potentially_evil_tlds))


manager.AnalysisManager.register_analyzer(DomainsSketchPlugin)
