# Copyright 2020 Google Inc. All rights reserved.
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
"""Timesketch Sigma lib functions."""

import re
import os
import codecs
import csv
import logging
from datetime import datetime
import yaml
import pandas as pd

from flask import current_app

import sigma.configuration as sigma_configuration

from sigma.backends import elasticsearch as sigma_es
from sigma.parser import collection as sigma_collection
from sigma.parser import exceptions as sigma_exceptions
from sigma.config.exceptions import SigmaConfigParseError


logger = logging.getLogger('timesketch.lib.sigma')


def get_sigma_config_file(config_file=None):
    """Get a sigma.configuration.SigmaConfiguration object.

    Args:
        config_file: Optional path to a config file
    Returns:
        A sigma.configuration.SigmaConfiguration object
    Raises:
        ValueError: If SIGMA_CONFIG is not found in the config file.
            or the Sigma config file is not readabale.
        SigmaConfigParseError: If config file could not be parsed.
    """
    if config_file:
        config_file_path = config_file
    else:
        config_file_path = current_app.config.get(
            'SIGMA_CONFIG', './data/sigma_config.yaml'
        )

    if not config_file_path:
        raise ValueError('No config_file_path set via param or config file')

    if not os.path.isfile(config_file_path):
        raise ValueError(
            'Unable to open: [{0:s}], does not exist.'.format(config_file_path)
        )

    if not os.access(config_file_path, os.R_OK):
        raise ValueError(
            'Unable to open file: [{0:s}], cannot open it for '
            'read, please check permissions.'.format(config_file_path)
        )

    with open(config_file_path, 'r', encoding='utf-8') as config_file_read:
        sigma_config_file = config_file_read.read()

    try:
        sigma_config = sigma_configuration.SigmaConfiguration(
            sigma_config_file
        )
    except SigmaConfigParseError:
        logger.error('Parsing error with {0:s}'.format(sigma_config_file))
        raise

    return sigma_config


def get_sigma_rules_path():
    """Get Sigma rules paths.

    Returns:
        A list of strings to the Sigma rules

    Raises:
        ValueError: If SIGMA_RULES_FOLDERS is not found in the config file.
            or the folders are not readabale.
    """
    try:
        rules_path = current_app.config.get('SIGMA_RULES_FOLDERS', [])
    except RuntimeError as e:
        raise ValueError('SIGMA_RULES_FOLDERS not found in config file') from e

    if not rules_path:
        raise ValueError('SIGMA_RULES_FOLDERS not found in config file')

    for folder in rules_path:
        if not os.path.isdir(folder):
            raise ValueError(
                'Unable to open dir: [{0:s}], it does not exist.'.format(
                    folder
                )
            )

        if not os.access(folder, os.R_OK):
            raise ValueError(
                'Unable to open dir: [{0:s}], cannot open it for '
                'read, please check permissions.'.format(folder)
            )

    return rules_path


def get_sigma_rules(rule_folder, sigma_config=None):
    """Returns the Sigma rules for a folder including subfolders.
    Args:
        rule_folder: folder to be checked for rules
        sigma_config: optional argument to pass a
                sigma.configuration.SigmaConfiguration object
    Returns:
        A array of Sigma rules as JSON
    Raises:
        ValueError: If SIGMA_RULES_FOLDERS is not found in the config file.
            or the folders are not readabale.
    """
    return_array = []

    blocklist_path = None
    ignore = get_sigma_blocklist(blocklist_path)
    ignore_list = list(ignore['path'].unique())

    for dirpath, dirnames, files in os.walk(rule_folder):
        if 'deprecated' in [x.lower() for x in dirnames]:
            dirnames.remove('deprecated')

        for rule_filename in files:
            if rule_filename.lower().endswith('.yml'):
                # if a sub dir is found, do not try to parse it.
                if os.path.isdir(os.path.join(dirpath, rule_filename)):
                    continue

                rule_file_path = os.path.join(dirpath, rule_filename)

                if any(x in rule_file_path for x in ignore_list):
                    continue

                parsed_rule = get_sigma_rule(rule_file_path, sigma_config)
                if parsed_rule:
                    return_array.append(parsed_rule)
    return return_array


def get_all_sigma_rules():
    """Returns all Sigma rules

    Returns:
        A array of Sigma rules

    Raises:
        ValueError: If SIGMA_RULES_FOLDERS is not found in the config file.
            or the folders are not readabale.
    """
    sigma_rules = []

    rules_paths = get_sigma_rules_path()

    for folder in rules_paths:
        sigma_rules.extend(get_sigma_rules(folder))

    return sigma_rules


