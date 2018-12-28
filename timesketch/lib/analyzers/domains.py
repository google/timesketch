"""Sketch analyzer plugin for domains."""
from __future__ import unicode_literals

import collections

from flask import current_app

try:
    from urlparse import urlparse
except ImportError:
    from urllib import parse as urlparse  # pylint: disable=no-name-in-module

from datasketch.minhash import MinHash

from timesketch.lib import emojis
from timesketch.lib import similarity
from timesketch.lib.analyzers import interface
from timesketch.lib.analyzers import manager


class DomainsSketchPlugin(interface.BaseSketchAnalyzer):
    """Sketch analyzer for domains."""

    NAME = 'domains'

    # Defines how deep into the most frequently visited top
    # level domains the analyzer should include in its watch list.
    WATCHED_DOMAINS_THRESHOLD = 5

    # The minimum Jaccard distance for a domain to be considered
    # similar to the domains in the watch list.
    WATCHED_DOMAINS_SCORE_THRESHOLD = 0.75

    # A list of domains to include in the watched domain list.
    # There are two ways to manually add domains, either adding
    # them to this list or the timesketch.conf file. By default
    # the list includes domains from the Alexa top 10 list (as of 2018-12-27).
    WATCHED_DOMAINS_BASE_LIST = [
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

    def _get_minhash_from_domain(self, domain):
        """Get the Minhash value from a domain name.

        This function takes a domain, removes the TLD extension
        from it and then creates a MinHash object from every
        remaining character in the domain.

        Args:
          domain: string with a full domain, eg. www.google.com

        Returns:
            A minhash (instance of datasketch.minhash.MinHash)
        """
        domain_items = domain.split('.')
        domain_part = '.'.join(domain_items[:-1])

        minhash = MinHash(similarity.DEFAULT_PERMUTATIONS)
        for char in domain_part:
            minhash.update(char.encode('utf8'))

        return minhash

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

            tld = self._get_tld(domain)
            tld_counter[tld] += 1

        watched_domains_list = current_app.config[
            'DOMAIN_ANALYZER_WATCHED_DOMAINS']
        watched_domains_list.extend([
            x for x, _ in tld_counter.most_common(self.WATCHED_DOMAINS_THRESHOLD)])
        watched_domains_list.extend(self.WATCHED_DOMAINS_BASE_LIST)
        watched_domains_list = list(set(watched_domains_list))

        # THROW AWAY FOR EXPERIMENTAL PURPOSES!!!
        print 'Domains to be inspected: {0:s}'.format(', '.join(watched_domains_list))

        watched_domains = {}
        potentially_evil_tlds = {}

        for domain in watched_domains_list:
            minhash = self._get_minhash_from_domain(domain)
            watched_domains[domain] = minhash

        for domain in tld_counter.iterkeys():
            if domain in watched_domains_list:
                continue
            minhash = self._get_minhash_from_domain(domain)

            # THROW AWAY FOR EXPERIMENTAL PURPOSES!!!
            if 'greendale' in domain or 'grendale' in domain:
                print 'inspecting: {}'.format(domain)

            for watched_domain, watched_hash in watched_domains.iteritems():
                score = watched_hash.jaccard(minhash)
                if score > self.WATCHED_DOMAINS_SCORE_THRESHOLD:
                    # THROW AWAY FOR EXPERIMENTAL PURPOSES!!!
                    print 'BINGO: domain {0:s} similar to {1:s} with score {2}'.format(domain, watched_domain, score)
                    potentially_evil_tlds.setdefault(domain, [])
                    potentially_evil_tlds[domain].append(watched_domain)

        for domain, count in domain_counter.iteritems():
            if count == 1:
                text = 'Domain: only occurance of domain'
            else:
                text = 'Domain seen: {0:d} times'.format(count)

            emojis_to_add = [emojis.SATELLITE]

            tld = self._get_tld(domain)
            if tld in potentially_evil_tlds:
                emojis_to_add.append(emojis.SKULL_CROSSBONE)
                added_text = 'domain similar to: {0:s}'.format(', '.join(
                    potentially_evil_tlds[tld]))
                text = '{0:s} - {1:s}'.format(text, added_text)

            for event in domains.get(domain, []):
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
