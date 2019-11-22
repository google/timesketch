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


class View(resource.BaseResource):
    """Saved view object.

    Attributes:
        id: Primary key of the view.
        name: Name of the view.
    """

    def __init__(self, view_id, view_name, sketch_id, api):
        """Initializes the View object.

        Args:
            view_id: Primary key ID for the view.
            view_name: The name of the view.
            sketch_id: ID of a sketch.
            api: Instance of a TimesketchApi object.
        """
        self.id = view_id
        self.name = view_name
        resource_uri = 'sketches/{0:d}/views/{1:d}/'.format(sketch_id, self.id)
        super(View, self).__init__(api, resource_uri)

    @property
    def query_string(self):
        """Property that returns the views query string.

        Returns:
            Elasticsearch query as string.
        """
        view = self.lazyload_data()
        return view['objects'][0]['query_string']

    @property
    def query_filter(self):
        """Property that returns the views filter.

        Returns:
            Elasticsearch filter as JSON string.
        """
        view = self.lazyload_data()
        return view['objects'][0]['query_filter']

    @property
    def query_dsl(self):
        """Property that returns the views query DSL.

        Returns:
            Elasticsearch DSL as JSON string.
        """
        view = self.lazyload_data()
        return view['objects'][0]['query_dsl']
