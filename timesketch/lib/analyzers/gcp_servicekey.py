"""Sketch analyzer plugin for GCP Service Key usage."""

from __future__ import unicode_literals

from timesketch.lib.analyzers import interface
from timesketch.lib.analyzers import manager


class GcpServiceKeySketchPlugin(interface.BaseAnalyzer):
    """Analyzer for GCP Service Key usage."""

    NAME = "gcp_servicekey"
    DISPLAY_NAME = "Google Compute Engine actions"
    DESCRIPTION = "Extract GCE actions from Stackdriver logs"

    def run(self):
        """Entry point for the analyzer.

        Returns:
            String with summary of the analyzer result
        """
        # TODO: update dftimewolf stackdriver module to produce more detailed
        # attributes
        query = "principalEmail:*gserviceaccount.com"
        return_fields = ["message", "methodName"]

        events = self.event_stream(query_string=query, return_fields=return_fields)

        simple_counter = 0

        for event in events:
            # Fields to analyze.
            method_name = event.source.get("methodName")

            if "CreateServiceAccount" in method_name:
                event.add_tags(["service-account-created"])

            if "compute.instances.insert" in method_name:
                event.add_tags(["gce-instance-created"])

            if "compute.firewalls.insert" in method_name:
                event.add_tags(["fw-rule-created"])

            if "compute.networks.insert" in method_name:
                event.add_tags(["network-created"])

            # Commit the event to the datastore.
            event.commit()
            simple_counter += 1

        # Create a saved view with our query.
        if simple_counter:
            self.sketch.add_view(
                view_name="GCP ServiceKey activity",
                analyzer_name=self.NAME,
                query_string=query,
            )

        return (
            "GCP ServiceKey analyzer completed with " "{0:d} service key marked"
        ).format(simple_counter)


manager.AnalysisManager.register_analyzer(GcpServiceKeySketchPlugin)
