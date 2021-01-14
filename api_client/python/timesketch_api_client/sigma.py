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
        self.api = api
        self._rule_uuid = None
        self._file_name = None
        self._title = None
        self._file_relpath = None
        self._es_query = None
        self._resource_uri = 'sigma/' # TODO: clarify: is that okay?
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
        sigma_data = self.data

        if not sigma_data:
            self.lazyload_data()
            return ''

        return sigma_data.get('id', '')

    @property
    def file_relpath(self):
        """Returns the relative filepath of the rule."""
        sigma_data = self.data

        if not sigma_data:
            return ''

        return sigma_data.get('file_relpath', '')

    @property
    def rule_uuid(self):
        """Returns the elastic search query."""
        sigma_data = self.data

        if not sigma_data:
            return ''

        return sigma_data.get('id', '')

    def from_rule_uuid(self, rule_uuid):
        """Get a Sigma object from a rule uuid.

        Args:
            rule_uuid: Id of the sigma rule.

        """
        self._rule_uuid = rule_uuid
        # TODO: not sure which one is the better one
        self.resource_uri = f'sigma/rule/{rule_uuid}'
        super().__init__(
            api=self.api, resource_uri=self.resource_uri)

        self.lazyload_data(refresh_cache=True)

    def from_text(self, rule_text):
        """Get a Sigma object from a rule text.

        Args:
            rule_text: Rule text to be parsed.

        """
        print(rule_text)
        self.resource_uri = '{0:s}/sigma/text/'.format(self.api.api_root)
        data = {'title': 'Get_Sigma_by_text', 'content': rule_text}
        response = self.api.session.post(self.resource_uri, data=data)
        response_dict = error.get_response_json(response, logger)
        print(f'dict: {response_dict}')

        objects = response_dict.get('objects')

        if not objects:
            logger.warning(
                'Unable to parse rule with given text')

        rule_dict = objects[0]
        self._rule_uuid = '' # rule has no id, or maybe it has?
        self._title = rule_dict.get('title', '')
        self._es_query = rule_dict.get('es_query', '')
        return response_dict
