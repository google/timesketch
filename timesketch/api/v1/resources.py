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
import os
import uuid

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
from timesketch.lib.errors import ApiHTTPError
from timesketch.lib.forms import SaveViewForm
from timesketch.lib.forms import EventAnnotationForm
from timesketch.lib.forms import ExploreForm
from timesketch.lib.forms import UploadFileForm
from timesketch.models import db_session
from timesketch.models.sketch import Event
from timesketch.models.sketch import SearchIndex
from timesketch.models.sketch import Sketch
from timesketch.models.sketch import View


class ResourceMixin(object):
    """Mixin for API resources."""
    # Schemas for database model resources
    searchindex_fields = {
        u'name': fields.String,
        u'index_name': fields.String,
        u'deleted': fields.Boolean,
        u'created_at': fields.DateTime,
        u'updated_at': fields.DateTime
    }

    timeline_fields = {
        u'name': fields.String,
        u'description': fields.String,
        u'color': fields.String,
        u'searchindex': fields.Nested(searchindex_fields),
        u'deleted': fields.Boolean,
        u'created_at': fields.DateTime,
        u'updated_at': fields.DateTime
    }

    view_fields = {
        u'id': fields.Integer,
        u'name': fields.String,
        u'query_string': fields.String,
        u'query_filter': fields.String,
        u'created_at': fields.DateTime,
        u'updated_at': fields.DateTime
    }

    user_fields = {
        u'username': fields.String
    }

    sketch_fields = {
        u'id': fields.Integer,
        u'name': fields.String,
        u'description': fields.String,
        u'user': fields.Nested(user_fields),
        u'timelines': fields.Nested(timeline_fields),
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
        u'view': view_fields,
        u'user': user_fields,
        u'sketch': sketch_fields,
        u'event_comment': comment_fields,
        u'event_label': label_fields
    }

    @property
    def datastore(self):
        """Property to get an instance of the datastore backend.

        Returns:
            Instance of timesketch.lib.datastores.elastic.ElasticSearchDatastore
        """
        return ElasticSearchDataStore(
            host=current_app.config[u'ELASTIC_HOST'],
            port=current_app.config[u'ELASTIC_PORT'])

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
            u'meta': meta,
            u'objects': [marshal(model, model_fields)]
        }
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
        sketches = Sketch.all_with_acl()
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
            views=[
                {
                    u'name': view.name,
                    u'id': view.id
                } for view in sketch.get_named_views.all()
            ])
        return self.to_json(sketch, meta=meta)


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
                query_filter=json.dumps(form.filter.data, ensure_ascii=False))
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
        if view.name == u'' and view.user != current_user:
            abort(HTTP_STATUS_CODE_FORBIDDEN)
        return self.to_json(view)


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
            query_filter = form.filter.data
            sketch_indices = [
                t.searchindex.index_name for t in sketch.timelines]
            indices = query_filter.get(u'indices', sketch_indices)

            # Make sure that the indices in the filter are part of the sketch
            if set(indices) - set(sketch_indices):
                abort(HTTP_STATUS_CODE_BAD_REQUEST)

            # Make sure we have a query string or star filter
            if not form.query.data and not query_filter.get(u'star'):
                abort(HTTP_STATUS_CODE_BAD_REQUEST)

            aggregations = {
                u'data_type': {
                    u'terms': {
                        u'field': u'data_type',
                        u'size': 0}
                }
            }
            result = self.datastore.search(
                sketch_id, form.query.data, query_filter, indices,
                aggregations=aggregations, return_results=True)

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
            view.query_filter = json.dumps(query_filter)
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
                u'histogram': result[u'aggregations'][u'data_type'][u'buckets']
            }
            schema = {
                u'meta': meta,
                u'objects': result[u'hits'][u'hits']
            }
            return jsonify(schema)
        return abort(HTTP_STATUS_CODE_BAD_REQUEST)


