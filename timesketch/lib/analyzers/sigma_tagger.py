"""Index analyzer plugin for sigma."""
from __future__ import unicode_literals

import logging
import time
import elasticsearch

from timesketch.lib.analyzers import utils

from timesketch.lib.analyzers import interface
from timesketch.lib.analyzers import manager
import timesketch.lib.sigma_util as ts_sigma_lib


logger = logging.getLogger('timesketch.analyzers.sigma_tagger')


class SigmaPlugin(interface.BaseSketchAnalyzer):
    """Index analyzer for Sigma."""

    NAME = 'sigma'

    def run_sigma_rule(self, query, tag_name):
        """Runs a sigma rule and applies the appropriate tags.

        Args:
            query: elastic search query for events to tag.
            tag_name: tag to apply to matching events.

        Returns:
            int: number of events tagged.
        """
        return_fields = []
        tagged_events_counter = 0
        events = self.event_stream(
            query_string=query, return_fields=return_fields)
        for event in events:
            event.add_tags(['sigma_{0:s}'.format(tag_name)])
            event.commit()
            tagged_events_counter += 1
        return tagged_events_counter

    def run(self):
        """Entry point for the analyzer.

        Returns:
            String with summary of the analyzer result.
        """

        tags_applied = {}
        sigma_rule_counter = 0
        sigma_rules = ts_sigma_lib.get_all_sigma_rules()

        if sigma_rules is None:
            logger.error('No  Sigma rules found. Check SIGMA_RULES_FOLDERS')

        problem_string = []
        output_string = []

        for rule in sigma_rules:
            tags_applied[rule.get('file_name')] = 0
            try:
                sigma_rule_counter += 1
                tagged_events_counter = self.run_sigma_rule(
                    rule.get('es_query'), rule.get('file_name'))
                tags_applied[rule.get('file_name')] += tagged_events_counter
            except elasticsearch.TransportError as e:
                logger.error(
                    'Timeout executing search for {0:s}: '
                    '{1!s} waiting for 10 seconds'.format(
                        rule.get('file_name'), e), exc_info=True)
                # this is caused by to many ES queries in short time range
                # thus waiting for 10 seconds before sending the next one.
                time.sleep(10)
            # This except block is by purpose very broad as one bad rule could
            # otherwise stop the whole analyzer run
            # it might be an option to write the problematic rules to the output
            except: # pylint: disable=bare-except
                logger.error(
                    'Problem with rule in file {0:s}: '.format(
                        rule.get('file_name')), exc_info=True)
                problem_string.append('* {0:s}\n'.format(
                    rule.get('file_name')))
                continue

        total_tagged_events = sum(tags_applied.values())
        output_string.append('Applied {0:d} tags\n'.format(total_tagged_events))
        for tag_name, tagged_events_counter in tags_applied.items():
            output_string.append('* {0:s}: {1:d}\n'.format(
                tag_name, tagged_events_counter))

        if sigma_rule_counter > 0:
            view = self.sketch.add_view(
                view_name='Sigma Rule matches', analyzer_name=self.NAME,
                query_string='tag:"sigma*"')
            agg_params = {
                'field': 'tag',
                'limit': 20,
            }
            agg_obj = self.sketch.add_aggregation(
                name='Top 20 Sigma tags', agg_name='field_bucket',
                agg_params=agg_params, view_id=view.id, chart_type='hbarchart',
                description='Created by the Sigma analyzer')

            story = self.sketch.add_story('Sigma Rule hits')
            story.add_text(
                utils.SIGMA_STORY_HEADER, skip_if_exists=True)

            story.add_text(
                '## Sigma Analyzer.\n\nThe Sigma '
                'analyzer takes Events and matches them with Sigma rules.'
                'In this timeline the analyzer discovered {0:d} '
                'Sigma tags.\n\nThis is a summary of '
                'it\'s findings.'.format(sigma_rule_counter))
            story.add_text(
                'The top 20 most commonly discovered tags were:')
            story.add_aggregation(agg_obj)
            story.add_text(
                'And an overview of all the discovered search terms:')
            story.add_view(view)

        output_string.append('\n Problematic rules:')
        output_string.append(''.join(problem_string))

        return output_string


class RulesSigmaPlugin(SigmaPlugin):
    """Sigma plugin to run rules."""

    NAME = 'sigma'

manager.AnalysisManager.register_analyzer(RulesSigmaPlugin)
