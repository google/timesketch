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
import math
import time
import six

import dateutil
from elasticsearch.exceptions import RequestError
import numpy as np
import pandas as pd

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


def _tag_event(row, tag_dict, tags_to_add, datastore, flush_interval):
    """Tag each event from a dataframe with tags.

    Args:
        row (np.Series): a single row of data with existing tags and
            information about the event in order to be able to add
            tags to it.
        tag_dict (dict): a dict that contains information to be returned
            by the API call to the user.
        tags_to_add (list[str]): a list of strings of tags to add to each
            event.
        datastore (elastic.ElasticsearchDataStore): the datastore object.
        flush_interval (int): the number of events to import before a bulk
            update is done with the datastore.
    """
    tag_dict['events_processed_by_api'] += 1
    existing_tags = set()

    if 'tag' in row:
        tag = row['tag']
        if isinstance(tag, (list, tuple)):
            existing_tags = set(tag)

        new_tags = list(set().union(existing_tags, set(tags_to_add)))
    else:
        new_tags = tags_to_add

    if set(existing_tags) == set(new_tags):
        return

    datastore.import_event(
        index_name=row['_index'], event_type=row['_type'],
        event_id=row['_id'], event={'tag': new_tags},
        flush_interval=flush_interval)

    tag_dict['tags_applied'] += len(new_tags)
    tag_dict['number_of_events_with_added_tags'] += 1


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

    # The number of events to bulk together for each query.
    EVENT_CHUNK_SIZE = 1000

    # The maximum number of events to tag in a single request.
    MAX_EVENTS_TO_TAG = 100000

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
            'events_processed_by_api': 0,
            'number_of_events_with_added_tags': 0,
            'tags_applied': 0,
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
        event_df = pd.DataFrame(events)
        tag_df = pd.DataFrame()

        event_size = event_df.shape[0]
        if event_size > self.MAX_EVENTS_TO_TAG:
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                'Cannot tag more than {0:d} events in a single '
                'request'.format(self.MAX_EVENTS_TO_TAG))

        tag_dict['number_of_events_passed_to_api'] = event_size

        verbose = form.get('verbose', False)
        if verbose:
            tag_dict['number_of_indices'] = len(event_df['_index'].unique())
            time_tag_gathering_start = time.time()

        for _index in event_df['_index'].unique():
            query_filter = {
                'time_start': None,
                'time_end': None,
                'indices': [_index],
            }

            index_slice = event_df[event_df['_index'] == _index]
            index_size = index_slice.shape[0]
            if verbose:
                tag_dict.setdefault('index_count', {})
                tag_dict['index_count'][_index] = index_size

            if index_size <= self.EVENT_CHUNK_SIZE:
                chunks = 1
            else:
                chunks = math.ceil(index_size / self.EVENT_CHUNK_SIZE)

            tags = []
            for index_chunk in np.array_split(
                    index_slice['_id'].unique(), chunks):
                should_list = [{'match': {'_id': x}} for x in index_chunk]
                query = {
                    'query': {
                        'bool': {
                            'should': should_list
                        }
                    }
                }
                try:
                    for result in datastore.search_stream(
                            sketch_id=sketch.id, query_dsl=json.dumps(query),
                            indices=[_index], return_fields=['tag'],
                            query_filter=query_filter, enable_scroll=False):
                        tag = result.get('_source', {}).get('tag', [])
                        if not tag:
                            continue
                        tags.append({'_id': result.get('_id'), 'tag': tag})
                except RequestError as e:
                    logger.error('Unable to query for events, {0!s}'.format(e))
                    abort(
                        HTTP_STATUS_CODE_BAD_REQUEST,
                        'Unable to query events, {0!s}'.format(e))

            if not tags:
                continue
            tag_df = pd.concat([tag_df, pd.DataFrame(tags)])

        if tag_df.shape[0]:
            event_df = event_df.merge(tag_df, on='_id', how='left')

        if verbose:
            tag_dict[
                'time_to_gather_tags'] = time.time() - time_tag_gathering_start
            tag_dict['number_of_events'] = len(events)
            if 'tag' in event_df:
                current_tag_events = event_df[~event_df['tag'].isna()].shape[0]
                tag_dict['number_of_events_with_tags'] = current_tag_events
            else:
                tag_dict['number_of_events_with_tags'] = 0

            tag_dict['tags_to_add'] = tags_to_add
            time_tag_start = time.time()

        if event_size > datastore.DEFAULT_FLUSH_INTERVAL:
            flush_interval = 10000
        else:
            flush_interval = datastore.DEFAULT_FLUSH_INTERVAL
        _ = event_df.apply(
            _tag_event, axis=1, tag_dict=tag_dict, tags_to_add=tags_to_add,
            datastore=datastore, flush_interval=flush_interval)
        datastore.flush_queued_events()

        if verbose:
            tag_dict['time_to_tag'] = time.time() - time_tag_start

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