class AggregationResource(ResourceMixin, Resource):
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
            query_filter = form.filter.data
            sketch_indices = [
                t.searchindex.index_name for t in sketch.timelines]
            indices = query_filter.get(u'indices', sketch_indices)

            # Make sure that the indices in the filter are part of the sketch
            if set(indices) - set(sketch_indices):
                abort(HTTP_STATUS_CODE_BAD_REQUEST)

            # Make sure we have a query string or star filter
            if not form.query.data and not query_filter.get(u'star'):
                abort(HTTP_STATUS_CODE_BAD_REQUEST)

            result = self.datastore.search(
                sketch_id, form.query.data, query_filter, indices,
                aggregations=aggregations, return_results=False)

            meta = {
                u'es_time': result[u'took'],
                u'es_total_count': result[u'hits'][u'total'],
                u'timeline_colors': tl_colors,
                u'timeline_names': tl_names,
                u'histogram': result[u'aggregations'][u'data_type'][u'buckets']
            }
            schema = {
                u'meta': meta,
                u'objects': result[u'hits'][u'hits']
            }
            return jsonify(schema)
        return abort(HTTP_STATUS_CODE_BAD_REQUEST)


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
                comment_dict = {
                    u'user': {
                        u'username': comment.user.username,
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
                    sketch=sketch, searchindex=searchindex,
                    document_id=event_id)

                # Add the annotation to the event object.
                if u'comment' in annotation_type:
                    annotation = Event.Comment(
                        comment=form.annotation.data, user=current_user)
                    event.comments.append(annotation)
                    self.datastore.set_label(
                        searchindex_id, event_id, event_type, sketch.id,
                        current_user.id, u'__ts_comment', toggle=False)

                elif u'label' in annotation_type:
                    annotation = Event.Label.get_or_create(
                        label=form.annotation.data, user=current_user)
                    if annotation not in event.labels:
                        event.labels.append(annotation)
                    toggle = False
                    if u'__ts_star' in form.annotation.data:
                        toggle = True
                    self.datastore.set_label(
                        searchindex_id, event_id, event_type, sketch.id,
                        current_user.id, form.annotation.data, toggle=toggle)
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
        UPLOAD_ENABLED = current_app.config[u'UPLOAD_ENABLED']
        UPLOAD_FOLDER = current_app.config[u'UPLOAD_FOLDER']

        form = UploadFileForm()
        if form.validate_on_submit() and UPLOAD_ENABLED:
            from timesketch.lib.tasks import run_plaso
            file_storage = form.file.data
            timeline_name = form.name.data
            # We do not need a human readable filename or
            # datastore index name, so we use UUIDs here.
            filename = unicode(uuid.uuid4().hex)
            index_name = unicode(uuid.uuid4().hex)

            file_path = os.path.join(UPLOAD_FOLDER, filename)
            file_storage.save(file_path)

            search_index = SearchIndex.get_or_create(
                name=timeline_name, description=timeline_name, user=None,
                index_name=index_name)
            search_index.grant_permission(None, u'read')
            search_index.set_status(u'processing')
            db_session.add(search_index)
            db_session.commit()

            run_plaso.apply_async(
                (file_path, timeline_name, index_name), task_id=index_name)

            return self.to_json(
                search_index, status_code=HTTP_STATUS_CODE_CREATED)
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
        indices = SearchIndex.query.filter(SearchIndex.status.any(
            status=u'processing')).all()
        schema = {u'objects': [], u'meta': {}}
        for search_index in indices:
            # pylint: disable=too-many-function-args
            celery_task = self.celery.AsyncResult(search_index.index_name)
            task = dict(
                task_id=celery_task.task_id, state=celery_task.state,
                successful=celery_task.successful(), name=search_index.name,
                result=False)
            if celery_task.state == u'SUCCESS':
                task[u'result'] = celery_task.result
            schema[u'objects'].append(task)
        return jsonify(schema)
