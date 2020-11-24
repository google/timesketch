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

import os
import codecs
import yaml
import sigma.configuration as sigma_configuration
import timesketch.lib.sigma as ts_sigma_lib

from flask import abort
from flask import jsonify
from flask import current_app
from flask_restful import Resource
from flask_restful import reqparse
from flask_login import login_required
from flask_login import current_user


from timesketch.api.v1 import resources
from timesketch.lib.definitions import HTTP_STATUS_CODE_OK
from timesketch.lib.definitions import HTTP_STATUS_CODE_CREATED
from timesketch.lib.definitions import HTTP_STATUS_CODE_BAD_REQUEST
from timesketch.lib.definitions import HTTP_STATUS_CODE_FORBIDDEN
from timesketch.lib.definitions import HTTP_STATUS_CODE_NOT_FOUND

from sigma.backends import elasticsearch as sigma_elasticsearch
from sigma.parser import collection as sigma_collection

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

        try:
            _RULES_PATH = ts_sigma_lib.get_sigma_rules_path()

        except ValueError as err:
            logger.error("OS error: {0}".format(err))
            abort(
                HTTP_STATUS_CODE_NOT_FOUND,
                err)

        sigma_rules = ts_sigma_lib.get_sigma_rules_for_folder(_RULES_PATH)
        meta = {'current_user': current_user.username, 'rules_count': len(sigma_rules)}
        return jsonify({'objects': sigma_rules, 'meta': meta})


class SigmaResource(resources.ResourceMixin, Resource):
    """Resource to get a Sigma rule."""

    def __init__(self):

        super().__init__()

    @login_required
    def get(self, rule_uuid):
        """Handles GET request to the resource.

        Returns:
            JSON sigma rule
        """

        try:
            sigma_config = ts_sigma_lib.get_sigma_config_file()
            sigma_backend = sigma_elasticsearch.ElasticsearchQuerystringBackend(sigma_config, {})
            _RULES_PATH = ts_sigma_lib.get_sigma_rules_path()

        except ValueError as err:
            logger.error("OS error: {0}".format(err))
            abort(
                HTTP_STATUS_CODE_NOT_FOUND,
                err)

        sigma_rules = ts_sigma_lib.get_sigma_rules_for_folder(_RULES_PATH)

        for rule in sigma_rules:
            logger.info(rule)
            if rule_uuid == rule['id']:
                logger.info("found the right rule")
                return rule
        
        abort(
                HTTP_STATUS_CODE_NOT_FOUND,
                'No sigma rule found withcool this ID.')
