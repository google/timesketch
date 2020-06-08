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
"""Event resources for version 1 of the Timesketch API."""

import codecs
import hashlib
import json
import logging
import time
import six

import dateutil

from flask import jsonify
from flask import request
from flask import abort
from flask_restful import Resource
from flask_restful import reqparse
from flask_login import login_required
from flask_login import current_user

from timesketch.api.v1 import resources
from timesketch.lib import forms
from timesketch.lib.definitions import HTTP_STATUS_CODE_OK
from timesketch.lib.definitions import HTTP_STATUS_CODE_CREATED
from timesketch.lib.definitions import HTTP_STATUS_CODE_BAD_REQUEST
from timesketch.lib.definitions import HTTP_STATUS_CODE_FORBIDDEN
from timesketch.lib.definitions import HTTP_STATUS_CODE_NOT_FOUND
from timesketch.models import db_session
from timesketch.models.sketch import Event
from timesketch.models.sketch import SearchIndex
from timesketch.models.sketch import Sketch
from timesketch.models.sketch import Timeline


logger = logging.getLogger('api_resources')


class EventCreateResource(resources.ResourceMixin, Resource):
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
        form = forms.EventCreateForm.build(request)
        if not form.validate_on_submit():
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                'Failed to add event, form data not validated')

        sketch = Sketch.query.get_with_acl(sketch_id)
        if not sketch:
            abort(
                HTTP_STATUS_CODE_NOT_FOUND, 'No sketch found with this ID.')
        if not sketch.has_permission(current_user, 'write'):
            abort(HTTP_STATUS_CODE_FORBIDDEN,
                  'User does not have write access controls on sketch.')

        timeline_name = 'sketch specific timeline'
        index_name_seed = 'timesketch' + str(sketch_id)
        event_type = 'user_created_event'

        # derive datetime from timestamp:
        parsed_datetime = dateutil.parser.parse(form.timestamp.data)
        timestamp = int(
            time.mktime(parsed_datetime.utctimetuple())) * 1000000
        timestamp += parsed_datetime.microsecond

        event = {
            'datetime': form.timestamp.data,
            'timestamp': timestamp,
            'timestamp_desc': form.timestamp_desc.data,
            'message': form.message.data,
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

        # TODO: Can this be narrowed down, both in terms of the scope it
        # applies to, as well as not to catch a generic exception.
        except Exception as e:  # pylint: disable=broad-except
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                'Failed to add event ({0!s})'.format(e))


class EventResource(resources.ResourceMixin, Resource):
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
        if not sketch:
            abort(
                HTTP_STATUS_CODE_NOT_FOUND, 'No sketch found with this ID.')
        if not sketch.has_permission(current_user, 'read'):
            abort(HTTP_STATUS_CODE_FORBIDDEN,
                  'User does not have read access controls on sketch.')

        searchindex_id = args.get('searchindex_id')
        searchindex = SearchIndex.query.filter_by(
            index_name=searchindex_id).first()
        event_id = args.get('event_id')
        indices = [
            t.searchindex.index_name for t in sketch.timelines
            if t.get_status.status.lower() == 'ready']

        # Check if the requested searchindex is part of the sketch
        if searchindex_id not in indices:
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                'Search index ID ({0!s}) does not belong to the list '
                'of indices'.format(searchindex_id))

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


