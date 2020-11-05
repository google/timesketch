"""Sketch analyzer plugin for feature extraction."""
from __future__ import unicode_literals

import logging
import re

import six

from timesketch.lib import emojis
from timesketch.lib.analyzers import interface
from timesketch.lib.analyzers import manager


logger = logging.getLogger('timesketch.analyzers.feature')
RE_FLAGS = [
    're.ASCII',
    're.IGNORECASE',
    're.LOCALE',
    're.MULTILINE',
    're.DOTALL',
    're.VERBOSE',
]


class FeatureExtractionSketchPlugin(interface.BaseSketchAnalyzer):
    """Sketch analyzer for FeatureExtraction."""

    NAME = 'feature_extraction'

    CONFIG_FILE = 'features.yaml'

    FORM_FIELDS = [
        {
            'name': 'query_string',
            'type': 'ts-dynamic-form-text-input',
            'label': 'The filter query to narrow down the result set',
            'placeholder': 'Query',
            'default_value': ''
        },
        {
            'name': 'query_dsl',
            'type': 'ts-dynamic-form-text-input',
            'label': 'The filter query DSL to narrow down the result',
            'placeholder': 'Query DSL',
            'default_value': ''
        },
        {
            'name': 'attribute',
            'type': 'ts-dynamic-form-text-input',
            'label': 'Name of the field to apply regular expression against',
            'placeholder': 'Field Name',
            'default_value': ''
        },
        {
            'name': 'store_as',
            'type': 'ts-dynamic-form-text-input',
            'label': 'Name of the field to store the extracted results in',
            'placeholder': 'Store results as field name',
            'default_value': ''
        },
        {
            'name': 're',
            'type': 'ts-dynamic-form-text-input',
            'label': 'The regular expression to extract data from field',
            'placeholder': 'Regular Expression',
            'default_value': ''
        },
        {
            'name': 're_flags',
            'type': 'ts-dynamic-form-multi-select-input',
            'label': 'List of flags to pass to the regular expression',
            'placeholder': 'Regular Expression flags',
            'default_value': [],
            'options': RE_FLAGS,
            'optional': True,
        },
        {
            'name': 'emojis',
            'type': 'ts-dynamic-form-multi-select-input',
            'label': 'List of emojis to add to events with matches',
            'placeholder': 'Emojis to add to events',
            'default_value': [],
            'options': [x.code for x in emojis.EMOJI_MAP.values()],
            'options-label': [
                '{0:s} - {1:s}'.format(
                    x, y.help) for x, y in emojis.EMOJI_MAP.items()],
            'optional': True,
        },
        {
            'name': 'tags',
            'type': 'ts-dynamic-form-text-input',
            'label': 'Tag to add to events with matches',
            'placeholder': 'Tag to add to events',
            'default_value': '',
            'optional': True,
        },
        {
            'name': 'create_view',
            'type': 'ts-dynamic-form-boolean',
            'label': 'Should a view be created if there is a match',
            'placeholder': 'Create a view',
            'default_value': False,
            'optional': True,
        },
        {
            'name': 'store_type_list',
            'type': 'ts-dynamic-form-boolean',
            'label': 'Store extracted result in type List',
            'placeholder': 'Store results as field type list',
            'default_value': False,
            'optional': True,
        },
        {
            'name': 'overwrite_store_as',
            'type': 'ts-dynamic-form-boolean',
            'label': 'Overwrite the field to store if already exist',
            'placeholder': 'Overwrite the field to store',
            'default_value': True,
            'optional': True,
        },
        {
            'name': 'overwrite_and_merge_store_as',
            'type': 'ts-dynamic-form-boolean',
            'label': 'Overwrite the field to store and merge value if exist',
            'placeholder': 'Overwrite the field to store and merge value',
            'default_value': False,
            'optional': True,
        },
        {
            'name': 'keep_multimatch',
            'type': 'ts-dynamic-form-boolean',
            'label': 'Keep multi match datas',
            'placeholder': 'Keep multi match',
            'default_value': False,
            'optional': True,
        },
        {
            'name': 'aggregate',
            'type': 'ts-dynamic-form-boolean',
            'label': 'Should results be aggregated if there is a match',
            'placeholder': 'Aggregate results',
            'default_value': False,
            'optional': True,
        },
    ]


    def __init__(self, index_name, sketch_id, config=None):
        """Initialize The Sketch Analyzer.

        Args:
            index_name: Elasticsearch index name
            sketch_id: Sketch ID
            config: Optional dict that contains the configuration for the
                analyzer. If not provided, the default YAML file will be
                loaded up.
        """
        self.index_name = index_name
        super(FeatureExtractionSketchPlugin, self).__init__(
            index_name, sketch_id)
        self._config = config

    def run(self):
        """Entry point for the analyzer.

        Returns:
            String with summary of the analyzer result.
        """
        config = self._config or interface.get_yaml_config(self.CONFIG_FILE)
        if not config:
            return 'Unable to parse the config file.'

        return_strings = []
        for name, feature_config in iter(config.items()):
            feature_string = self.extract_feature(name, feature_config)
            if feature_string:
                return_strings.append(feature_string)

        return ', '.join(return_strings)

    def extract_feature(self, name, config):
        """Extract features from events.

        Args:
            name: String with the name describing the feature to be extracted.
            config: A dict that contains the configuration for the feature
                extraction. See data/features.yaml for fields and further
                documentation of what needs to be defined.

        Returns:
            String with summary of the analyzer result.
        """
        query = config.get('query_string')
        query_dsl = config.get('query_dsl')
        attribute = config.get('attribute')
        store_type_list = config.get('store_type_list', False)
        keep_multimatch = config.get('keep_multimatch', False)
        overwrite_store_as = config.get('overwrite_store_as', True)
        overwrite_and_merge_store_as = \
            config.get('overwrite_and_merge_store_as', False)

        if not attribute:
            logger.warning('No attribute defined.')
            return ''

        store_as = config.get('store_as')
        if not store_as:
            logger.warning('No attribute defined to store results in.')
            return ''

        tags = config.get('tags', [])

        expression_string = config.get('re')
        expression_flags = config.get('re_flags')
        if not expression_string:
            logger.warning('No regular expression defined.')
            return ''

        if expression_flags:
            flags = set()
            for flag in expression_flags:
                try:
                    flags.add(getattr(re, flag))
                except AttributeError:
                    logger.warning('Unknown regular expression flag defined.')
                    return ''
            re_flag = sum(flags)
        else:
            re_flag = 0

        try:
            expression = re.compile(expression_string, flags=re_flag)
        except re.error as exception:
            # pylint: disable=logging-format-interpolation
            logger.warning((
                'Regular expression failed to compile, with '
                'error: {0!s}').format(exception))
            return ''

        emoji_names = config.get('emojis', [])
        emojis_to_add = [emojis.get_emoji(x) for x in emoji_names]

        return_fields = [attribute, store_as]

        events = self.event_stream(
            query_string=query, query_dsl=query_dsl,
            return_fields=return_fields)

        event_counter = 0
        for event in events:
            attribute_field = event.source.get(attribute)
            if isinstance(attribute_field, six.text_type):
                attribute_value = attribute_field
            elif isinstance(attribute_field, (list, tuple)):
                attribute_value = ','.join(attribute_field)
            elif isinstance(attribute_field, (int, float)):
                attribute_value = attribute_field
            else:
                attribute_value = None

            if not attribute_value:
                continue

            result = expression.findall(attribute_value)
            if not result:
                continue

            event_counter += 1
            store_type = event.source.get(store_as)
            if store_type and not overwrite_store_as:
                continue
            if isinstance(store_type, six.text_type):
                store_type_list = False
            elif isinstance(store_type, (list, tuple)):
                store_type_list = True
            if store_type_list:
                if keep_multimatch:
                    if store_type and overwrite_and_merge_store_as:
                        result_list = list(set(store_type) | set(result))
                        event.add_attributes({store_as: result_list})
                    else:
                        event.add_attributes({store_as: result})
                else:
                    if overwrite_and_merge_store_as and \
                       store_type and \
                       result[0] in store_type:
                        continue
                    event.add_attributes({store_as: [result[0]]})
            else:
                if keep_multimatch:
                    if store_type and overwrite_and_merge_store_as:
                        result_list = []
                        for elem_match in result:
                            if elem_match not in store_type:
                                result_list.append(elem_match)
                        if not result_list:
                            continue
                        event.add_attributes({store_as: store_type +
                                                        ',' +
                                                        ','.join(result_list)})
                    else:
                        event.add_attributes({store_as: ','.join(result)})
                else:
                    if overwrite_and_merge_store_as and \
                       store_type and \
                       result[0] in store_type:
                        continue
                    event.add_attributes({store_as: result[0]})
            event.add_emojis(emojis_to_add)
            event.add_tags(tags)

            # Commit the event to the datastore.
            event.commit()

        aggregate_results = config.get('aggregate', False)
        create_view = config.get('create_view', False)

        # If aggregation is turned on, we automatically create an aggregation.
        if aggregate_results:
            create_view = True

        if create_view and event_counter:
            view = self.sketch.add_view(
                name, self.NAME, query_string=query, query_dsl=query_dsl)

            if aggregate_results:
                params = {
                    'field': store_as,
                    'limit': 20,
                }
                self.sketch.add_aggregation(
                    name='Top 20 for: {0:s} [{1:s}]'.format(store_as, name),
                    agg_name='field_bucket', agg_params=params,
                    description='Created by the feature extraction analyzer',
                    view_id=view.id, chart_type='hbarchart')

        return 'Feature extraction [{0:s}] extracted {1:d} features.'.format(
            name, event_counter)


manager.AnalysisManager.register_analyzer(FeatureExtractionSketchPlugin)
