"""Main sketch analyzer for feature extraction."""

import logging

from timesketch.lib.analyzers import interface
from timesketch.lib.analyzers import manager
from timesketch.lib.analyzers.feature_plugins import manager as feature_manager

logger = logging.getLogger("timesketch.analyzers.feature")


class FeatureSketchPlugin(interface.BaseAnalyzer):
    """Main sketch analyzer for feature extraction."""

    NAME = "feature_extraction_main"
    DISPLAY_NAME = "Feature Extraction Sketch Analyzer"
    DESCRIPTION = "This analyzer runs all the feature extractions plugins in the index."

    DEPENDENCIES = frozenset()

    def __init__(
        self, index_name: str, sketch_id: int, timeline_id: int = None
    ) -> None:
        """Initializes the sketch analyzer.

        Args:
            index_name (str): OpenSearch index name.
            sketch_id (int): TimeSketch's sketch ID.
            timeline_id (int): The ID of the timeline.
        """

        super().__init__(
            index_name=index_name, sketch_id=sketch_id, timeline_id=timeline_id
        )

        self._feature_plugins = (
            feature_manager.FeatureExtractionPluginManager.get_plugins(self)
        )

    def run(self) -> str:
        """Entry point for the sketch analyzer.

        Returns:
            str: A summary of sketch analyzer result.
        """

        results = []

        for feature_plugin in self._feature_plugins:
            result = feature_plugin.run_plugin()
            if not result:
                logger.debug("No plugin result for %s", feature_plugin.NAME)
            results.append(result)

        return "\n".join(results)


manager.AnalysisManager.register_analyzer(FeatureSketchPlugin)
