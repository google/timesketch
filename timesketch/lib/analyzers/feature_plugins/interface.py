"""This file contains an interface to feature extraction plugins."""

import abc


class BaseFeatureExtractionPlugin(object):
    """A base plugin for the feature extraction.

    This is an interface for the feature extraction plugins.
    """

    NAME = "base_feature_extraction"
    DISPLAY_NAME = "Base Feature Extraction"
    DESCRIPTION = ""

    def __init__(self, analyzer_object) -> None:
        """Initializes the plugin.

        Args:
            analyzer_object (FeatureSketchPlugin): An object of class
                FeatureSketchPlugin.
        """

        super().__init__()
        self.analyzer_object = analyzer_object

    @abc.abstractmethod
    def run_plugin(self):
        """Main entry point to feature extraction plugins"""
