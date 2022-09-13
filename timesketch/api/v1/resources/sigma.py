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
from timesketch.lib.definitions import HTTP_STATUS_CODE_FORBIDDEN
from timesketch.lib.definitions import HTTP_STATUS_CODE_OK

from timesketch.models.sigma import SigmaRule
from timesketch.models import db_session


logger = logging.getLogger("timesketch.api.sigma")

def _enrich_sigma_rule_object(rule: SigmaRule):
    """Helper function: Returns an enriched Sigma object givin a SigmaRule.

    Args:
        SigmaRule: uuid of the rule

    Returns:
        enriched Sigma dict
    """
    parsed_rule = ts_sigma_lib.get_sigma_rule_by_text(rule.rule_yaml)
    parsed_rule["rule_uuid"] = parsed_rule.get("id",rule.rule_uuid)
    parsed_rule["created_at"] = str(rule.created_at)
    parsed_rule["updated_at"] = str(rule.updated_at)
    parsed_rule["status"] = rule.get_status.status
    parsed_rule["title"] = parsed_rule.get("title",rule.title)
    parsed_rule["description"] = parsed_rule.get("description",rule.description)
    parsed_rule["rule_yaml"] = rule.rule_yaml

    return parsed_rule

# TODO(jaegeral): deprecate this class
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
                "OS Error, unable to get the path to the Sigma rules", exc_info=True
            )
            abort(HTTP_STATUS_CODE_NOT_FOUND, f"Value Error, {e}")
        # TODO: idea for meta: add a list of folders that have been parsed
        meta = {"current_user": current_user.username, "rules_count": len(sigma_rules)}
        return jsonify({"objects": sigma_rules, "meta": meta})

# TODO(jaegeral): deprecate this class
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
            logger.error(
                "OS Error, unable to get the path to the Sigma rules", exc_info=True
            )
            abort(HTTP_STATUS_CODE_NOT_FOUND, f"ValueError {e}")
        for rule in sigma_rules:
            if rule is not None:
                if rule_uuid == rule.get("id"):
                    return_rule = rule

        if return_rule is None:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No sigma rule found with this ID.")

        meta = {"current_user": current_user.username, "rules_count": len(sigma_rules)}
        return jsonify({"objects": [return_rule], "meta": meta})

# TODO(jaegeral): deprecate this class
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
                HTTP_STATUS_CODE_BAD_REQUEST, "Missing values from the request."
            )

        try:
            sigma_rule = ts_sigma_lib.get_sigma_rule_by_text(content)

        except ValueError:
            logger.error(
                "Sigma Parsing error with the user provided rule", exc_info=True
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
                "Sigma parsing error: invalid yaml provided {0!s}".format(exception),
            )

        if sigma_rule is None:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No sigma was parsed")
        metadata = {"parsed": True}

        return jsonify({"objects": [sigma_rule], "meta": metadata})

class SigmaRuleListResource(resources.ResourceMixin, Resource):
    """Resource to get list of SigmaRules."""

    @login_required
    def get(self):
        """Handles GET request to the resource.

        Returns:
            Dict of sigma rules
        """
        sigma_rules = []

        try:
            sigma_rules_results = SigmaRule.query.all()
            # Return a subset of the Sigma objects to reduce the amount of
            # data sent to the client.
            for rule in sigma_rules_results:
                sigma_rules.append(_enrich_sigma_rule_object(rule=rule))

        except ValueError as e:
            logger.error(
                "Error, unable to get Sigma rules", exc_info=True
            )
            abort(HTTP_STATUS_CODE_NOT_FOUND, f"Value Error, {e}")
        meta = {"current_user": current_user.username, "rules_count": len(sigma_rules)}
        return jsonify({"objects": sigma_rules, "meta": meta})


