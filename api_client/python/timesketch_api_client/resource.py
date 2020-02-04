# Copyright 2019 Google Inc. All rights reserved.
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
"""Timesketch API client library."""
from __future__ import unicode_literals


class BaseResource(object):
    """Base resource object."""

    def __init__(self, api, resource_uri):
        """Initialize object.

        Args:
            api: An instance of TimesketchApi object.
        """
        self.api = api
        self.resource_uri = resource_uri
        self.resource_data = None

    def lazyload_data(self, refresh_cache=False):
        """Load resource data once and cache the result.

        Args:
            refresh_cache: Boolean indicating if to update cache.

        Returns:
            Dictionary with resource data.
        """
        if not self.resource_data or refresh_cache:
            self.resource_data = self.api.fetch_resource_data(self.resource_uri)
        return self.resource_data

    @property
    def data(self):
        """Property to fetch resource data.

        Returns:
            Dictionary with resource data.
        """
        return self.lazyload_data()
