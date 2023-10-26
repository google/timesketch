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
"""This file contains the plugin for Windows event logs feature extraction."""

import logging
from typing import List, Dict

from timesketch.lib.analyzers import interface as base_interface
from timesketch.lib.analyzers.feature_plugins import interface
from timesketch.lib.analyzers.feature_plugins import manager

logger = logging.getLogger("timesketch.analyzers.winevt_features")


class WindowsEventFeatureExtractionPlugin(interface.BaseFeatureExtractionPlugin):
    """A plugin for Windows event log feature extraction."""

    NAME = "winevt_feature_extraction"
    DISPLAY_NAME = "Windows Event Log Feature Extraction"
    DESCRIPTION = (
        "This plugin extracts Windows event logs attributes from plaso output"
        " attribute `strings`"
    )

    EVENT_FIELDS = ["strings"]

    def run_plugin(self, name: str, config: dict) -> str:
        """Extracts features from events.

        Args:
            name (str): Feature extraction name.
            config (dict): A dict that contains the configuration for the feature
                extraction.

        Returns:
            str: Returns summary of the feature extraction.
        """
        return self.extract_features(name, config)

    def validate_feature_config(self, name: str, config: dict) -> None:
        """Validates the name and configuration.

        Args:
            name (str): Name of the feature.
            config (dict): Configuration parameter.

        Raises:
            ValueError: Raises ValueError for value type errors.
        """
        if not name:
            raise ValueError(
                "Feature name is empty, please check your 'winevt_features.yaml' config!"
            )

        if not config:
            raise ValueError(
                "Feature configuration for [%s] value is empty, please check your 'winevt_features.yaml' config!"
                % name
            )```

        if not (
            isinstance(config.get("source_name"), list)
            or isinstance(config.get("provider_identifier"), list)
        ):
            raise ValueError(
                "[%s] Either 'source_name' or 'provider_identifier' are required and have to be a list!"
                % name
            )```

        if not isinstance(config.get("event_identifier"), int):
            raise ValueError(
                "[%s] Missing 'event_identifier' or it is not an integer!" % name
            )```

        if not isinstance(config.get("event_version"), int):
            raise ValueError(
                "[%s] Missing 'event_version' or it is not an integer!" % name
            )```

        if not isinstance(config.get("mapping"), list):
            raise ValueError("[%s] Missing 'mapping' or it is not a list!" % name)

        if not len(config.get("mapping")) > 0:
            raise ValueError("[%s] 'mapping' list cannot be empty!" % name)

        for entry in config.get("mapping"):
            if not isinstance(entry.get("name"), str):
                raise ValueError(
                    "[%s] 'mapping.name' is required and must be a string!"
                )

            if not isinstance(entry.get("string_index"), int):
                raise ValueError(
                    "[%s] 'mapping.string_index' is required and must be an integer!"
                )

    def extract_features(self, name: str, config: dict) -> str:
        """Extracts features from events.

        Args:
            name (str): Features extraction name.
            config (dict): A dict that contains the configuration fo the
                feature extraction.

        Returns:
            str: Returns summary of the feature extraction for `feature_name`.
        """
        self.validate_feature_config(name, config)

        source_name = config.get("source_name", [""])[0]
        provider_identifier = config.get("provider_identifier", [""])[0]

        event_identifier = int(config.get("event_identifier"))
        event_version = int(config.get("event_version"))

        mappings = config.get("mapping")


        # Building search query - Use source_name or provider_identifier and not both.
        query = ""
        if source_name:
            query = f"source_name:{source_name}"
        elif provider_identifier:
            query = f"provider_identifier:{provider_identifier}"

        query = (
            f"{query} AND event_identifier: {event_identifier}"
            f" AND event_version: {event_version}"
        )

        events = self.analyzer_object.event_stream(
            query_string=query, return_fields=self.EVENT_FIELDS
        )
        event_counter = 0

        for event in events:
            attributes = {}
            strings = event.source.get("strings", None)

            if not strings or not isinstance(strings, list):
                logger.debug(
                    "Missing or invalid strings field in the event. Skipping the"
                    " event %s.",
                    event.event_id,
                )
                continue

            for mapping in mappings:
                attribute_name = mapping.get("name")
                string_index = int(mapping.get("string_index"))

                attribute_aliases = mapping.get("aliases", [])

                try:
                    attribute_value = strings[string_index]
                except IndexError:
                    logger.warning(
                        "The index %d for field %s does not exist in strings. "
                        "Skipping the event %s",
                        string_index,
                        attribute_name,
                        event.event_id,
                    )
                    continue

                attributes[attribute_name] = attribute_value
                if attribute_aliases:
                    for alias in attribute_aliases:
                        attributes[alias] = attribute_value

            event.add_attributes(attributes)
            event.commit()
            event_counter += 1

        logger.debug("%d features extracted using feature %s", event_counter, name)
        return (
            f"winevt feature extraction: [{name}] extracted {event_counter} features."
        )

    @staticmethod
    def get_kwargs() -> List[Dict]:
        """Get keywords arguments.

        Returns:
            List[dict]: A list of dict containing features name and configuration.
        """
        # config_file winevt.yaml is located within the timesketch/data directory.
        config_file = "winevt_features.yaml"

        features_config = base_interface.get_yaml_config(config_file)
        if not features_config:
            logger.warning("No feature configuration data in %s", config_file)
            return []

        features_kwargs = [
            {"feature_name": feature, "feature_config": config}
            for feature, config in features_config.items()
        ]

        return features_kwargs


manager.PluginManager.register_plugin(WindowsEventFeatureExtractionPlugin)
