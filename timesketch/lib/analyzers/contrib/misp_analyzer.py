"""Index analyzer plugin for MISP."""

import ntpath

from flask import current_app
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

from timesketch.lib.analyzers import interface
from timesketch.lib.analyzers import manager

import logging

logger = logging.getLogger("timesketch.analyzers.misp")


class MispAnalyzer(interface.BaseAnalyzer):
    """Analyzer for MISP."""

    NAME = "misp_analyzer"
    DISPLAY_NAME = "MISP"
    DESCRIPTION = "Mark events using MISP"

    # DEPENDENCIES = frozenset(["domain"])

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
        self.cp = 0
        self.request_list = list()

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

    def get_attr(self, event, attr):
        """Search event on MISP.
            
        Returns:
            List of matching MISP attibutes.
        """
        results = requests.post(
            f"{self.misp_url}/attributes/restSearch/",
            data={"returnFormat": "json", "value": event, "type": attr},
            headers={"Authorization": self.misp_api_key},
            verify=False,
        )

        if results.status_code != 200:
            return []
        if not results.json()["response"]["Attribute"]:
            return []

        self.cp += 1

        return results.json()["response"]["Attribute"]

    def mark_event(self, event, result, attr):
        """Anotate an event with data from MISP result.
        
        Add a comment to the event.
        """
        self.sketch.add_view(
            view_name="MISP known attribute",
            analyzer_name=self.NAME,
            query_string=('tag:"MISP"'),
        )

        msg = "Event that match files:   "
        for misp_attr in result:
            msg += f"\"Event info\": \"{misp_attr['Event']['info']}\" - \"url\": {self.misp_url + '/events/view/' + misp_attr['Event']['id']}  || "

        event.add_comment(msg)
        event.add_tags([f"MISP-{attr}"])
        event.commit()

    def query_misp(self, query, attr, timesketch_attr):
        """ Get event from timesketch, request MISP and mark event. """
        events = self.event_stream(query_string=query, return_fields=[timesketch_attr])
        for event in events:
            loc = event.source.get(timesketch_attr)
            if attr == 'filename':
                loc = ntpath.basename(loc)
                if not loc:
                    head, loc = ntpath.split(event.source.get(timesketch_attr))

            if not loc in self.request_list:
                result = self.get_attr(loc, attr)
                if result:
                    self.mark_event(event, result, attr)

            self.request_list.append(loc)

    def run(self):
        """Entry point for the analyzer.

        Returns:
            String with summary of the analyzer result
        """
        if not self.misp_url or not self.misp_api_key:
            return "No MISP configuration settings found, aborting."

        query_sha = 'md5_hash:*'
        self.query_misp(query_sha, 'md5', 'md5_hash')

        query_sha = 'sha1_hash:*'
        self.query_misp(query_sha, 'sha1', 'sha1_hash')

        query_sha = 'sha256_hash:*'
        self.query_misp(query_sha, 'sha256', 'sha256_hash')

        query = 'filename:*'
        self.query_misp(query, 'filename', 'filename')

        return f"MISP Match: {self.cp}"


manager.AnalysisManager.register_analyzer(MispAnalyzer)
