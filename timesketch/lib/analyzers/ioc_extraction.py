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
        query, ret_fields, ioc_db = self.parse_config(config)
        if not query or not ret_fields:
            return 'Error to make query'
        if not ioc_db:
            return 'Error to parse config'
        logger.info((
            'Return field '
            'error: {0!s}').format(ret_fields))
        return self.extract_ioc(query, ret_fields, ioc_db)

    def parse_config(self, ioc_config):
        """Create IOC DB and make request

        Args:
            config: A dict that contains the configuration for the ioc
                extraction. See data/ioc.yaml for fields and further
                documentation of what needs to be defined.

        Returns:
            query: A string that contains elastic query to return
                events check ioc against.
            return_fields: A list that contains names of field to return
                from elastic request to check ioc against.
            ioc_db: A dict contains extracted config and IOC files
        """
        ioc_db = []
        query = ""
        return_fields = []
        list_fieldnames = self.get_fields_list()
        for name, config in iter(ioc_config.items()):
            elm = {'name': name, 'found': 0}
            path_file_ioc = config.get('path_file_ioc')
            if not path_file_ioc:
                logger.warning('No path for file IOC defined.')
                continue
            if not os.path.isfile(path_file_ioc):
                logger.warning('file IOC defined not exists.')
                return ''
            elm['ioc'] = None
            with open(path_file_ioc) as json_file:
                try:
                    elm['ioc'] = json.load(json_file)
                    if not isinstance(elm['ioc'], (list, tuple)):
                        continue
                    if not elm['ioc']:
                        continue
                except json.JSONDecodeError as exception:
                    logger.warning((
                        'File IOC error to parse: '
                        '{0!s}').format(exception))
                    continue
            elm['store_as'] = config.get('store_as')
            if not elm['store_as']:
                logger.warning('No attribute defined to store results in.')
                continue
            elm['attributes'] = config.get('attributes')
            attri_contains = config.get('attributes_contains')
            if attri_contains:
                for fn in list_fieldnames:
                    elm['attributes'] += [x for x in attri_contains if x in fn]
            elm['attributes'] = list(set(elm['attributes']))
            if not elm['attributes']:
                logger.warning('No attributes defined.')
                continue
            elm['tags'] = config.get('tags', [])
            elm['regexp'] = config.get(
                'match_re', '([^a-zA-Z0-9]|^)$value$([^a-zA-Z0-9]|$)')
            regexp_flags = config.get('re_flags')
            elm['re_flag'] = 0
            if regexp_flags:
                flags = set()
                for flag in regexp_flags:
                    try:
                        flags.add(getattr(re, flag))
                    except AttributeError:
                        logger.warning(
                            'Unknown regular expression flag defined.')
                        continue
                elm['re_flag'] = sum(flags)
            return_fields += elm['attributes'] + [elm['store_as']]
            ioc_db.append(elm)
            for attribute in elm['attributes']:
                if query:
                    query += ' AND '
                query += '_exists_:'+attribute
        return query, return_fields, ioc_db

    def extract_ioc(self, query, ret_fields, ioc_db):
        """Extract IOC from events.

        Args:
            query: A string that contains elastic query to return
                events check ioc against.
            return_fields: A list that contains names of field to return
                from elastic request to check ioc against.
            ioc_db: A dict contains extracted config and IOC files

        Returns:
            String with summary of the analyzer result.
        """
        events = self.event_stream(
            query_string=query, query_dsl='',
            return_fields=ret_fields)

        for event in events:
            value_store = {}
            tags_store = []
            attributes_fmt = {}
            for attribute in ret_fields:
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
                attributes_fmt[attribute] = attribute_value
            for elm in ioc_db:
                ioc_field = event.source.get(elm['store_as'])
                if ioc_field and not isinstance(ioc_field, (list, tuple)):
                    logger.warning('IOC field exist but not list type')
                    continue
                if ioc_field:
                    if elm['store_as'] in value_store:
                        value_store[elm['store_as']] += ioc_field
                    else:
                        value_store[elm['store_as']] = ioc_field
                elif not elm['store_as'] in value_store:
                    value_store[elm['store_as']] = []
                for ioc in elm['ioc']:
                    try:
                        regexp_tmp = elm['regexp'].replace(
                            '$value$', ioc)
                        regexp = re.compile(regexp_tmp, flags=elm['re_flag'])
                    except re.error as exception:
                        # pylint: disable=logging-format-interpolation
                        logger.warning((
                            'Regular expression failed to compile, with '
                            'error: {0!s}').format(exception))
                        continue
                    for attribute in elm['attributes']:
                        if not attribute in attributes_fmt:
                            continue
                        if regexp.match(attributes_fmt[attribute]):
                            tags_store += elm['tags']
                            elm['found'] += 1
                            if ioc not in value_store[elm['store_as']]:
                                value_store[elm['store_as']].append(ioc)
                            break
            if value_store:
                event.add_attributes(value_store)
                event.add_tags(list(set(tags_store)))
                # Commit the event to the datastore.
                event.commit()
        ret_string = 'IOC extraction'
        for elm in ioc_db:
            ret_string += ' [{0:s}] extracted {1:d} ioc.'.format(
                elm['name'], elm['found'])
        return ret_string

manager.AnalysisManager.register_analyzer(IOCExtractionSketchPlugin)
