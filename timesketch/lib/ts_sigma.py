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
"""Timesketch Sigma lib functions.
"""

import os
import codecs
import logging
import yaml

import sigma.configuration as sigma_configuration

from sigma.backends import elasticsearch as sigma_es
from sigma.parser import collection as sigma_collection

from flask import current_app

logger = logging.getLogger('timesketch.lib.sigma')


def get_sigma_config_file():
    """Get a sigma.configuration.SigmaConfiguration object.

        Args:
            None

        Returns:
            A sigma.configuration.SigmaConfiguration object
    """
    _CONFIG_FILE = current_app.config.get('SIGMA_CONFIG')

    if not _CONFIG_FILE:
        raise ValueError(
            'SIGMA_CONFIG not found in config file')

    if not os.path.isfile(_CONFIG_FILE):
        raise ValueError(
            'Unable to open file: [{0:s}], it does not exist.'.format(
                _CONFIG_FILE))

    if not os.access(_CONFIG_FILE, os.R_OK):
        raise ValueError(
            'Unable to open file: [{0:s}], cannot open it for '
            'read, please check permissions.'.format(_CONFIG_FILE))

    with open(_CONFIG_FILE, 'r') as config_file:
        sigma_config_file = config_file.read()

    sigma_config = sigma_configuration.SigmaConfiguration(sigma_config_file)

    return sigma_config

def get_sigma_rules_path():
    """Get the path for Sigma rules.

        Args:
            None

        Returns:
            A string
    """

    # TODO: Add functionality to have multiple paths for rule files.
    _RULES_PATH = current_app.config.get('SIGMA_RULES_FOLDER')

    if not _RULES_PATH:
        raise ValueError(
            'SIGMA_RULES_FOLDER not found in config file')

    if not os.path.isdir(_RULES_PATH):
        raise ValueError(
            'Unable to open dir: [{0:s}], it does not exist.'.format(
                _RULES_PATH))

    if not os.access(_RULES_PATH, os.R_OK):
        raise ValueError(
            'Unable to open dir: [{0:s}], cannot open it for '
            'read, please check permissions.'.format(_RULES_PATH))

    return _RULES_PATH


def get_sigma_rules(rule_folder):

    return_array = []

    for dirpath, dirnames, files in os.walk(rule_folder):
        # TODO: lowercase the folder name in case a folder is named dePreCatEd
        if 'deprecated' in dirnames:
            dirnames.remove('deprecated')

        for rule_filename in files:
            if rule_filename.lower().endswith('yml'):
                # if a sub dir is found, append it to be scanned for rules
                if os.path.isdir(os.path.join(dirpath, rule_filename)):
                    logger.info(
                        'this is a directory, skipping: {0:s}'.format(
                            rule_filename))
                    continue

                rule_file_path = os.path.join(dirpath, rule_filename)
                parsed_rule = get_sigma_rule(rule_file_path)
                return_array.append(parsed_rule)

    return return_array


def get_sigma_rule(filepath):
    """ Returns a JSON represenation for a rule

        Args:
            filepath: path to the sigma rule to be parsed

        Returns:
            Json representation of the parsed rule
        """


    logger.info("get_sigma_rule with arg: {0:s}".format(filepath))
    sigma_config = get_sigma_config_file()

    sigma_backend = sigma_es.ElasticsearchQuerystringBackend(sigma_config, {})

    if filepath.lower().endswith('yml'):
        # if a sub dir is found, append it to be scanned for rules
        if os.path.isdir(filepath):
            logger.info(
                'this is a directory, skipping: {0:s}'.format(
                    filepath))
            return False

        tag_name, _ = filepath.rsplit('.')
        abs_path = os.path.abspath(filepath)

        with codecs.open(
                abs_path, 'r', encoding='utf-8', errors='replace') as file:

            try:
                rule_file_content = file.read()
                # TODO the safe load still has problems with --- in a rule file
                rule_yaml_data = yaml.safe_load(rule_file_content)

                parser = sigma_collection.SigmaCollectionParser(
                    rule_file_content, sigma_config, None)
                parsed_sigma_rules = parser.generate(sigma_backend)

                sigma_es_query = ''
                for sigma_rule in parsed_sigma_rules:
                    logger.info(
                        '[sigma] Generated query {0:s}'
                        .format(sigma_rule))
                    sigma_es_query = sigma_rule

                rule_yaml_data.update(
                    {"es_query":sigma_es_query})
                rule_yaml_data.update(
                    {"file_name":tag_name})

                return rule_yaml_data

            except NotImplementedError as exception:
                logger.error(
                    'Error generating rule in file {0:s}: {1!s}'
                    .format(abs_path, exception))

    return None
