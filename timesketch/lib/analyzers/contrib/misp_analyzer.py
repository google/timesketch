"""Index analyzer plugin for MISP."""

import logging
import ntpath
import requests

from flask import current_app
from timesketch.lib.analyzers import interface
from timesketch.lib.analyzers import manager


logger = logging.getLogger("timesketch.analyzers.misp")


class MispAnalyzer(interface.BaseAnalyzer):
    """Analyzer for MISP."""

    NAME = "misp_analyzer"
    DISPLAY_NAME = "MISP"
    DESCRIPTION = "Mark events using MISP"

    def __init__(self, index_name, sketch_id, timeline_id=None, **kwargs):
        """Initialize the Analyzer.

        Args:
            index_name: OpenSearch index name
            sketch_id: The ID of the sketch.
            timeline_id: The ID of the timeline.
        """
        super().__init__(index_name, sketch_id, timeline_id=timeline_id)
        self.misp_url = kwargs.get("misp_url")
        self.misp_api_key = kwargs.get("misp_api_key")
        self.total_event_counter = 0
        self.request_set = set()
        self.result_dict = dict()

    @staticmethod
    def get_kwargs():
        """Get kwargs for the analyzer.

        Returns:
            Info to connect to MISP.
        """

        misp_url = current_app.config.get("MISP_URL")
        misp_api_key = current_app.config.get("MISP_API_KEY")

        if not misp_api_key or not misp_url:
            logger.error("MISP conf not found")
            return []

        matcher_kwargs = [{"misp_url": misp_url, "misp_api_key": misp_api_key}]
        return matcher_kwargs

    def get_misp_attributes(self, value, attr):
        """Search event on MISP.

        Args:
            value:  Can be a valur for: sha1 - sha256 - md5 - filename.
            attr:  type of the value.

        Returns:
            List of matching MISP attributes.
        """
        results = requests.post(
            f"{self.misp_url}/attributes/restSearch/",
            data={"returnFormat": "json", "value": value, "type": attr},
            headers={"Authorization": self.misp_api_key},
            verify=False,
        )

        if results.status_code != 200:
            msg_error = "Error with MISP query: Status code"
            logger.error("{} {}".format(msg_error, results.status_code))
            # logger.error(f"{msg_error} {results.status_code}")
            return []
        result_loc = results.json()
        if "name" in result_loc:
            if "Authentication failed." in result_loc["name"]:
                logger.error("Bad API key. Please change it.")
                return []
        if not result_loc["response"]["Attribute"]:
            return []

        return result_loc["response"]["Attribute"]

    def mark_event(self, event, result, attr):
        """Annotate an event with data from MISP result.

        Add a comment to the event.

        Args:
            event:  The OpenSearch event object that contains type of value we search
                    for and needs to be tagged or to add an attribute.
            result:  Dictionary with results from MISP.
            attr:  type of the current value.
        """

        msg = "Event that match files:   "
        for misp_attr in result:
            info = misp_attr["Event"]["info"]
            id_event = misp_attr["Event"]["id"]
            msg += f'"Event info": "{info}"'
            msg += f'- "url": {self.misp_url}/events/view/{id_event} || '

        event.add_comment(msg)
        event.add_tags([f"MISP-{attr}"])
        event.commit()

    def query_misp(self, query, attr, timesketch_attr):
        """Get event from timesketch, request MISP and mark event.

        Args:
            query:  Search for all events that contains 'timesketch_attr' value.
            attr:  type of the current value.
            timesketch_attr:  type of the current value in timesketch format.
        """
        events = self.event_stream(query_string=query, return_fields=[timesketch_attr])
        create_a_view = False
        for event in events:
            loc = event.source.get(timesketch_attr)
            if loc:
                if attr == "filename":
                    loc = ntpath.basename(loc)
                    if not loc:
                        _, loc = ntpath.split(event.source.get(timesketch_attr))

                if not loc in self.request_set:
                    result = self.get_misp_attributes(loc, attr)
                    if result:
                        self.total_event_counter += 1
                        create_a_view = True
                        self.mark_event(event, result, attr)
                        self.result_dict[f"{attr}:{loc}"] = result
                    else:
                        self.result_dict[f"{attr}:{loc}"] = False
                    self.request_set.add(loc)
                elif self.result_dict[f"{attr}:{loc}"]:
                    self.total_event_counter += 1
                    self.mark_event(event, self.result_dict[f"{attr}:{loc}"], attr)

        if create_a_view:
            self.sketch.add_view(
                view_name="MISP known attribute",
                analyzer_name=self.NAME,
                query_string='tag:"MISP"',
            )

    def run(self):
        """Entry point for the analyzer.

        Returns:
            String with summary of the analyzer result
        """
        if not self.misp_url or not self.misp_api_key:
            return "No MISP configuration settings found, aborting."

        query_sha = "md5_hash:*"
        self.query_misp(query_sha, "md5", "md5_hash")

        query_sha = "sha1_hash:*"
        self.query_misp(query_sha, "sha1", "sha1_hash")

        query_sha = "sha256_hash:*"
        self.query_misp(query_sha, "sha256", "sha256_hash")

        query = "filename:*"
        self.query_misp(query, "filename", "filename")

        return f"MISP Match: {self.total_event_counter}"


manager.AnalysisManager.register_analyzer(MispAnalyzer)
