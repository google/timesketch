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

import datetime
import json
import md5
import os
import time
import uuid

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
import pycypher

from timesketch.lib.aggregators import heatmap
from timesketch.lib.aggregators import histogram
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
from timesketch.lib.forms import AddTimelineSimpleForm
from timesketch.lib.forms import AggregationForm
from timesketch.lib.forms import CreateTimelineForm
from timesketch.lib.forms import SaveViewForm
from timesketch.lib.forms import NameDescriptionForm
from timesketch.lib.forms import EventAnnotationForm
from timesketch.lib.forms import EventCreateForm
from timesketch.lib.forms import ExploreForm
from timesketch.lib.forms import UploadFileForm
from timesketch.lib.forms import StoryForm
from timesketch.lib.forms import GraphExploreForm
from timesketch.lib.forms import SearchIndexForm
from timesketch.lib.utils import get_validated_indices
from timesketch.lib.cypher import transpile_query, InvalidQuery
from timesketch.models import db_session
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
    response = jsonify({u'message': message})
    response.status_code = HTTP_STATUS_CODE_BAD_REQUEST
    return response


class ResourceMixin(object):
    """Mixin for API resources."""
    # Schemas for database model resources

    status_fields = {
        u'id': fields.Integer,
        u'status': fields.String,
        u'created_at': fields.DateTime,
        u'updated_at': fields.DateTime
    }

    searchindex_fields = {
        u'id': fields.Integer,
        u'name': fields.String,
        u'description': fields.String,
        u'index_name': fields.String,
        u'status': fields.Nested(status_fields),
        u'deleted': fields.Boolean,
        u'created_at': fields.DateTime,
        u'updated_at': fields.DateTime
    }

    timeline_fields = {
        u'id': fields.Integer,
        u'name': fields.String,
        u'description': fields.String,
        u'status': fields.Nested(status_fields),
        u'color': fields.String,
        u'searchindex': fields.Nested(searchindex_fields),
        u'deleted': fields.Boolean,
        u'created_at': fields.DateTime,
        u'updated_at': fields.DateTime
    }

    user_fields = {u'username': fields.String}

    searchtemplate_fields = {
        u'id': fields.Integer,
        u'name': fields.String,
        u'user': fields.Nested(user_fields),
        u'query_string': fields.String,
        u'query_filter': fields.String,
        u'query_dsl': fields.String,
        u'created_at': fields.DateTime,
        u'updated_at': fields.DateTime
    }

    view_fields = {
        u'id': fields.Integer,
        u'name': fields.String,
        u'user': fields.Nested(user_fields),
        u'query_string': fields.String,
        u'query_filter': fields.String,
        u'query_dsl': fields.String,
        u'searchtemplate': fields.Nested(searchtemplate_fields),
        u'created_at': fields.DateTime,
        u'updated_at': fields.DateTime
    }

    sketch_fields = {
        u'id': fields.Integer,
        u'name': fields.String,
        u'description': fields.String,
        u'user': fields.Nested(user_fields),
        u'timelines': fields.List(fields.Nested(timeline_fields)),
        u'active_timelines': fields.List(fields.Nested(timeline_fields)),
        u'status': fields.Nested(status_fields),
        u'created_at': fields.DateTime,
        u'updated_at': fields.DateTime
    }

    story_fields = {
        u'id': fields.Integer,
        u'title': fields.String,
        u'content': fields.String,
        u'user': fields.Nested(user_fields),
        u'sketch': fields.Nested(sketch_fields),
        u'created_at': fields.DateTime,
        u'updated_at': fields.DateTime
    }

    comment_fields = {
        u'comment': fields.String,
        u'user': fields.Nested(user_fields),
        u'created_at': fields.DateTime,
        u'updated_at': fields.DateTime
    }

    label_fields = {
        u'name': fields.String,
        u'user': fields.Nested(user_fields),
        u'created_at': fields.DateTime,
        u'updated_at': fields.DateTime
    }

    fields_registry = {
        u'searchindex': searchindex_fields,
        u'timeline': timeline_fields,
        u'searchtemplate': searchtemplate_fields,
        u'view': view_fields,
        u'user': user_fields,
        u'sketch': sketch_fields,
        u'story': story_fields,
        u'event_comment': comment_fields,
        u'event_label': label_fields
    }

    @property
    def datastore(self):
        """Property to get an instance of the datastore backend.

        Returns:
            Instance of timesketch.lib.datastores.elastic.ElasticSearchDatastore
        """
        return ElasticsearchDataStore(
            host=current_app.config[u'ELASTIC_HOST'],
            port=current_app.config[u'ELASTIC_PORT'])

    @property
    def graph_datastore(self):
        """Property to get an instance of the graph database backend.

        Returns:
            Instance of timesketch.lib.datastores.neo4j.Neo4jDatabase
        """
        return Neo4jDataStore(
            host=current_app.config[u'NEO4J_HOST'],
            port=current_app.config[u'NEO4J_PORT'],
            username=current_app.config[u'NEO4J_USERNAME'],
            password=current_app.config[u'NEO4J_PASSWORD'])

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

        schema = {u'meta': meta, u'objects': []}

        if model:
            if not model_fields:
                try:
                    model_fields = self.fields_registry[model.__tablename__]
                except AttributeError:
                    model_fields = self.fields_registry[model[0].__tablename__]
            schema[u'objects'] = [marshal(model, model_fields)]

        response = jsonify(schema)
        response.status_code = status_code
        return response


