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

from sqlalchemy.exc import IntegrityError

import timesketch.lib.sigma_util as ts_sigma_lib

from timesketch.api.v1 import resources

from timesketch.lib.definitions import HTTP_STATUS_CODE_NOT_FOUND
from timesketch.lib.definitions import HTTP_STATUS_CODE_BAD_REQUEST
from timesketch.lib.definitions import HTTP_STATUS_CODE_CONFLICT
from timesketch.lib.definitions import HTTP_STATUS_CODE_CREATED
from timesketch.lib.definitions import HTTP_STATUS_CODE_OK
from timesketch.lib.definitions import HTTP_STATUS_CODE_INTERNAL_SERVER_ERROR
from timesketch.lib.definitions import HTTP_STATUS_CODE_FORBIDDEN

from timesketch.models.sigma import SigmaRule
from timesketch.models import db_session


logger = logging.getLogger("timesketch.api.sigma")


def _enrich_sigma_rule_object(rule: SigmaRule):
    """Helper function: Returns an enriched Sigma object given a SigmaRule.

    It will extract the `status`, `created_at` and `updated_at` and make them
    a field.

    Args:
        rule: type SigmaRule.

    Returns:
        Enriched Sigma dict.
    """
    parsed_rule = ts_sigma_lib.parse_sigma_rule_by_text(rule.rule_yaml)
    parsed_rule["rule_uuid"] = parsed_rule.get("id", rule.rule_uuid)
    parsed_rule["created_at"] = str(rule.created_at)
    parsed_rule["updated_at"] = str(rule.updated_at)
    parsed_rule["title"] = parsed_rule.get("title", rule.title)
    parsed_rule["description"] = parsed_rule.get("description", rule.description)
    parsed_rule["rule_yaml"] = rule.rule_yaml

    # via StatusMixin, values according to:
    # https://github.com/SigmaHQ/sigma/wiki/Specification#status-optional
    parsed_rule["status"] = rule.get_status.status

    return parsed_rule


# TODO(jaegeral): deprecate this class
class SigmaListResource(resources.ResourceMixin, Resource):
    """DEPRECATED: Resource to get list of Sigma rules.

    Will be removed as part of
    https://github.com/google/timesketch/issues/2301.

    """

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
        meta = {"rules_count": len(sigma_rules)}
        return jsonify({"objects": sigma_rules, "meta": meta})