def get_sigma_rule(filepath, sigma_config=None):
    """Returns a JSON represenation for a rule
    Args:
        filepath: path to the sigma rule to be parsed
        sigma_config: optional argument to pass a
                sigma.configuration.SigmaConfiguration object
    Returns:
        Json representation of the parsed rule
    Raises:
        ValueError: Parsing error
        IsADirectoryError: If a directory is passed as filepath
    """
    try:
        if isinstance(sigma_config, sigma_configuration.SigmaConfiguration):
            sigma_conf_obj = sigma_config
        elif isinstance(sigma_config, str):
            sigma_conf_obj = get_sigma_config_file(sigma_config)
        else:
            sigma_conf_obj = get_sigma_config_file()
    except ValueError as e:
        logger.error('Problem reading the Sigma config', exc_info=True)
        raise ValueError('Problem reading the Sigma config') from e

    sigma_backend = sigma_es.ElasticsearchQuerystringBackend(
        sigma_conf_obj, {}
    )

    try:
        sigma_rules_paths = get_sigma_rules_path()
    except ValueError:
        sigma_rules_paths = None

    if not filepath.lower().endswith('.yml'):
        raise ValueError(f'{filepath} does not end with .yml')

    # if a sub dir is found, nothing can be parsed
    if os.path.isdir(filepath):
        raise IsADirectoryError(f'{filepath} is a directory - must be a file')

    abs_path = os.path.abspath(filepath)

    with codecs.open(
        abs_path, 'r', encoding='utf-8', errors='replace'
    ) as file:
        try:
            rule_return = {}
            rule_yaml_data = yaml.safe_load_all(file.read())
            for doc in rule_yaml_data:
                rule_return.update(doc)
                parser = sigma_collection.SigmaCollectionParser(
                    yaml.safe_dump(doc), sigma_conf_obj, None
                )
                parsed_sigma_rules = parser.generate(sigma_backend)

        except NotImplementedError as exception:
            logger.error('Error rule {0:s}: {1!s}'.format(abs_path, exception))
            add_problematic_rule(
                filepath, doc.get('id'), 'Part of the rule not supported in TS'
            )
            return None

        except sigma_exceptions.SigmaParseError as exception:
            logger.error(
                'Sigma parsing error rule in file {0:s}: {1!s}'.format(
                    abs_path, exception
                )
            )
            add_problematic_rule(
                filepath, doc.get('id'), 'sigma_exceptions.SigmaParseError'
            )
            return None

        except yaml.parser.ParserError as exception:
            logger.error(
                'Yaml parsing error rule in file {0:s}: {1!s}'.format(
                    abs_path, exception
                )
            )
            add_problematic_rule(filepath, None, 'yaml.parser.ParserError')
            return None

        sigma_es_query = ''

        for sigma_rule in parsed_sigma_rules:

            sigma_es_query = _sanitize_query(sigma_rule)

        rule_return.update({'es_query': sigma_es_query})
        rule_return.update({'file_name': os.path.basename(filepath)})

        # in case multiple folders are in the config, need to remove them
        if sigma_rules_paths:
            for rule_path in sigma_rules_paths:
                file_relpath = os.path.relpath(filepath, rule_path)
        else:
            file_relpath = 'N/A'

        rule_return.update({'file_relpath': file_relpath})

        return rule_return


def _sanitize_query(sigma_rule_query: str) -> str:
    """Returns a sanitized query
    Args:
        sigma_rule_query: path to the sigma rule to be parsed
    Returns:
        String of a cleaned string
    """
    # TODO: Investigate how to handle .keyword
    # fields in Sigma.
    # https://github.com/google/timesketch/issues/1199#issuecomment-639475885

    sigma_rule_query = sigma_rule_query.replace('.keyword:', ':')
    sigma_rule_query = sigma_rule_query.replace('\\ ', ' ')
    sigma_rule_query = sigma_rule_query.replace('\\:', ':')
    sigma_rule_query = sigma_rule_query.replace('\\-', '-')
    sigma_rule_query = sigma_rule_query.replace('*\\\\', ' *')
    sigma_rule_query = sigma_rule_query.replace('::', r'\:\:')

    # TODO: Improve the whitespace handling
    # https://github.com/google/timesketch/issues/2007
    # check if there is a ' * '
    # if one is found split it up into elements seperated by space
    # and go backwards to the next star

    sigma_rule_query = sigma_rule_query.replace(' * OR', ' " OR')
    sigma_rule_query = sigma_rule_query.replace(' * AND', ' " AND')
    sigma_rule_query = sigma_rule_query.replace('OR * ', 'OR " ')
    sigma_rule_query = sigma_rule_query.replace('AND * ', 'AND " ')
    sigma_rule_query = sigma_rule_query.replace('(* ', '(" ')
    sigma_rule_query = sigma_rule_query.replace(' *)', ' ")')
    sigma_rule_query = sigma_rule_query.replace('*)', '")')
    sigma_rule_query = sigma_rule_query.replace('(*', '("')
    sigma_rule_query = sigma_rule_query.replace(
        r'\*:', ''
    )  # removes wildcard at the beginning of a rule es_query

    elements = re.split(r'\s+', sigma_rule_query)
    san = []
    for el in elements:
        if el.count('*') == 1:
            # indicates a string that had a space before with only one star
            san.append(el.replace('*', '"'))
        else:
            san.append(el)

    sigma_rule_query = ' '.join(san)

    # above method might create strings that have '' in them, workaround:
    sigma_rule_query = sigma_rule_query.replace('""', '"')

    return sigma_rule_query


