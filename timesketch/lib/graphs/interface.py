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
"""Interface for graphs."""

from flask import current_app
from timesketch.lib.datastores.elastic import ElasticsearchDataStore

import networkx as nx

import hashlib

GRAPH_TYPES = {
    'Graph': nx.Graph,
    'MultiGraph': nx.MultiGraph,
    'DiGraph': nx.DiGraph,
    'MultiDiGraph': nx.MultiDiGraph
}


class Graph(object):
    def __init__(self, graph_type):
        _nx_graph_class = GRAPH_TYPES.get(graph_type)
        self.nx_instance = _nx_graph_class()
        self.nodes = {}
        self.edges = {}

    def add_node(self, label, attributes):
        node = Node(label, attributes)
        self.nodes[node.id] = node
        return node

    def add_edge(self, source, target, label, event, attributes=None):

        edge_id_string = ''.join([source.id, target.id, label])
        edge_id = hashlib.md5(edge_id_string.encode('utf-8')).hexdigest()

        try:
            edge = self.edges[edge_id]
        except KeyError:
            edge = Edge(source, target, label, attributes)

        if edge.event_counter < 500:
            index = event.get('_index')
            doc_id = event.get('_id')
            events = edge.attributes.get('events', {})
            doc_ids = events.get(index, [])
            doc_ids.append(doc_id)
            edge.event_counter += 1
            events[index] = doc_ids
            edge.add_attribute('events', events)

        self.edges[edge_id] = edge

    def commit(self):
        for node_id, node in self.nodes.items():
            print('Adding node: ', node.label)
            self.nx_instance.add_node(
                node_id, label=node.label, **node.attributes)

        for edge_id, edge in self.edges.items():
            label = edge.label + ' ({0:d})'.format(edge.event_counter)
            print('Adding edge: ({}) --[{}]--> ({})'.format(edge.source.label, label, edge.target.label))
            self.nx_instance.add_edge(
                edge.source.id, edge.target.id, label=label,
                **edge.attributes)

    def to_json(self):
        _json = nx.readwrite.json_graph.cytoscape_data(self.nx_instance)
        return _json.get('elements', [])


class BaseGraphElement(object):
    def __init__(self, label='', attributes=None):
        self.label = label
        self.attributes = attributes or {}
        self.id = self.id_from_label(label)

    @staticmethod
    def id_from_label(label):
        return hashlib.md5(label.encode('utf-8')).hexdigest()

    def add_label(self, label):
        self.label = label
        self.id = self.id_from_label(label)

    def add_attribute(self, key, value):
        self.attributes[key] = value


class Node(BaseGraphElement):
    def __init__(self, label='', attributes=None):
        super(Node, self).__init__(label, attributes)


class Edge(BaseGraphElement):
    def __init__(self, source, target, label='', attributes=None):
        self.source = source
        self.target = target
        self.event_counter = 0
        super(Edge, self).__init__(label, attributes)


class BaseGraphPlugin(object):
    """Base class for a graph."""

    # Name that the graph will be registered as.
    NAME = 'name'

    # Type of graph. See NetworkX documentation for details:
    # https://networkx.org/documentation/stable/reference/classes/index.html
    GRAPH_TYPE = 'DiGraph'

    def __init__(self):
        """Initialize the chart object.

        Args:

        Raises:
            RuntimeError if values or encoding is missing from data.
        """
        self.datastore = ElasticsearchDataStore(
            host=current_app.config['ELASTIC_HOST'],
            port=current_app.config['ELASTIC_PORT'])
        self.graph = Graph(self.GRAPH_TYPE)

    def event_stream(
            self, query_string=None, query_filter=None, query_dsl=None,
            indices=None, return_fields=None, scroll=True):
        """Search ElasticSearch.

        Args:
            query_string: Query string.
            query_filter: Dictionary containing filters to apply.
            query_dsl: Dictionary containing Elasticsearch DSL query.
            indices: List of indices to query.
            return_fields: List of fields to return.
            scroll: Boolean determining whether we support scrolling searches
                or not. Defaults to True.

        Returns:
            Generator of Event objects.

        Raises:
            ValueError: if neither query_string or query_dsl is provided.
        """
        if not (query_string or query_dsl):
            raise ValueError('Both query_string and query_dsl are missing')

        return_fields = list(set(return_fields))

        # Refresh the index to make sure it is searchable.
        for index in indices:
            self.datastore.client.indices.refresh(index=index)

        event_generator = self.datastore.search_stream(
            query_string=query_string,
            query_filter={},
            query_dsl=query_dsl,
            indices=indices,
            return_fields=return_fields,
            enable_scroll=scroll,
        )
        return event_generator

    def generate(self):
        """Entry point for the graph."""
        raise NotImplementedError
