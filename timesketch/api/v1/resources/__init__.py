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
from timesketch.lib.datastores.opensearch import OpenSearchDataStore


logging.basicConfig(
    format="%(asctime)s %(levelname)-8s %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
)


class ResourceMixin(object):
    """Mixin for API resources."""

    # Schemas for database model resources
    group_fields = {"name": fields.String}

    user_profile_fields = {
        "picture_url": fields.String,
        "picture_filename": fields.String,
    }

    user_fields = {
        "id": fields.Integer,
        "username": fields.String,
        "name": fields.String,
        "email": fields.String,
        "admin": fields.Boolean,
        "active": fields.Boolean,
        "groups": fields.Nested(group_fields),
        "profile": fields.Nested(user_profile_fields),
    }

    aggregation_fields = {
        "id": fields.Integer,
        "name": fields.String,
        "description": fields.String,
        "agg_type": fields.String,
        "parameters": fields.String,
        "chart_type": fields.String,
        "label_string": fields.String,
        "user": fields.Nested(user_fields),
        "aggregationgroup_id": fields.Integer,
        "created_at": fields.DateTime("iso8601"),
        "updated_at": fields.DateTime("iso8601"),
    }

    aggregation_group_fields = {
        "id": fields.Integer,
        "name": fields.String,
        "description": fields.String,
        "aggregations": fields.Nested(aggregation_fields),
        "parameters": fields.String,
        "orientation": fields.String,
        "user": fields.Nested(user_fields),
        "created_at": fields.DateTime("iso8601"),
        "updated_at": fields.DateTime("iso8601"),
    }

    status_fields = {
        "id": fields.Integer,
        "status": fields.String,
        "created_at": fields.DateTime("iso8601"),
        "updated_at": fields.DateTime("iso8601"),
    }

    searchindex_fields = {
        "id": fields.Integer,
        "name": fields.String,
        "user": fields.Nested(user_fields),
        "description": fields.String,
        "index_name": fields.String,
        "status": fields.Nested(status_fields),
        "label_string": fields.String,
        "deleted": fields.Boolean,
        "created_at": fields.DateTime("iso8601"),
        "updated_at": fields.DateTime("iso8601"),
    }

    datasource_fields = {
        "id": fields.Integer,
        "user": fields.Nested(user_fields),
        "provider": fields.String,
        "context": fields.String,
        "file_on_disk": fields.String,
        "file_size": fields.Integer,
        "original_filename": fields.String,
        "data_label": fields.String,
        "error_message": fields.String,
        "created_at": fields.DateTime("iso8601"),
        "updated_at": fields.DateTime("iso8601"),
        "total_file_events": fields.Integer,
        "status": fields.Nested(status_fields),
    }

    timeline_fields = {
        "id": fields.Integer,
        "name": fields.String,
        "user": fields.Nested(user_fields),
        "description": fields.String,
        "status": fields.Nested(status_fields),
        "color": fields.String,
        "label_string": fields.String,
        "searchindex": fields.Nested(searchindex_fields),
        "datasources": fields.Nested(datasource_fields),
        "deleted": fields.Boolean,
        "created_at": fields.DateTime("iso8601"),
        "updated_at": fields.DateTime("iso8601"),
    }

    analysis_fields = {
        "id": fields.Integer,
        "name": fields.String,
        "description": fields.String,
        "analyzer_name": fields.String,
        "parameters": fields.String,
        "result": fields.String,
        "analysissession_id": fields.Integer,
        "log": fields.String,
        "user": fields.Nested(user_fields),
        "timeline": fields.Nested(timeline_fields),
        "status": fields.Nested(status_fields),
        "created_at": fields.DateTime("iso8601"),
        "updated_at": fields.DateTime("iso8601"),
    }

    analysis_session_fields = {
        "id": fields.Integer,
        "user": fields.Nested(user_fields),
        "analyses": fields.Nested(analysis_fields),
        "created_at": fields.DateTime("iso8601"),
        "updated_at": fields.DateTime("iso8601"),
    }

    searchtemplate_fields = {
        "id": fields.Integer,
        "name": fields.String,
        "description": fields.String,
        "short_name": fields.String,
        "user": fields.Nested(user_fields),
        "query_string": fields.String,
        "query_filter": fields.String,
        "query_dsl": fields.String,
        "template_uuid": fields.String,
        "template_json": fields.String,
        "created_at": fields.DateTime("iso8601"),
        "updated_at": fields.DateTime("iso8601"),
    }

    view_fields = {
        "id": fields.Integer,
        "name": fields.String,
        "description": fields.String,
        "user": fields.Nested(user_fields),
        "query_string": fields.String,
        "query_filter": fields.String,
        "query_dsl": fields.String,
        "searchtemplate": fields.Nested(searchtemplate_fields),
        "created_at": fields.DateTime("iso8601"),
        "updated_at": fields.DateTime("iso8601"),
    }

    view_compact_fields = {
        "id": fields.Integer,
        "name": fields.String,
        "user": fields.Nested(user_fields),
        "created_at": fields.DateTime("iso8601"),
        "updated_at": fields.DateTime("iso8601"),
    }

    story_fields = {
        "id": fields.Integer,
        "title": fields.String,
        "content": fields.String,
        "user": fields.Nested(user_fields),
        "created_at": fields.DateTime("iso8601"),
        "updated_at": fields.DateTime("iso8601"),
    }

    story_compact_fields = {
        "id": fields.Integer,
        "title": fields.String,
        "user": fields.Nested(user_fields),
        "created_at": fields.DateTime("iso8601"),
        "updated_at": fields.DateTime("iso8601"),
    }

    graph_fields = {
        "id": fields.Integer,
        "name": fields.String,
        "user": fields.Nested(user_fields),
        "description": fields.String,
        "created_at": fields.DateTime("iso8601"),
        "updated_at": fields.DateTime("iso8601"),
    }

    graphcache_fields = {
        "id": fields.Integer,
        "graph_elements": fields.String,
        "graph_config": fields.String,
        "created_at": fields.DateTime("iso8601"),
        "updated_at": fields.DateTime("iso8601"),
    }

    sketch_fields = {
        "id": fields.Integer,
        "name": fields.String,
        "description": fields.String,
        "user": fields.Nested(user_fields),
        "timelines": fields.List(fields.Nested(timeline_fields)),
        "graphs": fields.List(fields.Nested(graph_fields)),
        "active_timelines": fields.List(fields.Nested(timeline_fields)),
        "label_string": fields.String,
        "status": fields.Nested(status_fields),
        "all_permissions": fields.String,
        "my_permissions": fields.String,
        "created_at": fields.DateTime("iso8601"),
        "updated_at": fields.DateTime("iso8601"),
    }

    comment_fields = {
        "id": fields.Integer,
        "comment": fields.String,
        "user": fields.Nested(user_fields),
        "created_at": fields.DateTime("iso8601"),
        "updated_at": fields.DateTime("iso8601"),
    }

    label_fields = {
        "name": fields.String,
        "user": fields.Nested(user_fields),
        "created_at": fields.DateTime("iso8601"),
        "updated_at": fields.DateTime("iso8601"),
    }

    approach_fields = {
        "id": fields.Integer,
        "name": fields.String,
        "display_name": fields.String,
        "description": fields.String,
        "spec_json": fields.String,
        "search_templates": fields.List(fields.Nested(searchtemplate_fields)),
        "created_at": fields.DateTime("iso8601"),
        "updated_at": fields.DateTime("iso8601"),
    }

    question_conclusion_fields = {
        "id": fields.Integer,
        "user": fields.Nested(user_fields),
        "conclusion": fields.String,
        "automated": fields.Boolean,
        "created_at": fields.DateTime("iso8601"),
        "updated_at": fields.DateTime("iso8601"),
    }

    question_fields = {
        "id": fields.Integer,
        "name": fields.String,
        "display_name": fields.String,
        "description": fields.String,
        "dfiq_identifier": fields.String,
        "uuid": fields.String,
        "spec_json": fields.String,
        "user": fields.Nested(user_fields),
        "approaches": fields.List(fields.Nested(approach_fields)),
        "conclusions": fields.List(fields.Nested(question_conclusion_fields)),
        "created_at": fields.DateTime("iso8601"),
        "updated_at": fields.DateTime("iso8601"),
    }

    facet_fields = {
        "id": fields.Integer,
        "name": fields.String,
        "display_name": fields.String,
        "description": fields.String,
        "dfiq_identifier": fields.String,
        "uuid": fields.String,
        "spec_json": fields.String,
        "user": fields.Nested(user_fields),
        "questions": fields.List(fields.Nested(question_fields)),
        "stories": fields.List(fields.Nested(story_compact_fields)),
        "saved_searches": fields.List(fields.Nested(view_compact_fields)),
        "saved_graphs": fields.List(fields.Nested(graph_fields)),
        "saved_aggregations": fields.List(fields.Nested(aggregation_fields)),
        "created_at": fields.DateTime("iso8601"),
        "updated_at": fields.DateTime("iso8601"),
    }

    scenario_fields = {
        "id": fields.Integer,
        "status": fields.Nested(status_fields),
        "name": fields.String,
        "display_name": fields.String,
        "description": fields.String,
        "dfiq_identifier": fields.String,
        "uuid": fields.String,
        "spec_json": fields.String,
        "user": fields.Nested(user_fields),
        "facets": fields.List(fields.Nested(facet_fields)),
        "created_at": fields.DateTime("iso8601"),
        "updated_at": fields.DateTime("iso8601"),
    }

    sigmarule_fields = {
        "id": fields.Integer,
        "rule_uuid": fields.String,
        "description": fields.String,
        "title": fields.String,
        "query_string": fields.String,
        "user": fields.Nested(user_fields),
        "rule_yaml": fields.String,
        "created_at": fields.DateTime("iso8601"),
        "updated_at": fields.DateTime("iso8601"),
    }

    fields_registry = {
        "aggregation": aggregation_fields,
        "aggregationgroup": aggregation_group_fields,
        "searchindex": searchindex_fields,
        "analysis": analysis_fields,
        "analysissession": analysis_session_fields,
        "datasource": datasource_fields,
        "timeline": timeline_fields,
        "searchtemplate": searchtemplate_fields,
        "view": view_fields,
        "user": user_fields,
        "userprofile": user_profile_fields,
        "graph": graph_fields,
        "graphcache": graphcache_fields,
        "group": group_fields,
        "sketch": sketch_fields,
        "story": story_fields,
        "event_comment": comment_fields,
        "event_label": label_fields,
        "Investigativequestionapproach": approach_fields,
        "investigativequestionconclusion": question_conclusion_fields,
        "investigativequestion": question_fields,
        "facet": facet_fields,
        "scenario": scenario_fields,
        "sigmarule": sigmarule_fields,
    }

    @property
    def datastore(self):
        """Property to get an instance of the datastore backend.

        Returns:
            Instance of lib.datastores.opensearch.OpenSearchDatastore
        """
        return OpenSearchDataStore(
            host=current_app.config["OPENSEARCH_HOST"],
            port=current_app.config["OPENSEARCH_PORT"],
        )

    def to_json(
        self, model, model_fields=None, meta=None, status_code=HTTP_STATUS_CODE_OK
    ):
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

        schema = {"meta": meta, "objects": []}

        if model:
            if not model_fields:
                try:
                    model_fields = self.fields_registry[model.__tablename__]
                except AttributeError:
                    model_fields = self.fields_registry[model[0].__tablename__]
            schema["objects"] = [marshal(model, model_fields)]

        response = jsonify(schema)
        response.status_code = status_code
        return response
