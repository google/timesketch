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
import datetime
import json
import logging

import dateutil.parser
import pandas
import numpy
import networkx as nx

from . import error
from . import resource


logger = logging.getLogger("timesketch_api.graph")


class Graph(resource.SketchResource):
    """Graph object."""

    # This defines a list of layouts that are available
    # for the graph.
    _GRAPH_LAYOUTS = {
        "bipartite": nx.bipartite_layout,
        "circular": nx.circular_layout,
        "kamada": nx.kamada_kawai_layout,
        "kamada_kawai": nx.kamada_kawai_layout,
        "planar": nx.planar_layout,
        "random": nx.random_layout,
        "rescale": nx.rescale_layout,
        "shell": nx.shell_layout,
        "spectral": nx.spectral_layout,
        "multipartite": nx.multipartite_layout,
        "spring": nx.spring_layout,
    }

    def __init__(self, sketch):
        """Initialize the graph object."""
        resource_uri = f"sketches/{sketch.id}/graphs/"
        super().__init__(sketch=sketch, resource_uri=resource_uri)

        self._created_at = None
        self._graph = None
        self._description = ""
        self._layout = None
        self._name = ""
        self._timelines = []
        self._updated_at = None
        self._graph_config = {}

    def _parse_graph_dict(self, graph_dict):
        """Takes a dict object and constructs graph data from it.

        Args:
            graph_dict (dict): a dict that contains graph elements, as
                return back by the API.
        """
        graph_string = graph_dict.get("graph_elements")

        if isinstance(graph_string, str):
            try:
                self.resource_data = json.loads(graph_string)
            except json.JSONDecodeError as exc:
                raise ValueError("Unable to read graph data") from exc
        elif isinstance(graph_string, dict):
            self.resource_data = graph_string
        else:
            raise ValueError("Graph elements missing or not of correct value.")

        graph_config = graph_dict.get("graph_config")
        if graph_config:
            self._graph_config = json.loads(graph_config)

        self._created_at = dateutil.parser.parse(graph_dict.get("created_at", ""))
        self._updated_at = dateutil.parser.parse(graph_dict.get("updated_at", ""))

    def _serialize(self, config_dict):
        """Serialize a graph config dictionary as JSON.

        Due to networkx's use of numpy.ndarray to describe
        coordinates JSON is unable to serialize the dictionary.
        It is therefore needed to convert the ndarray into lists
        so that they can be serialized by JSON.

        Args:
            config_dict (dict): the graph config dictionary.

        Returns:
            A JSON serialized string with the dictionary's content.
        """
        for key, item in config_dict.get("layout", {}).items():
            if not isinstance(item, numpy.ndarray):
                continue
            config_dict["layout"][key] = list(item)

        return json.dumps(config_dict)

    @property
    def created_at(self):
        """Property that returns back the creation time of a graph."""
        if self._created_at:
            return self._created_at.isoformat()
        return self._created_at

    def delete(self):
        """Deletes the saved graph from the store."""
        if not self._resource_id:
            logger.warning(
                "Unable to delete the saved graph, it does not appear to be "
                "saved in the first place."
            )
            return False

        resource_url = (
            f"{self.api.api_root}/sketches/{self._sketch.id}/graphs/"
            f"{self._resource_id}/"
        )

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
        self.commit()

    @property
    def draw(self):
        """Property that returns back a drawing with the graph."""
        if not self.graph:
            return None

        if not self.graph.size():
            return None

        data = self.data.get("elements", {})
        nodes = data.get("nodes", [])

        label_dict = {
            x.get("data", {}).get("name", ""): x.get("data", {}).get("label", "")
            for x in nodes
        }

        edges = data.get("edges", [])
        edge_dict = {
            x.get("data", {}).get("name", ""): x.get("data", {}).get("label", "")
            for x in edges
        }
        label_dict.update(edge_dict)

        label_keys = list(label_dict.keys())
        for key in label_keys:
            if not key:
                _ = label_dict.pop(key)

        return nx.draw_networkx(
            self.graph, with_labels=True, labels=label_dict, pos=self.layout
        )

    @property
    def graph(self):
        """Property that returns back a graph object."""
        if self._graph:
            return self._graph

        if not self.resource_data:
            return nx.Graph()

        # It is necessary to do a deep copy, otherwise the upstream
        # nx library modifies the resource data.
        graph_dict = copy.deepcopy(self.resource_data)
        self._graph = nx.cytoscape_graph(graph_dict)
        return self._graph

    @property
    def graph_config(self):
        """Property that returns the graph config."""
        if self._graph_config:
            return self._graph_config

        self._graph_config = {
            "filter": {
                "indices": [t.index_name for t in self._sketch.list_timelines()],
            },
            "layout": self.layout,
        }
        return self._graph_config

    @graph_config.setter
    def graph_config(self, graph_config):
        """Change the graph config."""
        if not isinstance(graph_config, dict):
            raise ValueError("Graph config needs to be a dict.")

        self._graph_config = graph_config

    def from_graph(self, graph_obj):
        """Initialize from a networkx graph object.

        Args:
            graph_obj (nx.Graph): a graph object.
        """
        if not graph_obj.size():
            logger.warning("Unable to load graph from an empty graph object.")
            return
        self.resource_data = nx.cytoscape_data(graph_obj)
        self._graph = graph_obj
        self._name = ""
        self._description = "From a graph object."
        time = datetime.datetime.now(datetime.timezone.utc)
        self._created_at = time
        self._updated_at = time

    def from_manual(self, data, **kwargs):  # pylint: disable=arguments-differ
        """Generate a new graph using a dictionary.

        Args:
            data (dict): A dictionary of dictionaries adjacency representation.
            kwargs (dict[str, object]): Depending on the resource they may
                require different sets of arguments to be able to run a raw
                API request.

        Raises:
            ValueError: If the import is not successful.
        """
        super().from_manual(**kwargs)
        if not isinstance(data, dict):
            raise ValueError("Data needs to be a dict of dictionaries")

        try:
            graph = nx.from_dict_of_dicts(data)
        except AttributeError as exc:
            raise ValueError("Unable to generate a graph") from exc

        self.from_graph(graph)

    def from_plugin(self, plugin_name, plugin_config=None, refresh=False):
        """Initialize the graph from a cached plugin graph.

        Args:
            plugin_name (str): the name of the graph plugin to use.
            plugin_config (dict): optional dictionary to configure the plugin.
            refresh (bool): optional bool that if set refreshes the graph,
                otherwise the graph is pulled from the cache, if it exists.
                Defaults to False, meaning it pulls from the cache if it
                exists.

        Raises:
            ValueError: If the plugin doesn't exist or some issues came up
                during processing.
        """
        plugin_names = [x.get("name", "") for x in self.plugins]
        if plugin_name.lower() not in plugin_names:
            raise ValueError(
                f"Plugin [{plugin_name}] not part of the supported plugins."
            )

        if plugin_config and not isinstance(plugin_config, dict):
            raise ValueError("Plugin config needs to be a dict.")

        resource_url = f"{self.api.api_root}/sketches/{self._sketch.id}/graph/"
        data = {
            "plugin": plugin_name,
            "config": plugin_config,
            "refresh": bool(refresh),
        }

        if self.timelines:
            data["timeline_ids"] = self.timelines

        if plugin_config:
            if isinstance(plugin_config, str):
                self._graph_config = json.loads(plugin_config)
            else:
                self._graph_config = plugin_config

        response = self.api.session.post(resource_url, json=data)
        status = error.check_return_status(response, logger)
        if not status:
            error.error_message(
                response, "Unable to retrieve cached graph", error=RuntimeError
            )

        response_json = error.get_response_json(response, logger)
        cache_dict = response_json.get("objects", [{}])[0]
        self._parse_graph_dict(cache_dict)
        self._description = f"Graph created from the {plugin_name} plugin."

    def from_saved(self, graph_id):  # pylint: disable=arguments-differ
        """Initialize the graph object from a saved graph.

        Args:
            graph_id: integer value for the saved graph (primary key).

        Raises:
            ValueError: If issues came up during processing.
        """
        resource_id = f"sketches/{self._sketch.id}/graphs/{graph_id}/"
        data = self.api.fetch_resource_data(resource_id)

        objects = data.get("objects")
        if not objects:
            logger.warning(
                "Unable to load saved graph with ID: %d, are you sure it exists?",
                graph_id,
            )
        graph_dict = objects[0]
        self._parse_graph_dict(graph_dict)

        self._resource_id = graph_id
        self._name = graph_dict.get("name", "No name")
        self._description = graph_dict.get("description", "")
        self._username = graph_dict.get("user", {}).get("username", "System")
        self._created_at = dateutil.parser.parse(graph_dict.get("created_at", ""))
        self._updated_at = dateutil.parser.parse(graph_dict.get("updated_at", ""))

    @property
    def layout(self):
        """Property that returns back the layout of the graph."""
        if self._layout:
            return self._layout

        layout = self._GRAPH_LAYOUTS.get("spring")
        self._layout = layout(self.graph)
        return self._layout

    @layout.setter
    def layout(self, layout):
        """Change the layout manually."""
        if not isinstance(layout, dict):
            raise ValueError("Layout needs to be a dict.")
        self._layout = layout

    @property
    def layout_strings(self):
        """Property that returns a list of potential layouts to use."""
        return list(self._GRAPH_LAYOUTS.keys())

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
        plugin_dict = self.api.fetch_resource_data("graphs/")
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
            raise ValueError("No name for the graph. Please select a name first.")

        if not self.description:
            logger.warning("No description selected for graph, saving without one")

        if self._resource_id:
            resource_url = (
                f"{self.api.api_root}/sketches/{self._sketch.id}/graphs/"
                f"{self._resource_id}/"
            )
        else:
            resource_url = f"{self.api.api_root}/sketches/{self._sketch.id}/graphs/"

        cytoscape_json = nx.readwrite.json_graph.cytoscape_data(self.graph)
        elements = cytoscape_json.get("elements", [])
        element_list = []
        for group in elements:
            for element in elements[group]:
                element["group"] = group
                element_list.append(element)

        data = {
            "name": self.name,
            "graph_config": self._serialize(self.graph_config),
            "description": self.description,
            "elements": element_list,
        }

        response = self.api.session.post(resource_url, json=data)
        status = error.check_return_status(response, logger)
        if not status:
            error.error_message(response, "Unable to save search", error=RuntimeError)

        response_json = error.get_response_json(response, logger)

        graph_dict = response_json.get("objects", [{}])[0]
        self._resource_id = graph_dict.get("id", 0)
        return f"Saved graph to ID: {self._resource_id}"

    def set_layout_type(self, layout_string):
        """Use a layout from the layout strings."""
        layout = self._GRAPH_LAYOUTS.get(layout_string)
        if layout:
            self.layout = layout(self.graph)

    @property
    def timelines(self):
        """Property that returns the set of timelines this graph uses."""
        return self._timelines

    @timelines.setter
    def timelines(self, timelines):
        """Sets the timelines."""
        if not isinstance(timelines, (list, tuple)):
            logger.error("Unable to add timelines, this needs to be a list")

        for timeline in timelines:
            if isinstance(timeline, int):
                self._timelines.append(timeline)
                continue

            if hasattr(timeline, "id") and hasattr(timeline, "index_name"):
                self._timelines.append(timeline.id)

    def to_dict(self):
        """Returns a dict with the graph content."""
        return self.resource_data

    def to_pandas(self):
        """Returns a pandas dataframe with the graph content."""
        if not self.resource_data:
            return pandas.DataFrame()

        data = self.resource_data
        elements = data.get("elements", {})
        nodes = elements.get("nodes", [])
        edges = elements.get("edges", [])

        node_list = [x.get("data") for x in nodes]
        edge_list = [x.get("data") for x in edges]
        node_df = pandas.DataFrame(node_list)
        node_df["type"] = "node"
        edge_df = pandas.DataFrame(edge_list)
        edge_df["type"] = "edge"
        return pandas.concat([node_df, edge_df])

    @property
    def updated_at(self):
        """Property that returns back the last updated time of a graph."""
        if self._updated_at:
            return self._updated_at.isoformat()
        return self._updated_at
