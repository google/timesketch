"""Sketch analyzer plugin for domains."""
from __future__ import unicode_literals

import collections
import difflib

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

    # This list contains entries from Alexa top 10 list (as of 2018-12-27).
    # They are used to create the base of a domain watch list. For custom
    # entries use DOMAIN_ANALYZER_WATCHED_DOMAINS in timesketch.conf.
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

        self.domain_scoring_threshold = current_app.config[
            'DOMAIN_ANALYZER_WATCHED_DOMAINS_SCORE_THRESHOLD']
        self.domain_scoring_whitelist = current_app.config[
            'DOMAIN_ANALYZER_WHITELISTED_DOMAINS']

    def _get_minhash_from_domain(self, domain):
        """Get the Minhash value from a domain name.

        This function takes a domain, removes the TLD extension
        from it and then creates a MinHash object from every
        remaining character in the domain.

        If a domain starts with www., it will be stripped of the
        domain before the Minhash is calculated.

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

    def _get_similar_domains(self, domain, domain_dict):
        """Compare a domain to a list of domains and return similar domains.

        This function takes a domain and a dict object that contains
        as key domain names and value the calculated MinHash value for that
        domain. It will then strip www. if needed from the domain, and compare
        the Jaccard distance between all domains in the dict and the supplied
        domain (removing the TLD extension from all domains).

        If the Jaccard distance between the supplied domain and one or more of
        the domains in the domain dict is higher than the configured threshold
        the domain is further tested to see if there are overlapping substrings
        between the two domains. If there is a common substring that is longer
        than half the domain name and the Jaccard distance is above the
        threshold the domain is considered to be similar.

        Args:
            domain: string with a full domain, eg. www.google.com
            domain_dict: dict with domain names (keys) and MinHash objects
                (values) for all domains to compare against.

        Returns:
            a list of tuples (score, similar_domain_name) with the names of
            the similar domains as well as the Jaccard distance between
            the supplied domain and the matching one.
        """
        domain = self._strip_www(domain)

        similar = []
        if not '.' in domain:
            return similar

        if domain in domain_dict:
            return similar

        if any(domain.endswith(x) for x in domain_dict):
            return similar

        minhash = self._get_minhash_from_domain(domain)

        # We want to get rid of the TLD extension of the domain.
        # This is only used in the substring match in case the Jaccard
        # distance is above the threshold.
        domain_items = domain.split('.')
        domain_part = '.'.join(domain_items[:-1])

        for watched_domain, watched_hash in domain_dict.iteritems():
            score = watched_hash.jaccard(minhash)
            if score < self.domain_scoring_threshold:
                continue

            watched_domain_items = watched_domain.split('.')
            watched_domain_part = '.'.join(watched_domain_items[:-1])

            # Check if there are also any overlapping strings.
            sequence = difflib.SequenceMatcher(
                None, domain_part, watched_domain_part)
            match = sequence.find_longest_match(
                0, len(domain_part), 0, len(watched_domain_part))

            # We want to have at least half of the domain matching.
            match_size = min(
                int(len(domain_part)/2), int(len(watched_domain_part)/2))
            if match.size < match_size:
                continue
            similar.append((watched_domain, score))

        return similar

    def _get_tld(self, domain):
        """Get the top level domain from a domain string.

        Args:
          domain: string with a full domain, eg. www.google.com

        Returns:
          string: TLD or a top level domain extracted from the domain,
              eg: google.com
        """
        return '.'.join(domain.split('.')[-2:])

    def _strip_www(self, domain):
        """Strip www. from beginning of domain names."""
        if domain.startswith('www.'):
            return domain[4:]
        return domain

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
        domain_threshold = current_app.config[
            'DOMAIN_ANALYZER_WATCHED_DOMAINS_THRESHOLD']
        watched_domains_list.extend([
            self._strip_www(x) for x, _ in domain_counter.most_common(
                domain_threshold)])
        watched_domains_list.extend([
            x for x, _ in tld_counter.most_common(domain_threshold)])
        watched_domains_list.extend(self.WATCHED_DOMAINS_BASE_LIST)
        watched_domains_list_temp = set(watched_domains_list)
        watched_domains_list = []
        for domain in watched_domains_list_temp:
            if domain in self.domain_scoring_whitelist:
                continue
            if any(domain.endswith(x) for x in self.domain_scoring_whitelist):
                continue

            if not '.' in domain:
                continue
            watched_domains_list.append(domain)

        watched_domains = {}
        for domain in watched_domains_list:
            minhash = self._get_minhash_from_domain(domain)
            watched_domains[domain] = minhash

        similar_domain_counter = 0
        for domain, count in domain_counter.iteritems():
            emojis_to_add = [emojis.SATELLITE]
            tags_to_add = []

            if count == 1:
                text = 'Domain: only occurance of domain'
            else:
                text = 'Domain seen: {0:d} times'.format(count)

            similar_domains = self._get_similar_domains(
                domain, watched_domains)

            if similar_domains:
                similar_domain_counter += 1
                emojis_to_add.append(emojis.SKULL_CROSSBONE)
                tags_to_add.append('phishy_domain')
                similar_text_list = ['{0:s} [{1:.2f}]'.format(
                    phishy_domain,
                    score) for phishy_domain, score in similar_domains]
                added_text = 'domain {0:s} similar to: {1:s}'.format(
                    domain, ', '.join(similar_text_list))
                text = '{0:s} - {1:s}'.format(added_text, text)
                if any(domain.endswith(
                        x) for x in self.domain_scoring_whitelist):
                    tags_to_add.append('known_network')

            for event in domains.get(domain, []):
                event.add_emojis(emojis_to_add)
                event.add_tags(tags_to_add)
                event.add_human_readable(text, self.NAME, append=False)
                event.add_attributes({'domain_count': count})

        if similar_domain_counter:
            self.sketch.add_view(
                'Phishy Domains', query_string='tag:"phishy_domain"')

        return (
            'Domain extraction ({0:d} domains discovered with {1:d} TLDs) '
            'and {2:d} potentially evil domains discovered.').format(
                len(domains), len(tld_counter), similar_domain_counter)


manager.AnalysisManager.register_analyzer(DomainsSketchPlugin)
