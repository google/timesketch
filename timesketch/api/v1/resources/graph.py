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
"""Graph resources for version 1 of the Timesketch API."""
import logging
import json

from flask_restful import Resource
from flask_restful import reqparse
from flask_login import login_required
from flask_login import current_user

from flask import abort
from flask import jsonify
from flask import request

from timesketch.lib.graphs import manager
from timesketch.api.v1 import resources
from timesketch.api.v1 import utils
from timesketch.models import db_session
from timesketch.models.sketch import Sketch
from timesketch.models.sketch import Graph
from timesketch.models.sketch import GraphCache

from timesketch.lib.definitions import HTTP_STATUS_CODE_BAD_REQUEST
from timesketch.lib.definitions import HTTP_STATUS_CODE_CREATED
from timesketch.lib.definitions import HTTP_STATUS_CODE_OK
from timesketch.lib.definitions import HTTP_STATUS_CODE_FORBIDDEN
from timesketch.lib.definitions import HTTP_STATUS_CODE_NOT_FOUND

logger = logging.getLogger("timesketch.graph_api")


class GraphListResource(resources.ResourceMixin, Resource):
    """Resource to get all saved graphs for a sketch."""

    @login_required
    def get(self, sketch_id):
        """Handles GET request to the resource.

        Returns:
            List of graphs in JSON (instance of flask.wrappers.Response)
        """
        sketch = Sketch.get_with_acl(sketch_id)
        if not sketch:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No sketch found with this ID.")

        graphs = sketch.graphs
        return self.to_json(graphs)

    @login_required
    def post(self, sketch_id):
        """Handles POST request to the resource."""
        sketch = Sketch.get_with_acl(sketch_id)
        if not sketch:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No sketch found with this ID.")

        if not sketch.has_permission(current_user, "write"):
            abort(
                HTTP_STATUS_CODE_FORBIDDEN, "User does not have write access on sketch."
            )

        form = request.json

        name = form.get("name")
        description = form.get("description")
        elements = form.get("elements")
        graph_config = form.get("graph_config")

        if graph_config:
            if isinstance(graph_config, dict):
                graph_json = json.dumps(graph_config)
            elif isinstance(graph_config, str):
                graph_json = graph_config
            else:
                graph_json = ""
                logger.warning("Graph config not of the correct value, not saving.")
        else:
            graph_json = ""

        graph = Graph(
            user=current_user,
            sketch=sketch,
            name=str(name),
            graph_config=graph_json,
            description=description,
            graph_elements=json.dumps(elements),
        )

        db_session.add(graph)
        db_session.commit()

        # Update the last activity of a sketch.
        utils.update_sketch_last_activity(sketch)

        return self.to_json(graph, status_code=HTTP_STATUS_CODE_CREATED)


