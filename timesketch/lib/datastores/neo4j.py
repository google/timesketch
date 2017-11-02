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

from neo4jrestclient.client import GraphDatabase
from neo4jrestclient.constants import DATA_GRAPH

HIDDEN_FIELDS = [
    'type', 'id', 'sketch_id', 'source', 'target',
]

# Schema for Neo4j nodes and edges
SCHEMA = {
    u'nodes': {
        u'WindowsMachine': {
            u'label': u'\uf009\u00A0\u00A0{hostname}',
            u'hidden_fields': HIDDEN_FIELDS,
        },
        u'WindowsADUser': {
            u'label': u'\uf2c0\u00A0\u00A0{username}',
            u'hidden_fields': HIDDEN_FIELDS,
        },
        u'WindowsLocalUser': {
            u'label': u'\uf007\u00A0\u00A0{username}',
            u'hidden_fields': HIDDEN_FIELDS,
        },
        u'WindowsService': {
            u'label': u'{service_name}',
            u'hidden_fields': HIDDEN_FIELDS,
        },
        u'WindowsServiceImagePath': {
            u'label': u'\uf15b\u00A0\u00A0{image_path_short}',
            u'hidden_fields': HIDDEN_FIELDS,
        },
    },
    u'edges': {
        u'ACCESS': {
            u'label': u'{username} [{method}] ({count})',
            u'hidden_fields': HIDDEN_FIELDS,
            u'es_query': u'event_identifier:4624 AND xml_string:"{username}" AND xml_string:"{target.hostname}*"',  # pylint: disable=line-too-long
        },
        u'START': {
            u'label': u'{start_type} ({count})',
            u'hidden_fields': HIDDEN_FIELDS,
            u'es_query': u'event_identifier:7045 AND xml_string:"{start_type}" AND xml_string:"{source.service_name}" AND xml_string:"{target.hostname}*"',  # pylint: disable=line-too-long
        },
        u'HAS': {
            u'label': u'HAS',
            u'hidden_fields': HIDDEN_FIELDS,
            u'es_query': u'event_identifier:7045 AND xml_string:"{target.image_path}" AND xml_string:"{source.service_name}"',  # pylint: disable=line-too-long
        }
    }
}


class Neo4jDataStore(object):
    """Implements the Neo4j datastore.

    Attributes:
        client: Instance of Neo4j GraphDatabase
    """

    def __init__(self, username, password, host=u'127.0.0.1', port=7474):
        """Create a neo4j client.

        Args:
            username: Neo4j username
            password: Neo4j password
            host: Neo4j host
            port: Neo4j port
        """
        super(Neo4jDataStore, self).__init__()
        self.client = GraphDatabase(
            u'http://{0:s}:{1:d}/db/data/'.format(host, port),
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
        default_output_format = u'neo4j'
        formatter_registry = {
            u'neo4j': Neo4jOutputFormatter,
            u'cytoscape': CytoscapeOutputFormatter
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
        self.schema[u'stats'] = data.stats
        self.schema[u'graph'] = self.format_graph(data.graph)
        if return_rows:
            self.schema[u'rows'] = data.rows
        return self.schema

    def format_graph(self, graph):
        """Format the Neo4j graph result.

        Args:
            graph: Dictionary with Neo4j graph result

        Returns:
            Dictionary with formatted graph
        """
        if graph is None:
            return {u'nodes': [], u'edges': []}
        node_list = []
        edge_list = []
        for subgraph in graph:
            nodes = subgraph[u'nodes']
            edges = subgraph[u'relationships']
            for node in nodes:
                formatted_node = self.format_node(node)
                if formatted_node not in node_list:
                    node_list.append(formatted_node)
            for edge in edges:
                formatted_edge = self.format_edge(edge)
                if formatted_edge not in edge_list:
                    edge_list.append(formatted_edge)
        formatted_graph = {u'nodes': node_list, u'edges': edge_list}
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

    def __init__(self):
        """Initialize the Neo4j output formatter object."""
        super(Neo4jOutputFormatter, self).__init__()

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

    def __init__(self):
        """Initialize the Cytoscape output formatter object."""
        super(CytoscapeOutputFormatter, self).__init__()

    def format_node(self, node):
        """Format a Cytoscape graph node.

        Args:
            node: A dictionary with one node

        Returns:
            Dictionary with a Cytoscape formatted node
        """
        node_data = dict(id='node' + node[u'id'], type=node[u'labels'][0])
        if node.get('properties'):
            node_data.update(node['properties'])
        return {u'data': node_data}

    def format_edge(self, edge):
        """Format a Cytoscape graph egde.

        Args:
            edge: A dictionary with one edge

        Returns:
            Dictionary with a Cytoscape formatted edge
        """
        edge_data = dict(
            id='edge' + edge[u'id'], type=edge[u'type'],
            source='node' + edge[u'startNode'],
            target='node' + edge[u'endNode'],
        )
        if edge.get('properties'):
            edge_data.update(edge['properties'])
        return {u'data': edge_data}