class SketchListResource(ResourceMixin, Resource):
    """Resource for listing sketches."""

    def __init__(self):
        super(SketchListResource, self).__init__()
        self.parser = reqparse.RequestParser()
        self.parser.add_argument(u'name', type=unicode, required=True)
        self.parser.add_argument(u'description', type=unicode, required=False)

    @login_required
    def get(self):
        """Handles GET request to the resource.

        Returns:
            List of sketches (instance of flask.wrappers.Response)
        """
        # TODO: Handle offset parameter
        sketches = Sketch.all_with_acl().filter(
            not_(Sketch.Status.status == u'deleted'),
            Sketch.Status.parent).order_by(Sketch.updated_at.desc())
        paginated_result = sketches.paginate(1, 10, False)
        meta = {
            u'next': paginated_result.next_num,
            u'previous': paginated_result.prev_num,
            u'offset': paginated_result.page,
            u'limit': paginated_result.per_page
        }
        if not paginated_result.has_prev:
            meta[u'previous'] = None
        if not paginated_result.has_next:
            meta[u'next'] = None
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
            sketch.status.append(sketch.Status(user=None, status=u'new'))
            # Give the requesting user permissions on the new sketch.
            sketch.grant_permission(permission=u'read', user=current_user)
            sketch.grant_permission(permission=u'write', user=current_user)
            sketch.grant_permission(permission=u'delete', user=current_user)
            db_session.add(sketch)
            db_session.commit()
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
            views=[{
                u'name': view.name,
                u'id': view.id
            } for view in sketch.get_named_views],
            searchtemplates=[{
                u'name': searchtemplate.name,
                u'id': searchtemplate.id
            } for searchtemplate in SearchTemplate.query.all()])
        return self.to_json(sketch, meta=meta)


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
        query_filter = json.dumps(form.filter.data, ensure_ascii=False),
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
            query_filter = searchtemplate.query_filter,
            query_dsl = searchtemplate.query_dsl
            # WTF form returns a tuple for the filter. This is not
            # compatible with SQLAlchemy.
            if isinstance(query_filter, tuple):
                query_filter = query_filter[0]

        # Create a new search template based on this view (only if requested by
        # the user).
        if form.new_searchtemplate.data:
            query_filter_dict = json.loads(query_filter)
            if query_filter_dict.get(u'indices', None):
                query_filter_dict[u'indices'] = u'_all'

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
        if view.name == u'' and view.user != current_user:
            abort(HTTP_STATUS_CODE_FORBIDDEN)

        # Check if view has been deleted
        if view.get_status.status == u'deleted':
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

        if not sketch.has_permission(user=current_user, permission=u'write'):
            abort(HTTP_STATUS_CODE_FORBIDDEN)

        view.set_status(status=u'deleted')
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
                view.query_string = u''

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

        if form.validate_on_submit():
            query_dsl = form.dsl.data
            query_filter = form.filter.data
            sketch_indices = {
                t.searchindex.index_name
                for t in sketch.timelines
            }
            indices = query_filter.get(u'indices', sketch_indices)

            # If _all in indices then execute the query on all indices
            if u'_all' in indices:
                indices = sketch_indices

            # Make sure that the indices in the filter are part of the sketch.
            # This will also remove any deleted timeline from the search result.
            indices = get_validated_indices(indices, sketch_indices)

            # Make sure we have a query string or star filter
            if not (form.query.data, query_filter.get(u'star'),
                    query_filter.get(u'events'), query_dsl):
                abort(HTTP_STATUS_CODE_BAD_REQUEST)

            result = self.datastore.search(
                sketch_id,
                form.query.data,
                query_filter,
                query_dsl,
                indices,
                aggregations=None,
                return_fields=DEFAULT_SOURCE_FIELDS,
                enable_scroll=False)

            # Get labels for each event that matches the sketch.
            # Remove all other labels.
            for event in result[u'hits'][u'hits']:
                event[u'selected'] = False
                event[u'_source'][u'label'] = []
                try:
                    for label in event[u'_source'][u'timesketch_label']:
                        if sketch.id != label[u'sketch_id']:
                            continue
                        event[u'_source'][u'label'].append(label[u'name'])
                    del event[u'_source'][u'timesketch_label']
                except KeyError:
                    pass

            # Update or create user state view. This is used in the UI to let
            # the user get back to the last state in the explore view.
            view = View.get_or_create(
                user=current_user, sketch=sketch, name=u'')
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
                u'es_time': result[u'took'],
                u'es_total_count': result[u'hits'][u'total'],
                u'timeline_colors': tl_colors,
                u'timeline_names': tl_names,
            }
            schema = {u'meta': meta, u'objects': result[u'hits'][u'hits']}
            return jsonify(schema)
        return abort(HTTP_STATUS_CODE_BAD_REQUEST)


