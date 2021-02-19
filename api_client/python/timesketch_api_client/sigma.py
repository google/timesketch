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
        self._author = None
        self._date = None
        self._description = None
        self._detection = None
        self._es_query = None
        self._falsepositives = None
        self._file_name = None
        self._file_relpath = None
        self._id = None
        self._level = None
        self._logsource = None
        self._modified = None
        self._rule_uuid = None
        self._references = None
        self._resource_uri = 'sigma/' # TODO: clarify: is that okay?
        self._title = None

        super().__init__(
            api=api, resource_uri=self._resource_uri)

    @property
    def es_query(self):
        """Returns the elastic search query."""
        if self._es_query:
            return self._es_query

        if not self.data or self.data is None:
            self.lazyload_data(refresh_cache=True)

        try:
            self._es_query = self.data.get('es_query', '')
        except AttributeError: # in case self.data is Nonetype
            self._es_query = ''
        return self._es_query

    @property
    def title(self):
        """Returns the sigma rule title."""
        if self._title:
            return self._title

        if not self.data or self.data is None:
            self.lazyload_data(refresh_cache=True)

        try:
            self._title = self.data.get('title', '')
        except AttributeError: # in case self.data is Nonetype
            self._title = ''
        return self._title

    @property
    def id(self):
        """Returns the sigma rule id."""
        if self._id:
            return self._id
        sigma_data = self.data

        if not sigma_data:
            self.lazyload_data()
            return ''

        return sigma_data.get('id', '')

    @property
    def file_relpath(self):
        """Returns the relative filepath of the rule."""
        if self._file_relpath:
            return self._file_relpath
        sigma_data = self.data

        if not sigma_data:
            return ''

        return sigma_data.get('file_relpath', '')

    @property
    def rule_uuid(self):
        """Returns the rule id."""
        if self._id:
            return self._id
        sigma_data = self.data

        if not sigma_data:
            return ''

        return sigma_data.get('id', '')

    @property
    def file_name(self):
        """Returns the rule filename."""
        if self._file_name:
            return self._file_name
        sigma_data = self.data

        if not sigma_data:
            return ''

        return sigma_data.get('file_name', '')

    @property
    def description(self):
        """Returns the rule description."""
        if self._description:
            return self._description
        sigma_data = self.data

        if not sigma_data:
            return ''

        return sigma_data.get('description', '')

    @property
    def level(self):
        """Returns the rule confidence level."""
        if self._level:
            return self._level
        sigma_data = self.data

        if not sigma_data:
            return ''

        return sigma_data.get('level', '')

    @property
    def falsepositives(self):
        """Returns the rule falsepositives."""
        if self._falsepositives:
            return self._falsepositives
        sigma_data = self.data

        if not sigma_data:
            return ''

        return sigma_data.get('falsepositives', '')

    @property
    def author(self):
        """Returns the rule author."""
        if self._author:
            return self._author
        sigma_data = self.data

        if not sigma_data:
            return ''

        return sigma_data.get('author', '')

    @property
    def date(self):
        """Returns the rule date."""
        if self._date:
            return self._date
        sigma_data = self.data

        if not sigma_data:
            return ''

        return sigma_data.get('date', '')

    @property
    def modified(self):
        """Returns the rule modified date."""
        if self._modified:
            return self._modified
        sigma_data = self.data

        if not sigma_data:
            return ''

        return sigma_data.get('modified', '')

    @property
    def logsource(self):
        """Returns the rule logsource."""
        if self._logsource:
            return self._logsource
        sigma_data = self.data

        if not sigma_data:
            return ''

        return sigma_data.get('logsource', '')

    @property
    def detection(self):
        """Returns the rule detection."""
        if self._detection:
            return self._detection
        sigma_data = self.data

        if not sigma_data:
            return ''

        return sigma_data.get('detection', '')

    @property
    def references(self):
        """Returns the rule references."""
        if self._references:
            return self._references
        sigma_data = self.data

        if not sigma_data:
            return ''

        return sigma_data.get('references', '')

    def set_value(self, key, value):
        """Sets the value for a given key

        Args:
            key: key to set the value
            value: value to set

        """
        self.data[key] = value

    def from_rule_uuid(self, rule_uuid):
        """Get a Sigma object from a rule uuid.

        Args:
            rule_uuid: Id of the sigma rule.

        """
        self._rule_uuid = rule_uuid
        self.resource_uri = f'sigma/rule/{rule_uuid}'
        super().__init__(
            api=self.api, resource_uri=self.resource_uri)

        self.lazyload_data(refresh_cache=True)

    def from_text(self, rule_text):
        """Get a Sigma object from a rule text.

        Args:
            rule_text: Rule text to be parsed.

        """
        self.resource_uri = '{0:s}/sigma/text/'.format(self.api.api_root)
        data = {'title': 'Get_Sigma_by_text', 'content': rule_text}
        response = self.api.session.post(self.resource_uri, data=data)
        response_dict = error.get_response_json(response, logger)

        objects = response_dict.get('objects')

        if not objects:
            logger.warning(
                'Unable to parse rule with given text')

        rule_dict = objects[0]
        self._author = rule_dict.get('author', '')
        self._date = rule_dict.get('date', '')
        self._description = rule_dict.get('description', '')
        self._detection = rule_dict.get('detection', '')
        self._es_query = rule_dict.get('es_query', '')
        self._falsepositives = rule_dict.get('falsepositives', '')
        self._file_relpath = rule_dict.get('file_relpath', '')
        self._file_name = rule_dict.get('file_name', '')
        self._id = rule_dict.get('id', '')
        self._level = rule_dict.get('level', '')
        self._logsource = rule_dict.get('logsource', '')
        self._modified = rule_dict.get('modified', '')
        self._references = rule_dict.get('references', '')
        self._rule_uuid = rule_dict.get('id', '')
        self._title = rule_dict.get('title', '')
