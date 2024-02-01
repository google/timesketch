"""Sketch analyzer plugin for domain."""

from __future__ import unicode_literals

import collections
import logging
import numpy

from timesketch.lib.analyzers import interface
from timesketch.lib.analyzers import manager
from timesketch.lib.analyzers import utils


logger = logging.getLogger("timesketch.analyzers.domain")


class DomainSketchPlugin(interface.BaseAnalyzer):
    """Analyzer for Domain."""

    NAME = "domain"
    DISPLAY_NAME = "Domain"
    DESCRIPTION = (
        "Extract domain name from event, tag common and rare "
        "domains as well as mark known CDNs"
    )

    DEPENDENCIES = frozenset()

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

        return_fields = ["domain", "url"]

        events = self.event_stream("", query_dsl=query, return_fields=return_fields)

        domains = {}
        domain_counter = collections.Counter()
        tld_counter = collections.Counter()
        cdn_counter = collections.Counter()

        for event in events:
            domain = event.source.get("domain")

            if not domain:
                url = event.source.get("url")
                if not url:
                    continue
                domain = utils.get_domain_from_url(url)

            if not domain:
                continue

            domain_counter[domain] += 1
            domains.setdefault(domain, [])
            domains[domain].append(event)

            tld = ".".join(domain.split(".")[-2:])
            tld_counter[tld] += 1

        # Exit early if there are no domains in the data set to analyze.
        if not domain_counter:
            self.output.result_status = "SUCCESS"
            self.output.result_priority = "NOTE"
            self.output.result_summary = "No domains to analyze."
            return str(self.output)

        domain_count_array = numpy.array(list(domain_counter.values()))
        try:
            domain_20th_percentile = int(numpy.percentile(domain_count_array, 20))
        except IndexError:
            logger.warning("Unable to calculate the 20th percentile.")
            domain_20th_percentile = 0

        try:
            domain_85th_percentile = int(numpy.percentile(domain_count_array, 85))
        except IndexError:
            logger.warning("Unable to calculate the 85th percentile.")
            highest_count_domain = domain_counter.most_common(1)
            if highest_count_domain:
                _, highest_count = highest_count_domain[0]
                domain_85th_percentile = highest_count + 10
            else:
                domain_85th_percentile = 100

        common_domains = [
            x for x, y in domain_counter.most_common() if y >= domain_85th_percentile
        ]
        rare_domains = [
            x for x, y in domain_counter.most_common() if y <= domain_20th_percentile
        ]

        for domain, count in iter(domain_counter.items()):
            tags_to_add = []

            cdn_provider = utils.get_cdn_provider(domain)
            if cdn_provider:
                tags_to_add.append("known-cdn")
                cdn_counter[cdn_provider] += 1

            if domain in rare_domains:
                tags_to_add.append("rare-domain")

            for event in domains.get(domain, []):
                event.add_tags(tags_to_add)

                new_attributes = {"domain": domain, "domain_count": count}
                if domain in common_domains:
                    new_attributes["is_common_domain"] = True
                if cdn_provider:
                    new_attributes["cdn_provider"] = cdn_provider
                event.add_attributes(new_attributes)

                # Commit the event to the datastore.
                event.commit()

        self.output.result_status = "SUCCESS"
        self.output.result_priority = "NOTE"
        self.output.result_summary = (
            "{0:d} domains discovered ({1:d} TLDs) and {2:d} known "
            "CDN networks found."
        ).format(len(domains), len(tld_counter), len(cdn_counter))
        return str(self.output)


manager.AnalysisManager.register_analyzer(DomainSketchPlugin)
