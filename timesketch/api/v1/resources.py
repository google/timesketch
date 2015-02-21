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

import json

from flask import abort
from flask import jsonify
from flask import request
from flask_login import current_user
from flask_login import current_app
from flask_login import login_required
from flask_restful import fields
from flask_restful import marshal
from flask_restful import reqparse
from flask_restful import Resource

from timesketch.lib.definitions import HTTP_STATUS_CODE_OK
from timesketch.lib.definitions import HTTP_STATUS_CODE_CREATED
from timesketch.lib.definitions import HTTP_STATUS_CODE_BAD_REQUEST
from timesketch.lib.definitions import HTTP_STATUS_CODE_FORBIDDEN
from timesketch.lib.definitions import HTTP_STATUS_CODE_NOT_FOUND
from timesketch.lib.datastores.elastic import ElasticSearchDataStore
from timesketch.lib.forms import SaveViewForm
from timesketch.lib.forms import EventAnnotationForm
from timesketch.models import db_session
from timesketch.models.sketch import Event
from timesketch.models.sketch import SearchIndex
from timesketch.models.sketch import Sketch
from timesketch.models.sketch import View


class ResourceMixin(object):
    """Mixin for API resources."""
    # Schemas for database model resources
    searchindex_fields = {
        'name': fields.String,
        'index_name': fields.String,
        'deleted': fields.Boolean,
        'created_at': fields.DateTime,
        'updated_at': fields.DateTime
    }

    timeline_fields = {
        'name': fields.String,
        'description': fields.String,
        'color': fields.String,
        'searchindex': fields.Nested(searchindex_fields),
        'deleted': fields.Boolean,
        'created_at': fields.DateTime,
        'updated_at': fields.DateTime
    }

    view_fields = {
        'id': fields.Integer,
        'name': fields.String,
        'query_string': fields.String,
        'query_filter': fields.String,
        'created_at': fields.DateTime,
        'updated_at': fields.DateTime
    }

    user_fields = {
        'username': fields.String
    }

    sketch_fields = {
        'name': fields.String,
        'description': fields.String,
        'user': fields.Nested(user_fields),
        'timelines': fields.Nested(timeline_fields),
        'views': fields.Nested(view_fields),
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
        'timeline': timeline_fields,
        'view': view_fields,
        'user': user_fields,
        'sketch': sketch_fields,
        'event_comment': comment_fields,
        'event_label': label_fields
    }

    @property
    def datastore(self):
        """Property to get an instance of the datastore backend.

        Returns:
            Instance of timesketch.lib.datastores.elastic.ElasticSearchDatastore
        """
        return ElasticSearchDataStore(
            host=current_app.config['ELASTIC_HOST'],
            port=current_app.config['ELASTIC_PORT'])

    def to_json(
            self, model, model_fields=None, meta=None,
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
        if not model_fields:
            try:
                model_fields = self.fields_registry[model.__tablename__]
            except AttributeError:
                model_fields = self.fields_registry[model[0].__tablename__]

        schema = {
            'meta': meta,
            'objects': [marshal(model, model_fields)]
        }
        response = jsonify(schema)
        response.status_code = status_code
        return response


class SketchListResource(ResourceMixin, Resource):
    """Resource for listing sketches."""
    def __init__(self):
        super(SketchListResource, self).__init__()
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('name', type=str, required=True)
        self.parser.add_argument('description', type=str, required=False)

    @login_required
    def get(self):
        """Handles GET request to the resource.

        Returns:
            List of sketches (instance of flask.wrappers.Response)
        """
        # TODO: Handle offset parameter
        sketches = Sketch.all_with_acl()
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


class SketchResource(ResourceMixin, Resource):
    """Resource to get a sketch."""
    @login_required
    def get(self, sketch_id):
        """Handles GET request to the resource.

        Returns:
            A sketch in JSON (instance of flask.wrappers.Response)
        """
        sketch = Sketch.query.get_with_acl(sketch_id)
        return self.to_json(sketch)


class ViewListResource(ResourceMixin, Resource):
    """Resource to create a View."""
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
            view = View(
                name=form.name.data, sketch=sketch, user=current_user,
                query_string=form.query.data,
                query_filter=json.dumps(form.filter.data))
            db_session.add(view)
            db_session.commit()
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
        return self.to_json(view)


class ExploreResource(ResourceMixin, Resource):
    """Resource to search the datastore based on a query and a filter.

    HTTP Args:
        q: Query string
        filter: Query filter (JSON as string)
    """

    def __init__(self):
        super(ExploreResource, self).__init__()
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('q', type=str, required=False)
        self.parser.add_argument('filter', type=str, required=False)

    @login_required
    def get(self, sketch_id):
        """Handles GET request to the resource.
        Handler for /api/v1/sketches/:sketch_id/explore/

        Args:
            sketch_id: Integer primary key for a sketch database model

        Returns:
            JSON with list of matched events
        """
        args = self.parser.parse_args()
        sketch = Sketch.query.get_with_acl(sketch_id)
        query_filter = json.loads(args.get('filter'))
        sketch_indices = [t.searchindex.index_name for t in sketch.timelines]
        indices = query_filter.get('indices', sketch_indices)

        # Make sure that the indices in the filter is part of the sketch
        if set(indices) - set(sketch_indices):
            abort(HTTP_STATUS_CODE_BAD_REQUEST)

        # Make sure we have a query string or star filter
        if not args['q'] and not query_filter['star']:
            abort(HTTP_STATUS_CODE_BAD_REQUEST)

        result = self.datastore.search(
            sketch_id, args['q'], query_filter, indices)

        # Get labels for each event that matches the sketch.
        # Remove all other labels.
        for event in result['hits']['hits']:
            event['_source']['label'] = []
            try:
                for label in event['_source']['timesketch_label']:
                    if sketch.id != label['sketch_id']:
                        continue
                    event['_source']['label'].append(label['name'])
                del event['_source']['timesketch_label']
            except KeyError:
                pass

        # Update or create user state view. This is used in the UI to let the
        # user get back to the last state in the explore view.
        view = View.get_or_create(
            user=current_user, sketch=sketch, name='', query_string='',
            query_filter='')
        view.query_string = args['q']
        view.query_filter = json.dumps(query_filter)
        db_session.add(view)
        db_session.commit()

        # Add metadata for the query result. This is used by the UI to render
        # the event correctly and to display timing and hit count information.
        tl_colors = {}
        tl_names = {}
        for timeline in sketch.timelines:
            tl_colors[timeline.searchindex.index_name] = timeline.color
            tl_names[timeline.searchindex.index_name] = timeline.name
        meta = {
            'es_time': result['took'],
            'es_total_count': result['hits']['total'],
            'timeline_colors': tl_colors,
            'timeline_names': tl_names
        }
        schema = {
            'meta': meta,
            'objects': result['hits']['hits']
        }
        return jsonify(schema)


class EventResource(ResourceMixin, Resource):
    """Resource to get a single event from the datastore.

    HTTP Args:
        searchindex_id: The datastore searchindex id as string
        event_id: The datastore event id as string
    """
    def __init__(self):
        super(EventResource, self).__init__()
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('searchindex_id', type=str, required=True)
        self.parser.add_argument('event_id', type=str, required=True)

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
        searchindex = SearchIndex.query.get(searchindex_id)
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
                comment_dict = {
                    'user': {
                        'username': comment.user.username,
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
            sketch = Sketch.query.get_with_acl(sketch_id)
            indices = [t.searchindex.index_name for t in sketch.timelines]
            annotation_type = form.annotation_type.data
            searchindex_id = form.searchindex_id.data
            searchindex = SearchIndex.query.get(searchindex_id)
            event_id = form.event_id.data

            if searchindex_id not in indices:
                abort(HTTP_STATUS_CODE_BAD_REQUEST)

            def _set_label(label, toggle=False):
                """Set label on the event in the datastore."""
                self.datastore.set_label(
                    searchindex_id, event_id, sketch.id, current_user.id, label,
                    toggle=toggle)

            # Get or create an event in the SQL database to have something to
            # attach the annotation to.
            event = Event.get_or_create(
                sketch=sketch, searchindex=searchindex,
                document_id=event_id)

            # Add the annotation to the event object.
            if 'comment' in annotation_type:
                annotation = Event.Comment(
                    comment=form.annotation.data, user=current_user)
                event.comments.append(annotation)
                _set_label('__ts_comment')
            elif 'label' in annotation_type:
                annotation = Event.Label.get_or_create(
                    label=form.annotation.data, user=current_user)
                if annotation not in event.labels:
                    event.labels.append(annotation)
                toggle = False
                if '__ts_star' in form.annotation.data:
                    toggle = True
                _set_label(form.annotation.data, toggle)
            else:
                abort(HTTP_STATUS_CODE_BAD_REQUEST)

            # Save the event to the database
            db_session.add(event)
            db_session.commit()

            return self.to_json(
                annotation, status_code=HTTP_STATUS_CODE_CREATED)
        return abort(HTTP_STATUS_CODE_BAD_REQUEST)
