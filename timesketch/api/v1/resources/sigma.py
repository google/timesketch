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
from timesketch.lib.definitions import HTTP_STATUS_CODE_CONFLICT
from timesketch.lib.definitions import HTTP_STATUS_CODE_CREATED
from timesketch.lib.definitions import HTTP_STATUS_CODE_FORBIDDEN


from timesketch.models import sigma
from timesketch.models.sigma import Sigma
from timesketch.models import db_session

from sqlalchemy.exc import IntegrityError


logger = logging.getLogger("timesketch.api.sigma")


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
            logger.error(
                "OS Error, unable to get the path to the Sigma rules",
                exc_info=True,
            )
            abort(HTTP_STATUS_CODE_NOT_FOUND, f"Value Error, {e}")
        # TODO: idea for meta: add a list of folders that have been parsed
        meta = {
            "current_user": current_user.username,
            "rules_count": len(sigma_rules),
        }
        return jsonify({"objects": sigma_rules, "meta": meta})


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
        try:
            rule = Sigma.query.filter_by(rule_uuid=rule_uuid).first()
        except Exception as e:
            logger.error(
                "Unable to get the Sigma rule",
                exc_info=True,
            )
            abort(HTTP_STATUS_CODE_NOT_FOUND, f"ValueError {e}")

        if not rule:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No rule found with this ID.")
        return_rules = []

        assert isinstance(rule, Sigma)
        # Return a subset of the sigma objects to reduce the amount of
        # data sent to the client.
        return_rules.append(
            {
                "rule_uuid": rule.rule_uuid,
                "title": rule.title,
                "description": rule.description,
                "created_at": str(rule.created_at),
                "query_string": rule.query_string,
                "rule_yaml": rule.rule_yaml,
                "status": rule.get_status.status,
            }
        )

        meta = {
            "current_user": current_user.username,
        }
        return jsonify({"objects": return_rules, "meta": meta})

    @login_required
    def get_old_from_disk_deprecated(self, rule_uuid):
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
            logger.error(
                "OS Error, unable to get the path to the Sigma rules",
                exc_info=True,
            )
            abort(HTTP_STATUS_CODE_NOT_FOUND, f"ValueError {e}")
        for rule in sigma_rules:
            if rule is not None:
                if rule_uuid == rule.get("id"):
                    return_rule = rule

        if return_rule is None:
            abort(
                HTTP_STATUS_CODE_NOT_FOUND, "No sigma rule found with this ID."
            )

        meta = {
            "current_user": current_user.username,
            "rules_count": len(sigma_rules),
        }
        return jsonify({"objects": [return_rule], "meta": meta})

    @login_required
    def post(self, rule_uuid):
        """Handles POST request to the resource.

        Returns:
            HTTP status code indicating whether operation was sucessful.
        """
        form = request.json
        if not form:
            form = request.data

        rule_uuid = form.get("rule_uuid")
        title = form.get("title", "")

        if not rule_uuid:
            abort(
                HTTP_STATUS_CODE_NOT_FOUND,
                "No rule_uuid supplied.",
            )

        if not isinstance(rule_uuid, str):
            abort(
                HTTP_STATUS_CODE_FORBIDDEN, "rule_uuid needs to be a string."
            )
        sigma_rule = Sigma(rule_uuid=rule_uuid, user=current_user, title=title)
        sigma_rule.description = form.get("description", "")
        sigma_rule.query_string = form.get("query_string", "")
        sigma_rule.rule_yaml = form.get("rule_yaml", "")
        try:
            db_session.add(sigma_rule)
            db_session.commit()
        except IntegrityError:
            abort(HTTP_STATUS_CODE_CONFLICT, "Rule already exist")

        if sigma_rule is None:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No sigma was parsed")

        return self.to_json(sigma_rule, status_code=HTTP_STATUS_CODE_CREATED)


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

        content = form.get("content")
        if not content:
            return abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                "Missing values from the request.",
            )

        try:
            sigma_rule = ts_sigma_lib.get_sigma_rule_by_text(content)

        except ValueError:
            logger.error(
                "Sigma Parsing error with the user provided rule",
                exc_info=True,
            )
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                "Error unable to parse the provided Sigma rule",
            )

        except NotImplementedError as exception:
            logger.error(
                "Sigma Parsing error: Feature in the rule provided "
                " is not implemented in this backend",
                exc_info=True,
            )
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                "Error generating rule {0!s}".format(exception),
            )

        except sigma_exceptions.SigmaParseError as exception:
            logger.error("Sigma Parsing error: unknown error", exc_info=True)
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                "Sigma parsing error generating rule  with error: {0!s}".format(
                    exception
                ),
            )

        except yaml.parser.ParserError as exception:
            logger.error(
                "Sigma Parsing error: an invalid yml file has been provided",
                exc_info=True,
            )
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                "Sigma parsing error: invalid yaml provided {0!s}".format(
                    exception
                ),
            )

        if sigma_rule is None:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No sigma was parsed")
        metadata = {"parsed": True}

        return jsonify({"objects": [sigma_rule], "meta": metadata})
