# Copyright 2015 Google Inc. All rights reserved.
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

GET /sketches/
GET /sketches/:sketch_id/
GET /sketches/:sketch_id/explore/
GET /sketches/:sketch_id/event/
GET /sketches/:sketch_id/views/
GET /sketches/:sketch_id/views/:view_id/

POST /sketches/:sketch_id/event/
POST /sketches/:sketch_id/event/annotate/
POST /sketches/:sketch_id/views/
"""

from __future__ import unicode_literals

import codecs
import datetime
import json
import hashlib
import os
import time
import uuid

import six

from dateutil import parser
from flask import abort
from flask import current_app
from flask import jsonify
from flask import request
from flask_login import current_user
from flask_login import login_required
from flask_restful import fields
from flask_restful import marshal
from flask_restful import reqparse
from flask_restful import Resource
from sqlalchemy import desc
from sqlalchemy import not_

from timesketch.lib.aggregators import manager as aggregator_manager
from timesketch.lib.aggregators_old import heatmap
from timesketch.lib.aggregators_old import histogram
from timesketch.lib.definitions import DEFAULT_SOURCE_FIELDS
from timesketch.lib.definitions import HTTP_STATUS_CODE_OK
from timesketch.lib.definitions import HTTP_STATUS_CODE_CREATED
from timesketch.lib.definitions import HTTP_STATUS_CODE_BAD_REQUEST
from timesketch.lib.definitions import HTTP_STATUS_CODE_FORBIDDEN
from timesketch.lib.definitions import HTTP_STATUS_CODE_NOT_FOUND
from timesketch.lib.datastores.elastic import ElasticsearchDataStore
from timesketch.lib.datastores.neo4j import Neo4jDataStore
from timesketch.lib.datastores.neo4j import SCHEMA as neo4j_schema
from timesketch.lib.errors import ApiHTTPError
from timesketch.lib.emojis import get_emojis_as_dict
from timesketch.lib.forms import AddTimelineSimpleForm
from timesketch.lib.forms import AggregationExploreForm
from timesketch.lib.forms import AggregationLegacyForm
from timesketch.lib.forms import CreateTimelineForm
from timesketch.lib.forms import SaveAggregationForm
from timesketch.lib.forms import SaveViewForm
from timesketch.lib.forms import NameDescriptionForm
from timesketch.lib.forms import EventAnnotationForm
from timesketch.lib.forms import EventCreateForm
from timesketch.lib.forms import ExploreForm
from timesketch.lib.forms import UploadFileForm
from timesketch.lib.forms import StoryForm
from timesketch.lib.forms import GraphExploreForm
from timesketch.lib.forms import SearchIndexForm
from timesketch.lib.forms import TimelineForm
from timesketch.lib.utils import get_validated_indices
from timesketch.lib.experimental.utils import GRAPH_VIEWS
from timesketch.lib.experimental.utils import get_graph_views
from timesketch.lib.experimental.utils import get_graph_view
from timesketch.models import db_session
from timesketch.models.sketch import Aggregation
from timesketch.models.sketch import Event
from timesketch.models.sketch import SearchIndex
from timesketch.models.sketch import Sketch
from timesketch.models.sketch import Timeline
from timesketch.models.sketch import View
from timesketch.models.sketch import SearchTemplate
from timesketch.models.sketch import Story


def bad_request(message):
    """Function to set custom error message for HTTP 400 requests.

    Args:
        message: Message as string to return to the client.

    Returns: Response object (instance of flask.wrappers.Response)

    """
    response = jsonify({'message': message})
    response.status_code = HTTP_STATUS_CODE_BAD_REQUEST
    return response


class ResourceMixin(object):
    """Mixin for API resources."""
    # Schemas for database model resources
    user_fields = {'username': fields.String}

    aggregation_fields = {
        'id': fields.Integer,
        'name': fields.String,
        'description': fields.String,
        'agg_type': fields.String,
        'parameters': fields.String,
        'chart_type': fields.String,
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
        'searchindex': fields.Nested(searchindex_fields),
        'deleted': fields.Boolean,
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

    sketch_fields = {
        'id': fields.Integer,
        'name': fields.String,
        'description': fields.String,
        'user': fields.Nested(user_fields),
        'timelines': fields.List(fields.Nested(timeline_fields)),
        'stories': fields.List(fields.Nested(story_fields)),
        'active_timelines': fields.List(fields.Nested(timeline_fields)),
        'status': fields.Nested(status_fields),
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
        'searchindex': searchindex_fields,
        'timeline': timeline_fields,
        'searchtemplate': searchtemplate_fields,
        'view': view_fields,
        'user': user_fields,
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

    @property
    def graph_datastore(self):
        """Property to get an instance of the graph database backend.

        Returns:
            Instance of timesketch.lib.datastores.neo4j.Neo4jDatabase
        """
        return Neo4jDataStore(
            host=current_app.config['NEO4J_HOST'],
            port=current_app.config['NEO4J_PORT'],
            username=current_app.config['NEO4J_USERNAME'],
            password=current_app.config['NEO4J_PASSWORD'])

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


class SketchListResource(ResourceMixin, Resource):
    """Resource for listing sketches."""

    def __init__(self):
        super(SketchListResource, self).__init__()
        self.parser = reqparse.RequestParser()
        self.parser.add_argument(
            'name', type=six.text_type, required=True)
        self.parser.add_argument(
            'description', type=six.text_type, required=False)

    @login_required
    def get(self):
        """Handles GET request to the resource.

        Returns:
            List of sketches (instance of flask.wrappers.Response)
        """
        # TODO: Handle offset parameter
        sketches = Sketch.all_with_acl().filter(
            not_(Sketch.Status.status == 'deleted'),
            Sketch.Status.parent).order_by(Sketch.updated_at.desc())
        paginated_result = sketches.paginate(1, 10, False)
        meta = {
            'next': paginated_result.next_num,
            'previous': paginated_result.prev_num,
            'offset': paginated_result.page,
            'limit': paginated_result.per_page
        }
        if not paginated_result.has_prev:
            meta['previous'] = None
        if not paginated_result.has_next:
            meta['next'] = None
        result = self.to_json(paginated_result.items, meta=meta)
        return result

    @login_required
    def post(self):
        """Handles POST request to the resource.

        Returns:
            A sketch in JSON (instance of flask.wrappers.Response)
        """
        form = NameDescriptionForm.build(request)
        if form.validate_on_submit():
            sketch = Sketch(
                name=form.name.data,
                description=form.description.data,
                user=current_user)
            sketch.status.append(sketch.Status(user=None, status='new'))
            db_session.add(sketch)
            db_session.commit()
            # Give the requesting user permissions on the new sketch.
            sketch.grant_permission(permission='read', user=current_user)
            sketch.grant_permission(permission='write', user=current_user)
            sketch.grant_permission(permission='delete', user=current_user)
            return self.to_json(sketch, status_code=HTTP_STATUS_CODE_CREATED)
        return abort(HTTP_STATUS_CODE_BAD_REQUEST)


class SketchResource(ResourceMixin, Resource):
    """Resource to get a sketch."""

    @login_required
    def get(self, sketch_id):
        """Handles GET request to the resource.

        Returns:
            A sketch in JSON (instance of flask.wrappers.Response)
        """
        sketch = Sketch.query.get_with_acl(sketch_id)
        meta = dict(
            aggregations=[{
                'name': aggregation.name,
                'id': aggregation.id,
                'created_at': aggregation.created_at,
                'updated_at': aggregation.updated_at
            } for aggregation in sketch.get_named_aggregations],
            views=[{
                'name': view.name,
                'id': view.id,
                'created_at': view.created_at,
                'updated_at': view.updated_at
            } for view in sketch.get_named_views],
            searchtemplates=[{
                'name': searchtemplate.name,
                'id': searchtemplate.id
            } for searchtemplate in SearchTemplate.query.all()],
            emojis=get_emojis_as_dict(),
            permissions={
                'read': bool(sketch.has_permission(current_user, 'read')),
                'write': bool(sketch.has_permission(current_user, 'write')),
                'delete': bool(sketch.has_permission(current_user, 'delete')),
            })
        return self.to_json(sketch, meta=meta)

    @login_required
    def delete(self, sketch_id):
        """Handles DELETE request to the resource."""
        sketch = Sketch.query.get_with_acl(sketch_id)
        if not sketch.has_permission(current_user, 'delete'):
            abort(HTTP_STATUS_CODE_FORBIDDEN)
        sketch.set_status(status='deleted')
        return HTTP_STATUS_CODE_OK


class ViewListResource(ResourceMixin, Resource):
    """Resource to create a View."""

    @staticmethod
    def create_view_from_form(sketch, form):
        """Creates a view from form data.

        Args:
            sketch: Instance of timesketch.models.sketch.Sketch
            form: Instance of timesketch.lib.forms.SaveViewForm

        Returns:
            A view (Instance of timesketch.models.sketch.View)
        """
        # Default to user supplied data
        view_name = form.name.data
        query_string = form.query.data
        query_filter = json.dumps(form.filter.data, ensure_ascii=False)
        query_dsl = json.dumps(form.dsl.data, ensure_ascii=False)

        if isinstance(query_filter, tuple):
            query_filter = query_filter[0]

        # No search template by default (before we know if the user want to
        # create a template or use an existing template when creating the view)
        searchtemplate = None

        # Create view from a search template
        if form.from_searchtemplate_id.data:
            # Get the template from the datastore
            template_id = form.from_searchtemplate_id.data
            searchtemplate = SearchTemplate.query.get(template_id)

            # Copy values from the template
            view_name = searchtemplate.name
            query_string = searchtemplate.query_string
            query_filter = searchtemplate.query_filter
            query_dsl = searchtemplate.query_dsl
            # WTF form returns a tuple for the filter. This is not
            # compatible with SQLAlchemy.
            if isinstance(query_filter, tuple):
                query_filter = query_filter[0]

        # Create a new search template based on this view (only if requested by
        # the user).
        if form.new_searchtemplate.data:
            query_filter_dict = json.loads(query_filter)
            if query_filter_dict.get('indices', None):
                query_filter_dict['indices'] = '_all'

            query_filter = json.dumps(query_filter_dict, ensure_ascii=False)

            searchtemplate = SearchTemplate(
                name=view_name,
                user=current_user,
                query_string=query_string,
                query_filter=query_filter,
                query_dsl=query_dsl)
            db_session.add(searchtemplate)
            db_session.commit()

        # Create the view in the database
        view = View(
            name=view_name,
            sketch=sketch,
            user=current_user,
            query_string=query_string,
            query_filter=query_filter,
            query_dsl=query_dsl,
            searchtemplate=searchtemplate)
        db_session.add(view)
        db_session.commit()

        return view

    @login_required
    def get(self, sketch_id):
        """Handles GET request to the resource.

        Args:
            sketch_id: Integer primary key for a sketch database model

        Returns:
            Views in JSON (instance of flask.wrappers.Response)
        """
        sketch = Sketch.query.get_with_acl(sketch_id)
        return self.to_json(sketch.get_named_views)

    @login_required
    def post(self, sketch_id):
        """Handles POST request to the resource.

        Args:
            sketch_id: Integer primary key for a sketch database model

        Returns:
            A view in JSON (instance of flask.wrappers.Response)
        """
        form = SaveViewForm.build(request)
        if form.validate_on_submit():
            sketch = Sketch.query.get_with_acl(sketch_id)
            view = self.create_view_from_form(sketch, form)
            return self.to_json(view, status_code=HTTP_STATUS_CODE_CREATED)
        return abort(HTTP_STATUS_CODE_BAD_REQUEST)


class ViewResource(ResourceMixin, Resource):
    """Resource to get a view."""

    @login_required
    def get(self, sketch_id, view_id):
        """Handles GET request to the resource.

        Args:
            sketch_id: Integer primary key for a sketch database model
            view_id: Integer primary key for a view database model

        Returns:
            A view in JSON (instance of flask.wrappers.Response)
        """
        sketch = Sketch.query.get_with_acl(sketch_id)
        view = View.query.get(view_id)

        # Check that this view belongs to the sketch
        if view.sketch_id != sketch.id:
            abort(HTTP_STATUS_CODE_NOT_FOUND)

        # If this is a user state view, check that it
        # belongs to the current_user
        if view.name == '' and view.user != current_user:
            abort(HTTP_STATUS_CODE_FORBIDDEN)

        # Check if view has been deleted
        if view.get_status.status == 'deleted':
            meta = dict(deleted=True, name=view.name)
            schema = dict(meta=meta, objects=[])
            return jsonify(schema)

        # Make sure we have all expected attributes in the query filter.
        view.query_filter = view.validate_filter()
        db_session.add(view)
        db_session.commit()

        return self.to_json(view)

    @login_required
    def delete(self, sketch_id, view_id):
        """Handles DELETE request to the resource.

        Args:
            sketch_id: Integer primary key for a sketch database model
            view_id: Integer primary key for a view database model
        """
        sketch = Sketch.query.get_with_acl(sketch_id)
        view = View.query.get(view_id)

        # Check that this view belongs to the sketch
        if view.sketch_id != sketch.id:
            abort(HTTP_STATUS_CODE_NOT_FOUND)

        if not sketch.has_permission(user=current_user, permission='write'):
            abort(HTTP_STATUS_CODE_FORBIDDEN)

        view.set_status(status='deleted')
        return HTTP_STATUS_CODE_OK

    @login_required
    def post(self, sketch_id, view_id):
        """Handles POST request to the resource.

        Args:
            sketch_id: Integer primary key for a sketch database model
            view_id: Integer primary key for a view database model

        Returns:
            A view in JSON (instance of flask.wrappers.Response)
        """
        form = SaveViewForm.build(request)
        if form.validate_on_submit():
            sketch = Sketch.query.get_with_acl(sketch_id)
            view = View.query.get(view_id)
            view.query_string = form.query.data
            view.query_filter = json.dumps(form.filter.data, ensure_ascii=False)
            view.query_dsl = json.dumps(form.dsl.data, ensure_ascii=False)
            view.user = current_user
            view.sketch = sketch

            if form.dsl.data:
                view.query_string = ''

            db_session.add(view)
            db_session.commit()
            return self.to_json(view, status_code=HTTP_STATUS_CODE_CREATED)
        return abort(HTTP_STATUS_CODE_BAD_REQUEST)


class SearchTemplateResource(ResourceMixin, Resource):
    """Resource to get a search template."""

    @login_required
    def get(self, searchtemplate_id):
        """Handles GET request to the resource.

        Args:
            searchtemplate_id: Primary key for a search template database model

        Returns:
            Search template in JSON (instance of flask.wrappers.Response)
        """
        searchtemplate = SearchTemplate.query.get(searchtemplate_id)
        if not searchtemplate:
            abort(HTTP_STATUS_CODE_NOT_FOUND)
        return self.to_json(searchtemplate)


class SearchTemplateListResource(ResourceMixin, Resource):
    """Resource to create a search template."""

    @login_required
    def get(self):
        """Handles GET request to the resource.

        Returns:
            View in JSON (instance of flask.wrappers.Response)
        """
        return self.to_json(SearchTemplate.query.all())


class ExploreResource(ResourceMixin, Resource):
    """Resource to search the datastore based on a query and a filter."""

    @login_required
    def post(self, sketch_id):
        """Handles POST request to the resource.
        Handler for /api/v1/sketches/:sketch_id/explore/

        Args:
            sketch_id: Integer primary key for a sketch database model

        Returns:
            JSON with list of matched events
        """
        sketch = Sketch.query.get_with_acl(sketch_id)
        form = ExploreForm.build(request)

        if not form.validate_on_submit():
            return abort(HTTP_STATUS_CODE_BAD_REQUEST)

        query_dsl = form.dsl.data
        query_filter = form.filter.data
        return_fields = form.fields.data
        enable_scroll = form.enable_scroll.data
        scroll_id = form.scroll_id.data

        if not return_fields:
            return_fields = DEFAULT_SOURCE_FIELDS

        sketch_indices = {
            t.searchindex.index_name
            for t in sketch.timelines
        }
        if not query_filter:
            query_filter = {}

        indices = query_filter.get('indices', sketch_indices)

        # If _all in indices then execute the query on all indices
        if '_all' in indices:
            indices = sketch_indices

        # Make sure that the indices in the filter are part of the sketch.
        # This will also remove any deleted timeline from the search result.
        indices = get_validated_indices(indices, sketch_indices)

        # Make sure we have a query string or star filter
        if not (form.query.data, query_filter.get('star'),
                query_filter.get('events'), query_dsl):
            abort(HTTP_STATUS_CODE_BAD_REQUEST)

        if scroll_id:
            # pylint: disable=unexpected-keyword-arg
            result = self.datastore.client.scroll(
                scroll_id=scroll_id, scroll='1m')
        else:
            result = self.datastore.search(
                sketch_id,
                form.query.data,
                query_filter,
                query_dsl,
                indices,
                aggregations=None,
                return_fields=return_fields,
                enable_scroll=enable_scroll)

        # Get labels for each event that matches the sketch.
        # Remove all other labels.
        for event in result['hits']['hits']:
            event['selected'] = False
            event['_source']['label'] = []
            try:
                for label in event['_source']['timesketch_label']:
                    if sketch.id != label['sketch_id']:
                        continue
                    event['_source']['label'].append(label['name'])
                del event['_source']['timesketch_label']
            except KeyError:
                pass

        # Update or create user state view. This is used in the UI to let
        # the user get back to the last state in the explore view.
        view = View.get_or_create(
            user=current_user, sketch=sketch, name='')
        view.query_string = form.query.data
        view.query_filter = json.dumps(query_filter, ensure_ascii=False)
        view.query_dsl = json.dumps(query_dsl, ensure_ascii=False)
        db_session.add(view)
        db_session.commit()

        # Add metadata for the query result. This is used by the UI to
        # render the event correctly and to display timing and hit count
        # information.
        tl_colors = {}
        tl_names = {}
        for timeline in sketch.timelines:
            tl_colors[timeline.searchindex.index_name] = timeline.color
            tl_names[timeline.searchindex.index_name] = timeline.name

        meta = {
            'es_time': result['took'],
            'es_total_count': result['hits']['total'],
            'timeline_colors': tl_colors,
            'timeline_names': tl_names,
            'scroll_id': result.get('_scroll_id', ''),
        }
        schema = {'meta': meta, 'objects': result['hits']['hits']}
        return jsonify(schema)


class AggregationResource(ResourceMixin, Resource):
    """Resource to query for aggregated results."""

    @login_required
    def get(self, sketch_id, aggregation_id):  # pylint: disable=unused-argument
        """Handles POST request to the resource.

        Handler for /api/v1/sketches/:sketch_id/aggregation/:aggregation_id

        Args:
            sketch_id: Integer primary key for a sketch database model
            aggregation_id: Integer primary key for an agregation database model

        Returns:
            JSON with aggregation results
        """
        sketch = Sketch.query.get_with_acl(sketch_id)
        aggregation = Aggregation.query.get(aggregation_id)

        # Check that this aggregation belongs to the sketch
        if aggregation.sketch_id != sketch.id:
            abort(HTTP_STATUS_CODE_NOT_FOUND)

        # If this is a user state view, check that it
        # belongs to the current_user
        if aggregation.name == '' and aggregation.user != current_user:
            abort(HTTP_STATUS_CODE_FORBIDDEN)

        return self.to_json(aggregation)

    @login_required
    def post(self, sketch_id, aggregation_id):  # pylint: disable=unused-argument
        """Handles POST request to the resource.

        Handler for /api/v1/sketches/:sketch_id/aggregation/:aggregation_id

        Args:
            sketch_id: Integer primary key for a sketch database model
            aggregation_id: Integer primary key for an aggregation database
                model
        """
        form = SaveAggregationForm.build(request)
        if not form.validate_on_submit():
            return abort(HTTP_STATUS_CODE_BAD_REQUEST)

        sketch = Sketch.query.get_with_acl(sketch_id)
        aggregation = Aggregation.query.get(aggregation_id)

        aggregation.name = form.name.data
        aggregation.description = form.description.data
        aggregation.agg_type = form.agg_type.data
        aggregation.chart_type = form.chart_type.data
        aggregation.user = current_user
        aggregation.sketch = sketch

        aggregation.parameters = json.dumps(
            form.parameters.data, ensure_ascii=False)

        if form.view.data:
            aggregation.view = form.view_id.data

        db_session.add(aggregation)
        db_session.commit()

        return self.to_json(aggregation, status_code=HTTP_STATUS_CODE_CREATED)


class AggregationExploreResource(ResourceMixin, Resource):
    """Resource to send an aggregation request."""

    REMOVE_FIELDS = frozenset(['_shards', 'hits', 'timed_out', 'took'])

    @login_required
    def post(self, sketch_id):
        """Handles POST request to the resource.

        Handler for /api/v1/sketches/<int:sketch_id>/aggregation/explore/

        Args:
            sketch_id: Integer primary key for a sketch database model

        Returns:
            JSON with aggregation results
        """
        form = AggregationExploreForm.build(request)
        if not form.validate_on_submit():
            return abort(HTTP_STATUS_CODE_BAD_REQUEST)

        sketch = Sketch.query.get_with_acl(sketch_id)
        sketch_indices = {
            t.searchindex.index_name
            for t in sketch.timelines
        }

        aggregation_dsl = form.aggregation_dsl.data
        aggregator_name = form.aggregator_name.data

        if aggregator_name:
            aggregator_parameters = json.loads(form.aggregator_parameters.data)
            agg_class = aggregator_manager.AggregatorManager.get_aggregator(
                aggregator_name)
            if not agg_class:
                return {}
            if not aggregator_parameters:
                aggregator_parameters = {}
            aggregator = agg_class(sketch_id=sketch_id)
            time_before = time.time()
            result_obj = aggregator.run(**aggregator_parameters)
            time_after = time.time()

            buckets = result_obj.to_dict()
            buckets['buckets'] = buckets.pop('values')
            result = {
                'aggregation_result': {
                    aggregator_name: buckets
                }
            }
            meta = {
                'method': 'aggregator_run',
                'name': aggregator_name,
                'es_time': time_after - time_before,
            }

        elif aggregation_dsl:
            # pylint: disable=unexpected-keyword-arg
            result = self.datastore.client.search(
                index=','.join(sketch_indices), body=aggregation_dsl, size=0)

            meta = {
                'es_time': result.get('took', 0),
                'es_total_count': result.get('hits', {}).get('total', 0),
                'timed_out': result.get('timed_out', False),
                'method': 'aggregator_query',
                'max_score': result.get('hits', {}).get('max_score', 0.0)
            }
        else:
            return abort(HTTP_STATUS_CODE_BAD_REQUEST)

        result_keys = set(result.keys()) - self.REMOVE_FIELDS
        objects = [result[key] for key in result_keys]
        schema = {'meta': meta, 'objects': objects}
        return jsonify(schema)


class AggregationListResource(ResourceMixin, Resource):
    """Resource to query for a list of stored aggregation queries."""

    @login_required
    def get(self, sketch_id):
        """Handles GET request to the resource.

        Handler for /api/v1/sketches/<int:sketch_id>/aggregation/

        Args:
            sketch_id: Integer primary key for a sketch database model

        Returns:
            Views in JSON (instance of flask.wrappers.Response)
        """
        sketch = Sketch.query.get_with_acl(sketch_id)
        aggregations = sketch.get_named_aggregations
        return self.to_json(aggregations)

    @staticmethod
    def create_aggregation_from_form(sketch, form):
        """Creates an aggregation from form data.

        Args:
            sketch: Instance of timesketch.models.sketch.Sketch
            form: Instance of timesketch.lib.forms.SaveAggregationForm

        Returns:
            An aggregation (instance of timesketch.models.sketch.Aggregation)
        """
        # Default to user supplied data
        name = form.name.data
        description = form.description.data
        agg_type = form.agg_type.data
        parameters = json.dumps(form.parameters.data, ensure_ascii=False)
        chart_type = form.chart_type.data
        view_id = form.view_id.data

        # Create the aggregation in the database
        aggregation = Aggregation(
            name=name,
            description=description,
            agg_type=agg_type,
            parameters=parameters,
            chart_type=chart_type,
            user=current_user,
            sketch=sketch,
            view=view_id
        )
        db_session.add(aggregation)
        db_session.commit()

        return aggregation

    @login_required
    def post(self, sketch_id):
        """Handles POST request to the resource.

        Args:
            sketch_id: Integer primary key for a sketch database model

        Returns:
            An aggregation in JSON (instance of flask.wrappers.Response)
        """
        form = SaveAggregationForm.build(request)
        if not form.validate_on_submit():
            return abort(HTTP_STATUS_CODE_BAD_REQUEST)

        sketch = Sketch.query.get_with_acl(sketch_id)
        aggregation = self.create_aggregation_from_form(sketch, form)
        return self.to_json(aggregation, status_code=HTTP_STATUS_CODE_CREATED)


class AggregationLegacyResource(ResourceMixin, Resource):
    """Resource to query for the legacy aggregated results."""

    @login_required
    def post(self, sketch_id):
        """Handles POST request to the resource.
        Handler for /api/v1/sketches/:sketch_id/aggregation/legacy

        Args:
            sketch_id: Integer primary key for a sketch database model

        Returns:
            JSON with aggregation results
        """
        sketch = Sketch.query.get_with_acl(sketch_id)
        form = AggregationLegacyForm.build(request)

        if form.validate_on_submit():
            query_filter = form.filter.data
            query_dsl = form.dsl.data
            sketch_indices = [
                t.searchindex.index_name for t in sketch.timelines
            ]
            indices = query_filter.get('indices', sketch_indices)

            # If _all in indices then execute the query on all indices
            if '_all' in indices:
                indices = sketch_indices

            # Make sure that the indices in the filter are part of the sketch.
            # This will also remove any deleted timeline from the search result.
            indices = get_validated_indices(indices, sketch_indices)

            # Make sure we have a query string or star filter
            if not (form.query.data, query_filter.get('star'),
                    query_filter.get('events')):
                abort(HTTP_STATUS_CODE_BAD_REQUEST)

            result = []
            if form.aggtype.data == 'heatmap':
                result = heatmap(
                    es_client=self.datastore,
                    sketch_id=sketch_id,
                    query_string=form.query.data,
                    query_filter=query_filter,
                    query_dsl=query_dsl,
                    indices=indices)
            elif form.aggtype.data == 'histogram':
                result = histogram(
                    es_client=self.datastore,
                    sketch_id=sketch_id,
                    query_string=form.query.data,
                    query_filter=query_filter,
                    query_dsl=query_dsl,
                    indices=indices)

            else:
                abort(HTTP_STATUS_CODE_BAD_REQUEST)

            schema = {'objects': result}
            return jsonify(schema)
        return abort(HTTP_STATUS_CODE_BAD_REQUEST)


class EventCreateResource(ResourceMixin, Resource):
    """Resource to create an annotation for an event."""

    @login_required
    def post(self, sketch_id):
        """Handles POST request to the resource.
        Handler for /api/v1/sketches/:sketch_id/event/create/

        Args:
            sketch_id: Integer primary key for a sketch database model

        Returns:
            An annotation in JSON (instance of flask.wrappers.Response)
        """
        form = EventCreateForm.build(request)
        if form.validate_on_submit():
            sketch = Sketch.query.get_with_acl(sketch_id)
            timeline_name = 'sketch specific timeline'
            index_name_seed = 'timesketch' + str(sketch_id)
            event_type = 'user_created_event'

            # derive datetime from timestamp:
            parsed_datetime = parser.parse(form.timestamp.data)
            timestamp = int(
                time.mktime(parsed_datetime.utctimetuple())) * 1000000
            timestamp += parsed_datetime.microsecond

            event = {
                "datetime": form.timestamp.data,
                "timestamp": timestamp,
                "timestamp_desc": form.timestamp_desc.data,
                "message": form.message.data,
            }

            # We do not need a human readable filename or
            # datastore index name, so we use UUIDs here.
            index_name = hashlib.md5(index_name_seed.encode()).hexdigest()
            if six.PY2:
                index_name = codecs.decode(index_name, 'utf-8')

            # Try to create index
            try:
                # Create the index in Elasticsearch (unless it already exists)
                self.datastore.create_index(
                    index_name=index_name,
                    doc_type=event_type)

                # Create the search index in the Timesketch database
                searchindex = SearchIndex.get_or_create(
                    name=timeline_name,
                    description='internal timeline for user-created events',
                    user=current_user,
                    index_name=index_name)
                searchindex.grant_permission(
                    permission='read', user=current_user)
                searchindex.grant_permission(
                    permission='write', user=current_user)
                searchindex.grant_permission(
                    permission='delete', user=current_user)
                searchindex.set_status('ready')
                db_session.add(searchindex)
                db_session.commit()

                timeline = None
                if sketch and sketch.has_permission(current_user, 'write'):
                    self.datastore.import_event(
                        index_name,
                        event_type,
                        event,
                        flush_interval=1)

                    timeline = Timeline.get_or_create(
                        name=searchindex.name,
                        description=searchindex.description,
                        sketch=sketch,
                        user=current_user,
                        searchindex=searchindex)

                    if timeline not in sketch.timelines:
                        sketch.timelines.append(timeline)

                    db_session.add(timeline)
                    db_session.commit()

                # Return Timeline if it was created.
                # pylint: disable=no-else-return
                if timeline:
                    return self.to_json(
                        timeline, status_code=HTTP_STATUS_CODE_CREATED)
                else:
                    return self.to_json(
                        searchindex, status_code=HTTP_STATUS_CODE_CREATED)

            except Exception:
                raise ApiHTTPError(
                    message="failed to add event",
                    status_code=HTTP_STATUS_CODE_BAD_REQUEST)

        else:
            raise ApiHTTPError(
                message="failed to add event",
                status_code=HTTP_STATUS_CODE_BAD_REQUEST)


class EventResource(ResourceMixin, Resource):
    """Resource to get a single event from the datastore.

    HTTP Args:
        searchindex_id: The datastore searchindex id as string
        event_id: The datastore event id as string
    """

    def __init__(self):
        super(EventResource, self).__init__()
        self.parser = reqparse.RequestParser()
        self.parser.add_argument(
            'searchindex_id', type=six.text_type, required=True)
        self.parser.add_argument('event_id', type=six.text_type, required=True)

    @login_required
    def get(self, sketch_id):
        """Handles GET request to the resource.
        Handler for /api/v1/sketches/:sketch_id/event/

        Args:
            sketch_id: Integer primary key for a sketch database model

        Returns:
            JSON of the datastore event
        """

        args = self.parser.parse_args()
        sketch = Sketch.query.get_with_acl(sketch_id)
        searchindex_id = args.get('searchindex_id')
        searchindex = SearchIndex.query.filter_by(
            index_name=searchindex_id).first()
        event_id = args.get('event_id')
        indices = [t.searchindex.index_name for t in sketch.timelines]

        # Check if the requested searchindex is part of the sketch
        if searchindex_id not in indices:
            abort(HTTP_STATUS_CODE_BAD_REQUEST)

        result = self.datastore.get_event(searchindex_id, event_id)

        event = Event.query.filter_by(
            sketch=sketch, searchindex=searchindex,
            document_id=event_id).first()

        # Comments for this event
        comments = []
        if event:
            for comment in event.comments:
                if not comment.user:
                    username = 'System'
                else:
                    username = comment.user.username
                comment_dict = {
                    'user': {
                        'username': username,
                    },
                    'created_at': comment.created_at,
                    'comment': comment.comment
                }
                comments.append(comment_dict)

        schema = {
            'meta': {
                'comments': comments
            },
            'objects': result['_source']
        }
        return jsonify(schema)


class EventAnnotationResource(ResourceMixin, Resource):
    """Resource to create an annotation for an event."""

    @login_required
    def post(self, sketch_id):
        """Handles POST request to the resource.

        Args:
            sketch_id: Integer primary key for a sketch database model

        Returns:
            An annotation in JSON (instance of flask.wrappers.Response)
        """
        form = EventAnnotationForm.build(request)
        if form.validate_on_submit():
            annotations = []
            sketch = Sketch.query.get_with_acl(sketch_id)
            indices = [t.searchindex.index_name for t in sketch.timelines]
            annotation_type = form.annotation_type.data
            events = form.events.raw_data

            for _event in events:
                searchindex_id = _event['_index']
                searchindex = SearchIndex.query.filter_by(
                    index_name=searchindex_id).first()
                event_id = _event['_id']
                event_type = _event['_type']

                if searchindex_id not in indices:
                    abort(HTTP_STATUS_CODE_BAD_REQUEST)

                # Get or create an event in the SQL database to have something
                # to attach the annotation to.
                event = Event.get_or_create(
                    sketch=sketch,
                    searchindex=searchindex,
                    document_id=event_id)

                # Add the annotation to the event object.
                if 'comment' in annotation_type:
                    annotation = Event.Comment(
                        comment=form.annotation.data, user=current_user)
                    event.comments.append(annotation)
                    self.datastore.set_label(
                        searchindex_id,
                        event_id,
                        event_type,
                        sketch.id,
                        current_user.id,
                        '__ts_comment',
                        toggle=False)

                elif 'label' in annotation_type:
                    annotation = Event.Label.get_or_create(
                        label=form.annotation.data, user=current_user)
                    if annotation not in event.labels:
                        event.labels.append(annotation)
                    toggle = False
                    if '__ts_star' or '__ts_hidden' in form.annotation.data:
                        toggle = True
                    self.datastore.set_label(
                        searchindex_id,
                        event_id,
                        event_type,
                        sketch.id,
                        current_user.id,
                        form.annotation.data,
                        toggle=toggle)
                else:
                    abort(HTTP_STATUS_CODE_BAD_REQUEST)

                annotations.append(annotation)
                # Save the event to the database
                db_session.add(event)
                db_session.commit()
            return self.to_json(
                annotations, status_code=HTTP_STATUS_CODE_CREATED)
        return abort(HTTP_STATUS_CODE_BAD_REQUEST)


class UploadFileResource(ResourceMixin, Resource):
    """Resource that processes uploaded files."""

    @login_required
    def post(self):
        """Handles POST request to the resource.

        Returns:
            A view in JSON (instance of flask.wrappers.Response)

        Raises:
            ApiHTTPError
        """
        upload_enabled = current_app.config['UPLOAD_ENABLED']
        upload_folder = current_app.config['UPLOAD_FOLDER']

        form = UploadFileForm()
        if form.validate_on_submit() and upload_enabled:
            sketch_id = form.sketch_id.data or None
            file_storage = form.file.data
            _filename, _extension = os.path.splitext(file_storage.filename)
            file_extension = _extension.lstrip('.')
            timeline_name = form.name.data or _filename.rstrip('.')

            sketch = None
            if sketch_id:
                sketch = Sketch.query.get_with_acl(sketch_id)

            # We do not need a human readable filename or
            # datastore index name, so we use UUIDs here.
            filename = uuid.uuid4().hex
            if not isinstance(filename, six.text_type):
                filename = codecs.decode(filename, 'utf-8')

            index_name = uuid.uuid4().hex
            if not isinstance(index_name, six.text_type):
                index_name = codecs.decode(index_name, 'utf-8')

            file_path = os.path.join(upload_folder, filename)
            file_storage.save(file_path)

            # Create the search index in the Timesketch database
            searchindex = SearchIndex.get_or_create(
                name=timeline_name,
                description=timeline_name,
                user=current_user,
                index_name=index_name)
            searchindex.grant_permission(permission='read', user=current_user)
            searchindex.grant_permission(permission='write', user=current_user)
            searchindex.grant_permission(
                permission='delete', user=current_user)
            searchindex.set_status('processing')
            db_session.add(searchindex)
            db_session.commit()

            timeline = None
            if sketch and sketch.has_permission(current_user, 'write'):
                timeline = Timeline(
                    name=searchindex.name,
                    description=searchindex.description,
                    sketch=sketch,
                    user=current_user,
                    searchindex=searchindex)
                timeline.set_status('processing')
                sketch.timelines.append(timeline)
                db_session.add(timeline)
                db_session.commit()

            # Start Celery pipeline for indexing and analysis.
            # Import here to avoid circular imports.
            from timesketch.lib import tasks
            pipeline = tasks.build_index_pipeline(
                file_path, timeline_name, index_name, file_extension, sketch_id)
            pipeline.apply_async(task_id=index_name)

            # Return Timeline if it was created.
            # pylint: disable=no-else-return
            if timeline:
                return self.to_json(
                    timeline, status_code=HTTP_STATUS_CODE_CREATED)

            return self.to_json(
                searchindex, status_code=HTTP_STATUS_CODE_CREATED)

        raise ApiHTTPError(
            message=form.errors['file'][0],
            status_code=HTTP_STATUS_CODE_BAD_REQUEST)


class TaskResource(ResourceMixin, Resource):
    """Resource to get information on celery task."""

    def __init__(self):
        super(TaskResource, self).__init__()
        from timesketch import create_celery_app
        self.celery = create_celery_app()

    @login_required
    def get(self):
        """Handles GET request to the resource.

        Returns:
            A view in JSON (instance of flask.wrappers.Response)
        """
        TIMEOUT_THRESHOLD_SECONDS = current_app.config.get(
            'CELERY_TASK_TIMEOUT', 7200)
        indices = SearchIndex.query.filter(
            SearchIndex.status.any(status='processing')).filter_by(
                user=current_user).all()
        schema = {'objects': [], 'meta': {}}
        for search_index in indices:
            # pylint: disable=too-many-function-args
            celery_task = self.celery.AsyncResult(search_index.index_name)
            task = dict(
                task_id=celery_task.task_id,
                state=celery_task.state,
                successful=celery_task.successful(),
                name=search_index.name,
                result=False)
            if celery_task.state == 'SUCCESS':
                task['result'] = celery_task.result
            elif celery_task.state == 'PENDING':
                time_pending = (
                    search_index.updated_at - datetime.datetime.now())
                if time_pending.seconds > TIMEOUT_THRESHOLD_SECONDS:
                    search_index.set_status('timeout')
            schema['objects'].append(task)
        return jsonify(schema)


class StoryListResource(ResourceMixin, Resource):
    """Resource to get all stories for a sketch or to create a new story."""

    @login_required
    def get(self, sketch_id):
        """Handles GET request to the resource.

        Args:
            sketch_id: Integer primary key for a sketch database model

        Returns:
            Stories in JSON (instance of flask.wrappers.Response)
        """
        sketch = Sketch.query.get_with_acl(sketch_id)
        stories = []
        for story in Story.query.filter_by(
                sketch=sketch).order_by(desc(Story.created_at)):
            stories.append(story)
        return self.to_json(stories)

    @login_required
    def post(self, sketch_id):
        """Handles POST request to the resource.

        Args:
            sketch_id: Integer primary key for a sketch database model

        Returns:
            A view in JSON (instance of flask.wrappers.Response)
        """
        form = StoryForm.build(request)
        if form.validate_on_submit():
            title = ''
            if form.title.data:
                title = form.title.data
            sketch = Sketch.query.get_with_acl(sketch_id)
            story = Story(
                title=title, content='', sketch=sketch, user=current_user)
            db_session.add(story)
            db_session.commit()
            return self.to_json(story, status_code=HTTP_STATUS_CODE_CREATED)
        return abort(HTTP_STATUS_CODE_BAD_REQUEST)


class StoryResource(ResourceMixin, Resource):
    """Resource to get a story."""

    @login_required
    def get(self, sketch_id, story_id):
        """Handles GET request to the resource.

        Args:
            sketch_id: Integer primary key for a sketch database model
            story_id: Integer primary key for a story database model

        Returns:
            A story in JSON (instance of flask.wrappers.Response)
        """
        sketch = Sketch.query.get_with_acl(sketch_id)
        story = Story.query.get(story_id)

        # Check that this story belongs to the sketch
        if story.sketch_id != sketch.id:
            abort(HTTP_STATUS_CODE_NOT_FOUND)

        # Only allow editing if the current user is the author.
        # This is needed until we have proper collaborative editing and
        # locking implemented.
        meta = dict(is_editable=False)
        if current_user == story.user:
            meta['is_editable'] = True

        return self.to_json(story, meta=meta)

    @login_required
    def post(self, sketch_id, story_id):
        """Handles POST request to the resource.

        Args:
            sketch_id: Integer primary key for a sketch database model
            story_id: Integer primary key for a story database model

        Returns:
            A view in JSON (instance of flask.wrappers.Response)
        """
        form = StoryForm.build(request)
        if form.validate_on_submit():
            sketch = Sketch.query.get_with_acl(sketch_id)
            story = Story.query.get(story_id)

            if story.sketch_id != sketch.id:
                abort(HTTP_STATUS_CODE_NOT_FOUND)

            story.title = form.title.data
            story.content = form.content.data
            db_session.add(story)
            db_session.commit()
            return self.to_json(story, status_code=HTTP_STATUS_CODE_CREATED)
        return abort(HTTP_STATUS_CODE_BAD_REQUEST)


class QueryResource(ResourceMixin, Resource):
    """Resource to get a query."""

    @login_required
    def post(self, sketch_id):
        """Handles GET request to the resource.

        Args:
            sketch_id: Integer primary key for a sketch database model

        Returns:
            A story in JSON (instance of flask.wrappers.Response)
        """
        form = ExploreForm.build(request)
        if form.validate_on_submit():
            sketch = Sketch.query.get_with_acl(sketch_id)
            schema = {'objects': [], 'meta': {}}
            query_string = form.query.data
            query_filter = form.filter.data
            query_dsl = form.dsl.data
            query = self.datastore.build_query(sketch.id, query_string,
                                               query_filter, query_dsl)
            schema['objects'].append(query)
            return jsonify(schema)
        return abort(HTTP_STATUS_CODE_BAD_REQUEST)


class CountEventsResource(ResourceMixin, Resource):
    """Resource to number of events for sketch timelines."""

    @login_required
    def get(self, sketch_id):
        """Handles GET request to the resource.

        Args:
            sketch_id: Integer primary key for a sketch database model

        Returns:
            Number of events in JSON (instance of flask.wrappers.Response)
        """
        sketch = Sketch.query.get_with_acl(sketch_id)
        indices = [t.searchindex.index_name for t in sketch.active_timelines]
        count = self.datastore.count(indices)
        meta = dict(count=count)
        schema = dict(meta=meta, objects=[])
        return jsonify(schema)


class TimelineCreateResource(ResourceMixin, Resource):
    """Resource to create a timeline."""

    @login_required
    def post(self):
        """Handles POST request to the resource.

        Returns:
            A view in JSON (instance of flask.wrappers.Response)

        Raises:
            ApiHTTPError
        """
        upload_enabled = current_app.config['UPLOAD_ENABLED']
        form = CreateTimelineForm()
        if form.validate_on_submit() and upload_enabled:
            sketch_id = form.sketch_id.data
            timeline_name = form.name.data

            sketch = None
            if sketch_id:
                sketch = Sketch.query.get_with_acl(sketch_id)

            # We do not need a human readable filename or
            # datastore index name, so we use UUIDs here.
            index_name = uuid.uuid4().hex
            if not isinstance(index_name, six.text_type):
                index_name = codecs.decode(index_name, 'utf-8')

            # Create the search index in the Timesketch database
            searchindex = SearchIndex.get_or_create(
                name=timeline_name,
                description=timeline_name,
                user=current_user,
                index_name=index_name)
            searchindex.grant_permission(permission='read', user=current_user)
            searchindex.grant_permission(permission='write', user=current_user)
            searchindex.grant_permission(
                permission='delete', user=current_user)
            searchindex.set_status('processing')
            db_session.add(searchindex)
            db_session.commit()

            timeline = None
            if sketch and sketch.has_permission(current_user, 'write'):
                timeline = Timeline(
                    name=searchindex.name,
                    description=searchindex.description,
                    sketch=sketch,
                    user=current_user,
                    searchindex=searchindex)
                sketch.timelines.append(timeline)
                db_session.add(timeline)
                db_session.commit()

            # Return Timeline if it was created.
            # pylint: disable=no-else-return
            if timeline:
                return self.to_json(
                    timeline, status_code=HTTP_STATUS_CODE_CREATED)

            return self.to_json(
                searchindex, status_code=HTTP_STATUS_CODE_CREATED)

        raise ApiHTTPError(
            message="failed to create timeline",
            status_code=HTTP_STATUS_CODE_BAD_REQUEST)


class TimelineListResource(ResourceMixin, Resource):
    """Resource to get all timelines for sketch."""

    @login_required
    def get(self, sketch_id):
        """Handles GET request to the resource.

        Returns:
            View in JSON (instance of flask.wrappers.Response)
        """
        sketch = Sketch.query.get_with_acl(sketch_id)
        return self.to_json(sketch.timelines)

    @login_required
    def post(self, sketch_id):
        """Handles POST request to the resource.

        Returns:
            A sketch in JSON (instance of flask.wrappers.Response)
        """
        sketch = Sketch.query.get_with_acl(sketch_id)
        form = AddTimelineSimpleForm.build(request)
        metadata = {'created': True}

        searchindex_id = form.timeline.data
        searchindex = SearchIndex.query.get_with_acl(searchindex_id)
        timeline_id = [
            t.searchindex.id for t in sketch.timelines
            if t.searchindex.id == searchindex_id
        ]

        if form.validate_on_submit():
            if not sketch.has_permission(current_user, 'write'):
                abort(HTTP_STATUS_CODE_FORBIDDEN)

            if not timeline_id:
                return_code = HTTP_STATUS_CODE_CREATED
                timeline = Timeline(
                    name=searchindex.name,
                    description=searchindex.description,
                    sketch=sketch,
                    user=current_user,
                    searchindex=searchindex)
                sketch.timelines.append(timeline)
                db_session.add(timeline)
                db_session.commit()
            else:
                metadata['created'] = False
                return_code = HTTP_STATUS_CODE_OK
                timeline = Timeline.query.get(timeline_id)

            # If enabled, run sketch analyzers when timeline is added.
            # Import here to avoid circular imports.
            if current_app.config.get('ENABLE_SKETCH_ANALYZERS'):
                from timesketch.lib import tasks
                sketch_analyzer_group = tasks.build_sketch_analysis_pipeline(
                    sketch_id)
                if sketch_analyzer_group:
                    pipeline = (tasks.run_sketch_init.s(
                        [searchindex.index_name]) | sketch_analyzer_group)
                    pipeline.apply_async(task_id=searchindex.index_name)

            return self.to_json(
                timeline, meta=metadata, status_code=return_code)

        return abort(HTTP_STATUS_CODE_BAD_REQUEST)


class TimelineResource(ResourceMixin, Resource):
    """Resource to get timeline."""

    @login_required
    def get(self, sketch_id, timeline_id):
        """Handles GET request to the resource.

        Args:
            sketch_id: Integer primary key for a sketch database model
            timeline_id: Integer primary key for a timeline database model
        """
        sketch = Sketch.query.get_with_acl(sketch_id)
        timeline = Timeline.query.get(timeline_id)

        # Check that this timeline belongs to the sketch
        if timeline.sketch_id != sketch.id:
            abort(HTTP_STATUS_CODE_NOT_FOUND)

        if not sketch.has_permission(user=current_user, permission='read'):
            abort(HTTP_STATUS_CODE_FORBIDDEN)

        return self.to_json(timeline)

    @login_required
    def post(self, sketch_id, timeline_id):
        """Handles GET request to the resource.

        Args:
            sketch_id: Integer primary key for a sketch database model
            timeline_id: Integer primary key for a timeline database model
        """
        sketch = Sketch.query.get_with_acl(sketch_id)
        timeline = Timeline.query.get(timeline_id)
        form = TimelineForm.build(request)

        # Check that this timeline belongs to the sketch
        if timeline.sketch_id != sketch.id:
            abort(HTTP_STATUS_CODE_NOT_FOUND)

        if not sketch.has_permission(user=current_user, permission='write'):
            abort(HTTP_STATUS_CODE_FORBIDDEN)

        if not form.validate_on_submit():
            abort(HTTP_STATUS_CODE_BAD_REQUEST)

        timeline.name = form.name.data
        timeline.description = form.description.data
        timeline.color = form.color.data
        db_session.add(timeline)
        db_session.commit()

        return HTTP_STATUS_CODE_OK

    @login_required
    def delete(self, sketch_id, timeline_id):
        """Handles DELETE request to the resource.

        Args:
            sketch_id: Integer primary key for a sketch database model
            timeline_id: Integer primary key for a timeline database model
        """
        sketch = Sketch.query.get_with_acl(sketch_id)
        timeline = Timeline.query.get(timeline_id)

        # Check that this timeline belongs to the sketch
        if timeline.sketch_id != sketch.id:
            abort(HTTP_STATUS_CODE_NOT_FOUND)

        if not sketch.has_permission(user=current_user, permission='write'):
            abort(HTTP_STATUS_CODE_FORBIDDEN)

        sketch.timelines.remove(timeline)
        db_session.commit()
        return HTTP_STATUS_CODE_OK


class GraphResource(ResourceMixin, Resource):
    """Resource to get result from graph query."""

    @login_required
    def post(self, sketch_id):
        """Handles GET request to the resource.

        Args:
            sketch_id: Integer primary key for a sketch database model

        Returns:
            Graph in JSON (instance of flask.wrappers.Response) or None if
            form does not validate on submit.
        """
        # Check access to the sketch
        Sketch.query.get_with_acl(sketch_id)

        form = GraphExploreForm.build(request)
        if form.validate_on_submit():
            graph_view_id = form.graph_view_id.data
            parameters = form.parameters.data
            output_format = form.output_format.data

            graph_view = GRAPH_VIEWS[graph_view_id]
            query = graph_view['query']

            parameters['sketch_id'] = str(sketch_id)

            result = self.graph_datastore.query(
                query, params=parameters, output_format=output_format)

            for edge in result['graph']['edges']:
                edge_data = edge['data']
                timestamps = edge_data.get('timestamps', [])
                edge_data['count'] = str(len(timestamps))

                if edge_data.get('timestamps_incomplete'):
                    edge_data['count'] += '+'
                if edge_data['count'] == '0+':
                    edge_data['count'] = '???'

            schema = {
                'meta': {
                    'schema': neo4j_schema
                },
                'objects': [{
                    'graph': result['graph'],
                }]
            }
            return jsonify(schema)

        return None


class GraphViewListResource(ResourceMixin, Resource):
    """Resource to get result from graph query."""

    @login_required
    def get(self, sketch_id):
        """Handles GET requests to the resource.

        Args:
            sketch_id: Integer primary key for a sketch database model.

        Returns:
            Graph in JSON (instance of flask.wrappers.Response)
        """
        # Check access to the sketch
        Sketch.query.get_with_acl(sketch_id)

        schema = {
            'objects': [{
                'views': get_graph_views()
            }]
        }
        return jsonify(schema)


class GraphViewResource(ResourceMixin, Resource):
    """Resource to get result from graph query."""

    @login_required
    def get(self, sketch_id, view_id):
        """Handles GET request to the resource.

        Args:
            sketch_id: Integer primary key for a sketch database model.
            view_id: Integer key for a graph view.

        Returns:
            Graph in JSON (instance of flask.wrappers.Response)
        """
        # Check access to the sketch
        Sketch.query.get_with_acl(sketch_id)
        view = get_graph_view(view_id)

        if not view:
            return abort(HTTP_STATUS_CODE_NOT_FOUND)

        schema = {
            'objects': [{
                'views': view
            }]
        }
        return jsonify(schema)


class SearchIndexListResource(ResourceMixin, Resource):
    """Resource to get all search indices."""

    @login_required
    def get(self):
        """Handles GET request to the resource.

        Returns:
            List of search indices in JSON (instance of flask.wrappers.Response)
        """
        indices = SearchIndex.all_with_acl(current_user).all()
        return self.to_json(indices)

    @login_required
    def post(self):
        """Handles POST request to the resource.

        Returns:
            A search index in JSON (instance of flask.wrappers.Response)
        """
        form = SearchIndexForm.build(request)
        searchindex_name = form.searchindex_name.data
        es_index_name = form.es_index_name.data
        public = form.public.data

        if form.validate_on_submit():
            searchindex = SearchIndex.query.filter_by(
                index_name=es_index_name).first()
            metadata = {'created': True}

            if searchindex:
                metadata['created'] = False
                status_code = HTTP_STATUS_CODE_OK
            else:
                searchindex = SearchIndex.get_or_create(
                    name=searchindex_name,
                    description=searchindex_name,
                    user=current_user,
                    index_name=es_index_name)
                searchindex.grant_permission(
                    permission='read', user=current_user)

                if public:
                    searchindex.grant_permission(permission='read', user=None)

                # Create the index in Elasticsearch
                self.datastore.create_index(
                    index_name=es_index_name, doc_type='generic_event')

                db_session.add(searchindex)
                db_session.commit()
                status_code = HTTP_STATUS_CODE_CREATED

            return self.to_json(
                searchindex, meta=metadata, status_code=status_code)

        return abort(HTTP_STATUS_CODE_BAD_REQUEST)


class SearchIndexResource(ResourceMixin, Resource):
    """Resource to get search index."""

    @login_required
    def get(self, searchindex_id):
        """Handles GET request to the resource.

        Returns:
            Search index in JSON (instance of flask.wrappers.Response)
        """
        searchindex = SearchIndex.query.get_with_acl(searchindex_id)
        return self.to_json(searchindex)
