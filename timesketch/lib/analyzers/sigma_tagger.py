"""Index analyzer plugin for sigma."""
from __future__ import unicode_literals

import logging

from timesketch.lib.analyzers import utils

from timesketch.lib.analyzers import interface
from timesketch.lib.analyzers import manager
import timesketch.lib.sigma_util as ts_sigma_lib
from timesketch.models.sigma import SigmaRule


logger = logging.getLogger("timesketch.analyzers.sigma_tagger")


class SigmaPlugin(interface.BaseAnalyzer):
    """Analyzer for Sigma Rules."""

    NAME = "sigma"
    DISPLAY_NAME = "Sigma"
    DESCRIPTION = "Run pre-defined Sigma rules and tag matching events"

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

    def run_sigma_rule(self, query, rule_name, tag_list=None):
        """Runs a sigma rule and applies the appropriate tags.

        This method is only intended to be called if the Status of a rule is
        stable

        Args:
            query: OpenSearch search query for events to tag.
            rule_name: rule_name to apply to matching events.
            tag_list: a list of additional tags to be added to the event(s)

        Returns:
            int: number of events tagged.
        """
        if not tag_list:
            tag_list = []
        return_fields = []
        tagged_events_counter = 0
        events = self.event_stream(
            query_string=query, return_fields=return_fields
        )
        for event in events:
            ts_sigma_rules = event.source.get("ts_sigma_rule", [])
            ts_sigma_rules.append(rule_name)
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

        tags_applied = {}
        sigma_rule_counter = 0
        tagged_events_counter = 0

        rule = self._rule
        if not rule:
            logger.error("No  Sigma rule given.")
            return "Unable to run, no rule given to the analyzer"
        rule_name = rule.get("title", "N/A")
        problem_strings = []
        output_strings = []

        if rule.get("status", "experimental") != "stable":
            problem_strings.append(
                "{0:s} ignored because status not stable".format(rule_name)
            )
        else:
            tags_applied[rule.get("title")] = 0
            try:
                sigma_rule_counter += 1
                tagged_events_counter = self.run_sigma_rule(
                    rule.get("search_query"),
                    rule.get("title"),
                    tag_list=rule.get("tags"),
                )
                tags_applied[rule.get("title")] += tagged_events_counter
            except:  # pylint: disable=bare-except
                error_msg = "* {0:s} {1:s}".format(
                    rule.get("title"), rule.get("id")
                )
                logger.error(
                    error_msg,
                    exc_info=True,
                )
                problem_strings.append(error_msg)

            output_strings.append(
                f"{tagged_events_counter} events tagged for rule [{rule_name}]"
            )

        if len(problem_strings) > 0:
            output_strings.append("Problematic rule:")
            output_strings.extend(problem_strings)

        return "\n".join(output_strings)

    def add_sigma_match_view(self, sigma_rule_counter):
        """Adds a view with the top 20 matching rules.

        Args:
            sigma_rule_counter number of matching rules

        """
        view = self.sketch.add_view(
            view_name="Sigma Rule matches",
            analyzer_name=self.NAME,
            query_string='tag:"sigma*"',
        )
        agg_params = {
            "field": "tag",
            "limit": 20,
            "index": [self.timeline_id],
        }
        agg_obj = self.sketch.add_aggregation(
            name="Top 20 Sigma tags",
            agg_name="field_bucket",
            agg_params=agg_params,
            view_id=view.id,
            chart_type="hbarchart",
            description="Created by the Sigma analyzer",
        )

        story = self.sketch.add_story("Sigma Rule hits")
        story.add_text(utils.SIGMA_STORY_HEADER, skip_if_exists=True)

        story.add_text(
            "## Sigma Analyzer.\n\nThe Sigma "
            "analyzer takes Events and matches them with Sigma rules."
            "In this timeline the analyzer discovered {0:d} "
            "Sigma tags.\n\nThis is a summary of "
            "it's findings.".format(sigma_rule_counter)
        )
        story.add_text("The top 20 most commonly discovered tags were:")
        story.add_aggregation(agg_obj)
        story.add_text("And an overview of all the discovered search terms:")
        story.add_view(view)

    @staticmethod
    def get_kwargs():
        """Returns an array of all rules of Timesketch.

        Returns:
            sigma_rules All Sigma rules
        """
        sigma_rules = []
        for rule in ts_sigma_lib.get_all_sigma_rules():
            sigma_rules.append({"rule": rule})

        return sigma_rules


class RulesSigmaPlugin(SigmaPlugin):
    """Sigma plugin to run rules."""

    NAME = "sigma"


manager.AnalysisManager.register_analyzer(RulesSigmaPlugin)