class EventTaggingResource(resources.ResourceMixin, Resource):
    """Resource to fetch and set tags to an event."""

    @login_required
    def post(self, sketch_id):
        """Handles POST request to the resource.

        Args:
            sketch_id: Integer primary key for a sketch database model

        Returns:
            An annotation in JSON (instance of flask.wrappers.Response)
        """
        sketch = Sketch.query.get_with_acl(sketch_id)
        if not sketch:
            msg = 'No sketch found with this ID.'
            abort(HTTP_STATUS_CODE_NOT_FOUND, msg)

        if not sketch.has_permission(current_user, 'write'):
            abort(
                HTTP_STATUS_CODE_FORBIDDEN, (
                    'User does not have sufficient access rights to '
                    'modify a sketch.'))

        form = request.json
        if not form:
            form = request.data

        tag_dict = {
            'event_count': 0,
            'tag_count': 0,
        }
        datastore = self.datastore

        try:
            tags_to_add = json.loads(form.get('tag_string', ''))
        except json.JSONDecodeError as e:
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                'Unable to read the tags, with error: {0!s}'.format(e))
        if not isinstance(tags_to_add, list):
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST, 'Tags need to be a list')

        if not all([isinstance(x, str) for x in tags_to_add]):
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                'Tags need to be a list of strings')

        events = form.get('events', [])
        for _event in events:
            query = {
                'query': {
                    'bool': {
                        'filter': {
                            'term': {
                                '_id': _event['_id'],
                            }
                        }
                    }
                }
            }
            results = datastore.client.search(
                index=[_event['_index']], body=query)

            ds_events = results['hits']['hits']
            if len(ds_events) != 1:
                logger.error(
                    'Unable to tag event: {0:s}, couldn\'t find the '
                    'event.'.format(_event['_id']))
                continue

            source = ds_events[0].get('_source', {})
            existing_tags = source.get('tag', [])
            new_tags = list(set().union(existing_tags, tags_to_add))

            if set(existing_tags) == set(new_tags):
                continue

            datastore.import_event(
                index_name=_event['_index'], event_type=_event['_type'],
                event_id=_event['_id'], event={'tag': new_tags})

            tag_dict['event_count'] += 1
            tag_dict['tag_count'] += len(new_tags)

        datastore.flush_queued_events()
        schema = {
            'meta': tag_dict,
            'objects': []}
        response = jsonify(schema)
        response.status_code = HTTP_STATUS_CODE_OK
        return response


class EventAnnotationResource(resources.ResourceMixin, Resource):
    """Resource to create an annotation for an event."""

    @login_required
    def post(self, sketch_id):
        """Handles POST request to the resource.

        Args:
            sketch_id: Integer primary key for a sketch database model

        Returns:
            An annotation in JSON (instance of flask.wrappers.Response)
        """
        form = forms.EventAnnotationForm.build(request)
        if not form.validate_on_submit():
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST, 'Unable to validate form data.')

        annotations = []
        sketch = Sketch.query.get_with_acl(sketch_id)
        if not sketch:
            abort(
                HTTP_STATUS_CODE_NOT_FOUND, 'No sketch found with this ID.')
        if not sketch.has_permission(current_user, 'write'):
            abort(HTTP_STATUS_CODE_FORBIDDEN,
                  'User does not have write access controls on sketch.')

        indices = [
            t.searchindex.index_name for t in sketch.timelines
            if t.get_status.status.lower() == 'ready']
        annotation_type = form.annotation_type.data
        events = form.events.raw_data

        for _event in events:
            searchindex_id = _event['_index']
            searchindex = SearchIndex.query.filter_by(
                index_name=searchindex_id).first()
            event_id = _event['_id']
            event_type = _event['_type']

            if searchindex_id not in indices:
                abort(
                    HTTP_STATUS_CODE_BAD_REQUEST,
                    'Search index ID ({0!s}) does not belong to the list '
                    'of indices'.format(searchindex_id))

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
                abort(
                    HTTP_STATUS_CODE_BAD_REQUEST,
                    'Annotation type needs to be either label or comment, '
                    'not {0!s}'.format(annotation_type))

            annotations.append(annotation)
            # Save the event to the database
            db_session.add(event)
            db_session.commit()

        return self.to_json(
            annotations, status_code=HTTP_STATUS_CODE_CREATED)


class CountEventsResource(resources.ResourceMixin, Resource):
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
        if not sketch:
            abort(
                HTTP_STATUS_CODE_NOT_FOUND, 'No sketch found with this ID.')
        if not sketch.has_permission(current_user, 'read'):
            abort(HTTP_STATUS_CODE_FORBIDDEN,
                  'User does not have read access controls on sketch.')
        indices = [
            t.searchindex.index_name for t in sketch.active_timelines
            if t.get_status.status != 'archived'
        ]
        count = self.datastore.count(indices)
        meta = dict(count=count)
        schema = dict(meta=meta, objects=[])
        return jsonify(schema)
