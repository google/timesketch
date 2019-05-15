# Copyright 2017 Google Inc. All rights reserved.
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
"""Neo4j graph datastore."""

from __future__ import unicode_literals

from neo4jrestclient.client import GraphDatabase
from neo4jrestclient.constants import DATA_GRAPH

HIDDEN_FIELDS = [
    'type', 'id', 'sketch_id', 'source', 'target',
]

# Schema for Neo4j nodes and edges
SCHEMA = {
    'nodes': {
        'WindowsMachine': {
            'label': '\uf009\u00A0\u00A0{hostname}',
            'hidden_fields': HIDDEN_FIELDS,
        },
        'WindowsADUser': {
            'label': '\uf2c0\u00A0\u00A0{username}',
            'hidden_fields': HIDDEN_FIELDS,
        },
        'WindowsLocalUser': {
            'label': '\uf007\u00A0\u00A0{username}',
            'hidden_fields': HIDDEN_FIELDS,
        },
        'WindowsService': {
            'label': '{service_name}',
            'hidden_fields': HIDDEN_FIELDS,
        },
        'WindowsServiceImagePath': {
            'label': '\uf15b\u00A0\u00A0{image_path_short}',
            'hidden_fields': HIDDEN_FIELDS,
        },
    },
    'edges': {
        'ACCESS': {
            'label': '{username} [{method}] ({count})',
            'hidden_fields': HIDDEN_FIELDS,
            'es_query': 'event_identifier:4624 AND xml_string:"{username}" AND xml_string:"{target.hostname}*"',  # pylint: disable=line-too-long
        },
        'START': {
            'label': '{start_type} ({count})',
            'hidden_fields': HIDDEN_FIELDS,
            'es_query': 'event_identifier:7045 AND xml_string:"{start_type}" AND xml_string:"{source.service_name}" AND xml_string:"{target.hostname}*"',  # pylint: disable=line-too-long
        },
        'HAS': {
            'label': 'HAS',
            'hidden_fields': HIDDEN_FIELDS,
            'es_query': 'event_identifier:7045 AND xml_string:"{target.image_path}" AND xml_string:"{source.service_name}"',  # pylint: disable=line-too-long
        }
    }
}


class Neo4jDataStore(object):
    """Implements the Neo4j datastore.

    Attributes:
        client: Instance of Neo4j GraphDatabase
    """

    def __init__(self, username, password, host='127.0.0.1', port=7474):
        """Create a neo4j client.

        Args:
            username: Neo4j username
            password: Neo4j password
            host: Neo4j host
            port: Neo4j port
        """
        super(Neo4jDataStore, self).__init__()
        self.client = GraphDatabase(
            'http://{0:s}:{1:d}/db/data/'.format(host, port),
            username=username,
            password=password)

    @staticmethod
    def _get_formatter(output_format):
        """Get format class instance from format name.

        Args:
            output_format: Name as string of output format

        Returns:
            Output formatter object
        """
        default_output_format = 'neo4j'
        formatter_registry = {
            'neo4j': Neo4jOutputFormatter,
            'cytoscape': CytoscapeOutputFormatter
        }
        formatter = formatter_registry.get(output_format, None)
        if not formatter:
            formatter = formatter_registry.get(default_output_format)
        return formatter()

    def query(self, query, params=None, output_format=None, return_rows=False):
        """Search the graph.

        Args:
            query: A cypher query
            params: A dictionary with query parameters
            output_format: Name of the output format to use
            return_rows: Boolean indicating if rows should be returned

        Returns:
            Dictionary with formatted query result
        """
        data_content = DATA_GRAPH
        if return_rows:
            data_content = True
        query_result = self.client.query(
            query, params=params, data_contents=data_content)
        formatter = self._get_formatter(output_format)
        return formatter.format(query_result, return_rows)


class OutputFormatterBaseClass(object):
    """Base class for output formatter.

    Attributes:
        schema: Dictionary structure to return
    """

    def __init__(self):
        """Initialize the output formatter object."""
        super(OutputFormatterBaseClass, self).__init__()
        self.schema = dict(stats=None, rows=None, graph=None)

    def format(self, data, return_rows):
        """Format Neo4j query result.

        Args:
            data: Neo4j query result dictionary
            return_rows: Boolean indicating if rows should be returned

        Returns:
            Dictionary with formatted result
        """
        self.schema['stats'] = data.stats
        self.schema['graph'] = self.format_graph(data.graph)
        if return_rows:
            self.schema['rows'] = data.rows
        return self.schema

    def format_graph(self, graph):
        """Format the Neo4j graph result.

        Args:
            graph: Dictionary with Neo4j graph result

        Returns:
            Dictionary with formatted graph
        """
        if graph is None:
            return {'nodes': [], 'edges': []}
        node_list = []
        edge_list = []
        for subgraph in graph:
            nodes = subgraph['nodes']
            edges = subgraph['relationships']
            for node in nodes:
                formatted_node = self.format_node(node)
                if formatted_node not in node_list:
                    node_list.append(formatted_node)
            for edge in edges:
                formatted_edge = self.format_edge(edge)
                if formatted_edge not in edge_list:
                    edge_list.append(formatted_edge)
        formatted_graph = {'nodes': node_list, 'edges': edge_list}
        return formatted_graph

    # pylint: disable=unused-argument
    def format_node(self, node):
        """Format a graph node.

        Args:
            node: A dictionary with one node
        """
        return NotImplemented

    # pylint: disable=unused-argument
    def format_edge(self, edge):
        """Format a graph edge.

        Args:
            edge: A dictionary with one edge
        """
        return NotImplemented


class Neo4jOutputFormatter(OutputFormatterBaseClass):
    """Neo4j raw formatter.

    This formatter will return the original Neo4j result
    without any formatting.
    """

    def format_graph(self, graph):
        """Format the Neo4j graph result.

        Args:
            graph: Dictionary with Neo4j graph result

        Returns:
            Dictionary with formatted graph
        """
        return graph


class CytoscapeOutputFormatter(OutputFormatterBaseClass):
    """Cytoscape formatter.

    This formatter will return the graph compatible with the open source
    graph Javascript library Cytoscape (http://js.cytoscape.org/).
    """

    def format_node(self, node):
        """Format a Cytoscape graph node.

        Args:
            node: A dictionary with one node

        Returns:
            Dictionary with a Cytoscape formatted node
        """
        node_data = dict(id='node' + node['id'], type=node['labels'][0])
        if node.get('properties'):
            node_data.update(node['properties'])
        return {'data': node_data}

    def format_edge(self, edge):
        """Format a Cytoscape graph egde.

        Args:
            edge: A dictionary with one edge

        Returns:
            Dictionary with a Cytoscape formatted edge
        """
        edge_data = dict(
            id='edge' + edge['id'], type=edge['type'],
            source='node' + edge['startNode'],
            target='node' + edge['endNode'],
        )
        if edge.get('properties'):
            edge_data.update(edge['properties'])
        return {'data': edge_data}
