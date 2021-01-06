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
"""This module holds version 1 of the Timesketch API.

The timesketch API is a RESTful API that exposes the following resources:
"""
from __future__ import unicode_literals

import logging

from flask import current_app
from flask import jsonify
from flask_restful import fields
from flask_restful import marshal

from timesketch.lib.definitions import HTTP_STATUS_CODE_OK
from timesketch.lib.datastores.elastic import ElasticsearchDataStore


logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')


class ResourceMixin(object):
    """Mixin for API resources."""
    # Schemas for database model resources
    group_fields = {'name': fields.String}

    user_fields = {
        'username': fields.String,
        'admin':  fields.Boolean,
        'active': fields.Boolean,
        'groups': fields.Nested(group_fields),
    }

    aggregation_fields = {
        'id': fields.Integer,
        'name': fields.String,
        'description': fields.String,
        'agg_type': fields.String,
        'parameters': fields.String,
        'chart_type': fields.String,
        'label_string': fields.String,
        'user': fields.Nested(user_fields),
        'created_at': fields.DateTime,
        'updated_at': fields.DateTime
    }

    aggregation_group_fields = {
        'id': fields.Integer,
        'name': fields.String,
        'description': fields.String,
        'aggregations': fields.Nested(aggregation_fields),
        'parameters': fields.String,
        'orientation': fields.String,
        'user': fields.Nested(user_fields),
        'created_at': fields.DateTime,
        'updated_at': fields.DateTime
    }

    status_fields = {
        'id': fields.Integer,
        'status': fields.String,
        'created_at': fields.DateTime,
        'updated_at': fields.DateTime
    }

    searchindex_fields = {
        'id': fields.Integer,
        'name': fields.String,
        'user': fields.Nested(user_fields),
        'description': fields.String,
        'index_name': fields.String,
        'status': fields.Nested(status_fields),
        'label_string': fields.String,
        'deleted': fields.Boolean,
        'created_at': fields.DateTime,
        'updated_at': fields.DateTime
    }

    timeline_fields = {
        'id': fields.Integer,
        'name': fields.String,
        'user': fields.Nested(user_fields),
        'description': fields.String,
        'status': fields.Nested(status_fields),
        'color': fields.String,
        'label_string': fields.String,
        'searchindex': fields.Nested(searchindex_fields),
        'deleted': fields.Boolean,
        'created_at': fields.DateTime,
        'updated_at': fields.DateTime
    }

    analysis_fields = {
        'id': fields.Integer,
        'name': fields.String,
        'description': fields.String,
        'analyzer_name': fields.String,
        'parameters': fields.String,
        'result': fields.String,
        'analysissession_id': fields.Integer,
        'log': fields.String,
        'user': fields.Nested(user_fields),
        'timeline': fields.Nested(timeline_fields),
        'status': fields.Nested(status_fields),
        'created_at': fields.DateTime,
        'updated_at': fields.DateTime
    }

    analysis_session_fields = {
        'id': fields.Integer,
        'user': fields.Nested(user_fields),
        'analyses': fields.Nested(analysis_fields),
        'created_at': fields.DateTime,
        'updated_at': fields.DateTime
    }

    searchtemplate_fields = {
        'id': fields.Integer,
        'name': fields.String,
        'user': fields.Nested(user_fields),
        'query_string': fields.String,
        'query_filter': fields.String,
        'query_dsl': fields.String,
        'created_at': fields.DateTime,
        'updated_at': fields.DateTime
    }

    view_fields = {
        'id': fields.Integer,
        'name': fields.String,
        'description': fields.String,
        'user': fields.Nested(user_fields),
        'query_string': fields.String,
        'query_filter': fields.String,
        'query_dsl': fields.String,
        'searchtemplate': fields.Nested(searchtemplate_fields),
        'aggregation': fields.Nested(aggregation_fields),
        'created_at': fields.DateTime,
        'updated_at': fields.DateTime
    }

    story_fields = {
        'id': fields.Integer,
        'title': fields.String,
        'content': fields.String,
        'user': fields.Nested(user_fields),
        'created_at': fields.DateTime,
        'updated_at': fields.DateTime
    }

    graph_fields = {
        'id': fields.Integer,
        'name': fields.String,
        'user': fields.Nested(user_fields),
        'description': fields.String,
        'created_at': fields.DateTime,
        'updated_at': fields.DateTime
    }

    graphcache_fields = {
        'id': fields.Integer,
        'graph_elements': fields.String,
        'graph_config': fields.String,
        'created_at': fields.DateTime,
        'updated_at': fields.DateTime
    }

    sketch_fields = {
        'id': fields.Integer,
        'name': fields.String,
        'description': fields.String,
        'user': fields.Nested(user_fields),
        'timelines': fields.List(fields.Nested(timeline_fields)),
        'stories': fields.List(fields.Nested(story_fields)),
        'graphs': fields.List(fields.Nested(graph_fields)),
        'aggregations': fields.Nested(aggregation_fields),
        'aggregationgroups': fields.Nested(aggregation_group_fields),
        'active_timelines': fields.List(fields.Nested(timeline_fields)),
        'label_string': fields.String,
        'status': fields.Nested(status_fields),
        'all_permissions': fields.String,
        'my_permissions': fields.String,
        'created_at': fields.DateTime,
        'updated_at': fields.DateTime
    }

    comment_fields = {
        'comment': fields.String,
        'user': fields.Nested(user_fields),
        'created_at': fields.DateTime,
        'updated_at': fields.DateTime
    }

    label_fields = {
        'name': fields.String,
        'user': fields.Nested(user_fields),
        'created_at': fields.DateTime,
        'updated_at': fields.DateTime
    }

    fields_registry = {
        'aggregation': aggregation_fields,
        'aggregationgroup': aggregation_group_fields,
        'searchindex': searchindex_fields,
        'analysis': analysis_fields,
        'analysissession': analysis_session_fields,
        'timeline': timeline_fields,
        'searchtemplate': searchtemplate_fields,
        'view': view_fields,
        'user': user_fields,
        'graph': graph_fields,
        'graphcache': graphcache_fields,
        'group': group_fields,
        'sketch': sketch_fields,
        'story': story_fields,
        'event_comment': comment_fields,
        'event_label': label_fields
    }

    @property
    def datastore(self):
        """Property to get an instance of the datastore backend.

        Returns:
            Instance of timesketch.lib.datastores.elastic.ElasticSearchDatastore
        """
        return ElasticsearchDataStore(
            host=current_app.config['ELASTIC_HOST'],
            port=current_app.config['ELASTIC_PORT'])

    def to_json(self,
                model,
                model_fields=None,
                meta=None,
                status_code=HTTP_STATUS_CODE_OK):
        """Create json response from a database models.

        Args:
            model: Instance of a timesketch database model
            model_fields: Dictionary describing the resulting schema
            meta: Dictionary holding any metadata for the result
            status_code: Integer used as status_code in the response

        Returns:
            Response in json format (instance of flask.wrappers.Response)
        """
        if not meta:
            meta = dict()

        schema = {'meta': meta, 'objects': []}

        if model:
            if not model_fields:
                try:
                    model_fields = self.fields_registry[model.__tablename__]
                except AttributeError:
                    model_fields = self.fields_registry[model[0].__tablename__]
            schema['objects'] = [marshal(model, model_fields)]

        response = jsonify(schema)
        response.status_code = status_code
        return response