class GraphResource(resources.ResourceMixin, Resource):
    """Resource to get a saved graph."""

    def __init__(self):
        super().__init__()
        self.parser = reqparse.RequestParser()
        self.parser.add_argument("format", type=str, required=False, location="args")

    @login_required
    def get(self, sketch_id, graph_id):
        """Handles GET request to the resource.

        Returns:
            List of graphs in JSON (instance of flask.wrappers.Response)
        """
        args = self.parser.parse_args()
        output_format = args.get("format", None)

        sketch = Sketch.get_with_acl(sketch_id)
        if not sketch:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No sketch found with this ID.")

        graph = Graph.get_by_id(graph_id)
        if not graph:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No graph found with this ID.")

        if not sketch.id == graph.sketch.id:
            abort(HTTP_STATUS_CODE_BAD_REQUEST, "Graph does not belong to this sketch.")

        # If requested use a format suitable for the CytoscapeJS frontend.
        if output_format == "cytoscape":
            response = self.to_json(graph).json
            response["objects"][0]["graph_elements"] = graph.graph_elements
            return jsonify(response)

        # Reformat elements to work with networkx python library.
        # TODO: Change frontend to save directed and multigraph attributes.
        graph_elements = json.loads(graph.graph_elements)
        formatted_graph = {
            "data": [],
            "directed": True,
            "multigraph": True,
            "elements": {"nodes": [], "edges": []},
        }
        for element in graph_elements:
            group = element["group"]
            element_data = {"data": element["data"]}
            formatted_graph["elements"][group].append(element_data)

        response = self.to_json(graph).json
        response["objects"][0]["graph_elements"] = formatted_graph
        response["objects"][0]["graph_config"] = graph.graph_config

        # Update the last activity of a sketch.
        utils.update_sketch_last_activity(sketch)

        return jsonify(response)

    @login_required
    def post(self, sketch_id, graph_id):
        """Handles GET request to the resource.

        Returns:
            List of graphs in JSON (instance of flask.wrappers.Response)
        """
        sketch = Sketch.get_with_acl(sketch_id)
        if not sketch:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No sketch found with this ID.")

        if not sketch.has_permission(current_user, "write"):
            abort(
                HTTP_STATUS_CODE_FORBIDDEN,
                "User does not have write access controls on sketch.",
            )

        graph = Graph.get_by_id(graph_id)
        if not graph:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No graph found with this ID.")

        if not sketch.id == graph.sketch.id:
            abort(HTTP_STATUS_CODE_BAD_REQUEST, "Graph does not belong to this sketch.")

        form = request.json
        if not form:
            form = request.data

        name = form.get("name")
        if name:
            graph.name = name

        description = form.get("description")
        if description:
            graph.description = description

        elements = form.get("elements")
        if elements:
            graph.graph_elements = json.dumps(elements)

        graph_config = form.get("graph_config")
        graph_json = ""
        if graph_config:
            if isinstance(graph_config, dict):
                graph_json = json.dumps(graph_config)
            elif isinstance(graph_config, str):
                graph_json = graph_config
        if graph_json:
            graph.graph_config = graph_json

        db_session.add(graph)
        db_session.commit()

        # Update the last activity of a sketch.
        utils.update_sketch_last_activity(sketch)

        return self.to_json(graph, status_code=HTTP_STATUS_CODE_CREATED)

    @login_required
    def delete(self, sketch_id, graph_id):
        """Handles DELETE request to the resource.

        Args:
            sketch_id: Integer primary key for a sketch database model
            graph_id: Integer primary key for a graph database model
        """
        sketch = Sketch.get_with_acl(sketch_id)
        graph = Graph.get_by_id(graph_id)

        if not graph:
            msg = "No Graph found with this ID."
            abort(HTTP_STATUS_CODE_NOT_FOUND, msg)

        if not sketch:
            msg = "No sketch found with this ID."
            abort(HTTP_STATUS_CODE_NOT_FOUND, msg)

        # Check that this graph belongs to the sketch
        if graph.sketch.id != sketch.id:
            msg = (
                f"The sketch ID ({sketch.id}) does not match with the story"
                f"sketch ID ({graph.sketch.id})"
            )
            abort(HTTP_STATUS_CODE_FORBIDDEN, msg)

        if not sketch.has_permission(user=current_user, permission="write"):
            abort(
                HTTP_STATUS_CODE_FORBIDDEN,
                "The user does not have write permission on the sketch.",
            )

        sketch.graphs.remove(graph)
        db_session.commit()

        # Update the last activity of a sketch.
        utils.update_sketch_last_activity(sketch)

        return HTTP_STATUS_CODE_OK


class GraphPluginListResource(resources.ResourceMixin, Resource):
    """Resource to get all graph plugins."""

    @login_required
    def get(self):
        """Handles GET request to the resource.

        Returns:
            List of graphs in JSON (instance of flask.wrappers.Response)
        """
        graph_plugins = manager.GraphManager.get_graphs()
        graphs = []
        for name, graph_class in graph_plugins:
            graph_plugin = {
                "name": name,
                "display_name": graph_class.DISPLAY_NAME,
                "description": graph_class.DESCRIPTION,
            }
            graphs.append(graph_plugin)

        return jsonify(graphs)


class GraphCacheResource(resources.ResourceMixin, Resource):
    """Resource to get a cached graph."""

    @login_required
    def post(self, sketch_id):
        """Handles POST request to the resource.

        Returns:
            Graph in JSON (instance of flask.wrappers.Response)
        """
        sketch = Sketch.get_with_acl(sketch_id)
        if not sketch:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No sketch found with this ID.")

        form = request.json
        plugin_name = form.get("plugin")
        graph_config = form.get("config")
        refresh = form.get("refresh")
        timeline_ids = form.get("timeline_ids", None)

        if timeline_ids and not isinstance(timeline_ids, (list, tuple)):
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                "Timeline IDs if supplied need to be a list.",
            )

        if timeline_ids and not all([isinstance(x, int) for x in timeline_ids]):
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                "Timeline IDs needs to be a list of integers.",
            )

        sketch_indices = [
            timeline.searchindex.index_name for timeline in sketch.active_timelines
        ]

        cache = GraphCache.get_or_create(sketch=sketch, graph_plugin=plugin_name)

        if graph_config:
            cache_config = graph_config
        else:
            cache_config = cache.graph_config

        if isinstance(cache_config, str):
            cache_config = json.loads(cache_config)

        # Refresh cache if timelines have been added/removed from the sketch.
        if cache_config:
            cache_graph_filter = cache_config.get("filter", {})
            cache_filter_indices = cache_graph_filter.get("indices", [])
            if set(sketch_indices) ^ set(cache_filter_indices):
                refresh = True

        if cache.graph_elements and not refresh:
            return self.to_json(cache)

        graph_class = manager.GraphManager.get_graph(plugin_name)
        graph = graph_class(sketch=sketch, timeline_ids=timeline_ids)
        cytoscape_json = graph.generate().to_cytoscape()

        if cytoscape_json:
            cache.graph_elements = json.dumps(cytoscape_json)
            cache.graph_config = json.dumps(graph_config)
            cache.update_modification_time()
            db_session.add(cache)
            db_session.commit()

        # Update the last activity of a sketch.
        utils.update_sketch_last_activity(sketch)

        return self.to_json(cache)
