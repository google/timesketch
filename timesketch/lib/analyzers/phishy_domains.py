"""Sketch analyzer plugin for domains."""

from __future__ import unicode_literals

import collections
import difflib

import logging

from flask import current_app
from datasketch.minhash import MinHash

from timesketch.lib import emojis
from timesketch.lib import similarity
from timesketch.lib.analyzers import interface
from timesketch.lib.analyzers import manager
from timesketch.lib.analyzers import utils


logger = logging.getLogger("timesketch.analyzers.phishy_domains")


class PhishyDomainsSketchPlugin(interface.BaseAnalyzer):
    """Analyzer for phishy domains."""

    NAME = "phishy_domains"
    DISPLAY_NAME = "Phishy domains"
    DESCRIPTION = (
        "Comparing domains visited against a list of the most "
        "frequently visited domains to find potentially phishy "
        "domains."
    )

    DEPENDENCIES = frozenset(["domain"])

    # This list contains entries from Alexa top 10 list (as of 2018-12-27).
    # They are used to create the base of a domain watch list. For custom
    # entries use DOMAIN_ANALYZER_WATCHED_DOMAINS in timesketch.conf.
    WATCHED_DOMAINS_BASE_LIST = [
        "google.com",
        "youtube.com",
        "facebook.com",
        "baidu.com",
        "wikipedia.org",
        "qq.com",
        "amazon.com",
        "yahoo.com",
        "taobao.com",
        "reddit.com",
    ]

    def __init__(self, index_name, sketch_id, timeline_id=None):
        """Initialize The Sketch Analyzer.

        Args:
            index_name: OpenSearch index name
            sketch_id: Sketch ID
            timeline_id: The ID of the timeline.
        """
        self.index_name = index_name
        super().__init__(index_name, sketch_id, timeline_id=timeline_id)

        self.domain_scoring_threshold = current_app.config.get(
            "DOMAIN_ANALYZER_WATCHED_DOMAINS_SCORE_THRESHOLD", 0.75
        )
        self.domain_scoring_exclude_domains = current_app.config.get(
            "DOMAIN_ANALYZER_EXCLUDE_DOMAINS", []
        )

        # TODO: remove that after a 6 months, this following check is to ensure
        # compatibility of the config file.
        if len(self.domain_scoring_exclude_domains) == 0:
            logger.warning(
                "Warning, DOMAIN_ANALYZER_WHITELISTED_DOMAINS has been "
                "deprecated. Please update timesketch.conf."
            )
            self.domain_scoring_exclude_domains = current_app.config.get(
                "DOMAIN_ANALYZER_WHITELISTED_DOMAINS", []
            )

    @staticmethod
    def _get_minhash_from_domain(domain):
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
        domain_items = domain.split(".")
        domain_part = ".".join(domain_items[:-1])

        minhash = MinHash(similarity.DEFAULT_PERMUTATIONS)
        for char in domain_part:
            minhash.update(char.encode("utf8"))

        return minhash

    def _get_similar_domains(self, domain, domain_dict):
        """Compare a domain to a list of domains and return similar domains.

        This function takes a domain and a dict object that contains
        as key domain names and value the calculated MinHash value for that
        domain as well as the domains depth (mbl.is is 2, foobar.evil.com would
        be 3). It will then strip www. if needed from the domain, and compare
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
        domain = utils.strip_www_from_domain(domain)

        similar = []
        if "." not in domain:
            return similar

        if domain in domain_dict:
            return similar

        if any(domain.endswith(".{0:s}".format(x)) for x in domain_dict):
            return similar

        # We want to get rid of the TLD extension of the domain.
        # This is only used in the substring match in case the Jaccard
        # distance is above the threshold.
        domain_items = domain.split(".")
        domain_depth = len(domain_items)
        domain_part = ".".join(domain_items[:-1])

        minhashes = {}
        for index in range(0, domain_depth - 1):
            minhashes[domain_depth - index] = self._get_minhash_from_domain(
                ".".join(domain_items[index:])
            )

        for watched_domain, watched_item in iter(domain_dict.items()):
            watched_hash = watched_item.get("hash")
            watched_depth = watched_item.get("depth")

            minhash = minhashes.get(watched_depth)
            if not minhash:
                # The supplied domains length does not match this watched
                # domain.
                continue
            score = watched_hash.jaccard(minhash)
            if score < self.domain_scoring_threshold:
                continue

            watched_domain_items = watched_domain.split(".")
            watched_domain_part = ".".join(watched_domain_items[:-1])

            # Check if there are also any overlapping strings.
            sequence = difflib.SequenceMatcher(None, domain_part, watched_domain_part)
            match = sequence.find_longest_match(
                0, len(domain_part), 0, len(watched_domain_part)
            )

            # We want to have at least half of the domain matching.
            # TODO: This can be improved, this is a value and part that
            # needs or can be tweaked. Perhaps move this to a config option
            # that is the min length of strings.
            match_size = min(
                int(len(domain_part) / 2), int(len(watched_domain_part) / 2)
            )
            if match.size < match_size:
                continue
            similar.append((watched_domain, score))

        return similar

    def run(self):
        """Entry point for the analyzer.

        Returns:
            String with summary of the analyzer result
        """
        query = (
            '{"query": { "bool": { "should": [ '
            '{ "exists" : { "field" : "url" }}, '
            '{ "exists" : { "field" : "domain" }} ] } } }'
        )

        return_fields = ["domain", "url", "message", "human_readable"]

        events = self.event_stream("", query_dsl=query, return_fields=return_fields)

        domains = {}
        domain_counter = collections.Counter()
        tld_counter = collections.Counter()

        for event in events:
            domain = event.source.get("domain")

            if not domain:
                continue

            domain_counter[domain] += 1
            domains.setdefault(domain, [])
            domains[domain].append(event)

            tld = utils.get_tld_from_domain(domain)
            tld_counter[tld] += 1

        if not domain_counter:
            return "No domains discovered, so no phishy domains."

        watched_domains_list = current_app.config.get(
            "DOMAIN_ANALYZER_WATCHED_DOMAINS", []
        )
        domain_threshold = current_app.config.get(
            "DOMAIN_ANALYZER_WATCHED_DOMAINS_THRESHOLD", 10
        )
        watched_domains_list.extend(
            [
                utils.strip_www_from_domain(x)
                for x, _ in domain_counter.most_common(domain_threshold)
            ]
        )
        watched_domains_list.extend(
            [x for x, _ in tld_counter.most_common(domain_threshold)]
        )
        watched_domains_list.extend(self.WATCHED_DOMAINS_BASE_LIST)
        watched_domains_list_temp = set(watched_domains_list)
        watched_domains_list = []
        for domain in watched_domains_list_temp:
            if domain in self.domain_scoring_exclude_domains:
                continue
            if any(domain.endswith(x) for x in self.domain_scoring_exclude_domains):
                continue

            if "." not in domain:
                continue
            watched_domains_list.append(domain)

        watched_domains = {}
        for domain in watched_domains_list:
            minhash = self._get_minhash_from_domain(domain)
            watched_domains[domain] = {"hash": minhash, "depth": len(domain.split("."))}

        similar_domain_counter = 0
        allowlist_encountered = False
        evil_emoji = emojis.get_emoji("SKULL_CROSSBONE")
        phishing_emoji = emojis.get_emoji("FISHING_POLE")
        for domain, _ in iter(domain_counter.items()):
            emojis_to_add = []
            tags_to_add = []
            text = None

            similar_domains = self._get_similar_domains(domain, watched_domains)

            if similar_domains:
                similar_domain_counter += 1
                emojis_to_add.append(evil_emoji)
                emojis_to_add.append(phishing_emoji)
                tags_to_add.append("phishy-domain")
                similar_text_list = [
                    "{0:s} [score: {1:.2f}]".format(phishy_domain, score)
                    for phishy_domain, score in similar_domains
                ]
                text = "Domain {0:s} is similar to {1:s}".format(
                    domain, ", ".join(similar_text_list)
                )
                if any(domain.endswith(x) for x in self.domain_scoring_exclude_domains):
                    tags_to_add.append("known-domain")
                    allowlist_encountered = True

            for event in domains.get(domain, []):
                event.add_emojis(emojis_to_add)
                event.add_tags(tags_to_add)
                if text:
                    event.add_human_readable(text, self.NAME, append=False)

                # Commit the event to the datastore.
                event.commit()

        if similar_domain_counter:
            self.sketch.add_view(
                view_name="Phishy Domains",
                analyzer_name=self.NAME,
                query_string='tag:"phishy-domain"',
            )

            if allowlist_encountered:
                self.sketch.add_view(
                    view_name="Phishy Domains, excl. known domains",
                    analyzer_name=self.NAME,
                    query_string=('tag:"phishy-domain" AND NOT tag:"known-domain"'),
                )

        return ("{0:d} potentially phishy domains discovered.").format(
            similar_domain_counter
        )


manager.AnalysisManager.register_analyzer(PhishyDomainsSketchPlugin)
