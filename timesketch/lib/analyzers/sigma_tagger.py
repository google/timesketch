"""Index analyzer plugin for sigma."""

from __future__ import unicode_literals

import logging

from timesketch.lib.analyzers import interface
from timesketch.lib.analyzers import manager
import timesketch.lib.sigma_util as ts_sigma_lib

logger = logging.getLogger("timesketch.analyzers.sigma_tagger")


class SigmaPlugin(interface.BaseAnalyzer):
    """Analyzer for Sigma Rules."""

    NAME = "sigma"
    DISPLAY_NAME = "Sigma"
    DESCRIPTION = "Run pre-defined Sigma rules (only stable) and tag matching events"

    def __init__(self, index_name, sketch_id, timeline_id=None, **kwargs):
        """Initialize The Sigma Analyzer.

        Args:
            index_name: OpenSearch index name
            sketch_id: Sketch ID
            timeline_id: The ID of the timeline.
        """
        self.index_name = index_name
        self._rule = kwargs.get("rule")
        super().__init__(index_name, sketch_id, timeline_id=timeline_id)

    def run_sigma_rule(self, query, rule_title, tag_list=None, rule_id=None):
        """Runs a sigma rule and applies the tags from the rule.

        This method is only intended to be called if the Status of a rule is
        stable.

        A Sigma rule can have no tags, in that case this method will only add
        the rule title to the matching events.

        Args:
            query: OpenSearch search query for events to tag.
            rule_title: rule_name to apply to matching events.
            tag_list(optional): List of additional tags to be added
                to the event(s).
            rule_id(optional): rule_id to apply to matching events.

        Returns:
            int: number of events tagged.
        """
        if not tag_list:
            tag_list = []
        return_fields = []
        tagged_events_counter = 0
        events = self.event_stream(query_string=query, return_fields=return_fields)
        for event in events:
            ts_sigma_rules = event.source.get("ts_sigma_rule", [])
            ts_sigma_rules.append(rule_title)
            if rule_id:
                ts_sigma_rules.append(rule_id)
            event.add_attributes({"ts_sigma_rule": list(set(ts_sigma_rules))})
            ts_ttp = event.source.get("ts_ttp", [])
            special_tags = []
            for tag in tag_list:
                # Special handling for sigma tags that TS considers TTPs
                # https://car.mitre.org and https://attack.mitre.org
                if tag.startswith(("attack.", "car.")):
                    ts_ttp.append(tag)
                    special_tags.append(tag)
            # add the remaining tags as plain tags
            tags_to_add = list(set(tag_list) - set(special_tags))
            event.add_tags(tags_to_add)
            if len(ts_ttp) > 0:
                event.add_attributes({"ts_ttp": list(set(ts_ttp))})
            event.commit()
            tagged_events_counter += 1

        return tagged_events_counter

    def run(self):
        """Entry point for the analyzer.

        It will iterate over all Sigma rules of the Timesketch installation.

        If a rule has a status other than `stable` it is not considered in
        this analyzer.

        Returns:
            String with summary of the analyzer result.
        """

        sigma_rule_counter = 0
        tagged_events_counter = 0

        rule = self._rule
        if not rule:
            logger.error("No  Sigma rule given.")
            return "Unable to run, no rule given to the analyzer"
        rule_name = rule.get("title", "N/A")
        try:
            sigma_rule_counter += 1
            tagged_events_counter = self.run_sigma_rule(
                rule.get("search_query"),
                rule_name,
                tag_list=rule.get("tags"),
                rule_id=rule.get("id"),
            )
        except:  # pylint: disable=bare-except
            error_msg = "* {0:s} {1:s}".format(rule_name, rule.get("id"))
            logger.error(
                error_msg,
                exc_info=True,
            )
            return error_msg

        return f"{tagged_events_counter} events tagged for rule [{rule_name}] ({rule.get('id')})"  # pylint: disable=line-too-long

    @staticmethod
    def get_kwargs():
        """Returns an array of all rules of Timesketch.

        Returns:
            sigma_rules All Sigma rules
        """
        sigma_rules = []
        for rule in ts_sigma_lib.get_all_sigma_rules(parse_yaml=True):
            if rule.get("status") == "stable":
                sigma_rules.append({"rule": rule})

        return sigma_rules


class RulesSigmaPlugin(SigmaPlugin):
    """Sigma plugin to run rules."""

    NAME = "sigma"


manager.AnalysisManager.register_analyzer(RulesSigmaPlugin)
