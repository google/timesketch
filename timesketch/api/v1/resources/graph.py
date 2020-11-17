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
from flask_login import login_required
from flask_login import current_user

from flask import abort
from flask import jsonify
from flask import request

from timesketch.lib.graphs import manager
from timesketch.api.v1 import resources
from timesketch.models import db_session
from timesketch.models.sketch import Sketch
from timesketch.models.sketch import Graph
from timesketch.models.sketch import GraphCache

from timesketch.lib.definitions import HTTP_STATUS_CODE_NOT_FOUND
from timesketch.lib.definitions import HTTP_STATUS_CODE_FORBIDDEN
from timesketch.lib.definitions import HTTP_STATUS_CODE_BAD_REQUEST

logger = logging.getLogger('timesketch.graph_api')


class GraphListResource(resources.ResourceMixin, Resource):
    """Resource to get all saved graphs for a sketch."""

    @login_required
    def get(self, sketch_id):
        """Handles GET request to the resource.

        Returns:
            List of graphs in JSON (instance of flask.wrappers.Response)
        """
        sketch = Sketch.query.get_with_acl(sketch_id)
        if not sketch:
            abort(HTTP_STATUS_CODE_NOT_FOUND, 'No sketch found with this ID.')

        graphs = sketch.graphs
        return self.to_json(graphs)

    def post(self, sketch_id):
        """Handles POST request to the resource."""
        sketch = Sketch.query.get_with_acl(sketch_id)
        if not sketch:
            abort(HTTP_STATUS_CODE_NOT_FOUND, 'No sketch found with this ID.')

        if not sketch.has_permission(current_user, 'write'):
            abort(HTTP_STATUS_CODE_FORBIDDEN,
                  'User does not have write access on sketch.')

        form = request.json
        name = form.get('name')
        elements = form.get('elements')

        graph = Graph(
            user=current_user, sketch=sketch, name=str(name),
            graph_elements=json.dumps(elements))
        db_session.add(graph)
        db_session.commit()

        return self.to_json(graph)


class GraphResource(resources.ResourceMixin, Resource):
    """Resource to get all graphs."""

    @login_required
    def get(self, sketch_id, graph_id):
        """Handles GET request to the resource.

        Returns:
            List of graphs in JSON (instance of flask.wrappers.Response)
        """
        sketch = Sketch.query.get_with_acl(sketch_id)
        if not sketch:
            abort(HTTP_STATUS_CODE_NOT_FOUND, 'No sketch found with this ID.')

        graph = Graph.query.get(graph_id)
        if not graph:
            abort(HTTP_STATUS_CODE_NOT_FOUND, 'No graph found with this ID.')

        if not sketch.id == graph.sketch.id:
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                'Graph does not belong to this sketch.')

        response = self.to_json(graph).json
        response['objects'][0]['elements'] = graph.graph_elements

        return jsonify(response)


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
                'name': name,
                'display_name': graph_class.DISPLAY_NAME,
                'description': graph_class.DESCRIPTION
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
        sketch = Sketch.query.get_with_acl(sketch_id)
        if not sketch:
            abort(HTTP_STATUS_CODE_NOT_FOUND, 'No sketch found with this ID.')

        form = request.json
        plugin_name = form.get('plugin')
        graph_config = form.get('config')
        refresh = form.get('refresh')

        sketch_indices = [
            timeline.searchindex.index_name
            for timeline in sketch.active_timelines
        ]

        cache = GraphCache.get_or_create(
            sketch=sketch, graph_plugin=plugin_name)

        # Refresh cache if timelines have been added/removed from the sketch.
        if cache.graph_config:
            cache_graph_config = json.loads(cache.graph_config)
            if cache_graph_config:
                cache_graph_config = json.loads(cache.graph_config)
                cache_graph_filter = cache_graph_config.get('filter', {})
                cache_filter_indices = cache_graph_filter.get('indices', [])
                if set(sketch_indices) ^ set(cache_filter_indices):
                    refresh = True

        if cache.graph_elements and not refresh:
            return self.to_json(cache)

        graph_class = manager.GraphManager.get_graph(plugin_name)
        graph = graph_class(sketch=sketch)
        cytoscape_json = graph.generate().to_cytoscape()

        if cytoscape_json:
            cache.graph_elements = json.dumps(cytoscape_json)
            cache.graph_config = json.dumps(graph_config)
            cache.update_modification_time()
            db_session.add(cache)
            db_session.commit()

        return self.to_json(cache)
