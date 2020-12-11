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
"""Timesketch API graph object."""
import datetime
import json
import logging

import pandas

from . import error
from . import resource


logger = logging.getLogger('timesketch_api.graph')

"""
    (GraphListResource, '/sketches/<int:sketch_id>/graphs/'),
    (GraphResource, '/sketches/<int:sketch_id>/graphs/<int:graph_id>/'),
    (GraphPluginListResource, '/graphs/'),
    (GraphCacheResource, '/sketches/<int:sketch_id>/graph/')
"""

class Graph(resource.SketchResource):
    """Graph object."""

    def __init__(self, sketch):
        resource_uri = f'sketches/{sketch.id}/graphs/'
        super().__init__(sketch=sketch, resource_uri=resource_uri)

        self._sketch_id = sketch.id

        self._created_at = ''
        self._description = ''
        self._max_entries = self.DEFAULT_SIZE_LIMIT
        self._name = ''
        self._query_dsl = ''
        self._query_filter = {}
        self._query_string = ''
        self._raw_response = None
        self._return_fields = ''
        self._scrolling = None
        self._searchtemplate = ''
        self._updated_at = ''

    @property
    def created_at(self):
        """Property that returns back the creation time of a search."""
        return self._created_at

    def delete(self):
        """Deletes the saved graph from the store."""
        # TODO: Implement this in the API.
        if not self._resource_id:
            logger.warning(
                'Unable to delete the saved graph, it does not appear to be '
                'saved in the first place.')
            return False

        # TODO: FIX THE RESOURCE URL
        resource_url = (
            f'{self.api.api_root}/sketches/{self._sketch.id}/views/'
            f'{self._resource_id}/')
        response = self.api.session.delete(resource_url)
        return error.check_return_status(response, logger)

    @property
    def description(self):
        """Property that returns back the description of the saved search."""
        return self._description

    @description.setter
    def description(self, description):
        """Make changes to the saved search description field."""
        self._description = description
        self.save()

    def from_manual(  # pylint: disable=arguments-differ
            self,
            **kwargs):
        """Generate a new graph.

        Args:
            kwargs (dict[str, object]): Depending on the resource they may
                require different sets of arguments to be able to run a raw
                API request.

        Raises:
            ValueError: if unable to query for the results.
            RuntimeError: if the query is missing needed values, or if the
                sketch is archived.
        """
        super().from_manual(**kwargs)
        # TODO: Implement

    def from_cache(self, plugin_name, plugin_config=None, refresh=False):
        """Initialize the graph from a cached graph."""
        resource_url = f'{self.api.api_root}/sketches/{self._sketch_id}/graph/'
        data = {
            'plugin': plugin_name,
            'config': plugin_config,
            'refresh': refresh
        }

        response = self.api.session.post(resource_url, json=data)
        status = error.check_return_status(response, logger)
        if not status:
            error.error_message(
                response, 'Unable to retrieve cached graph', error=RuntimeError)

        response_json = error.get_response_json(response, logger)
        cache_dict = response_json.get('objects', [{}])[0]
        # TODO: Complete this implementation.
        return cache_dict

    def from_saved(self, graph_id):  # pylint: disable=arguments-differ
        """Initialize the graph object from a saved graph.

        Args:
            search_id: integer value for the saved
                search (primary key).
        """
        # TODO: Implement.

    @property
    def name(self):
        """Property that returns the query name."""
        return self._name

    @name.setter
    def name(self, name):
        """Make changes to the saved search name."""
        self._name = name
        self.commit()

    def save(self):
        """Save the search in the database.

        Raises:
            ValueError: if there are values missing in order to save the query.
        """
        if not self.name:
            raise ValueError(
                'No name for the query saved. Please select a name first.')

        if not self.description:
            logger.warning(
                'No description selected for search, saving without one')

        if self._resource_id:
            resource_url = (
                f'{self.api.api_root}/sketches/{self._sketch.id}/views/'
                f'{self._resource_id}/')
        else:
            resource_url = (
                f'{self.api.api_root}/sketches/{self._sketch.id}/views/')

        return False
        # TODO: Implement this.
        data = {
            'name': self.name,
            'description': self.description,
            'query': self.query_string,
            'filter': self.query_filter,
            'dsl': self.query_dsl,
            'labels': json.dumps(self.labels),
        }
        response = self.api.session.post(resource_url, json=data)
        status = error.check_return_status(response, logger)
        if not status:
            error.error_message(
                response, 'Unable to save search', error=RuntimeError)

        response_json = error.get_response_json(response, logger)
        search_dict = response_json.get('objects', [{}])[0]
        self._resource_id = search_dict.get('id', 0)
        return f'Saved search to ID: {self._resource_id}'

    def to_dict(self):
        """Returns a dict with the respone of the query."""
        if not self._raw_response:
            self._execute_query()

        return self._raw_response

    def to_pandas(self):
        """The interface requires this to be implemented."""
        return pandas.DataFrame()
