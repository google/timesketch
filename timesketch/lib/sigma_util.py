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
import logging
import string
from functools import lru_cache
import yaml

from flask import current_app

import sigma.configuration as sigma_configuration

from sigma.backends import elasticsearch as sigma_es
from sigma.parser import collection as sigma_collection
from sigma.parser import exceptions as sigma_exceptions
from sigma.config.exceptions import SigmaConfigParseError
from timesketch.models.sigma import SigmaRule

logger = logging.getLogger("timesketch.lib.sigma")


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
            "SIGMA_CONFIG", "./data/sigma_config.yaml"
        )

    if not config_file_path:
        raise ValueError("No config_file_path set via param or config file")

    if not os.path.isfile(config_file_path):
        raise ValueError(
            "Unable to open: [{0:s}], does not exist.".format(config_file_path)
        )

    if not os.access(config_file_path, os.R_OK):
        raise ValueError(
            "Unable to open file: [{0:s}], cannot open it for "
            "read, please check permissions.".format(config_file_path)
        )

    with open(config_file_path, "r", encoding="utf-8") as config_file_read:
        sigma_config_file = config_file_read.read()

    try:
        sigma_config = sigma_configuration.SigmaConfiguration(sigma_config_file)
    except SigmaConfigParseError:
        logger.error("Parsing error with {0:s}".format(sigma_config_file))
        raise

    return sigma_config


def enrich_sigma_rule_object(rule: SigmaRule, parse_yaml: bool = False):
    """Helper function: Returns an enriched Sigma object given a SigmaRule.

    It will extract the `status`, `created_at` and `updated_at` and make them
    a field.

    Args:
        rule: type SigmaRule.
        parse_yaml: type bool. If set to True, the rule will be parsed from
            the yaml (slower).

    Returns:
        Enriched Sigma dict.
    """
    parsed_rule = {}

    # Parsing the yaml file takes a lot of time, per default, we do not need
    # that information, so we only parse it if we need it.

    if parse_yaml:
        parsed_rule = parse_sigma_rule_by_text(rule.rule_yaml)

    parsed_rule["rule_uuid"] = parsed_rule.get("id", rule.rule_uuid)
    parsed_rule["id"] = parsed_rule.get("id", rule.rule_uuid)
    parsed_rule["created_at"] = str(rule.created_at)
    parsed_rule["updated_at"] = str(rule.updated_at)
    parsed_rule["title"] = parsed_rule.get("title", rule.title)
    parsed_rule["description"] = parsed_rule.get("description", rule.description)
    parsed_rule["rule_yaml"] = rule.rule_yaml

    # via StatusMixin, values according to:
    # https://github.com/SigmaHQ/sigma/wiki/Specification#status-optional
    parsed_rule["status"] = rule.get_status.status

    return parsed_rule


def get_all_sigma_rules(parse_yaml: bool = False):
    """Returns all Sigma rules from the database.

    Args:
        parse_yaml: type bool. If set to True, the rule will be parsed from
            the yaml (slower).
    Returns:
        A array of Sigma rules


    """
    sigma_rules = []

    for rule in SigmaRule.query.all():
        sigma_rules.append(enrich_sigma_rule_object(rule=rule, parse_yaml=parse_yaml))

    return sigma_rules


def _sanitize_query(sigma_rule_query: str) -> str:
    """Returns a sanitized query.

    This function requires more thorough testing as it
    generated OpenSearch queries with an invalid syntax. The Sigma library
    does a good enough job at generating compatible (albeit maybe inefficient)
    queries.

    Args:
        sigma_rule_query: path to the sigma rule to be parsed
    Returns:
        String of a cleaned string
    """
    # TODO: Investigate how to handle .keyword
    # fields in Sigma.
    # https://github.com/google/timesketch/issues/1199#issuecomment-639475885

    sigma_rule_query = sigma_rule_query.replace(".keyword:", ":")
    sigma_rule_query = sigma_rule_query.replace("\\ ", " ")
    sigma_rule_query = sigma_rule_query.replace("\\:", ":")
    sigma_rule_query = sigma_rule_query.replace("\\-", "-")
    sigma_rule_query = sigma_rule_query.replace("*\\\\", " *")
    sigma_rule_query = sigma_rule_query.replace("::", r"\:\:")

    # TODO: Improve the whitespace handling
    # https://github.com/google/timesketch/issues/2007
    # check if there is a ' * '
    # if one is found split it up into elements separated by space
    # and go backwards to the next star

    sigma_rule_query = sigma_rule_query.replace(" * OR", ' " OR')
    sigma_rule_query = sigma_rule_query.replace(" * AND", ' " AND')
    sigma_rule_query = sigma_rule_query.replace("OR * ", 'OR " ')
    sigma_rule_query = sigma_rule_query.replace("AND * ", 'AND " ')
    sigma_rule_query = sigma_rule_query.replace("(* ", '(" ')
    sigma_rule_query = sigma_rule_query.replace(" *)", ' ")')
    sigma_rule_query = sigma_rule_query.replace("*)", '")')
    sigma_rule_query = sigma_rule_query.replace("(*", '("')
    sigma_rule_query = sigma_rule_query.replace(
        r"\*:", ""
    )  # removes wildcard at the beginning of a rule search_query

    elements = re.split(r"\s+", sigma_rule_query)
    san = []
    for el in elements:
        if el.count("*") == 1:
            # indicates a string that had a space before with only one star
            san.append(el.replace("*", '"'))
        else:
            san.append(el)

    sigma_rule_query = " ".join(san)
    # above method might create strings that have '' in them, workaround:
    sigma_rule_query = sigma_rule_query.replace('""', '"')

    return sigma_rule_query


