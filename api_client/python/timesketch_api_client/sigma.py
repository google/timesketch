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
"""Timesketch API sigma library."""
from __future__ import unicode_literals

import logging

from . import resource
from . import error

logger = logging.getLogger("timesketch_api.sigma")


class SigmaRule(resource.BaseResource):
    """Timesketch SigmaRule object.

    A SigmaRule object in Timesketch is a collection of one or more rules.

    Attributes:
        rule_uuid: The ID of the rule.
    """

    def __init__(self, api):
        """Initializes the Sigma object.

        Args:
            api: An instance of TimesketchApi object.

        """
        self._attr_dict = {}
        resource_uri = "sigmarules/"
        super().__init__(api=api, resource_uri=resource_uri)

    @property
    def attributes(self):
        """Returns a list of all attribute keys for the rule"""
        return list(self._attr_dict.keys())

    def get_attribute(self, key):
        """Get a value for a given key in case it has no dedicated property"""
        if not self._attr_dict:
            return ""
        return self._attr_dict.get(key, "")

    @property
    def search_query(self):
        """Returns the Search query."""
        return self.get_attribute("search_query")

    @property
    def title(self):
        """Returns the Sigma rule title."""
        return self.get_attribute("title")

    @property
    def id(self):
        """Returns the Sigma rule id."""
        return self.get_attribute("id")

    @property
    def rule_uuid(self):
        """Returns the rule id."""
        return self.get_attribute("id")

    @property
    def description(self):
        """Returns the rule description."""
        return self.get_attribute("description")

    @property
    def level(self):
        """Returns the rule confidence level."""
        return self.get_attribute("level")

    @property
    def falsepositives(self):
        """Returns the rule falsepositives."""
        return self.get_attribute("falsepositives")

    @property
    def author(self):
        """Returns the rule author."""
        return self.get_attribute("author")

    @property
    def date(self):
        """Returns the rule date."""
        return self.get_attribute("date")

    @property
    def modified(self):
        """Returns the rule modified date."""
        return self.get_attribute("modified")

    @property
    def logsource(self):
        """Returns the rule logsource."""
        return self.get_attribute("logsource")

    @property
    def detection(self):
        """Returns the rule detection."""
        return self.get_attribute("detection")

    @property
    def references(self):
        """Returns the rule references."""
        return self.get_attribute("references")

    @property
    def status(self):
        """Returns the rule status."""
        return self.get_attribute("status")

    def set_value(self, key, value):
        """Sets the value for a given key

        Args:
            key: key to set the value
            value: value to set

        """
        self._attr_dict[key] = value

    def _load_rule_dict(self, rule_dict):
        """Load a dict into a rule"""
        for key, value in rule_dict.items():
            self.set_value(key, value)

    def from_rule_uuid(self, rule_uuid):
        """Get a SigmaRule object from a rule UUID.

        Args:
            rule_uuid: Id of the sigma rule.

        """
        self.resource_uri = f"sigmarules/{rule_uuid}"

        self.lazyload_data(refresh_cache=True)
        objects = self.data.get("objects")
        if not objects:
            error_msg = "Unable to parse Sigma rule {0} with given text".format(
                rule_uuid
            )
            logger.error(error_msg)
            raise ValueError(error_msg)
        rule_dict = objects[0]
        for key, value in rule_dict.items():
            self.set_value(key, value)

    def from_text(self, rule_text):
        """Obtain a parsed Sigma rule by providing text.

        Args:
            rule_text: Rule text to be parsed.

        Raises:
            ValueError: If rule could not be parsed.
        """
        self.resource_uri = "{0:s}/sigmarules/text/".format(self.api.api_root)
        data = {"title": "Get_Sigma_by_text", "content": rule_text}
        response = self.api.session.post(self.resource_uri, json=data)
        response_dict = error.get_response_json(response, logger)

        objects = response_dict.get("objects")
        if not objects:
            error_msg = "Sigma rule Parsing error with provided rule"
            logger.warning(error_msg)
            raise ValueError(error_msg)

        rule_dict = objects[0]
        for key, value in rule_dict.items():
            self.set_value(key, value)

    def delete(self):
        """Deletes the Sigma rule from Timesketch."""
        if not self.get_attribute("id"):
            logger.warning(
                "Unable to delete the Sigma rule, it does not appear to be "
                "saved in the first place."
            )
            return False

        resource_url = f"{self.api.api_root}/sigmarules/{self.get_attribute('id')}"

        response = self.api.session.delete(resource_url)
        return error.check_return_status(response, logger)
