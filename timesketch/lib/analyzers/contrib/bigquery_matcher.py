"""Index analyzer plugin for matching against data in BigQuery tables."""

import itertools
import logging

from timesketch.lib import emojis
from timesketch.lib.analyzers import interface
from timesketch.lib.analyzers import manager

has_required_deps = True
try:
    from google.cloud import bigquery
    from google.auth import exceptions as google_auth_exceptions
except ImportError:
    has_required_deps = False

logger = logging.getLogger("timesketch.analyzers.bigquery_matcher")


class BigQueryMatcherPlugin(interface.BaseAnalyzer):
    """Analyzer for matching events to BigQuery data."""

    NAME = "bigquery_matcher"
    DISPLAY_NAME = "BigQuery matcher"
    DESCRIPTION = "Match pre-defined event fields to data in BigQuery tables"

    _BQ_BATCH_SIZE = 10000  # Number of entries per BQ query

    def __init__(self, index_name, sketch_id, timeline_id=None, **kwargs):
        """Initialize the BQ Matcher Analyzer.

        Args:
            index_name: OpenSearch index name
            sketch_id: Sketch ID
            timeline_id: The ID of the timeline
        """
        self.index_name = index_name
        self._matcher_name = kwargs.get("matcher_name")
        self._matcher_config = kwargs.get("matcher_config")
        super().__init__(index_name, sketch_id, timeline_id=timeline_id)

    @staticmethod
    def get_kwargs():
        """Get kwargs for the analyzer.

        Returns:
            List of matchers.
        """
        bq_config = interface.get_yaml_config("bigquery_matcher.yaml")
        if not bq_config:
            logger.error("BigQuery Matcher could not load configuration file.")
            return []

        matcher_kwargs = [
            {"matcher_name": matcher_name, "matcher_config": matcher_config}
            for matcher_name, matcher_config in bq_config.items()
        ]
        return matcher_kwargs

    def run(self):
        """Entry point for the analyzer.

        Returns:
            String with summary of the analyzer result.
        """
        if self._matcher_name is None or self._matcher_config is None:
            return "Configuration file is not valid for this analyzer."
        return self.matcher(self._matcher_name, self._matcher_config)

    def bigquery_match(self, bq_client, bq_query, event_field_name, values):
        """Run a BigQuery query for rows with matching event_field_name values.

        Returns:
            BigQuery query job.
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ArrayQueryParameter(event_field_name, "STRING", values),
            ]
        )
        return bq_client.query(bq_query, job_config=job_config)

    def matcher(self, name, config):
        """Entry point for the analyzer.

        Returns:
            String with summary of the analyzer result.
        """
        event_field_name = config.get("event_field_name")
        bq_query = config.get("bq_query")
        bq_project = config.get("bq_project")
        tags = config.get("tags")
        emoji_names = config.get("emojis")
        emojis_to_add = [emojis.get_emoji(x) for x in emoji_names]

        es_query = (
            '{"query": { "bool": { "should": [ '
            '{ "exists" : { "field" : "' + event_field_name + '" }} ] } } }'
        )
        events_stream = self.event_stream(
            query_dsl=es_query,
            return_fields=[event_field_name],
        )

        events = {}
        for event in events_stream:
            field = event.source.get(event_field_name)
            events.setdefault(field, []).append(event)

        try:
            bq_client = bigquery.Client(project=bq_project)
        except google_auth_exceptions.DefaultCredentialsError as exception:
            return "Could not authenticate to BigQuery: {0!s}".format(exception)

        num_matches = 0
        for i in range(0, len(events), self._BQ_BATCH_SIZE):
            batch = list(itertools.islice(events, i, i + self._BQ_BATCH_SIZE))
            query_job = self.bigquery_match(
                bq_client, bq_query, event_field_name, batch
            )
            for row in query_job:
                for event in events[row[0]]:
                    event.add_tags(tags)
                    event.add_emojis(emojis_to_add)
                    event.commit()
                    num_matches += 1
        return ("{0:d} events found for matcher [{1:s}]").format(num_matches, name)


if has_required_deps:
    manager.AnalysisManager.register_analyzer(BigQueryMatcherPlugin)
