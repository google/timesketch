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
"""The feature extraction plugins manager object."""

import logging
from typing import List, Type


class PluginManager(object):
    """ "A class that implements the plugins manager."""

    _plugin_classes: dict = {}
    logger = logging.getLogger(__name__)

    @classmethod
    def register_plugin(cls, plugin_class: Type["BaseFeatureExtractionPlugin"]) -> None:
        """Registers a plugin class.

        Args:
            plugin_class (Type[BaseFeatureExtractionPlugin]): A class object of a
                plugin.

        Raises:
            KeyError: If the plugin_class is already registered.
        """
        plugin_name = plugin_class.NAME.lower()
        if plugin_name in cls._plugin_classes:
            raise KeyError(f"Plugin class {plugin_class.NAME} is already registered.")

        cls.logger.debug("Registering plugin class %s", plugin_class.NAME)
        cls._plugin_classes[plugin_name] = plugin_class

    @classmethod
    def register_plugins(
        cls, plugin_classes: List[Type["BaseFeatureExtractionPlugin"]]
    ) -> None:
        """Registers multiple plugin classes.

        Args:
            plugin_classes (List[Type[BaseFeatureExtractionPlugin]]): A list of plugin
                class objects.

        Raises:
            KeyError: If plugin classes are already registered.
        """
        for plugin_class in plugin_classes:
            cls.register_plugin(plugin_class=plugin_class)

    @classmethod
    def deregister_plugin(
        cls, plugin_class: Type["BaseFeatureExtractionPlugin"]
    ) -> None:
        """Deregisters a plugin class.

        Args:
            plugin_class (Type[BaseFeatureExtractionPlugin]): A plugin class to be
                deregistered.

        Raises:
            KeyError: If the plugin class is not registered.
        """
        plugin_name = plugin_class.NAME.lower()
        if plugin_name not in cls._plugin_classes:
            raise KeyError(f"Plugin class {plugin_class.NAME} is not registered.")

        cls.logger.debug("Deregistering plugin class: %s", plugin_class.NAME)
        del cls._plugin_classes[plugin_name]

    @classmethod
    def get_plugin(
        cls, plugin_name: str, analyzer_object: "FeatureSketchPlugin"
    ) -> "BaseFeatureExtractionPlugin":
        """Returns plugin class.

        Args:
            plugin_name (str): The name of the plugin to retrieve.
            analyzer_object (FeatureSketchPlugin): An instance of FeatureSketchPlugin.

        Returns:
            BaseFeatureExtractionPlugin: The plugin class object.
        """
        for plugin_class in cls._plugin_classes.values():
            if plugin_class.NAME.lower() == plugin_name:
                return plugin_class(analyzer_object)

        return None  # Return None if plugin not found

    @classmethod
    def get_plugins(
        cls, analyzer_object: "FeatureSketchPlugin"
    ) -> List["BaseFeatureExtractionPlugin"]:
        """Retrieves plugins classes.

        Args:
            analayzer_object (FeatureSketchPlugin): An instance of FeatureSketchPlugin.

        Returns:
            List[BaseFeatureExtractionPlugin]: A list of plugin class objects.
        """
        return [
            plugin_class(analyzer_object)
            for plugin_class in cls._plugin_classes.values()
        ]
