"""Sketch analyzer plugin for GCP Logging."""
from __future__ import unicode_literals

import random # Remove before merge (issues/2051)
import string # Remove before merge (issues/2051)
import re

from timesketch.lib.analyzers import interface
from timesketch.lib.analyzers import manager


class GCPLoggingSketchPlugin(interface.BaseAnalyzer):
    """Analyzer for GCP Logging"""

    NAME = 'gcp_logging'
    DISPLAY_NAME = 'Google Cloud Logging Analyzer'
    DESCRIPTION = ('Extract features and tag security relevant actions in '
        'Google Cloud Logging.')

    def _format_resource_name(self, resource_name):
        """Format resource names for storage as sketch attributes.

        Returns:
          Tuple in format ('resource_type', 'resource_identifier')
        """
        resource_identifier = resource_name.rsplit('/', maxsplit=2)[-1]
        resource_type = 'gcp_' + resource_name.rsplit('/', maxsplit=2)[-2]
        return (resource_type, resource_identifier)

    def run(self):
        """Entry point for the analyzer.

        Returns:
            String with summary of the analyzer result
        """
        query = ('data_type:"gcp:log:json"')
        return_fields = ['principalEmail', 'methodName', 'resourceName']
        events = self.event_stream(query_string=query,
            return_fields=return_fields)

        users = []
        resources = {}

        for event in events:
            principal_email = event.source.get('principalEmail')
            method_name = event.source.get('methodName')
            resource_name = event.source.get('resourceName')

            if principal_email:
                if principal_email not in users:
                    users.append(principal_email)

                if re.match(r'\d{12}-compute@developer\.gserviceaccount\.com',
                  principal_email):
                    event.add_tags(['default-service-account'])

            if resource_name:
                resource_type, resource_identifier = (
                  self._format_resource_name(resource_name))
                if resource_type not in resources:
                    resources[resource_type] = []

                if resource_identifier not in resources[resource_type]:
                    resources[resource_type].append(resource_identifier)

            if method_name:
                if 'CreateServiceAccount' in method_name:
                    event.add_tags(['service-account-created'])

                if 'compute.instances.insert' in method_name:
                    event.add_tags(['gce-instance-created'])

                if 'compute.firewalls.insert' in method_name:
                    event.add_tags(['fw-rule-created'])

                if 'compute.networks.insert' in method_name:
                    event.add_tags(['network-created'])

                if 'compute.projects.setCommonInstanceMetadata' in method_name:
                    event.add_tags(['compute-metadata-changed'])

                if 'compute.instances.setMetadata' in method_name:
                    event.add_tags(['compute-metadata-changed'])

            event.commit()

        # Adding a random string to attribute names due to a bug where deleted
        # attributes cannot be re-added with the same name (issues/2051).
        # Remove before merge.
        unique = ''.join(
          random.choices(string.ascii_uppercase + string.digits, k=4))

        # Remove unique (issues/2051)
        self.sketch.add_sketch_attribute(
          'gcp_identities' + unique, users, 'text')

        # Remove unique (issues/2051)
        for resource_type, resource_list in resources.items():
            self.sketch.add_sketch_attribute(
              resource_type + unique, resource_list, 'text')

        for user in users:
            view_name = 'GCP User {0:s}'.format(user)
            query_string = ('principalEmail:"{0:s}"'.format(user))
            self.sketch.add_view(
              view_name=view_name, analyzer_name=self.NAME,
              query_string=query_string)

        return ('GCP logging analyzer completed with '
                '{0:d} resource types extracted.').format(len(resources))


manager.AnalysisManager.register_analyzer(GCPLoggingSketchPlugin)