class AggregationResource(ResourceMixin, Resource):
    """Resource to query for aggregated results."""

    @login_required
    def post(self, sketch_id):
        """Handles POST request to the resource.
        Handler for /api/v1/sketches/:sketch_id/aggregation/

        Args:
            sketch_id: Integer primary key for a sketch database model

        Returns:
            JSON with aggregation results
        """
        sketch = Sketch.query.get_with_acl(sketch_id)
        form = AggregationForm.build(request)

        if form.validate_on_submit():
            query_filter = form.filter.data
            query_dsl = form.dsl.data
            sketch_indices = [
                t.searchindex.index_name for t in sketch.timelines
            ]
            indices = query_filter.get(u'indices', sketch_indices)

            # If _all in indices then execute the query on all indices
            if u'_all' in indices:
                indices = sketch_indices

            # Make sure that the indices in the filter are part of the sketch.
            # This will also remove any deleted timeline from the search result.
            indices = get_validated_indices(indices, sketch_indices)

            # Make sure we have a query string or star filter
            if not (form.query.data, query_filter.get(u'star'),
                    query_filter.get(u'events')):
                abort(HTTP_STATUS_CODE_BAD_REQUEST)

            result = []
            if form.aggtype.data == u'heatmap':
                result = heatmap(
                    es_client=self.datastore,
                    sketch_id=sketch_id,
                    query_string=form.query.data,
                    query_filter=query_filter,
                    query_dsl=query_dsl,
                    indices=indices)
            elif form.aggtype.data == u'histogram':
                result = histogram(
                    es_client=self.datastore,
                    sketch_id=sketch_id,
                    query_string=form.query.data,
                    query_filter=query_filter,
                    query_dsl=query_dsl,
                    indices=indices)

            else:
                abort(HTTP_STATUS_CODE_BAD_REQUEST)

            schema = {u'objects': result}
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
            timeline_name = u'sketch specific timeline'
            index_name_seed = u'timesketch' + str(sketch_id)
            event_type = u'user_created_event'

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
            index_name = unicode(md5.new(index_name_seed).hexdigest())

            # Try to create index
            try:
                # Create the index in Elasticsearch (unless it already exists)
                self.datastore.create_index(
                    index_name=index_name,
                    doc_type=event_type)

                # Create the search index in the Timesketch database
                searchindex = SearchIndex.get_or_create(
                    name=timeline_name,
                    description=u'internal timeline for user-created events',
                    user=current_user,
                    index_name=index_name)
                searchindex.grant_permission(
                    permission=u'read', user=current_user)
                searchindex.grant_permission(
                    permission=u'write', user=current_user)
                searchindex.grant_permission(
                    permission=u'delete', user=current_user)
                searchindex.set_status(u'ready')
                db_session.add(searchindex)
                db_session.commit()

                timeline = None
                if sketch and sketch.has_permission(current_user, u'write'):
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
        self.parser.add_argument(u'searchindex_id', type=unicode, required=True)
        self.parser.add_argument(u'event_id', type=unicode, required=True)

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
        searchindex_id = args.get(u'searchindex_id')
        searchindex = SearchIndex.query.filter_by(
            index_name=searchindex_id).first()
        event_id = args.get(u'event_id')
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
                    username = u'System'
                else:
                    username = comment.user.username
                comment_dict = {
                    u'user': {
                        u'username': username,
                    },
                    u'created_at': comment.created_at,
                    u'comment': comment.comment
                }
                comments.append(comment_dict)

        schema = {
            u'meta': {
                u'comments': comments
            },
            u'objects': result[u'_source']
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
                searchindex_id = _event[u'_index']
                searchindex = SearchIndex.query.filter_by(
                    index_name=searchindex_id).first()
                event_id = _event[u'_id']
                event_type = _event[u'_type']

                if searchindex_id not in indices:
                    abort(HTTP_STATUS_CODE_BAD_REQUEST)

                # Get or create an event in the SQL database to have something
                # to attach the annotation to.
                event = Event.get_or_create(
                    sketch=sketch,
                    searchindex=searchindex,
                    document_id=event_id)

                # Add the annotation to the event object.
                if u'comment' in annotation_type:
                    annotation = Event.Comment(
                        comment=form.annotation.data, user=current_user)
                    event.comments.append(annotation)
                    self.datastore.set_label(
                        searchindex_id,
                        event_id,
                        event_type,
                        sketch.id,
                        current_user.id,
                        u'__ts_comment',
                        toggle=False)

                elif u'label' in annotation_type:
                    annotation = Event.Label.get_or_create(
                        label=form.annotation.data, user=current_user)
                    if annotation not in event.labels:
                        event.labels.append(annotation)
                    toggle = False
                    if u'__ts_star' or u'__ts_hidden' in form.annotation.data:
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
        upload_enabled = current_app.config[u'UPLOAD_ENABLED']
        upload_folder = current_app.config[u'UPLOAD_FOLDER']

        form = UploadFileForm()
        if form.validate_on_submit() and upload_enabled:
            sketch_id = form.sketch_id.data or None
            file_storage = form.file.data
            _filename, _extension = os.path.splitext(file_storage.filename)
            file_extension = _extension.lstrip(u'.')
            timeline_name = form.name.data or _filename.rstrip(u'.')

            sketch = None
            if sketch_id:
                sketch = Sketch.query.get_with_acl(sketch_id)

            # We do not need a human readable filename or
            # datastore index name, so we use UUIDs here.
            filename = unicode(uuid.uuid4().hex)
            index_name = unicode(uuid.uuid4().hex)

            file_path = os.path.join(upload_folder, filename)
            file_storage.save(file_path)

            # Create the search index in the Timesketch database
            searchindex = SearchIndex.get_or_create(
                name=timeline_name,
                description=timeline_name,
                user=current_user,
                index_name=index_name)
            searchindex.grant_permission(permission=u'read', user=current_user)
            searchindex.grant_permission(permission=u'write', user=current_user)
            searchindex.grant_permission(
                permission=u'delete', user=current_user)
            searchindex.set_status(u'processing')
            db_session.add(searchindex)
            db_session.commit()

            timeline = None
            if sketch and sketch.has_permission(current_user, u'write'):
                timeline = Timeline(
                    name=searchindex.name,
                    description=searchindex.description,
                    sketch=sketch,
                    user=current_user,
                    searchindex=searchindex)
                timeline.set_status(u'processing')
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
            else:
                return self.to_json(
                    searchindex, status_code=HTTP_STATUS_CODE_CREATED)

        else:
            raise ApiHTTPError(
                message=form.errors[u'file'][0],
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
            u'CELERY_TASK_TIMEOUT', 7200)
        indices = SearchIndex.query.filter(
            SearchIndex.status.any(status=u'processing')).filter_by(
                user=current_user).all()
        schema = {u'objects': [], u'meta': {}}
        for search_index in indices:
            # pylint: disable=too-many-function-args
            celery_task = self.celery.AsyncResult(search_index.index_name)
            task = dict(
                task_id=celery_task.task_id,
                state=celery_task.state,
                successful=celery_task.successful(),
                name=search_index.name,
                result=False)
            if celery_task.state == u'SUCCESS':
                task[u'result'] = celery_task.result
            elif celery_task.state == u'PENDING':
                time_pending = (
                    search_index.updated_at - datetime.datetime.now())
                if time_pending.seconds > TIMEOUT_THRESHOLD_SECONDS:
                    search_index.set_status(u'timeout')
            schema[u'objects'].append(task)
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
            sketch = Sketch.query.get_with_acl(sketch_id)
            story = Story(
                title=u'', content=u'', sketch=sketch, user=current_user)
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
            meta[u'is_editable'] = True

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
            story_id: Integer primary key for a story database model

        Returns:
            A story in JSON (instance of flask.wrappers.Response)
        """
        form = ExploreForm.build(request)
        if form.validate_on_submit():
            sketch = Sketch.query.get_with_acl(sketch_id)
            schema = {u'objects': [], u'meta': {}}
            query_string = form.query.data
            query_filter = form.filter.data
            query_dsl = form.dsl.data
            query = self.datastore.build_query(sketch.id, query_string,
                                               query_filter, query_dsl)
            schema[u'objects'].append(query)
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
    @login_required
    def post(self):
        """Handles POST request to the resource.

        Returns:
            A view in JSON (instance of flask.wrappers.Response)

        Raises:
            ApiHTTPError
        """
        upload_enabled = current_app.config[u'UPLOAD_ENABLED']
        form = CreateTimelineForm()
        if form.validate_on_submit() and upload_enabled:
            sketch_id = form.sketch_id.data
            timeline_name = form.name.data

            sketch = None
            if sketch_id:
                sketch = Sketch.query.get_with_acl(sketch_id)

            # We do not need a human readable filename or
            # datastore index name, so we use UUIDs here.
            index_name = unicode(uuid.uuid4().hex)

            # Create the search index in the Timesketch database
            searchindex = SearchIndex.get_or_create(
                name=timeline_name,
                description=timeline_name,
                user=current_user,
                index_name=index_name)
            searchindex.grant_permission(permission=u'read', user=current_user)
            searchindex.grant_permission(permission=u'write', user=current_user)
            searchindex.grant_permission(
                permission=u'delete', user=current_user)
            searchindex.set_status(u'processing')
            db_session.add(searchindex)
            db_session.commit()

            timeline = None
            if sketch and sketch.has_permission(current_user, u'write'):
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
            else:
                return self.to_json(
                    searchindex, status_code=HTTP_STATUS_CODE_CREATED)

        else:
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
        metadata = {u'created': True}

        searchindex_id = form.timeline.data
        searchindex = SearchIndex.query.get_with_acl(searchindex_id)
        timeline_id = [
            t.searchindex.id for t in sketch.timelines
            if t.searchindex.id == searchindex_id
        ]

        if form.validate_on_submit():
            if not sketch.has_permission(current_user, u'write'):
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
                metadata[u'created'] = False
                return_code = HTTP_STATUS_CODE_OK
                timeline = Timeline.query.get(timeline_id)

            # If enabled, run sketch analyzers when timeline is added.
            # Import here to avoid circular imports.
            if current_app.config.get(u'ENABLE_SKETCH_ANALYZERS'):
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

        if not sketch.has_permission(user=current_user, permission=u'read'):
            abort(HTTP_STATUS_CODE_FORBIDDEN)

        return self.to_json(timeline)

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

        if not sketch.has_permission(user=current_user, permission=u'write'):
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
            Graph in JSON (instance of flask.wrappers.Response)
        """
        # Check access to the sketch
        Sketch.query.get_with_acl(sketch_id)

        form = GraphExploreForm.build(request)
        if form.validate_on_submit():
            query = form.query.data
            output_format = form.output_format.data

            try:
                transpiled = transpile_query(query, sketch_id)
            except (pycypher.CypherParseError, InvalidQuery) as e:
                return bad_request(e.message)

            intermediate_result = self.graph_datastore.query(
                transpiled, output_format='neo4j', return_rows=True)
            nodes = []
            edges = []
            timestamps_by_edge_id = {}
            if intermediate_result['rows'] is None:
                intermediate_result['rows'] = []
            for node_ids, edge_ids, timestamps_s in intermediate_result['rows']:
                nodes.extend(node_ids)
                for edge_id, timestamps in zip(edge_ids, timestamps_s):
                    if edge_id not in timestamps_by_edge_id:
                        timestamps_by_edge_id[edge_id] = []
                    if timestamps is None:
                        timestamps = []
                    timestamps_by_edge_id[edge_id].extend(timestamps)
            nodes = list(set(nodes))
            edges = list(timestamps_by_edge_id.keys())
            for edge_id in timestamps_by_edge_id:
                timestamps_by_edge_id[edge_id] = list(set(
                    timestamps_by_edge_id[edge_id]
                ))
            final_query = '''
                UNWIND {edge_ids} AS edge_id MATCH ()-[e]->()
                WHERE id(e) = edge_id AND e.sketch_id = {sketch_id}
                RETURN e, null AS n
                UNION ALL
                UNWIND {node_ids} AS node_id MATCH (n)
                WHERE id(n) = node_id AND n.sketch_id = {sketch_id}
                RETURN null AS e, n
            '''

            result = self.graph_datastore.query(final_query, params={
                'sketch_id': sketch_id, 'edge_ids': edges, 'node_ids': nodes,
            }, output_format=output_format)
            for edge in result['graph']['edges']:
                edge_data = edge['data']
                edge_data['timestamps'] = timestamps_by_edge_id[
                    int(edge_data['id'].replace('edge', ''))
                ]
                edge_data['count'] = str(len(edge_data['timestamps']))
                if edge_data.get('timestamps_incomplete'):
                    edge_data['count'] += '+'
                if edge_data['count'] == '0+':
                    edge_data['count'] = '???'

            schema = {
                u'meta': {
                    u'schema': neo4j_schema
                },
                u'objects': [{
                    u'graph': result[u'graph'],
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
            metadata = {u'created': True}

            if searchindex:
                metadata[u'created'] = False
                status_code = HTTP_STATUS_CODE_OK
            else:
                searchindex = SearchIndex.get_or_create(
                    name=searchindex_name,
                    description=searchindex_name,
                    user=current_user,
                    index_name=es_index_name)
                searchindex.grant_permission(
                    permission=u'read', user=current_user)

                if public:
                    searchindex.grant_permission(permission=u'read', user=None)

                # Create the index in Elasticsearch
                self.datastore.create_index(
                    index_name=es_index_name, doc_type=u'generic_event')

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
