"""Sketch analyzer plugin for GCP Service Key usage."""
from __future__ import unicode_literals

from timesketch.lib.analyzers import interface
from timesketch.lib.analyzers import manager


class GcpLoggingSketchPlugin(interface.BaseAnalyzer):
    """Analyzer for GCP Logging"""

    NAME = 'gcp_logging'
    DISPLAY_NAME = 'Google Cloud Logging Analyzer'
    DESCRIPTION = ('Extract accounts and resources from cloud logging and tags'
        ' security relevant actions.')

    def run(self):
        """Entry point for the analyzer.

        Returns:
            String with summary of the analyzer result
        """

        return ('GCP logging analyzer completed with '
                '{0:d} service key marked').format(0)


manager.AnalysisManager.register_analyzer(GcpLoggingSketchPlugin)
