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

    def _get_top_level_attribute(self, name, default_value=None, refresh=False):
        """Returns a top level attribute from a view object.

        Args:
            name: String with the attribute name.
            default_value: The default value if the attribute does not exit,
                defaults to None.
            refresh: If set to True then the data will be refreshed.

        Returns:
            The dict value of the key "name".
        """
        view = self.lazyload_data(refresh_cache=refresh)
        objects = view.get('objects')
        if not objects:
            return ''
        if not len(objects) == 1:
            return ''

        first_object = objects[0]
        return first_object.get(name, default_value)

    @property
    def description(self):
        """Property that returns the description value of a view.

        Returns:
            Description of the view as a string.
        """
        return self._get_top_level_attribute('description', default_value='')

    @property
    def query_string(self):
        """Property that returns the views query string.

        Returns:
            Elasticsearch query as string.
        """
        return self._get_top_level_attribute('query_string', default_value='')

    @property
    def query_filter(self):
        """Property that returns the views filter.

        Returns:
            Elasticsearch filter as JSON string.
        """
        return self._get_top_level_attribute('query_filter', default_value='')

    @property
    def query_dsl(self):
        """Property that returns the views query DSL.

        Returns:
            Elasticsearch DSL as JSON string.
        """
        return self._get_top_level_attribute('query_dsl', default_value='')
