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

from . import resource


class SearchIndex(resource.BaseResource):
    """Timesketch searchindex object.

    Attributes:
        id: The ID of the search index.
        api: An instance of TimesketchApi object.
    """

    def __init__(self, searchindex_id, api, searchindex_name=None):
        """Initializes the SearchIndex object.

        Args:
            searchindex_id: Primary key ID of the searchindex.
            searchindex_name: Name of the searchindex (optional).
        """
        self.id = searchindex_id
        self._searchindex_name = searchindex_name
        self._resource_uri = 'searchindices/{0:d}'.format(self.id)
        super(SearchIndex, self).__init__(
            api=api, resource_uri=self._resource_uri)

    @property
    def name(self):
        """Property that returns searchindex name.

        Returns:
            Searchindex name as string.
        """
        if not self._searchindex_name:
            searchindex = self.lazyload_data()
            self._searchindex_name = searchindex['objects'][0]['name']
        return self._searchindex_name

    @property
    def index_name(self):
        """Property that returns Elasticsearch index name.

        Returns:
            Elasticsearch index name as string.
        """
        searchindex = self.lazyload_data()
        return searchindex['objects'][0]['index_name']

    def delete(self):
        """Deletes the index."""
        resource_url = '{0:s}/searchindices/{1:d}/'.format(
            self.api.api_root, self.id)
        response = self.api.session.delete(resource_url)
        return response.status_code in definitions.HTTP_STATUS_CODE_20X

