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

import logging

from flask import abort
from flask import jsonify
from flask_restful import Resource
from flask_login import login_required
from flask_login import current_user

import timesketch.lib.ts_sigma as ts_sigma_lib

from timesketch.api.v1 import resources
from timesketch.lib.definitions import HTTP_STATUS_CODE_NOT_FOUND

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

        sigma_rules = ts_sigma_lib.get_sigma_rules(_RULES_PATH)
        meta = {'current_user': current_user.username,
                'rules_count': len(sigma_rules)}
        return jsonify({'objects': sigma_rules, 'meta': meta})


class SigmaResource(resources.ResourceMixin, Resource):
    """Resource to get a Sigma rule."""

    @login_required
    def get(self, rule_uuid):
        """Handles GET request to the resource.

        Returns:
            JSON sigma rule
        """

        return_rule = None

        try:
            _RULES_PATH = ts_sigma_lib.get_sigma_rules_path()

        except ValueError as err:
            logger.error("OS error: {0}".format(err))
            abort(
                HTTP_STATUS_CODE_NOT_FOUND,
                err)

        sigma_rules = ts_sigma_lib.get_sigma_rules(_RULES_PATH)

        for rule in sigma_rules:
            logger.info(rule)
            if rule_uuid == rule['id']:
                logger.info("found the right rule")
                return_rule = rule

        if return_rule = None:
            abort(
                HTTP_STATUS_CODE_NOT_FOUND, 'No sigma rule found with this ID.')

        else:
            return return_rule