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
import yaml

from flask import abort
from flask import jsonify
from flask import request
from flask_restful import Resource
from flask_login import login_required
from flask_login import current_user

from sigma.parser import exceptions as sigma_exceptions

import timesketch.lib.sigma_util as ts_sigma_lib

from timesketch.api.v1 import resources
from timesketch.lib.definitions import HTTP_STATUS_CODE_NOT_FOUND
from timesketch.lib.definitions import HTTP_STATUS_CODE_BAD_REQUEST

logger = logging.getLogger('timesketch.api.sigma')


class SigmaListResource(resources.ResourceMixin, Resource):
    """Resource to get list of Sigma rules."""

    @login_required
    def get(self):
        """Handles GET request to the resource.

        Returns:
            Dict of sigma rules
        """
        sigma_rules = []

        try:
            sigma_rules = ts_sigma_lib.get_all_sigma_rules()

        except ValueError as e:
            logger.error('OS Error, unable to get the path to the Sigma rules',
                         exc_info=True)
            abort(
                HTTP_STATUS_CODE_NOT_FOUND,
                f'Value Error, {e}')
        # TODO: idea for meta: add a list of folders that have been parsed
        meta = {'current_user': current_user.username,
                'rules_count': len(sigma_rules)}
        return jsonify({'objects': sigma_rules, 'meta': meta})


class SigmaResource(resources.ResourceMixin, Resource):
    """Resource to get a Sigma rule."""

    @login_required
    def get(self, rule_uuid):
        """Handles GET request to the resource.

        Args:
            rule_uuid: uuid of the sigma rule

        Returns:
            JSON sigma rule
        """
        return_rule = None
        try:
            sigma_rules = ts_sigma_lib.get_all_sigma_rules()

        except ValueError as e:
            logger.error('OS Error, unable to get the path to the Sigma rules',
                         exc_info=True)
            abort(
                HTTP_STATUS_CODE_NOT_FOUND,
                f'ValueError {e}')
        for rule in sigma_rules:
            if rule is not None:
                if rule_uuid == rule.get('id'):
                    return_rule = rule

        if return_rule is None:
            abort(
                HTTP_STATUS_CODE_NOT_FOUND, 'No sigma rule found with this ID.')

        meta = {'current_user': current_user.username,
                'rules_count': len(sigma_rules)}
        return jsonify({'objects': [return_rule], 'meta': meta})


class SigmaByTextResource(resources.ResourceMixin, Resource):
    """Resource to get a Sigma rule by text."""

    @login_required
    def post(self):
        """Handles POST request to the resource.

        Returns:
            JSON sigma rule
        """

        form = request.json
        if not form:
            form = request.data

        content = form.get('content')
        if not content:
            return abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                'Missing values from the request.')

        try:
            sigma_rule = ts_sigma_lib.get_sigma_rule_by_text(content)

        except ValueError:
            logger.error('Sigma Parsing error with the user provided rule',
                         exc_info=True)
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                'Error unable to parse the provided Sigma rule')

        except NotImplementedError as exception:
            logger.error(
                'Sigma Parsing error: Feature in the rule provided '
                ' is not implemented in this backend', exc_info=True)
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                'Error generating rule {0!s}'.format(exception))

        except sigma_exceptions.SigmaParseError as exception:
            logger.error(
                'Sigma Parsing error: unknown error', exc_info=True)
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                'Sigma parsing error generating rule  with error: {0!s}'.format(
                    exception))

        except yaml.parser.ParserError as exception:
            logger.error(
                'Sigma Parsing error: an invalid yml file has been provided',
                exc_info=True)
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                'Sigma parsing error: invalid yaml provided {0!s}'.format(
                    exception))

        if sigma_rule is None:
            abort(
                HTTP_STATUS_CODE_NOT_FOUND, 'No sigma was parsed')
        metadata = {'parsed': True}

        return jsonify({'objects': [sigma_rule], 'meta': metadata})
