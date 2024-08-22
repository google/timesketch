"""Sketch analyzer plugin for feature extraction."""

from __future__ import unicode_literals

import logging

import six

from timesketch.lib import emojis
from timesketch.lib.analyzers import interface as base_interface
from timesketch.lib.analyzers.feature_extraction_plugins import interface
from timesketch.lib.analyzers.feature_extraction_plugins import manager
from timesketch.lib.analyzers import utils


logger = logging.getLogger("timesketch.analyzers.feature_extraction.regex")
RE_FLAGS = [
    "re.ASCII",
    "re.IGNORECASE",
    "re.LOCALE",
    "re.MULTILINE",
    "re.DOTALL",
    "re.VERBOSE",
]


class RegexFeatureExtractionPlugin(interface.BaseFeatureExtractionPlugin):
    """Analyzer for FeatureExtraction."""

    NAME = "regex_extraction_plugin"
    DISPLAY_NAME = "Regex feature extractor"
    DESCRIPTION = (
        "Extract features from event based on stored regex definitions in the "
        "'regex_features.yaml' config."
    )

    FORM_FIELDS = [
        {
            "name": "query_string",
            "type": "ts-dynamic-form-text-input",
            "label": "The filter query to narrow down the result set",
            "placeholder": "Query",
            "default_value": "",
        },
        {
            "name": "query_dsl",
            "type": "ts-dynamic-form-text-input",
            "label": "The filter query DSL to narrow down the result",
            "placeholder": "Query DSL",
            "default_value": "",
        },
        {
            "name": "attribute",
            "type": "ts-dynamic-form-text-input",
            "label": "Name of the field to apply regular expression against",
            "placeholder": "Field Name",
            "default_value": "",
        },
        {
            "name": "store_as",
            "type": "ts-dynamic-form-text-input",
            "label": "Name of the field to store the extracted results in",
            "placeholder": "Store results as field name",
            "default_value": "",
        },
        {
            "name": "re",
            "type": "ts-dynamic-form-text-input",
            "label": "The regular expression to extract data from field",
            "placeholder": "Regular Expression",
            "default_value": "",
        },
        {
            "name": "re_flags",
            "type": "ts-dynamic-form-multi-select-input",
            "label": "List of flags to pass to the regular expression",
            "placeholder": "Regular Expression flags",
            "default_value": [],
            "options": RE_FLAGS,
            "optional": True,
        },
        {
            "name": "emojis",
            "type": "ts-dynamic-form-multi-select-input",
            "label": "List of emojis to add to events with matches",
            "placeholder": "Emojis to add to events",
            "default_value": [],
            "options": [x.code for x in emojis.EMOJI_MAP.values()],
            "options-label": [
                "{0:s} - {1:s}".format(x, y.help) for x, y in emojis.EMOJI_MAP.items()
            ],
            "optional": True,
        },
        {
            "name": "tags",
            "type": "ts-dynamic-form-text-input",
            "label": "Tag to add to events with matches",
            "placeholder": "Tag to add to events",
            "default_value": "",
            "optional": True,
        },
        {
            "name": "create_view",
            "type": "ts-dynamic-form-boolean",
            "label": "Should a view be created if there is a match",
            "placeholder": "Create a view",
            "default_value": False,
            "optional": True,
        },
        {
            "name": "store_type_list",
            "type": "ts-dynamic-form-boolean",
            "label": "Store extracted result in type List",
            "placeholder": "Store results as field type list",
            "default_value": False,
            "optional": True,
        },
        {
            "name": "overwrite_store_as",
            "type": "ts-dynamic-form-boolean",
            "label": "Overwrite the field to store if already exist",
            "placeholder": "Overwrite the field to store",
            "default_value": True,
            "optional": True,
        },
        {
            "name": "overwrite_and_merge_store_as",
            "type": "ts-dynamic-form-boolean",
            "label": "Overwrite the field to store and merge value if exist",
            "placeholder": "Overwrite the field to store and merge value",
            "default_value": False,
            "optional": True,
        },
        {
            "name": "keep_multimatch",
            "type": "ts-dynamic-form-boolean",
            "label": "Keep multi match datas",
            "placeholder": "Keep multi match",
            "default_value": False,
            "optional": True,
        },
        {
            "name": "aggregate",
            "type": "ts-dynamic-form-boolean",
            "label": "Should results be aggregated if there is a match",
            "placeholder": "Aggregate results",
            "default_value": False,
            "optional": True,
        },
    ]

    def run_plugin(self, name: str, config: dict) -> str:
        """Entry point for the analyzer.

        Args:
            name (str): Feature extraction name.
            config (dict): A dict that contains the configuration for the feature
                extraction.

        Returns:
            str: String with summary of the analyzer result.
        """
        return self.extract_feature(name, config)

    @staticmethod
    def _get_attribute_value(
        current_val, extracted_value, keep_multi, merge_values, type_list
    ):
        """Returns the attribute value as it should be stored.

        Args:
            current_val: current value of store_as.
            extracted_value: values matched from regexp (type list).
            keep_multi: choice if you keep all match from regex (type boolean).
            merge_values: choice if you merge value from extracted
                 and current (type boolean).
            type_list: choice if you store values in list type(type boolean).

        Returns:
            Value to store
        """
        if not current_val:
            merge_values = False
        if len(extracted_value) == 1:
            keep_multi = False
        if type_list:
            if merge_values and keep_multi:
                return sorted(list(set(current_val) | set(extracted_value)))
            if merge_values:
                if extracted_value[0] not in current_val:
                    current_val.append(extracted_value[0])
                return sorted(current_val)
            if keep_multi:
                return sorted(extracted_value)
            return [extracted_value[0]]
        if merge_values and keep_multi:
            list_cur = current_val.split(",")
            merge_list = sorted(list(set(list_cur) | set(extracted_value)))
            return ",".join(merge_list)
        if merge_values:
            if extracted_value[0] in current_val:
                return current_val
            return f"{current_val},{extracted_value[0]}"
        if keep_multi:
            return ",".join(extracted_value)
        return extracted_value[0]

    def extract_feature(self, name, config):
        """Extract features from events.

        Args:
            name: String with the name describing the feature to be extracted.
            config: A dict that contains the configuration for the feature
                extraction. See data/regex_features.yaml for fields and further
                documentation of what needs to be defined.

        Returns:
            String with summary of the analyzer result.
        """
        query = config.get("query_string")
        query_dsl = config.get("query_dsl")
        attribute = config.get("attribute")
        store_type_list = config.get("store_type_list", False)
        keep_multimatch = config.get("keep_multimatch", False)
        overwrite_store_as = config.get("overwrite_store_as", True)
        overwrite_and_merge_store_as = config.get("overwrite_and_merge_store_as", False)

        if not attribute:
            logger.warning("No attribute defined.")
            return ""

        store_as = config.get("store_as")
        if not store_as:
            logger.warning("No attribute defined to store results in.")
            return ""

        tags = config.get("tags", [])

        expression_string = config.get("re")
        if not expression_string:
            logger.warning("No regular expression defined.")
            return ""

        expression = utils.compile_regular_expression(
            expression_string=expression_string, expression_flags=config.get("re_flags")
        )

        emoji_names = config.get("emojis", [])
        emojis_to_add = [emojis.get_emoji(x) for x in emoji_names]

        return_fields = [attribute, store_as]

        events = self.analyzer_object.event_stream(
            query_string=query, query_dsl=query_dsl, return_fields=return_fields
        )

        event_counter = 0
        for event in events:
            attribute_field = event.source.get(attribute)
            if isinstance(attribute_field, six.text_type):
                attribute_value = attribute_field
            elif isinstance(attribute_field, (list, tuple)):
                attribute_value = ",".join(attribute_field)
            elif isinstance(attribute_field, (int, float)):
                attribute_value = attribute_field
            else:
                attribute_value = None

            if not attribute_value:
                continue

            result = expression.findall(attribute_value)
            if not result:
                continue
            result = list(set(result))

            event_counter += 1
            store_as_current_val = event.source.get(store_as)
            if store_as_current_val and not overwrite_store_as:
                continue
            if isinstance(store_as_current_val, six.text_type):
                store_type_list = False
            elif isinstance(store_as_current_val, (list, tuple)):
                store_type_list = True
            new_value = self._get_attribute_value(
                store_as_current_val,
                result,
                keep_multimatch,
                overwrite_and_merge_store_as,
                store_type_list,
            )
            if not new_value:
                continue
            event.add_attributes({store_as: new_value})
            event.add_emojis(emojis_to_add)
            event.add_tags(tags)

            # Commit the event to the datastore.
            event.commit()

        return "Feature extraction [{0:s}] extracted {1:d} features.".format(
            name, event_counter
        )

    @staticmethod
    def get_kwargs():
        """Get kwargs for the analyzer.

        Returns:
            List of features to search for.
        """
        features_config = base_interface.get_yaml_config("regex_features.yaml")
        if not features_config:
            # Backwards compatibility with old config name:
            features_config = base_interface.get_yaml_config("features.yaml")
            if not features_config:
                return (
                    "Unable to parse the 'regex_features.yaml' or "
                    "'features.yaml' config file!"
                )

        features_kwargs = [
            {"feature_name": feature, "feature_config": config}
            for feature, config in features_config.items()
        ]
        return features_kwargs


manager.PluginManager.register_plugin(RegexFeatureExtractionPlugin)
