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

logger = logging.getLogger('timesketch.graph_api')


class GraphListResource(resources.ResourceMixin, Resource):
    """Resource to get all graphs."""

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

    @staticmethod
    def post(sketch_id):
        """Handles POST request to the resource."""
        sketch = Sketch.query.get_with_acl(sketch_id)
        if not sketch:
            abort(HTTP_STATUS_CODE_NOT_FOUND, 'No sketch found with this ID.')

        form = request.json
        elements = form.get('elements')

        from datetime import date
        today = date.today()

        graph = Graph(
            user=current_user, sketch=sketch, name=str(today),
            graph_elements=json.dumps(elements))
        db_session.add(graph)
        db_session.commit()


class GraphResource(resources.ResourceMixin, Resource):
    """Resource to get all graphs."""

    @login_required
    def get(self, sketch_id, graph_id):
        """Handles GET request to the resource.

        Returns:
            List of graphs in JSON (instance of flask.wrappers.Response)
        """
        sketch = Sketch.query.get_with_acl(sketch_id)
        graph = Graph.query.get(graph_id)

        if not sketch:
            abort(HTTP_STATUS_CODE_NOT_FOUND, 'No sketch found with this ID.')

        if not sketch.id == graph.sketch.id:
            abort(
                HTTP_STATUS_CODE_NOT_FOUND,
                'Graph does not belong to this sketch.')

        response = self.to_json(graph).json
        response['objects'][0]['elements'] = graph.elements

        return jsonify(response)


class GraphCacheListResource(resources.ResourceMixin, Resource):
    """Resource to get all graphs."""

    @login_required
    def get(self):
        """Handles GET request to the resource.

        Returns:
            List of graphs in JSON (instance of flask.wrappers.Response)
        """
        graphs = manager.GraphManager.get_graphs()
        graph_names = {name: graph_class().DISPLAY_NAME for name, graph_class in
                       graphs}
        return jsonify(graph_names)


class GraphCacheResource(resources.ResourceMixin, Resource):
    """Resource to get a graph."""

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

        cache = GraphCache.query.filter_by(
            sketch=sketch, graph_plugin=plugin_name).first()
        if cache:
            return jsonify(json.loads(cache.elements))
        else:
            cache = GraphCache(sketch=sketch, graph_plugin=plugin_name)

        graph_class = manager.GraphManager.get_graph(plugin_name)
        graph = graph_class(sketch=sketch)
        cytoscape_json = graph.generate().to_cytoscape()

        cache.elements = json.dumps(cytoscape_json)
        db_session.add(cache)
        db_session.commit()
        return jsonify(cytoscape_json)
