"""Index analyzer plugin for Hashlookup."""

import logging

from flask import current_app
import requests

from timesketch.lib.analyzers import interface
from timesketch.lib.analyzers import manager
from timesketch.lib import emojis


logger = logging.getLogger("timesketch.analyzers.hashlookup")


class HashlookupAnalyzer(interface.BaseAnalyzer):
    """Analyzer for Hashlookup."""

    NAME = "hashlookup_analyzer"
    DISPLAY_NAME = "Hashlookup"
    DESCRIPTION = "Mark events using Hashlookup"

    def __init__(self, index_name, sketch_id, timeline_id=None, **kwargs):
        """Initialize the Analyzer.

        Args:
            index_name: OpenSearch index name
            sketch_id: The ID of the sketch.
            timeline_id: The ID of the timeline.
        """
        super().__init__(index_name, sketch_id, timeline_id=timeline_id)
        self.hashlookup_url = kwargs.get("hashlookup_url")
        self.total_event_counter = 0
        self.request_set = set()

    @staticmethod
    def get_kwargs():
        """Get kwargs for the analyzer.

        Returns:
            Info to connect to Hashlookup.
        """

        hashlookup_url = current_app.config.get("HASHLOOKUP_URL")

        if not hashlookup_url:
            logger.error("Hashlookup conf not found")
            return []

        matcher_kwargs = [{"hashlookup_url": hashlookup_url}]
        return matcher_kwargs

    def get_hash_info(self, hash_value):
        """Search event on Hashlookup.

        Returns:
            JSON of Hashlookup's results
        """
        results = requests.get(f"{self.hashlookup_url}sha256/{hash_value}")

        if not "message" in results.json() and results.status_code != 200:
            logger.error("Error with Hashlookup url")
            return []
        if "message" in results.json():
            return []

        self.total_event_counter += 1

        return results.json()

    def mark_event(self, event, hash_value):
        """Annotate an event with data from Hashlookup

        Tags with validate emoji, adds a comment to the event.
        """

        event.add_comment(f"{self.hashlookup_url}sha256/{hash_value}")

        event.add_tags(["Hashlookup"])
        event.add_emojis([emojis.get_emoji("VALIDATE")])
        event.commit()

    def query_hashlookup(self, query, return_fields):
        """Get event from timesketch, request Hashlookup and mark event."""

        events = self.event_stream(query_string=query, return_fields=return_fields)
        create_a_view = False
        for event in events:
            hash_value = None
            for key in return_fields:
                if key in event.source.keys():
                    hash_value = event.source.get(key)
                    break
            if not hash_value:
                error_hash_counter += 1
                logger.warning(
                    "No matching field with a hash found in this event! "
                    "-- Event Source: %s",
                    str(event.source),
                )
                continue

            if len(hash_value) != 64:
                logger.warning(
                    "The extracted hash does not match the required "
                    "lenght (64) of a SHA256 hash. Skipping this "
                    "event! Hash: %s - Lenght: %d",
                    hash_value,
                    len(hash_value),
                )
                error_hash_counter += 1
                continue

            if not hash_value in self.request_set:
                result = self.get_hash_info(hash_value)
                if result:
                    create_a_view = True
                    self.mark_event(event, hash_value)
                self.request_set.add(hash_value)
            else:
                self.mark_event(event, hash_value)

        if create_a_view:
            self.sketch.add_view(
                view_name="Hashlookup",
                analyzer_name=self.NAME,
                query_string=('tag:"Hashlookup"'),
            )

    def run(self):
        """Entry point for the analyzer.

        Returns:
            String with summary of the analyzer result
        """
        if not self.hashlookup_url:
            return "No Hashlookup configuration settings found, aborting."

        # Note: Add fieldnames that contain sha256 values in your events.
        query = (
            "_exists_:hash_sha256 OR _exists_:sha256 OR _exists_:hash OR "
            "_exists_:sha256_hash"
        )

        # Note: Add fieldnames that contain sha256 values in your events.
        return_fields = ["hash_sha256", "hash", "sha256", "sha256_hash"]
        self.query_hashlookup(query, return_fields)

        return f"Hashlookup Matches: {self.total_event_counter}"


manager.AnalysisManager.register_analyzer(HashlookupAnalyzer)