def get_sigma_blocklist(blocklist_path=None):
    """Get a dataframe of sigma rules to ignore.

    This includes filenames, paths, ids.

    Args:
        blocklist_path(str): Path to a blocklist file.
            The default value is None

    Returns:
        Pandas dataframe with blocklist

    Raises:
        ValueError: Sigma blocklist file is not readabale.
    """

    return pd.read_csv(get_sigma_blocklist_path(blocklist_path))


def get_sigma_blocklist_path(blocklist_path=None):
    """Checks and returns the Sigma blocklist path.

    This includes filenames, paths, ids.

    Args:
        blocklist_path(str): Path to a blocklist file.
            The default value is './data/sigma_blocklist.csv'

    Returns:
        Sigma Blocklist path

    Raises:
        ValueError: Sigma blocklist file is not readabale.
    """
    logger.error(blocklist_path)

    if not blocklist_path or blocklist_path == '':
        blocklist_path = current_app.config.get(
            'SIGMA_BLOCKLIST_CSV', './data/sigma_blocklist.csv'
        )
    if not blocklist_path:
        raise ValueError('No blocklist_file_path set via param or config file')

    if not os.path.isfile(blocklist_path):
        raise ValueError(
            'Unable to open file: [{0:s}] does not exist'.format(
                blocklist_path
            )
        )

    if not os.access(blocklist_path, os.R_OK):
        raise ValueError(
            'Unable to open file: [{0:s}], cannot open it for '
            'read, please check permissions.'.format(blocklist_path)
        )

    return blocklist_path


def add_problematic_rule(filepath, rule_uuid=None, reason=None):
    """Adds a problematic rule to the blocklist.csv.

    Args:
        filepath: path to the sigma rule that caused problems
        rule_uuid: rule uuid
        reason: optional reason why file is moved
    """
    blocklist_file_path = get_sigma_blocklist_path()

    # we only want to store the relative paths in the blocklist file

    try:
        sigma_rules_paths = get_sigma_rules_path()
    except ValueError:
        sigma_rules_paths = None

    if sigma_rules_paths:
        for rule_path in sigma_rules_paths:
            file_relpath = os.path.relpath(filepath, rule_path)

    # path,bad,reason,last_ckecked,rule_id
    fields = [
        file_relpath,
        'bad',
        reason,
        datetime.now().strftime('%Y-%m-%d'),
        rule_uuid,
    ]

    with open(blocklist_file_path, 'a', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(fields)


def get_sigma_rule_by_text(rule_text, sigma_config=None):
    """Returns a JSON represenation for a rule

    Args:
        rule_text: Text of the sigma rule to be parsed
        sigma_config: config file object

    Returns:
        Json representation of the parsed rule
    Raises:
        sigma_exceptions.SigmaParseError: Issue with parsing the given rule
        yaml.parser.ParserError: Not a correct YAML text provided
        NotImplementedError: A feature in the provided Sigma rule is not
            implemented in Sigma for Timesketch
    """

    try:
        if isinstance(sigma_config, sigma_configuration.SigmaConfiguration):
            sigma_conf_obj = sigma_config
        elif isinstance(sigma_config, str):
            sigma_conf_obj = get_sigma_config_file(sigma_config)
        else:
            sigma_conf_obj = get_sigma_config_file()
    except ValueError as e:
        logger.error('Problem reading the Sigma config', exc_info=True)
        raise ValueError('Problem reading the Sigma config') from e

    sigma_backend = sigma_es.ElasticsearchQuerystringBackend(
        sigma_conf_obj, {}
    )

    rule_return = {}
    # TODO check if input validation is needed / useful.
    try:
        rule_yaml_data = yaml.safe_load_all(rule_text)

        for doc in rule_yaml_data:

            parser = sigma_collection.SigmaCollectionParser(
                str(doc), sigma_conf_obj, None
            )
            parsed_sigma_rules = parser.generate(sigma_backend)
            rule_return.update(doc)

    except NotImplementedError as exception:
        logger.error('Error generating rule {0!s}'.format(exception))
        raise

    except sigma_exceptions.SigmaParseError as exception:
        logger.error('Sigma parsing error rule {0!s}'.format(exception))
        raise

    except yaml.parser.ParserError as exception:
        logger.error('Yaml parsing error rule {0!s}'.format(exception))
        raise

    sigma_es_query = ''

    for sigma_rule in parsed_sigma_rules:
        sigma_es_query = _sanitize_query(sigma_rule)

    rule_return.update({'es_query': sigma_es_query})
    rule_return.update({'file_name': 'N/A'})
    rule_return.update({'file_relpath': 'N/A'})
    return rule_return
