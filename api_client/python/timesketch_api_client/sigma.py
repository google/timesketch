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
import pandas

from . import resource

logger = logging.getLogger('timesketch_api.sigma')


class Sigma(resource.BaseResource):
    """Timesketch sigma object.

    A sigma object in Timesketch is a collection of one or more rules.

    Attributes:
        rule_uuid: The ID of the rule.
    """


    def __init__(self, rule_uuid, api):
        """Initializes the Sigma object.

        Args:
            rule_uuid: Id of the sigma rule.
            api: An instance of TimesketchApi object.

        """
        self.rule_uuid = rule_uuid
        self._resource_uri = f'sigma/{self.rule_uuid}'
        super().__init__(
            api=api, resource_uri=self._resource_uri)

    @property
    def es_query(self):
        """Returns the elastic search query."""
        sigma_data = self.data

        if not sigma_data:
            return None

        return sigma_data.get('es_query', None)

    @property
    def title(self):
        """Returns the sigma rule title."""
        sigma_data = self.data

        if not sigma_data:
            return None

        return sigma_data.get('title', None)

    @property
    def id(self):
        """Returns the sigma rule id."""
        sigma_data = self.data

        if not sigma_data:
            return None

        return sigma_data.get('id', None)

    def to_pandas(self):
        """Returns a pandas DataFrame."""
        sigma_data = self.data

        if not sigma_data:
            return pandas.DataFrame()

        return pandas.DataFrame(sigma_data)
