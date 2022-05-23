# Copyright 2021 Google Inc. All rights reserved.
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
"""The class definitions for the data finder, or the data analyzer."""

import logging

from flask import current_app

from timesketch.lib.analyzers import utils
from timesketch.lib.datastores.opensearch import OpenSearchDataStore


logger = logging.getLogger("timesketch.data_finder")


class DataFinder:
    """The data finder class."""

    def __init__(self):
        """Initialize the data finder."""
        self._end_date = ""
        self._indices = []
        self._parameters = {}
        self._rule = {}
        self._start_date = ""
        self._timeline_ids = []

        self._datastore = OpenSearchDataStore(
            host=current_app.config["OPENSEARCH_HOST"],
            port=current_app.config["OPENSEARCH_PORT"],
        )

    def can_run(self):
        """Returns a boolean whether the data finder can be run."""
        if not self._rule:
            logger.warning("Unable to run data finder since no rule has been defined.")
            return False

        if not self._start_date:
            logger.warning(
                "Unable to run data finder since no start date has been " "defined."
            )
            return False

        if not self._end_date:
            logger.warning(
                "Unable to run data finder since no end date has been " "defined."
            )
            return False

        if not self._parameters:
            return True

        re_parameters = self._rule.get("re_parameters", [])
        for parameter in re_parameters:
            if not parameter in self._parameters:
                logger.warning(
                    "Parameters are defined, but parameter: [{0:s}] does not "
                    "exist in parameter definitions for the rule.".format(parameter)
                )
                return False

        return True

    def set_end_date(self, end_date):
        """Sets the end date of the time period the data finder uses."""
        # TODO: Implement a check if this is a valid ISO formatted date.
        self._end_date = end_date

    def set_indices(self, indices):
        """Sets the value of the indices."""
        self._indices = indices

    def set_parameter(self, parameter, value):
        """Sets the value of a single parameter.

        Args:
            parameter (str): The string value of the parameter name.
            value (any): The value of the parameter.
        """
        self._parameters[parameter] = value

    def set_parameters(self, parameter_dict):
        """Set multiple parameters at once using a dict.

        Args:
            parameter_dict (dict): A set of parameters and their values.
        """
        if isinstance(parameter_dict, dict):
            self._parameters.update(parameter_dict)

    def set_rule(self, rule_dict):
        """Sets the rules of the data finder.

        Args:
            rule_dict (dict): A dict with the parameters for the data
                finder to operate, this include search parameters,
                regular expression, etc.
        """
        self._rule = rule_dict

    def set_start_date(self, start_date):
        """Sets the start date of the time period the data finder uses."""
        # TODO: Implement a check if this is a valid ISO formatted date.
        self._start_date = start_date

    def set_timeline_ids(self, timeline_ids):
        """Sets the timeline identifiers."""
        self._timeline_ids = timeline_ids

    def find_data(self):
        """Returns a tuple with a bool on whether data was found and a message.

        Raises:
            RuntimeError: If the data finder cannot run.

        Returns:
            A tuple with two entries:
                bool: whether data was discovered or not.
                str: a message string indicating how the data was found or the
                    the reason why it wasn't.
        """
        if not self.can_run():
            return False, "Unable to run the data finder, missing information."

        query_string = self._rule.get("query_string")
        query_dsl = self._rule.get("query_dsl")

        if not query_string and not query_dsl:
            raise RuntimeError(
                "Unable to run, missing either a query string or a DSL to "
                "perform the search."
            )

        attribute = self._rule.get("attribute")
        regular_expression = self._rule.get("regular_expression")
        if regular_expression:
            if not attribute:
                raise RuntimeError(
                    "Attribute must be set in a rule if a regular expression "
                    "is used."
                )
            expression = utils.compile_regular_expression(
                expression_string=regular_expression,
                expression_flags=self._rule.get("re_flags"),
                expression_parameters=self._rule.get("re_parameters"),
            )
        else:
            expression = None

        query_filter = {
            "chips": [
                {
                    "field": "",
                    "type": "datetime_range",
                    "operator": "must",
                    "active": True,
                    "value": f"{self._start_date},{self._end_date}",
                }
            ]
        }

        event_generator = self._datastore.search_stream(
            query_string=query_string,
            query_dsl=query_dsl,
            query_filter=query_filter,
            indices=self._indices,
            return_fields=attribute,
            enable_scroll=True,
            timeline_ids=self._timeline_ids,
        )

        for event in event_generator:
            # TODO: Save the result to the Investigation object when that
            # exist in the future.
            if not expression:
                return True, "Data discovered"

            source = event.get("_source", {})
            value = source.get(attribute)
            if not value:
                logger.warning("Attribute: [{0:s}] is empty".format(attribute))

            result = expression.findall(value)
            if not result:
                continue

            return True, "Data discovered using Regular Expression"

        return False, "No hits discovered"
