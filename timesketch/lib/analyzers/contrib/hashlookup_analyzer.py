"""Index analyzer plugin for Hashlookup."""

from flask import current_app
import requests

from timesketch.lib.analyzers import interface
from timesketch.lib.analyzers import manager
from timesketch.lib import emojis

import logging

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
        self.cp = 0
        self.request_list = list()


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

        matcher_kwargs = [
            {"hashlookup_url": hashlookup_url}
        ]
        return matcher_kwargs


    def get_hash_info(self, hash):
        """Search event on Hashlookup.

        Returns:
            JSON of Hashlookup's results
        """
        results = requests.get(f"{self.hashlookup_url}sha256/{hash}")

        if results.status_code != 200:
            return []
        if 'message' in list(results.json().keys()):
            return []

        self.cp += 1
        
        return results.json()

    def mark_event(self, event, hash):
        """ Annotate an event with data from Hashlookup

        Tags with validate emoji, adds a comment to the event. 
        """
        self.sketch.add_view(
                view_name="Hashlookup",
                analyzer_name=self.NAME,
                query_string=('tag:"Hashlookup"'),
            )

        event.add_comment(f"{self.hashlookup_url}sha256/{hash}")

        event.add_tags(["Hashlookup"])
        event.add_emojis([emojis.get_emoji("VALIDATE")])
        event.commit()

    def query_hashlookup(self, query, hash_type):
        """
        """
        events = self.event_stream(query_string=query, return_fields=[hash_type])
        for event in events:
            loc = event.source.get(hash_type)

            if not loc in self.request_list:
                result = self.get_hash_info(loc)
                if result:
                    self.mark_event(event, loc)

            self.request_list.append(loc)

    def run(self):
        """Entry point for the analyzer.

        Returns:
            String with summary of the analyzer result
        """
        if not self.hashlookup_url:
            return "No Hashlookup configuration settings found, aborting."

        query_sha = 'sha256_hash:*'
        self.query_hashlookup(query_sha, 'sha256_hash')

        return (
            f"Hash Match: {self.cp}"
        )


manager.AnalysisManager.register_analyzer(HashlookupAnalyzer)
