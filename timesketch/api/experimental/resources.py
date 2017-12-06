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
"""Experimental parts of the Timesketch API."""

from flask import jsonify
from flask_restful import Resource
from flask_login import login_required

from timesketch.api.v1.resources import ResourceMixin
from timesketch.lib.experimental.win_logins import win_logins
from timesketch.lib.experimental.win_services import win_services
from timesketch.lib.experimental.create_graph import create_graph
from timesketch.lib.experimental.delete_graph import delete_graph


class WinLoginsResource(Resource):

    @login_required
    def get(self, sketch_id):
        """Only for debugging."""
        return jsonify(win_logins(sketch_id))


class WinServicesResource(Resource):

    @login_required
    def get(self, sketch_id):
        """Only for debugging."""
        return jsonify(win_services(sketch_id))


class CreateGraphResource(ResourceMixin, Resource):

    @login_required
    def post(self, sketch_id):
        """For given sketch, create a lateral movement graph from Elasticsearch
        events and save it to Neo4j. Nodes and edges have sketch_id property.
        """
        # Maximun number of timestamps to add to edges.
        max_timestamps = 1000

        result = []
        params = {
            u'sketch_id': sketch_id,
            u'max_timestamps': max_timestamps,
            u'win_logins': win_logins(sketch_id),
            u'win_services': win_services(sketch_id),
        }
        for statement in create_graph.split(';'):
            statement = statement.strip()
            if not statement or statement.startswith('//'):
                continue
            result.append(self.graph_datastore.query(statement, params=params))
        return jsonify(result)


class DeleteGraphResource(ResourceMixin, Resource):

    @login_required
    def post(self, sketch_id):
        """Delete all nodes and edges corresponding to given sketch."""
        result = self.graph_datastore.query(
            delete_graph, params={
                u'sketch_id': sketch_id,
            })
        return jsonify(result)
