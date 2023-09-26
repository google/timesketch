"""This file contains the plugin for Windows event logs feature extraction."""

from typing import List

import logging

from timesketch.lib.analyzers import interface as base_interface
from timesketch.lib.analyzers.feature_plugins import interface
from timesketch.lib.analyzers.feature_plugins import manager

logger = logging.getLogger("timesketch.analyzers.feature")


class WindowsEventFeatureExtractionPlugin(interface.BaseFeatureExtractionPlugin):
    """A plugin for Windows event log feature extraction."""

    NAME = "winevt_feature_extraction"
    DISPLAY_NAME = "Windows Event Log Feature Extraction"
    DESCRIPTION = (
        "This plugin extracts Windows event logs attributes from plaso output"
        " attribute `strings`"
    )

    EVENT_FIELDS = ["strings"]

    def run_plugin(self) -> str:
        """Initializes plugin class object.

        Returns:
            str: Summary of plugin output.
        """

        # Stores extraction summary for each feature.
        results = []

        feature_kwargs = self.load_feature_config()
        if not feature_kwargs:
            return f"No feature configuration data for {self.NAME}"

        for feature in feature_kwargs:
            # NOTE: feature_name and feature_config value checking is done at the sink
            # function `extract_features`.
            feature_name = feature.get("feature", None)
            feature_config = feature.get("feature_config", None)

            result = self.extract_features(feature_name, feature_config)
            if not result:
                logger.debug("No result for plugin run for %s", feature_name)
            results.append(result)

        return "\n".join(results)

    def extract_features(self, name: str, config: dict) -> str:
        """Extracts features from events.

        Args:
            name (str): Features extraction name.
            config (dict): A dict that contains the configuration fo the
                feature extraction.

        Returns:
            str: Returns summary of the feature extraction for `feature_name`.
        """

        if not name:
            raise ValueError("Feature name is empty")

        if not config:
            raise ValueError("Feature configuration value is empty")

        source_name = config.get("source_name", None)
        if not source_name:
            raise ValueError("source_name is empyt")

        if not isinstance(source_name, list):
            raise TypeError(
                f"Expecting source_name as a list in {name} and got {type(source_name)}"
            )

        source_name = source_name[0]

        # Using -1 as a default value for event_identifier and event_version as
        # 0 is considered as None.
        event_identifier = int(config.get("event_identifier", -1))
        event_version = int(config.get("event_version", -1))

        if not source_name:
            raise ValueError("source_name is empty")

        if event_identifier < 0:
            raise ValueError(
                f"event_identifier is {event_identifier}. Expecting the value >= 0"
            )

        if event_version < 0:
            raise ValueError(f"event_version is {event_version}. Expecting value >= 0")

        mappings = config.get("mapping", None)
        if not mappings:
            raise ValueError(f"mapping value for {name} is empty")

        query = (
            f"source_name: {source_name} AND event_identifier: {event_identifier}"
            f" AND event_version: {event_version}"
        )

        events = self.analyzer_object.event_stream(
            query_string=query, return_fields=self.EVENT_FIELDS
        )
        event_counter = 0

        for event in events:
            attributes = {}

            strings = event.source.get("strings", None)
            if not strings:
                logger.debug("No strings attribute in event ID: %s", event.event_id)
                continue

            for mapping in mappings:
                attribute_name = mapping.get("name", None)
                string_index = int(mapping.get("string_index", -1))
                attribute_aliases = mapping.get("aliases", None)

                attribute_value = ""
                try:
                    attribute_value = strings[string_index]
                except IndexError:
                    logger.warning(
                        "The index %d does not exist in strings", string_index
                    )
                    continue

                attributes[attribute_name] = attribute_value
                if attribute_aliases:
                    for alias in attribute_aliases:
                        attributes[alias] = attribute_value

            event.add_attributes(attributes)
            event.commit()

            event_counter += 1

        return f"{event_counter} events updated by {name}."

    def load_feature_config(self) -> List[dict]:
        """Load feature configuration from a file.

        Returns:
            List[dict]: A list of dictionary containing feature name and config.
            None: Returns None if configuration file is empty.
        """

        # config_file winevt.yaml is located within the timesketch/data directory.
        config_file = "winevt.yaml"

        features_config = base_interface.get_yaml_config(config_file)
        if not features_config:
            logger.debug("No feature configuration data in %s", config_file)
            return None

        features_kwargs = [
            {"feature": feature, "feature_config": config}
            for feature, config in features_config.items()
        ]

        return features_kwargs


manager.FeatureExtractionPluginManager.register_plugin(
    WindowsEventFeatureExtractionPlugin
)
