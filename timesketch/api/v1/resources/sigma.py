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
"""Sigma resources for version 1 of the Timesketch API."""

from flask import abort
from flask_restful import Resource
from flask_restful import reqparse
from flask_login import login_required
from flask_login import current_user
from flask import jsonify
from flask import current_app

import six
import os
import codecs
import yaml

from timesketch.api.v1 import resources
from timesketch.lib.definitions import HTTP_STATUS_CODE_OK
from timesketch.lib.definitions import HTTP_STATUS_CODE_CREATED
from timesketch.lib.definitions import HTTP_STATUS_CODE_BAD_REQUEST
from timesketch.lib.definitions import HTTP_STATUS_CODE_FORBIDDEN
from timesketch.lib.definitions import HTTP_STATUS_CODE_NOT_FOUND

from sigma.backends import elasticsearch as sigma_elasticsearch
import sigma.configuration as sigma_configuration
from sigma.parser import collection as sigma_collection


# TODO maybe do that moving forward and move code from here to the model
#from timesketch.models.sigma import Sigma
from timesketch.lib.analyzers import interface

import logging

logger = logging.getLogger('timesketch.api.sigma')

class SigmaListResource(resources.ResourceMixin, Resource):
    """Resource to get list of users."""

    @login_required
    def get(self):
        """Handles GET request to the resource.

        Returns:
            Dict of sigma rules
        """
        sigma_rules = []
        
        # TODO: that should be part of the Timesketch config.
        try:
            _CONFIG_FILE = current_app.config['SIGMA_CONFIG']
        except KeyError:
            logger.error("SIGMA_CONFIG not found in config file")
            _CONFIG_FILE = '../../../../data/sigma_config.yaml'

        # Path to the directory containing the Sigma Rules to run, relative to
        # this file.
        # TODO check if get is better for getting the key errors
        try:
            _RULES_PATH = current_app.config['SIGMA_RULES_FOLDER']
        except KeyError:
            logger.error("SIGMA_RULES_FOLDER not found in config file")
            _RULES_PATH = '../../../../data/sigma/rules/'

        sigma_config_path = os.path.join(os.path.dirname(__file__), _CONFIG_FILE)

        with open(sigma_config_path, 'r') as sigma_config_file:
            sigma_config_file = sigma_config_file.read()
        sigma_config = sigma_configuration.SigmaConfiguration(sigma_config_file)
    
        sigma_backend = sigma_elasticsearch.ElasticsearchQuerystringBackend(
            sigma_config, {})
        
        rules_path = os.path.join(os.path.dirname(__file__), _RULES_PATH)


        for dirpath, dirnames, files in os.walk(rules_path):

            if 'deprecated' in dirnames:
                dirnames.remove('deprecated')

            for rule_filename in files:
                if rule_filename.lower().endswith('yml'):
                    print(rule_filename)
                    # if a sub dir is found, append it to be scanned for rules
                    if os.path.isdir(os.path.join(rules_path, rule_filename)):
                        logger.error(
                            'this is a directory, skipping: {0:s}'.format(
                                rule_filename))
                        continue

                    tag_name, _ = rule_filename.rsplit('.')
                    rule_file_path = os.path.join(dirpath, rule_filename)
                    rule_file_path = os.path.abspath(rule_file_path)

                    with codecs.open(rule_file_path, 'r', encoding='utf-8',errors='replace') as rule_file:
                                try:
                                    rule_file_content = rule_file.read()
                                    rule_yaml_data =yaml.safe_load(rule_file_content)
                                    sigma_rules.append(rule_yaml_data)
                                except NotImplementedError as exception:
                                    logger.error(
                                        'Error generating rule in file {0:s}: {1!s}'
                                        .format(rule_file_path, exception))
                                    continue
        
        # TODO: is that actually needed?
        meta = {'current_user': current_user.username}
        return jsonify({'objects': sigma_rules, 'meta': meta})


class SigmaResource(resources.ResourceMixin, Resource):
    """Resource to get a Sigma rule."""

    def __init__(self):
    
        super(SigmaResource, self).__init__()
        

    @login_required
    def get(self, rule_uuid):
        """Handles GET request to the resource.

        Returns:
            JSON sigma rule
        """

        logger.info(rule_uuid)

        # TODO: that should be part of the Timesketch config.
        try:
            _CONFIG_FILE = current_app.config['SIGMA_CONFIG']
        except KeyError:
            logger.error("SIGMA_CONFIG not found in config file")
            _CONFIG_FILE = '../../../../data/sigma_config.yaml'

        # Path to the directory containing the Sigma Rules to run, relative to
        # this file.
        # TODO check if get is better for getting the key errors
        try:
            _RULES_PATH = current_app.config['SIGMA_RULES_FOLDER']
        except KeyError:
            logger.error("SIGMA_RULES_FOLDER not found in config file")
            _RULES_PATH = '../../../../data/sigma/rules/'

        sigma_config_path = os.path.join(os.path.dirname(__file__), _CONFIG_FILE)

        with open(sigma_config_path, 'r') as sigma_config_file:
            sigma_config_file = sigma_config_file.read()
        sigma_config = sigma_configuration.SigmaConfiguration(sigma_config_file)
    
        sigma_backend = sigma_elasticsearch.ElasticsearchQuerystringBackend(sigma_config, {})
        
        rules_path = os.path.join(os.path.dirname(__file__), _RULES_PATH)

        return_value = None

        for dirpath, dirnames, files in os.walk(rules_path):

            if 'deprecated' in dirnames:
                dirnames.remove('deprecated')

            for rule_filename in files:
                if rule_filename.lower().endswith('yml'):
                    print(rule_filename)
                    # if a sub dir is found, append it to be scanned for rules
                    if os.path.isdir(os.path.join(rules_path, rule_filename)):
                        logger.error(
                            'this is a directory, skipping: {0:s}'.format(
                                rule_filename))
                        continue

                    tag_name, _ = rule_filename.rsplit('.')
                    rule_file_path = os.path.join(dirpath, rule_filename)
                    rule_file_path = os.path.abspath(rule_file_path)

                    with codecs.open(rule_file_path, 'r', encoding='utf-8',errors='replace') as rule_file:
                        try:
                            rule_file_content = rule_file.read()
                            rule_yaml_data = yaml.safe_load(rule_file_content)

                            parser = sigma_collection.SigmaCollectionParser(
                                rule_file_content, sigma_config, None)
                            parsed_sigma_rules = parser.generate(sigma_backend)

                            # parse the rule
                            sigma_rule_value = ''
                            for sigma_rule in parsed_sigma_rules:
                                logger.info(
                                    '[sigma] Generated query {0:s}'
                                    .format(sigma_rule))
                                sigma_rule_value = sigma_rule
                            
                            if rule_uuid == rule_yaml_data['id']:
                                return_value = rule_yaml_data
                                return_value.update({"es_query":sigma_rule_value})
                                return_value.update({"file_name":tag_name})
                                logger.info("found the right rule")
                                return return_value
                        
                        except NotImplementedError as exception:
                            logger.error(
                                'Error generating rule in file {0:s}: {1!s}'
                                .format(rule_file_path, exception))
                            continue
            abort(
                HTTP_STATUS_CODE_NOT_FOUND,
                'No sigma rule found withcool  this ID.')

        
