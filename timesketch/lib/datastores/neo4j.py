# Copyright 2015 Google Inc. All rights reserved.
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
"""Neo4j graph database."""

from neo4jrestclient.client import GraphDatabase
from neo4jrestclient.constants import DATA_GRAPH


class Neo4jDataStore(object):
    """Implements the datastore."""
    def __init__(self, username, password, host=u'127.0.0.1', port=7474):
        """Create a neo4j client."""
        super(Neo4jDataStore, self).__init__()
        self.client = GraphDatabase(
            u'http://{0:s}:{1:d}/db/data/'.format(host, port),
            username=username, password=password)

    @staticmethod
    def _get_formatter(output_format):
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
        data_content = DATA_GRAPH
        if return_rows:
            data_content = True
        query_result = self.client.query(query, data_contents=data_content)
        formatter = self._get_formatter(output_format)
        return formatter.format(query_result, return_rows)


class OutputFormatterBaseClass(object):
    def __init__(self):
        super(OutputFormatterBaseClass, self).__init__()
        self.schema = dict(stats=None, rows=None, graph=None)

    def format(self, data, return_rows):
        self.schema[u'stats'] = data.stats
        self.schema[u'graph'] = self.format_graph(data.graph)
        if return_rows:
            self.schema[u'rows'] = data.rows
        return self.schema

    def format_graph(self, graph):
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

    def format_node(self, node):
        return NotImplemented

    def format_edge(self, edge):
        return NotImplemented


class Neo4jOutputFormatter(OutputFormatterBaseClass):
    def __init__(self):
        super(Neo4jOutputFormatter, self).__init__()

    def format_graph(self, graph):
        return graph


class CytoscapeOutputFormatter(OutputFormatterBaseClass):
    def __init__(self):
        super(CytoscapeOutputFormatter, self).__init__()

    def format_node(self, node):
        cytoscape_node = {
            u'data': {
                u'id': node[u'id'],
                u'label': node[u'properties'][u'name'],
                u'type': node[u'labels'][0]
            }
        }
        return cytoscape_node

    def format_edge(self, edge):
        try:
            label = edge[u'properties'][u'human_readable']
        except KeyError:
            label = edge[u'type']
        cytoscape_edge = {
            u'data': {
                u'id': edge[u'id'],
                u'source': edge[u'startNode'],
                u'target': edge[u'endNode'],
                u'label': label
            }
        }
        return cytoscape_edge
