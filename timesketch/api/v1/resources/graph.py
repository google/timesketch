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

from flask_restful import Resource
from flask_login import login_required
from flask import jsonify
from flask import request

from timesketch.lib.graphs import manager
from timesketch.api.v1 import resources
from timesketch.models.sketch import SearchIndex


logger = logging.getLogger('timesketch.graph_api')


class GraphListResource(resources.ResourceMixin, Resource):
    """Resource to get all graphs."""

    @login_required
    def get(self):
        """Handles GET request to the resource.

        Returns:
            List of graphs in JSON (instance of flask.wrappers.Response)
        """
        graphs = manager.GraphManager.get_graphs()
        graph_names = []
        for graph_name, _ in graphs:
            graph_names.append(graph_name)
        return jsonify(graph_names)


class GraphResource(resources.ResourceMixin, Resource):
    """Resource to get a graph."""

    @login_required
    def get(self, sketch_id):
        """Handles POST request to the resource.

        Returns:
            Graph in JSON (instance of flask.wrappers.Response)
        """
        #form = request.json
        #graph_name = form.get('name')
        graph_class = manager.GraphManager.get_graph('winmulti')
        graph = graph_class()
        result = graph.generate()
        return jsonify(result)
