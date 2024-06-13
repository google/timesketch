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
        self.misp_url = current_app.config.get("MISP_URL")
        self.misp_api_key = current_app.config.get("MISP_API_KEY")
        self.total_event_counter = 0
        self.result_dict = dict()
        self._query_string = kwargs.get("query_string")
        self._attr = kwargs.get("attr")
        self._timesketch_attr = kwargs.get("timesketch_attr")

    @staticmethod
    def get_kwargs():
        """Get kwargs for the analyzer.

        Returns:
            List of attributes to search for in Timesketch and query in MISP
        """

        to_query = [
            {
                "query_string": "md5_hash:*",
                "attr": "md5",
                "timesketch_attr": "md5_hash",
            },
            {
                "query_string": "sha1_hash:*",
                "attr": "sha1",
                "timesketch_attr": "sha1_hash",
            },
            {
                "query_string": "sha256_hash:*",
                "attr": "sha256",
                "timesketch_attr": "sha256_hash",
            },
            {
                "query_string": "filename:*",
                "attr": "filename",
                "timesketch_attr": "filename",
            },
        ]
        return to_query

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
            json={"returnFormat": "json", "value": value, "type": attr},
            headers={"Authorization": self.misp_api_key},
            verify=False,
        )

        if results.status_code != 200:
            msg_error = "Error with MISP query: Status code"
            logger.error("{} {}".format(msg_error, results.status_code))
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
        query_list = list()
        events_list = list()

        # Create a list to make only one query to misp
        for event in events:
            loc = event.source.get(timesketch_attr)
            if loc:
                events_list.append(event)  # Make a copy of event in a list
                if attr == "filename":
                    loc = ntpath.basename(loc)
                    if not loc:
                        _, loc = ntpath.split(event.source.get(timesketch_attr))

                if not loc in query_list:
                    query_list.append(loc)
                self.result_dict[f"{attr}:{loc}"] = []

        result = self.get_misp_attributes(query_list, attr)
        if result:
            create_a_view = True
            for event in events_list:  # Use list of event
                loc = event.source.get(timesketch_attr)
                if loc:
                    if attr == "filename":
                        loc = ntpath.basename(loc)
                        if not loc:
                            _, loc = ntpath.split(event.source.get(timesketch_attr))

                    loc_key = f"{attr}:{loc}"
                    for element in result:
                        if loc == element["value"]:
                            self.result_dict[loc_key].append(element)

                    # Mark event if there's a result
                    if self.result_dict[loc_key]:
                        self.total_event_counter += 1
                        self.mark_event(event, self.result_dict[loc_key], attr)

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

        self.query_misp(self._query_string, self._attr, self._timesketch_attr)

        return f"[{self._timesketch_attr}] MISP Match: {self.total_event_counter}"


manager.AnalysisManager.register_analyzer(MispAnalyzer)