# TODO(jaegeral): deprecate this class
class SigmaResource(resources.ResourceMixin, Resource):
    """DEPRECATED: Resource to get a Sigma rule.

    Will be removed as part of
    https://github.com/google/timesketch/issues/2301.
    """

    @login_required
    def get(self, rule_uuid):
        """DEPRECATED: Handles GET request to the resource.
        Args:
            rule_uuid: UUID of the sigma rule
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
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No sigma rule found with this ID.")

        meta = {
            "current_user": current_user.username,
            "rules_count": len(sigma_rules),
        }
        return jsonify({"objects": [return_rule], "meta": meta})


# TODO(jaegeral): deprecate this class
class SigmaByTextResource(resources.ResourceMixin, Resource):
    """DEPRECATED: Resource to get a Sigma rule by text.

    Will be removed as part of
    https://github.com/google/timesketch/issues/2301.

    """

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
            sigma_rule = ts_sigma_lib.parse_sigma_rule_by_text(content)

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
                "Sigma Parsing error: Feature in the rule provided "
                " is not implemented in this backend: {0!s}".format(exception),
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
                "Sigma parsing error: invalid YAML provided: {0!s}".format(exception),
            )

        return jsonify({"objects": [sigma_rule], "meta": {}})


class SigmaRuleListResource(resources.ResourceMixin, Resource):
    """Resource to get list of all SigmaRules."""

    @login_required
    def get(self):
        """Fetches Sigma rules from the database.

        Fetches all Sigma rules stored in the database on the system
        and returns a list of JSON representations of the rules.

        Returns:
            List of sigma rules represented in JSON e.g.
                {"objects": [sigma_rules], "meta": {"rules_count": 42}.
        """
        sigma_rules = []

        all_sigma_rules = SigmaRule.query.all()
        for rule in all_sigma_rules:
            sigma_rules.append(_enrich_sigma_rule_object(rule=rule))

        meta = {"rules_count": len(sigma_rules)}
        return jsonify({"objects": sigma_rules, "meta": meta})

    @login_required
    def post(self):
        """Adds a single Sigma rule to the database.

        Adds a single Sigma rule to the database when `/sigmarule/` is called
        with a POST request.

        All attributes of the rule are taken by the `rule_yaml` value in the
        POST request.

        If no `rule_yaml` is found in the reuqest, the method will fail as this
        is required to parse the rule.

        Remark: To update a rule, use `PUT`instead.

        Returns:
            Sigma rule object and HTTP status 200 code indicating
            whether operation was sucessful.
            HTTP Error code 400 if no `rule_yaml` is provided or a parsing
                error occurs.
            HTTP Error code 400 if rule_uuid does not match id in the YAML.
        """
        rule_yaml = request.json.get("rule_yaml")

        if not rule_yaml:
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                "No rule_yaml supplied in the POST request to the API.",
            )

        try:
            parsed_rule = ts_sigma_lib.parse_sigma_rule_by_text(rule_yaml)
        except ValueError as e:
            error_msg = "Sigma Rule Parsing error: {0!s}".format(e)
            logger.debug(error_msg)
            return abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                error_msg,
            )

        rule_uuid = parsed_rule.get("id")

        # Query rules to see if it already exist and exit if found
        sigma_rule_from_db = SigmaRule.query.filter_by(rule_uuid=rule_uuid).first()
        if sigma_rule_from_db:
            error_msg = "Rule {0!s} was already found in the database".format(rule_uuid)
            logger.debug(error_msg)
            abort(HTTP_STATUS_CODE_FORBIDDEN, error_msg)

        sigma_rule = SigmaRule.get_or_create(
            rule_uuid=rule_uuid,
            rule_yaml=rule_yaml,
            description=parsed_rule.get("description"),
            title=parsed_rule.get("title"),
            user=current_user,
        )

        sigma_rule.set_status(parsed_rule.get("status", "experimental"))
        # query string is not stored in the database but we attach it to
        # the JSON result here as it is added in the GET methods
        sigma_rule.query_string = parsed_rule.get("search_query")

        try:
            db_session.add(sigma_rule)
            db_session.commit()
        except IntegrityError as e:
            error_msg = "Error adding Sigma rule {0!s}".format(e)
            logger.error(error_msg)
            abort(
                HTTP_STATUS_CODE_CONFLICT,
                error_msg,
            )

        return self.to_json(sigma_rule, status_code=HTTP_STATUS_CODE_CREATED)


class SigmaRuleResource(resources.ResourceMixin, Resource):
    """Resource to read / delete / create / update a Sigma rule."""

    @login_required
    def get(self, rule_uuid):
        """Fetches a single Sigma rule from the databse.

        Fetches a single Sigma rule selected by the `UUID` in
        `/sigmarule/<string:rule_uuid>/` and returns a JSON represantion of the
        rule.

        Args:
            rule_uuid: UUID of the rule.

        Returns:
            JSON sigma rule representation
            e.g.:  {"objects": [return_rule], "meta": {}}.
        """
        try:
            rule = SigmaRule.query.filter_by(rule_uuid=rule_uuid).first()

        except Exception as e:  # pylint: disable=broad-except
            error_msg = "Unable to get the Sigma rule {0!s}".format(e)
            logger.error(
                error_msg,
                exc_info=True,
            )
            abort(
                HTTP_STATUS_CODE_INTERNAL_SERVER_ERROR,
                error_msg,
            )

        if not rule:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No rule found with this ID.")
        return_rule = []

        return_rule.append(_enrich_sigma_rule_object(rule=rule))

        return jsonify({"objects": return_rule, "meta": {}})

    @login_required
    def delete(self, rule_uuid):
        """Deletes a Sigma rule from the database.

        Deletes a single Sigma rule selected by the `uuid` in
        `/sigmarule/<string:rule_uuid>/`.

        Args:
            rule_uuid: UUID of the rule to be deleted.

        Returns:
            HTTP_STATUS_CODE_NOT_FOUND if rule not found.
            HTTP_STATUS_CODE_OK if rule deleted.
        """
        rule = SigmaRule.query.filter_by(rule_uuid=rule_uuid).first()

        if not rule:
            error_msg = "No rule found with rule_uuid.{0!s}".format(rule_uuid)
            logger.debug(error_msg)  # only needed in debug cases
            abort(
                HTTP_STATUS_CODE_NOT_FOUND,
                error_msg,
            )

        db_session.delete(rule)
        db_session.commit()

        return HTTP_STATUS_CODE_OK

    @login_required
    def put(self, rule_uuid):
        """Update an existing Sigma rule in the database.

        Handles calls to `/sigmarule/<string:rule_uuid>/`, where
        `rule_uuid` is used to identify the rule.

        The remaining attributes of the rule are provided in request itself
        through the `rule_yaml` key.
        If no `rule_yaml` is found in the request, the request will fail as this
        is required to parse the rule.

        If `rule_uuid` doesn't match the UUI in `rule_yaml`, the request will fail.

        Args:
            rule_uuid: UUID of the rule.

        Returns:
            The updated Sigma object in JSON.
        """

        rule_yaml = request.json.get("rule_yaml")
        if not rule_yaml:
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                "Error parsing Sigma rule {0!s}: no YAML provided".format(rule_uuid),
            )
        try:
            parsed_rule = ts_sigma_lib.parse_sigma_rule_by_text(rule_yaml)
        except ValueError as e:
            error_msg = "Error parsing Sigma rule {0!s}: {1!s}".format(rule_uuid, e)
            abort(HTTP_STATUS_CODE_BAD_REQUEST, error_msg)

        if rule_uuid != parsed_rule.get("id"):
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                "Rule ID mismatch parameter:{0!s} and YAML content:{1!s}".format(
                    rule_uuid, parsed_rule.get("id")
                ),
            )

        sigma_rule_from_db = SigmaRule.query.filter_by(rule_uuid=rule_uuid).first()

        if not sigma_rule_from_db:
            error_msg = "Sigma rule with UUID: {0!s} not found".format(rule_uuid)
            logger.error(error_msg)
            abort(HTTP_STATUS_CODE_NOT_FOUND, error_msg)

        sigma_rule_from_db.rule_yaml = rule_yaml
        sigma_rule_from_db.title = parsed_rule.get("title")
        sigma_rule_from_db.description = parsed_rule.get("description")
        sigma_rule_from_db.set_status(parsed_rule.get("status", "experimental"))

        try:
            db_session.add(sigma_rule_from_db)
            db_session.commit()
        except IntegrityError as e:
            error_msg = "Error adding Sigma rule {0!s}".format(e)
            logger.error(error_msg)
            abort(
                HTTP_STATUS_CODE_CONFLICT,
                error_msg,
            )

        return self.to_json(sigma_rule_from_db, status_code=HTTP_STATUS_CODE_OK)


class SigmaRuleByTextResource(resources.ResourceMixin, Resource):
    """Get a Sigma rule by providing a text."""

    @login_required
    def post(self):
        """Obtain a parsed Sigma rule by providing text.

        Will parse a provided text `rule_yaml`, parse it and return as JSON.
        If no form content is given, the method will abort with HTTP error 400.

        Returns:
            JSON sigma rule e.g.
                {"objects": [sigma_rule], "meta": {"parsed": True}}.
        """
        content = request.json.get("content")
        if not content:
            return abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                "Missing value in the request. Nothing to parse",
            )

        try:
            sigma_rule = ts_sigma_lib.parse_sigma_rule_by_text(content)
        except ValueError as e:
            error_msg = "Sigma rule Parsing error with provided rule {0!s}".format(
                str(e)
            )
            logger.error(
                error_msg,
                exc_info=True,
            )
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                error_msg,
            )

        except NotImplementedError as e:
            error_msg = (
                "Sigma Parsing error: Feature in the rule provided"
                " is not implemented in this backend {0!s}".format(e)
            )
            logger.error(
                error_msg,
                exc_info=True,
            )
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                error_msg,
            )

        except sigma_exceptions.SigmaParseError as e:
            error_msg = "Sigma parsing error generating rule"
            " with error: {0:s}".format(str(e))
            logger.error(error_msg, exc_info=True)
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                error_msg,
            )

        except yaml.parser.ParserError as e:
            error_msg = "Sigma parsing error: invalid YAML provided {0!s}".format(e)
            logger.error(
                error_msg,
                exc_info=True,
            )
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                error_msg,
            )

        metadata = {"parsed": True}

        return jsonify({"objects": [sigma_rule], "meta": metadata})
