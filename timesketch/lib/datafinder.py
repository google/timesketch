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


class DataFinder:
    """The data finder class."""

    def __init__(self):
        """Initialize the data finder."""
        self._end_date = ''
        self._parameters = {}
        self._rule = {}
        self._start_date = ''

    def can_run(self):
        """Returns a boolean whether the data finder can be run."""
        if not self._rule:
            return False

        if not self._start_date:
            return False

        if not self._end_date:
            return False

        if not self._parameters:
            return True

        re_parameters = self._rule.get('re_parameters', [])
        for parameter in re_parameters:
            if not parameter in self._parameters:
                return False

        return True

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
        self._parameters.update(parameter_dict)

    def set_rule(self, rule_dict):
        """Sets the rules of the data finder.

        Args:
            rule_dict (dict): A dict with the parameters for the data
                finder to operate, this include search parameters,
                regular expression, etc.
        """
        self._rule = rule_dict

    def find_data(self):
        """Returns a tuple with a boolen on whether data was found and text."""
        # TODO: Implement, query data, and inspect.
        return False, 'No search performed'
