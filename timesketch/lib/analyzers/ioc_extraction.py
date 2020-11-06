"""Sketch analyzer plugin for ioc extraction."""
from __future__ import unicode_literals

import logging
import re

import os
import json

import six

from timesketch.lib.analyzers import interface
from timesketch.lib.analyzers import manager


logger = logging.getLogger('timesketch.analyzers.ioc')
RE_FLAGS = [
    're.ASCII',
    're.IGNORECASE',
    're.LOCALE',
    're.MULTILINE',
    're.DOTALL',
    're.VERBOSE',
]


class IOCExtractionSketchPlugin(interface.BaseSketchAnalyzer):
    """Sketch analyzer for IOCExtraction."""

    NAME = 'ioc_extraction'

    CONFIG_FILE = 'ioc_extract.yaml'

    FORM_FIELDS = [
        {
            'name': 'path_file_ioc',
            'type': 'ts-dynamic-form-text-input',
            'label': 'Path to file contains IOC in json format',
            'placeholder': 'IOC db',
            'default_value': ''
        },
        {
            'name': 'attributes',
            'type': 'ts-dynamic-form-multi-select-input',
            'label': 'Name of fields to apply ioc search against',
            'placeholder': 'Field Name',
            'default_value': ''
        },
        {
            'name': 'attributes_contains',
            'type': 'ts-dynamic-form-multi-select-input',
            'label': 'Partial name of fields to apply ioc search against',
            'placeholder': 'Partial Field Name',
            'default_value': '',
            'optional': True
        },
        {
            'name': 'match_re',
            'type': 'ts-dynamic-form-text-input',
            'label': 'The regular expression to extract data from field',
            'placeholder': 'Regular Expression',
            'default_value': '([^a-zA-Z0-9]|^)$value$([^a-zA-Z0-9]|$)',
            'optional': True
        },
        {
            'name': 're_flags',
            'type': 'ts-dynamic-form-multi-select-input',
            'label': 'List of flags to pass to the regular expression',
            'placeholder': 'Regular Expression flags',
            'default_value': [],
            'options': RE_FLAGS,
            'optional': True
        },
        {
            'name': 'store_as',
            'type': 'ts-dynamic-form-text-input',
            'label': 'Name of the field to store the extracted ioc in',
            'placeholder': 'Store results as field name',
            'default_value': 'ioc'
        },
        {
            'name': 'tags',
            'type': 'ts-dynamic-form-multi-select-input',
            'label': 'Tag to add to events with matches',
            'placeholder': 'Tag to add to events',
            'default_value': '',
            'optional': True
        }
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
        super(IOCExtractionSketchPlugin, self).__init__(
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
        for name, ioc_config in iter(config.items()):
            ioc_string = self.extract_ioc(name, ioc_config)
            if ioc_string:
                return_strings.append(ioc_string)

        return ', '.join(return_strings)

    def extract_ioc(self, name, config):
        """Extract IOC from events.

        Args:
            name: String with the name describing the feature to be extracted.
            config: A dict that contains the configuration for the ioc
                extraction. See data/ioc.yaml for fields and further
                documentation of what needs to be defined.

        Returns:
            String with summary of the analyzer result.
        """
        path_file_ioc = config.get('path_file_ioc')
        if not path_file_ioc:
            logger.warning('No path for file IOC defined.')
            return ''
        if not os.path.isfile(path_file_ioc):
            logger.warning('file IOC defined not exists.')
            return ''
        ioc_db = None
        with open(path_file_ioc) as json_file:
            try:
                ioc_db = json.load(json_file)
            except json.JSONDecodeError as exception:
                logger.warning((
                    'File IOC error to parse: '
                    '{0!s}').format(exception))
                return ''
        if not ioc_db:
            logger.warning('No data IOC in file IOC defined.')
            return ''
        if not isinstance(ioc_db, (list, tuple)):
            logger.warning('IOC data doesnt list type.')
            return ''

        attributes = config.get('attributes')
        attributes_contains = config.get('attributes_contains')
        if not attributes and not attributes_contains:
            logger.warning('No attributes defined.')
            return ''

        store_as = config.get('store_as')
        if not store_as:
            logger.warning('No attribute defined to store results in.')
            return ''

        tags = config.get('tags', [])

        expression_string = config.get(
            'match_re', '([^a-zA-Z0-9]|^)$value$([^a-zA-Z0-9]|$)')
        expression_flags = config.get('re_flags')

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

        attributes_list = attributes
        if attributes_contains:
            list_fieldnames = self.get_fields_list()
            if list_fieldnames:
                for fieldname in list_fieldnames:
                    for elm in attributes_contains:
                        if elm in fieldname:
                            if fieldname not in attributes_list:
                                attributes_list.append(fieldname)
        return_fields = attributes_list + [store_as]

        query = ''
        for attribute in attributes_list:
            if query:
                query += ' AND '
            query += '_exists_:'+attribute
        events = self.event_stream(
            query_string=query, query_dsl='',
            return_fields=return_fields)

        event_counter = 0
        for event in events:
            add_ioc = []
            ioc_field = event.source.get(store_as)
            if ioc_field and not isinstance(ioc_field, (list, tuple)):
                logger.warning('IOC field exist but not list type')
                continue
            if ioc_field:
                add_ioc = ioc_field
            attributes_fmt = []
            for attribute in attributes_list:
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
                attributes_fmt.append(attribute_value)
            for ioc in ioc_db:
                try:
                    expression_tmp = expression_string.replace('$value$', ioc)
                    expression = re.compile(expression_tmp, flags=re_flag)
                except re.error as exception:
                    # pylint: disable=logging-format-interpolation
                    logger.warning((
                        'Regular expression failed to compile, with '
                        'error: {0!s}').format(exception))
                    return ''
                for attribute in attributes_fmt:
                    if expression.match(attribute):
                        if ioc not in add_ioc:
                            add_ioc.append(ioc)
                        break
            if add_ioc:
                event_counter += 1
                event.add_attributes({store_as: add_ioc})
                event.add_tags(tags)

                # Commit the event to the datastore.
                event.commit()

        return 'IOC extraction [{0:s}] extracted {1:d} ioc.'.format(
            name, event_counter)


manager.AnalysisManager.register_analyzer(IOCExtractionSketchPlugin)
