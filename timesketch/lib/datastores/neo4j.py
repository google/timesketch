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


def get_node_object(entity):
    node_registry = {
        u'Machine': MachineNode,
        u'User': UserNode,
        u'Service': ServiceNode,
        u'ServiceImagePath': ServiceImagePathNode
    }

    edge_registry = {
        u'ACCESS': AccessEdge,
        u'START': StartEdge,
        u'HAS': HasEdge
    }

    try:
        _type = entity[u'labels'][0]
        registry = node_registry
    except KeyError:
        _type = entity[u'type']
        registry = edge_registry

    return registry.get(_type)(entity)


class BaseEdgeNode(object):

    def __init__(self, node):
        self.id = node[u'id']
        try:
            self.type = node[u'labels'][0]
        except KeyError:
            self.type = node[u'type']
            self.startNode = node[u'startNode']
            self.endNode = node[u'endNode']

        properties = node[u'properties']
        for key in properties:
            setattr(self, key, properties[key])

    @property
    def human_readable(self):
        return NotImplemented

    def to_dict(self):
        attributes = self.__dict__
        attributes[u'human_readable'] = self.human_readable
        return attributes


class MachineNode(BaseEdgeNode):

    def __init__(self, node):
        super(MachineNode, self).__init__(node)

    @property
    def human_readable(self):
        return self.hostname


class UserNode(BaseEdgeNode):

    def __init__(self, node):
        super(UserNode, self).__init__(node)

    @property
    def human_readable(self):
        return self.username


class ServiceNode(BaseEdgeNode):

    def __init__(self, node):
        super(ServiceNode, self).__init__(node)

    @property
    def human_readable(self):
        return self.service_name


class ServiceImagePathNode(BaseEdgeNode):

    def __init__(self, node):
        super(ServiceImagePathNode, self).__init__(node)

    @property
    def human_readable(self):
        return self.image_path


class AccessEdge(BaseEdgeNode):

    def __init__(self, edge):
        super(AccessEdge, self).__init__(edge)

    @property
    def human_readable(self):
        return self.method


class StartEdge(BaseEdgeNode):

    def __init__(self, edge):
        super(StartEdge, self).__init__(edge)

    @property
    def human_readable(self):
        return self.start_type


class HasEdge(BaseEdgeNode):

    def __init__(self, edge):
        super(HasEdge, self).__init__(edge)

    @property
    def human_readable(self):
        return self.type


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

    def search(self, query, output_format=None, return_rows=False):
        """Search the graph.

        Args:
            query: A cypher query
            output_format: Name of the output format to use
            return_rows: Boolean indicating if rows should be returned

        Returns:
            Dictionary with formatted query result
        """
        data_content = DATA_GRAPH
        if return_rows:
            data_content = True
        query_result = self.client.query(query, data_contents=data_content)
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

    def _human_readable_helper(self, data):
        """Helper function to format human readable string

        Args:
            data: Dictionary for a Node or Edge

        Returns:
            Human readable string
        """

    def format_node(self, node):
        """Format a Cytoscape graph node.

        Args:
            node: A dictionary with one node

        Returns:
            Dictionary with a Cytoscape formatted node
        """
        node_dict = get_node_object(node).to_dict()
        cytoscape_node = {u'data': node_dict}
        return cytoscape_node

    def format_edge(self, edge):
        """Format a Cytoscape graph egde.

        Args:
            edge: A dictionary with one edge

        Returns:
            Dictionary with a Cytoscape formatted edge
        """
        edge_dict = get_node_object(edge).to_dict()
        edge_dict[u'source'] = edge_dict.pop(u'startNode')
        edge_dict[u'target'] = edge_dict.pop(u'endNode')
        cytoscape_edge = {u'data': edge_dict}
        return cytoscape_edge
