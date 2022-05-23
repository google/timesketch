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

import hashlib

from flask import current_app
import networkx as nx

from timesketch.lib.datastores.opensearch import OpenSearchDataStore


GRAPH_TYPES = {
    "Graph": nx.Graph,
    "MultiGraph": nx.MultiGraph,
    "DiGraph": nx.DiGraph,
    "MultiDiGraph": nx.MultiDiGraph,
}

MAX_EVENTS_PER_EDGE = 500


class Graph:
    """Graph object with helper methods.

    Attributes:
        nx_instance: Networkx graph object.
    """

    def __init__(self, graph_type):
        """Initialize Graph object.

        Args:
            graph_type: (str) Name of graph type.
        """
        _nx_graph_class = GRAPH_TYPES.get(graph_type)
        self.nx_instance = _nx_graph_class()
        self._nodes = {}
        self._edges = {}

    def add_node(self, label, attributes):
        """Add node to graph.

        Args:
            label: (str) Label for the node.
            attributes: (dict) Attributes to add to node.

        Returns:
              Instance of Node object.
        """
        if not attributes:
            attributes = {}

        node = Node(label, attributes)
        node.set_attribute("id", node.id)
        if node.id not in self._nodes:
            self._nodes[node.id] = node
        return node

    def add_edge(self, source, target, label, event, attributes=None):
        """Add edge to graph.

        Args:
            source: (Node) Node to use as source.
            target: (Node) Node to use as target.
            label: (str) Label for the node.
            event: (dict): OpenSearch event.
            attributes: (dict) Attributes to add to node.
        """
        if not attributes:
            attributes = {}

        attributes["id"] = "".join([source.id, target.id, label]).lower()

        edge = Edge(source, target, label, attributes)

        if edge.node_counter < MAX_EVENTS_PER_EDGE:
            index = event.get("_index")
            doc_id = event.get("_id")
            events = edge.attributes.get("events", {})
            doc_ids = events.get(index, [])
            doc_ids.append(doc_id)
            edge.node_counter += 1
            events[index] = doc_ids
            edge.set_attribute("events", events)

        self._edges[edge.id] = edge

    def commit(self):
        """Commit all nodes and edges to the networkx graph object."""
        for node_id, node in self._nodes.items():
            self.nx_instance.add_node(node_id, label=node.label, **node.attributes)

        for _, edge in self._edges.items():
            label = edge.label + f" ({edge.node_counter})"
            self.nx_instance.add_edge(
                edge.source.id, edge.target.id, label=label, **edge.attributes
            )

    def to_cytoscape(self):
        """Output graph in Cytoscape JSON format.

        Returns:
            Graph in Cytoscape JSON format.
        """
        return nx.readwrite.json_graph.cytoscape_data(self.nx_instance)


class BaseGraphElement:
    """Base class for graph elements.

    Attributes:
        label (str): Node/Edge label to show in the UI.
        attributes (dict): Attributed to add to the node/edge.
        id (str): Uniq value generated from the label.
    """

    def __init__(self, label="", attributes=None):
        """Initialize the base element object.

        Args:
            label (str): Node/Edge label to show in the UI.
            attributes (dict): Attributes to add to the node/edge.
        """
        self.label = label
        self.attributes = attributes or {}
        self.id = self._generate_id()

    def _generate_id(self):
        """Generate ID for node/edge.

        Returns:
            MD5 hash (str): MD5 hash of the provided label.
        """

        id_string = self.attributes.get("id", self.label)
        return hashlib.md5(id_string.encode("utf-8")).hexdigest()

    def set_attribute(self, key, value):
        """Add or replace an attribute to the element.

        Args:
            key (str): Attribute key.
            value (str): Attribute value.
        """
        self.attributes[key] = value


class Node(BaseGraphElement):
    """Graph node object."""

    # TODO: Add logic for Nodes when needed.


class Edge(BaseGraphElement):
    """Graph edge object.

    Attributes:
        source (Node): Node to add as source node.
        target (Node): Node to add as target node.
        node_counter (int): Counter for number of nodes referenced for the edge.
    """

    def __init__(self, source, target, label="", attributes=None):
        """Initialize the Edge object.

        Args:
            label (str): Node/Edge label to show in the UI.
            attributes (dict): Attributes to add to the edge.
        """
        self.source = source
        self.target = target
        self.node_counter = 0
        super().__init__(label, attributes)


class BaseGraphPlugin:
    """Base class for a graph.

    Attributes:
        datastore (OpenSearchDataStore): OpenSearch datastore object.
        graph (nx.Graph): NetworkX Graph object.
    """

    # Name that the graph will be registered as.
    NAME = "name"

    # Display name (used in the UI)
    DISPLAY_NAME = "display_name"

    # Description of the plugin (used in the UI)
    DESCRIPTION = "description"

    # Type of graph. There are four supported types: Undirected Graph,
    # Undirected Multi Graph, Directed Graph, Directed  Multi Graph.
    # If you have multiple edges between nodes you need to use the multi graphs.
    #
    # See NetworkX documentation for details:
    # https://networkx.org/documentation/stable/reference/classes/index.html
    GRAPH_TYPE = "MultiDiGraph"

    def __init__(self, sketch=None, timeline_ids=None):
        """Initialize the graph object.

        Args:
            sketch (Sketch): Sketch object.
            timeline_ids (List[int]): An optional list of timeline IDs.

        Raises:
            KeyError if graph type specified is not supported.
        """
        self.datastore = OpenSearchDataStore(
            host=current_app.config["OPENSEARCH_HOST"],
            port=current_app.config["OPENSEARCH_PORT"],
        )
        if not GRAPH_TYPES.get(self.GRAPH_TYPE):
            raise KeyError(f"Graph type {self.GRAPH_TYPE} is not supported")
        self.graph = Graph(self.GRAPH_TYPE)
        self.sketch = sketch
        self.timeline_ids = timeline_ids

    def _get_sketch_indices(self):
        """List all indices in the Sketch, or those that belong to a timeline.

        Returns:
            List of index names.
        """
        active_timelines = self.sketch.active_timelines

        if self.timeline_ids:
            indices = [
                t.searchindex.index_name
                for t in active_timelines
                if t.id in self.timeline_ids
            ]
        else:
            indices = [t.searchindex.index_name for t in active_timelines]

        return indices

    # TODO: Refactor this to reuse across analyzers and graphs.
    def event_stream(
        self,
        query_string=None,
        query_filter=None,
        query_dsl=None,
        indices=None,
        return_fields=None,
        scroll=True,
    ):
        """Search OpenSearch.

        Args:
            query_string: Query string.
            query_filter: Dictionary containing filters to apply.
            query_dsl: Dictionary containing OpenSearch DSL query.
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
            raise ValueError("Both query_string and query_dsl are missing")

        # Query all sketch indices if none are specified.
        if not indices:
            indices = self._get_sketch_indices()

        if not query_filter:
            query_filter = {}

        return_fields = list(set(return_fields))

        if self.timeline_ids:
            timeline_ids = self.timeline_ids
        else:
            timeline_ids = None

        event_generator = self.datastore.search_stream(
            query_string=query_string,
            query_filter=query_filter,
            query_dsl=query_dsl,
            indices=indices,
            return_fields=return_fields,
            timeline_ids=timeline_ids,
            enable_scroll=scroll,
        )
        return event_generator

    def generate(self):
        """Entry point for the graph."""
        raise NotImplementedError
