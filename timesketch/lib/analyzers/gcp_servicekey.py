"""Sketch analyzer plugin for GCP Service Key usage."""
from __future__ import unicode_literals

from timesketch.lib import emojis
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
        query = ('event_subtype:compute.instances.insert AND user:*gserviceaccount*')
        return_fields = ['message', 'event_subtype', 'event_type', 'user', 'name']

        # Generator of events based on your query.
        events = self.event_stream(
            query_string=query, return_fields=return_fields)

        gcp_servicekey_counter = 0

        for event in events:
            # Fields to analyze.
            message = event.source.get('message')
            event_subtype = event.source.get('event_subtype')
            event_type = event.source.get('event_type')
            user = event.source.get('user')
            name = event.source.get('name')

            if event_type == 'GCE_OPERATION_DONE':
                event.add_star()
                event.add_tags('GCP Success Event')
                event.add_label('vm_created')

            # Commit the event to the datastore.
            event.commit()
            gcp_servicekey_counter += 1

        # Create a saved view with our query.
        if gcp_servicekey_counter:
            self.sketch.add_view('GCP ServiceKey activity', 'gcp_servicekey', query_string=query)

        # TODO: Return a summary from the analyzer.
        return 'GCP ServiceKey analyzer completed, {0:d} service key marked'.format(gcp_servicekey_counter)


manager.AnalysisManager.register_analyzer(GcpServiceKeySketchPlugin)
