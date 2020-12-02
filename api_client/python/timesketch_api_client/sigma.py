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

logger = logging.getLogger('timesketch_api.sigma')


class Sigma(resource.BaseResource):
    """Timesketch sigma object.

    A sigma object in Timesketch is a collection of one or more rules.

    Attributes:
        rule_uuid: The ID of the rule.
    """


    def __init__(self, rule_uuid, api, es_query=None,
                 file_name=None, title=None, description=None,
                 file_relpath=None):
        """Initializes the Sigma object.

        Args:
            rule_uuid: Id of the sigma rule.
            api: An instance of TimesketchApi object.
            es_query: Elastic Search query of the rule
            file_name: File name of the rule
            title: Title of the rule
            description: Description of the rule
            file_relpath: path of the file relative to the config value

        """
        self.rule_uuid = rule_uuid
        self._description = description
        self._es_query = es_query
        self._file_name = file_name
        self._title = title
        self._file_relpath = file_relpath
        self._resource_uri = f'sigma/{self.rule_uuid}'
        super().__init__(
            api=api, resource_uri=self._resource_uri)

    @property
    def es_query(self):
        """Returns the elastic search query."""
        sigma_data = self.data

        if not sigma_data:
            return ''

        return sigma_data.get('es_query', '')

    @property
    def title(self):
        """Returns the sigma rule title."""
        sigma_data = self.data

        if not sigma_data:
            return ''

        return sigma_data.get('title', '')

    @property
    def id(self):
        """Returns the sigma rule id."""
        sigma_data = self.data

        if not sigma_data:
            return ''

        return sigma_data.get('id', '')

    @property
    def file_relpath(self):
        """Returns the relative filepath of the rule."""
        sigma_data = self.data

        if not sigma_data:
            return ''

        return sigma_data.get('file_relpath', '')
