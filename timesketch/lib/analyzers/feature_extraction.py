# Copyright 2023 Google Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Main sketch analyzer for feature extraction."""

import logging
from typing import List, Optional, Dict

from timesketch.lib.analyzers import interface
from timesketch.lib.analyzers import manager
from timesketch.lib.analyzers.feature_extraction_plugins import (
    manager as feature_manager,
)

logger = logging.getLogger("timesketch.analyzers.feature_extraction")


class FeatureExtractionSketchPlugin(interface.BaseAnalyzer):
    """Main sketch analyzer for feature extraction.

    This analyzer runs all the feature extractions within the feature_plugins directory.
    """

    NAME = "feature_extraction"
    DISPLAY_NAME = "Feature Extractions"
    DESCRIPTION = (
        "Runs all feature extraction plugins on selected timelines. "
        "Currently implemented extractions: * regex features * winevt features."
    )

    DEPENDENCIES = frozenset()

    def __init__(
        self,
        index_name: str,
        sketch_id: int,
        timeline_id: Optional[int] = None,
        **kwargs,
    ) -> None:
        """Initializes the sketch analyzer.

        Args:
            index_name (str): OpenSearch index name.
            sketch_id (int): TimeSketch's sketch ID.
            timeline_id (int): The ID of the timeline.
        """
        self._plugin_name: str = kwargs.get("plugin_name")
        self._feature_name: str = kwargs.get("feature_name")
        self._feature_config: Dict = kwargs.get("feature_config")

        super().__init__(
            index_name=index_name, sketch_id=sketch_id, timeline_id=timeline_id
        )

    @property
    def plugin_name(self) -> str:
        return self._plugin_name

    @plugin_name.setter
    def plugin_name(self, value: str) -> None:
        self._plugin_name = value

    @property
    def feature_name(self) -> str:
        return self._feature_name

    @feature_name.setter
    def feature_name(self, value: str) -> None:
        self._feature_name = value

    @property
    def feature_config(self) -> Dict:
        return self._feature_config

    @feature_config.setter
    def feature_config(self, value: Dict) -> None:
        self._feature_config = value

    def run(self) -> str:
        """Entry point for the sketch analyzer.

        Returns:
            str: A summary of sketch analyzer result.
        """
        # Handling unset self._plugin_name
        if not self._plugin_name:
            logger.debug("Feature extraction plugin name is empty")
            return "Feature extraction plugin name is empty"

        try:
            plugin_class = feature_manager.PluginManager.get_plugin(
                self._plugin_name, self
            )
            if not plugin_class:
                raise ValueError(
                    f"Feature extraction plugin {self._plugin_name} is not "
                    "registered. Check if the feature is registered in "
                    "feature_plugins."
                )

            return plugin_class.run_plugin(self._feature_name, self._feature_config)
        except ValueError as exception:
            logger.error(str(exception))
            return f"Error: {str(exception)}"

    @staticmethod
    def get_kwargs() -> List[Dict]:
        """Get kwargs for the analyzer.

        Returns:
            List[dict]: A list of dict containing plugin name, feature name and feature
                config.
        """
        feature_kwargs_list = []

        plugin_classes = feature_manager.PluginManager.get_plugins(None)
        for plugin in plugin_classes:
            feature_list = plugin.get_kwargs()
            if not feature_list:
                logger.debug("No configuration for %s", plugin.NAME)
                continue

            for feature_config in feature_list:
                feature_config["plugin_name"] = plugin.NAME.lower()
                feature_kwargs_list.append(feature_config)

        return feature_kwargs_list


manager.AnalysisManager.register_analyzer(FeatureExtractionSketchPlugin)
