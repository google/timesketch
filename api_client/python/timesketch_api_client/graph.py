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
import copy
import json
import logging

import dateutil.parser
import pandas
import networkx as nx

from . import error
from . import resource


logger = logging.getLogger('timesketch_api.graph')

"""
    (GraphListResource, '/sketches/<int:sketch_id>/graphs/'),
    (GraphResource, '/sketches/<int:sketch_id>/graphs/<int:graph_id>/'),
    (GraphPluginListResource, '/graphs/'),
"""

class Graph(resource.SketchResource):
    """Graph object."""

    def __init__(self, sketch):
        resource_uri = f'sketches/{sketch.id}/graphs/'
        super().__init__(sketch=sketch, resource_uri=resource_uri)

        self._created_at = None
        self._graph = None
        self._description = ''
        self._name = ''
        self._updated_at = None

    @property
    def created_at(self):
        """Property that returns back the creation time of a search."""
        if self._created_at:
            return self._created_at.isoformat()
        return self._created_at

    @property
    def graph(self):
        """Property that returns back a graph object."""
        if self._graph:
            return self._graph

        if not self.resource_data:
            return nx.Graph()

        graph_dict = copy.deepcopy(self.resource_data)
        self._graph = nx.cytoscape_graph(graph_dict)
        return self._graph

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
        # TODO: Implement
        super().from_manual(**kwargs)
        self._resource_id = 0
        self.resource_data = {}

    def _parse_graph_dict(self, graph_dict):
        """Takes a dict object and constructs graph data from it."""
        graph_string = graph_dict.get('graph_elements')

        if isinstance(graph_string, str):
            try:
                self.resource_data = json.loads(graph_string)
            except json.JSONDecodeError as exc:
                raise ValueError('Unable to read graph data') from exc
        elif isinstance(graph_string, dict):
            self.resource_data = graph_string
        else:
            raise ValueError('Graph elements missing or not of correct value.')

        self._created_at = dateutil.parser.parse(
            graph_dict.get('created_at', ''))
        self._updated_at = dateutil.parser.parse(
            graph_dict.get('updated_at', ''))

    def from_plugin(self, plugin_name, plugin_config=None, refresh=False):
        """Initialize the graph from a cached plugin graph.

        Args:
            plugin_name (str): the name of the graph plugin to use.
            plugin_config (dict): optional dictionary to configure the plugin.
            refresh (bool): optional bool that if set refreshes the graph,
                otherwise the graph is pulled from the cache, if it exists.
                Defaults to False, meaning it pulls from the cache if it
                exists.
        """
        plugin_names = [x.get('name', '') for x in self.plugins]
        if plugin_name.lower() not in plugin_names:
            raise ValueError(
                f'Plugin [{plugin_name}] not part of the supported plugins.')

        resource_url = f'{self.api.api_root}/sketches/{self._sketch.id}/graph/'
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
        self._parse_graph_dict(cache_dict)
        self._description = f'Graph created from the {plugin_name} plugin.'

    def from_saved(self, graph_id):  # pylint: disable=arguments-differ
        """Initialize the graph object from a saved graph.

        Args:
            graph_id: integer value for the saved graph (primary key).
        """
        resource_id = f'sketches/{self._sketch.id}/graphs/{graph_id}/'
        data = self.api.fetch_resource_data(resource_id)
        objects = data.get('objects')
        if not objects:
            logger.warning(
                'Unable to load saved graph with ID: %d, '
                'are you sure it exists?', graph_id)
        graph_dict = objects[0]
        self._parse_graph_dict(graph_dict)

        self._resource_id = graph_id
        self._name = graph_dict.get('name', 'No name')
        self._description = graph_dict.get('description', '')
        self._username = graph_dict.get('user', {}).get('username', 'System')
        self._updated_at = dateutil.parser.parse(
            graph_dict.get('updated_at', ''))

    def from_graph(self, graph_obj):
        """Initialize from a networkx graph object."""
        if not graph_obj.size():
            logger.warning('Unable to load graph from an empty graph object.')
            return
        self.resource_data = nx.cytoscape_data(graph_obj)
        self._graph = graph_obj
        self._name = ''
        self._description = 'From a graph object.'

    @property
    def name(self):
        """Property that returns the query name."""
        return self._name

    @name.setter
    def name(self, name):
        """Make changes to the saved search name."""
        self._name = name
        self.commit()

    @property
    def plugins(self):
        """Property that returns back the supported plugins."""
        plugin_dict = self.api.fetch_resource_data('graphs/')
        return plugin_dict

    @property
    def plugins_table(self):
        """Property that returns a dataframe with the available plugins."""
        return pandas.DataFrame(self.plugins)

    def save(self):
        """Save the search in the database.

        Raises:
            ValueError: if there are values missing in order to save the query.
        """
        if not self.name:
            raise ValueError(
                'No name for the graph. Please select a name first.')

        if not self.description:
            logger.warning(
                'No description selected for graph, saving without one')

        if self._resource_id:
            # pylint: disable=unused-variable
            # TODO: Remove this when completed implemention.
            resource_url = (
                f'{self.api.api_root}/sketches/{self._sketch.id}/graphs/'
                f'{self._resource_id}/')
        else:
            resource_url = (
                f'{self.api.api_root}/sketches/{self._sketch.id}/graphs/')

        return False

    def to_dict(self):
        """Returns a dict with the graph content."""
        return self.resource_data

    def to_pandas(self):
        """Returns a pandas dataframe with the graph content."""
        if not self.resource_data:
            return pandas.DataFrame()

        data = self.resource_data
        elements = data.get('elements', {})
        nodes = elements.get('nodes', [])
        edges = elements.get('edges', [])

        node_list = [x.get('data') for x in nodes]
        edge_list = [x.get('data') for x in edges]
        node_df = pandas.DataFrame(node_list)
        node_df['type'] = 'node'
        edge_df = pandas.DataFrame(edge_list)
        edge_df['type'] = 'edge'
        return pandas.concat([node_df, edge_df])
