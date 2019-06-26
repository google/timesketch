"""Sketch analyzer plugin for GCP Service Key usage."""
from __future__ import unicode_literals

from timesketch.lib.analyzers import interface
from timesketch.lib.analyzers import manager


class GcpServiceKeySketchPlugin(interface.BaseSketchAnalyzer):
    """Sketch analyzer for GCP Service Key usage."""

    NAME = 'gcp_servicekey'

    def __init__(self, index_name, sketch_id):
        """Initialize The Sketch Analyzer.

        Args:
            index_name: Elasticsearch index name
            sketch_id: Sketch ID
        """
        self.index_name = index_name
        super(GcpServiceKeySketchPlugin, self).__init__(index_name, sketch_id)

    def run(self):
        """Entry point for the analyzer.

        Returns:
            String with summary of the analyzer result
        """
        query = ('principalEmail:*gserviceaccount*')
        return_fields = ['message', 'methodName']

        events = self.event_stream(
            query_string=query, return_fields=return_fields)

        gcp_servicekey_counter = 0

        for event in events:
            # Fields to analyze.
            message = event.source.get('message')
            methodName = event.source.get('methodName')

            if 'CreateServiceAccount' in methodName:
                event.add_star()
                event.add_label('New ServiceAccount Created')

            if 'compute.instances.insert' in methodName:
                event.add_star()
                event.add_label('VM created')

            if 'compute.firewalls.insert' in methodName:
                event.add_star()
                event.add_label('FW rule created')

            if 'compute.networks.insert' in methodName:
                event.add_star()
                event.add_label('Network Insert Event')

            # Commit the event to the datastore.
            event.commit()
            gcp_servicekey_counter += 1

        # Create a saved view with our query.
        if gcp_servicekey_counter:
            self.sketch.add_view('GCP ServiceKey activity', \
            'gcp_servicekey', query_string=query)

        # Return a summary from the analyzer.
        return 'GCP ServiceKey analyzer completed, \
        {0:d} service key marked'.format(gcp_servicekey_counter)


manager.AnalysisManager.register_analyzer(GcpServiceKeySketchPlugin)