class SigmaRuleResource(resources.ResourceMixin, Resource):
    """Resource to get / delete / post / put a Sigma rule."""

    @login_required
    def get(self, rule_uuid):
        """Handles GET request to the resource.

        Args:
            rule_uuid: uuid of the rule

        Returns:
            JSON sigma rule
        """
        try:
            rule = SigmaRule.query.filter_by(rule_uuid=rule_uuid).first()

        except Exception as e: # pylint: disable=broad-except
            logger.error(
                "Unable to get the Sigma rule",
                exc_info=True,
            )
            abort(HTTP_STATUS_CODE_NOT_FOUND, f"ValueError {e}")

        if not rule:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No rule found with this ID.")
        return_rules = []

        assert isinstance(rule, SigmaRule)

        return_rules.append(
            _enrich_sigma_rule_object(rule=rule))

        meta = {
            "current_user": current_user.username,
        }
        return jsonify({"objects": return_rules, "meta": meta})

    @login_required
    def delete(self, rule_uuid):
        """Handles DELETE request to the resource.
        Args:
            rule_uuid: uuid of the rule
        """

        rule = SigmaRule.query.filter_by(rule_uuid=rule_uuid).first()

        db_session.delete(rule)
        db_session.commit()

        return HTTP_STATUS_CODE_OK

    @login_required
    def put(self, rule_uuid):
        """Handles update request to Sigma rules
        Args:
            rule_uuid: uuid of the rule
        Returns:
            The updated sigma object in JSON (instance of
            flask.wrappers.Response)
        """

        try:
            rule = SigmaRule.query.filter_by(rule_uuid=rule_uuid).first()

        except Exception as e: # pylint: disable=broad-except
            logger.error(
                "Unable to get the Sigma rule",
                exc_info=True,
            )
            abort(HTTP_STATUS_CODE_NOT_FOUND, f"ValueError {e}")

        form = request.json
        if not form:
            form = request.data
        if not form.validate_on_submit():
            abort(HTTP_STATUS_CODE_BAD_REQUEST, "Unable to validate form data.")

        abort(HTTP_STATUS_CODE_NOT_FOUND, "Method not implemented yet")

        # TODO(jaegeral): complete this method
        rule_yaml = form.get("rule_yaml", "")
        parsed_rule = ts_sigma_lib.get_sigma_rule_by_text(rule_yaml)

        logger.debug(rule_yaml + parsed_rule + rule)



    @login_required
    def post(self, rule_uuid=None):
        """Handles POST request to the resource.
        Args:
            rule_uuid: uuid of the rule

        Returns:
            Sigma rule object and HTTP status code indicating
            whether operation was sucessful.
        """
        form = request.json
        if not form:
            form = request.data

        rule_yaml = form.get("rule_yaml", "")

        if not rule_yaml:
            abort(
                HTTP_STATUS_CODE_NOT_FOUND,
                "No rule_yaml supplied.",
            )

        if not isinstance(rule_yaml, str):
            abort(
                HTTP_STATUS_CODE_FORBIDDEN, "rule_yaml needs to be a string."
            )

        parsed_rule = ts_sigma_lib.get_sigma_rule_by_text(rule_yaml)

        if not rule_uuid:
            rule_uuid = parsed_rule.get("id")

        # Query rules to see if it already exist
        rule = SigmaRule.query.filter_by(rule_uuid=rule_uuid).first()
        if rule:
            if rule.rule_uuid == parsed_rule.get("rule_uuid"):
                abort(HTTP_STATUS_CODE_CONFLICT, "Rule already exist")

        sigma_rule = SigmaRule.get_or_create(
            rule_yaml=form.get("rule_yaml", ""),
            description = parsed_rule.get("description", ""),
            title = parsed_rule.get("title", ""),
            user = current_user
            )

        sigma_rule.query_string = parsed_rule.get("query_string", "")
        sigma_rule.rule_uuid = parsed_rule.get("id", None)

        if sigma_rule is None:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No sigma was parsed")

        try:
            db_session.add(sigma_rule)
            db_session.commit()
        except IntegrityError as e:
            logger.error("Unable to add Sigma rule to DB, with error: %s", e)
            abort(HTTP_STATUS_CODE_CONFLICT, "Problem adding Sigma rule")


        return self.to_json(sigma_rule, status_code=HTTP_STATUS_CODE_CREATED)


class SigmaRuleByTextResource(resources.ResourceMixin, Resource):
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
                HTTP_STATUS_CODE_BAD_REQUEST, "Missing values from the request."
            )

        try:
            sigma_rule = ts_sigma_lib.get_sigma_rule_by_text(content)

        except ValueError:
            logger.error(
                "Sigma Parsing error with the user provided rule", exc_info=True
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
                "Sigma parsing error: invalid yaml provided {0!s}".format(exception),
            )

        if sigma_rule is None:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No sigma was parsed")
        metadata = {"parsed": True}

        return jsonify({"objects": [sigma_rule], "meta": metadata})
