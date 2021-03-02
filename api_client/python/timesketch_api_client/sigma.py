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

logger = logging.getLogger('timesketch_api.sigma')


class Sigma(resource.BaseResource):
    """Timesketch sigma object.

    A sigma object in Timesketch is a collection of one or more rules.

    Attributes:
        rule_uuid: The ID of the rule.
    """


    def __init__(self, api):
        """Initializes the Sigma object.

        Args:
            api: An instance of TimesketchApi object.

        """
        self._attr_dict = {}
        resource_uri = 'sigma/'
        super().__init__(
            api=api, resource_uri=resource_uri)

    @property
    def attributes(self):
        """Returns a list of all attribute keys for the rule"""
        return list(self._attr_dict.keys())

    def get_attribute(self, key):
        """Get a value for a given key in case it has no dedicated property"""
        if not self._attr_dict:
            return ''
        return self._attr_dict.get(key, '')

    @property
    def es_query(self):
        """Returns the ElasticSearch query."""
        return self.get_attribute('es_query')

    @property
    def title(self):
        """Returns the sigma rule title."""
        return self.get_attribute('title')

    @property
    def id(self):
        """Returns the sigma rule id."""
        return self.get_attribute('id')

    @property
    def file_relpath(self):
        """Returns the relative filepath of the rule."""
        return self.get_attribute('file_relpath')

    @property
    def rule_uuid(self):
        """Returns the rule id."""
        return self.get_attribute('rule_uuid')

    @property
    def file_name(self):
        """Returns the rule filename."""
        return self.get_attribute('file_name')

    @property
    def description(self):
        """Returns the rule description."""
        return self.get_attribute('description')

    @property
    def level(self):
        """Returns the rule confidence level."""
        return self.get_attribute('level')

    @property
    def falsepositives(self):
        """Returns the rule falsepositives."""
        return self.get_attribute('falsepositives')

    @property
    def author(self):
        """Returns the rule author."""
        return self.get_attribute('author')

    @property
    def date(self):
        """Returns the rule date."""
        return self.get_attribute('date')

    @property
    def modified(self):
        """Returns the rule modified date."""
        return self.get_attribute('modified')


    @property
    def logsource(self):
        """Returns the rule logsource."""
        return self.get_attribute('logsource')

    @property
    def detection(self):
        """Returns the rule detection."""
        return self.get_attribute('detection')

    @property
    def references(self):
        """Returns the rule references."""
        return self.get_attribute('references')

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
        """Get a Sigma object from a rule uuid.

        Args:
            rule_uuid: Id of the sigma rule.

        """
        self.resource_uri = f'sigma/rule/{rule_uuid}'
        super().__init__(
            api=self.api, resource_uri=self.resource_uri)

        self.lazyload_data(refresh_cache=True)
        objects = self.data.get('objects')
        if not objects:
            logger.error('Unable to parse rule with given text')
            raise ValueError('No rules found.')
        rule_dict = objects[0]
        for key, value in rule_dict.items():
            self.set_value(key, value)

    def from_text(self, rule_text):
        """Get a Sigma object from a rule text.

        Args:
            rule_text: Rule text to be parsed.

        Raises:
            ValueError: If no response was given
        """
        self.resource_uri = '{0:s}/sigma/text/'.format(self.api.api_root)
        data = {'title': 'Get_Sigma_by_text', 'content': rule_text}
        response = self.api.session.post(self.resource_uri, json=data)
        response_dict = error.get_response_json(response, logger)

        objects = response_dict.get('objects')
        if not objects:
            logger.warning(
                'Unable to parse rule with given text')
            raise ValueError('No rules found.')

        rule_dict = objects[0]
        for key, value in rule_dict.items():
            self.set_value(key, value)