def sanitize_incoming_sigma_rule_text(rule_text: string):
    """Removes things that are not supported in Timesketch
    right now as early as possible

    Args:
        rule_text: Text of the sigma rule to be parsed

    Returns:
        Cleaned version of the rule_text

    """

    rule_text = rule_text.replace("|endswith", "")
    rule_text = rule_text.replace("|startswith", "")

    return rule_text


@lru_cache(maxsize=8)
def parse_sigma_rule_by_text(rule_text, sigma_config=None, sanitize=True):
    """Returns a JSON representation for a rule

    Args:
        rule_text: Text of the sigma rule to be parsed
        sigma_config: config file object
        sanitize: If set to True, sanitization rules will be ran over the
            resulting Lucene query.

    Returns:
        JSON representation of the parsed rule
    Raises:
        sigma_exceptions.SigmaParseError: Issue with parsing the given rule
        yaml.parser.ParserError: Not a correct YAML text provided
        NotImplementedError: A feature in the provided Sigma rule is not
            implemented in Sigma for Timesketch
        ValueError: If one of the following fields are missing in the YAML file:
            - title
            - description
        ValueError: If provided rule_text is not a string
    """

    if not isinstance(rule_text, str):
        raise ValueError("rule_text needs to be a string.")

    try:
        if isinstance(sigma_config, sigma_configuration.SigmaConfiguration):
            sigma_conf_obj = sigma_config
        elif isinstance(sigma_config, str):
            sigma_conf_obj = get_sigma_config_file(sigma_config)
        else:
            sigma_conf_obj = get_sigma_config_file()
    except ValueError as e:
        logger.error("Problem reading the Sigma config", exc_info=True)
        raise ValueError("Problem reading the Sigma config") from e

    sigma_backend = sigma_es.ElasticsearchQuerystringBackend(sigma_conf_obj, {})

    rule_text = sanitize_incoming_sigma_rule_text(rule_text)

    rule_return = {}
    parsed_sigma_rules = None
    # TODO check if input validation is needed / useful.
    try:
        rule_yaml_data = yaml.safe_load_all(rule_text)

        for doc in rule_yaml_data:
            parser = sigma_collection.SigmaCollectionParser(
                str(rule_text), sigma_conf_obj, None
            )
            parsed_sigma_rules = parser.generate(sigma_backend)
            rule_return.update(doc)

    except NotImplementedError as exception:
        logger.error("Error generating rule {0!s}".format(exception))
        raise

    except sigma_exceptions.SigmaParseError as exception:
        logger.error("Sigma parsing error rule {0!s}".format(exception))
        raise

    except yaml.parser.ParserError as exception:
        logger.error("Yaml parsing error rule {0!s}".format(exception))
        raise

    assert parsed_sigma_rules is not None

    sigma_search_query = list(parsed_sigma_rules)[0]
    if sanitize:
        sigma_search_query = _sanitize_query(sigma_search_query)
    sigma_search_query = sigma_search_query.replace("*.keyword:", "message.keyword:")

    if not isinstance(rule_return.get("title"), str):
        error_msg = "Missing value: 'title' from the YAML data."
        logger.error(error_msg)
        raise ValueError(error_msg)

    if not isinstance(rule_return.get("description"), str):
        error_msg = "Missing value: 'description' from the YAML data."
        logger.error(error_msg)
        raise ValueError(error_msg)

    if not isinstance(rule_return.get("id"), str):
        error_msg = "Missing value: 'id' from the YAML data."
        logger.error(error_msg)
        raise ValueError(error_msg)

    rule_return.update({"search_query": sigma_search_query})
    rule_return.update({"file_name": "N/A"})
    return rule_return
