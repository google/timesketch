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

import json
import logging

from . import error
from . import resource


logger = logging.getLogger('timesketch_api.index')


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
        self._labels = []
        self._searchindex_name = searchindex_name
        self._resource_uri = 'searchindices/{0:d}'.format(self.id)
        super(SearchIndex, self).__init__(
            api=api, resource_uri=self._resource_uri)

    def _get_object_dict(self):
        """Returns the object dict from the resources dict."""
        data = self.lazyload_data()
        objects = data.get('objects', [])
        if not objects:
            return {}

        return objects[0]

    @property
    def labels(self):
        """Property that returns the SearchIndex labels."""
        if self._labels:
            return self._labels

        index_data = self._get_object_dict()
        if not index_data:
            return self._labels

        label_string = index_data.get('label_string', '')
        if label_string:
            self._labels = json.loads(label_string)
        else:
            self._labels = []

        return self._labels

    @property
    def name(self):
        """Property that returns searchindex name.

        Returns:
            Searchindex name as string.
        """
        if not self._searchindex_name:
            index_data = self._get_object_dict()
            self._searchindex_name = index_data.get('name', 'no name defined')
        return self._searchindex_name

    @property
    def index_name(self):
        """Property that returns Elasticsearch index name.

        Returns:
            Elasticsearch index name as string.
        """
        index_data = self._get_object_dict()
        return index_data.get('index_name', 'unkown index name')

    @property
    def status(self):
        """Property that returns the index status.

        Returns:
            String with the index status.
        """
        index_data = self._get_object_dict()
        status_list = index_data.get('status')
        if not status_list:
            return 'Unknown'

        status = status_list[0]
        return status.get('status')

    @property
    def description(self):
        """Property that returns the description of the index."""
        index_data = self._get_object_dict()
        return index_data.get('description', 'no description provided')

    def delete(self):
        """Deletes the index."""
        resource_url = '{0:s}/searchindices/{1:d}/'.format(
            self.api.api_root, self.id)
        response = self.api.session.delete(resource_url)
        return error.check_return_status(response, logger)
