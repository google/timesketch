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

import os
import codecs
import logging
import yaml

from flask import current_app

import sigma.configuration as sigma_configuration

from sigma.backends import elasticsearch as sigma_es
from sigma.parser import collection as sigma_collection
from sigma.parser import exceptions as sigma_exceptions

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
    """
    if config_file:
        config_file_path = config_file
    else:
        config_file_path = current_app.config.get('SIGMA_CONFIG')

    if not config_file_path:
        raise ValueError('No config_file_path set via param or config file')

    if not os.path.isfile(config_file_path):
        raise ValueError(
            'Unable to open file: [{0:s}], it does not exist.'.format(
                config_file_path))

    if not os.access(config_file_path, os.R_OK):
        raise ValueError(
            'Unable to open file: [{0:s}], cannot open it for '
            'read, please check permissions.'.format(config_file_path))

    with open(config_file_path, 'r') as config_file_read:
        sigma_config_file = config_file_read.read()

    sigma_config = sigma_configuration.SigmaConfiguration(sigma_config_file)

    if not sigma_config:
        raise ValueError(
            'sigma_config is none - Error')

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
        raise ValueError(
            'SIGMA_RULES_FOLDERS not found in config file') from e

    if not rules_path:
        raise ValueError(
            'SIGMA_RULES_FOLDERS not found in config file')

    for folder in rules_path:
        if not os.path.isdir(folder):
            raise ValueError(
                'Unable to open dir: [{0:s}], it does not exist.'.format(
                    folder))

        if not os.access(folder, os.R_OK):
            raise ValueError(
                'Unable to open dir: [{0:s}], cannot open it for '
                'read, please check permissions.'.format(folder))

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

    for dirpath, dirnames, files in os.walk(rule_folder):
        if 'deprecated' in [x.lower() for x in dirnames]:
            dirnames.remove('deprecated')

        for rule_filename in files:
            if rule_filename.lower().endswith('.yml'):
                # if a sub dir is found, do not try to parse it.
                if os.path.isdir(os.path.join(dirpath, rule_filename)):
                    continue

                rule_file_path = os.path.join(dirpath, rule_filename)
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
    """ Returns a JSON represenation for a rule
    Args:
        filepath: path to the sigma rule to be parsed
        sigma_config: optional argument to pass a
                sigma.configuration.SigmaConfiguration object
    Returns:
        Json representation of the parsed rule
    """
    try:
        if sigma_config:
            sigma_conf_obj = sigma_config
        else:
            sigma_conf_obj = get_sigma_config_file()
    except ValueError as e:
        logger.error(
            'Problem reading the Sigma config {0:s}: '
            .format(e), exc_info=True)
        return None

    sigma_backend = sigma_es.ElasticsearchQuerystringBackend(sigma_conf_obj, {})

    try:
        sigma_rules_paths = get_sigma_rules_path()
    except ValueError:
        sigma_rules_paths = None

    if not filepath.lower().endswith('.yml'):
        return None

    # if a sub dir is found, nothing can be parsed
    if os.path.isdir(filepath):
        return None

    try:
        sigma_rules_paths = get_sigma_rules_path()
    except ValueError:
        sigma_rules_paths = None

    if not filepath.lower().endswith('.yml'):
        return None

    # if a sub dir is found, nothing can be parsed
    if os.path.isdir(filepath):
        return None

    abs_path = os.path.abspath(filepath)

    with codecs.open(
            abs_path, 'r', encoding='utf-8', errors='replace') as file:
        try:
            rule_return = {}
            rule_yaml_data = yaml.safe_load_all(file.read())
            for doc in rule_yaml_data:
                rule_return.update(doc)
                parser = sigma_collection.SigmaCollectionParser(
                    str(doc), sigma_config, None)
                parsed_sigma_rules = parser.generate(sigma_backend)

        except NotImplementedError as exception:
            logger.error(
                'Error generating rule in file {0:s}: {1!s}'
                .format(abs_path, exception))
            return None

        except sigma_exceptions.SigmaParseError as exception:
            logger.error(
                'Sigma parsing error generating rule in file {0:s}: {1!s}'
                .format(abs_path, exception))
            return None

        except yaml.parser.ParserError as exception:
            logger.error(
                'Yaml parsing error generating rule in file {0:s}: {1!s}'
                .format(abs_path, exception))
            return None

        sigma_es_query = ''

        for sigma_rule in parsed_sigma_rules:
            sigma_es_query = sigma_rule

        rule_return.update(
            {'es_query':sigma_es_query})
        rule_return.update(
            {'file_name':os.path.basename(filepath)})

        # in case multiple folders are in the config, need to remove them
        if sigma_rules_paths:
            for rule_path in sigma_rules_paths:
                file_relpath = os.path.relpath(filepath, rule_path)
        else:
            file_relpath = 'N/A'

        rule_return.update(
            {'file_relpath':file_relpath})

        return rule_return

def get_sigma_rule_by_text(rule_text, sigma_config=None):
    """ Returns a JSON represenation for a rule

    Args:
        rule_text: Text of the sigma rule to be parsed
        sigma_config: config file object

    Returns:
        Json representation of the parsed rule
    """
    if sigma_config is None:
        sigma_config = get_sigma_config_file()

    sigma_backend = sigma_es.ElasticsearchQuerystringBackend(sigma_config, {})

    rule_return = {}

    try:
        parser = sigma_collection.SigmaCollectionParser(
                        rule_text, sigma_config, None)
        parsed_sigma_rules = parser.generate(sigma_backend)
        rule_yaml_data = yaml.safe_load_all(rule_text)
        for doc in rule_yaml_data:
            rule_return.update(doc)

    except NotImplementedError as exception:
        logger.error(
            'Error generating rule in file {0!s}'
            .format(exception))
        return None

    except sigma_exceptions.SigmaParseError as exception:
        logger.error(
            'Sigma parsing error generating rule {0!s}'
            .format(exception))
        return None

    except yaml.parser.ParserError as exception:
        logger.error(
            'Yaml parsing error generating rule in {0!s}'
            .format(exception))
        return None

    sigma_es_query = ''

    for sigma_rule in parsed_sigma_rules:
        sigma_es_query = sigma_rule

    rule_return.update(
        {'es_query':sigma_es_query})
    rule_return.update(
        {'file_name':'N/A'})

    rule_return.update(
        {'file_relpath':'N/A'})

    return rule_return
