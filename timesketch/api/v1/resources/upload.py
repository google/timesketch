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
"""Upload resources for version 1 of the Timesketch API."""

import codecs
import os
import uuid

from flask import jsonify
from flask import request
from flask import abort
from flask import current_app
from flask_restful import Resource
from flask_login import login_required
from flask_login import current_user

from timesketch.api.v1 import resources
from timesketch.api.v1 import utils
from timesketch.lib.definitions import HTTP_STATUS_CODE_CREATED
from timesketch.lib.definitions import HTTP_STATUS_CODE_BAD_REQUEST
from timesketch.lib.definitions import HTTP_STATUS_CODE_FORBIDDEN
from timesketch.lib.definitions import HTTP_STATUS_CODE_NOT_FOUND
from timesketch.models import db_session
from timesketch.models.sketch import SearchIndex
from timesketch.models.sketch import Sketch
from timesketch.models.sketch import Timeline


class UploadFileResource(resources.ResourceMixin, Resource):
    """Resource that processes uploaded files."""

    def _get_index(
            self, name, description, sketch, index_name='',
            data_label='', extension=''):
        """Returns a SearchIndex object to be used for uploads.

        Args:
            name: the name of the searchindex.
            description: the description of the searchindex.
            sketch: sketch object (instance of Sketch).
            index_name: optional index name, if supplied and if it exists
                then the index associated with that will be returned.
            data_label: optional label of the data, if supplied will be used to
                determine whether an already existing index can be
                used or a new one created.
            extension: optional file extension if a file is being uploaded,
                if supplied and no data label used, then the extension will be
                used as a data label.

        Returns:
            A SearchIndex object.
        """
        if index_name:
            if not isinstance(index_name, str):
                index_name = codecs.decode(index_name, 'utf-8')

            searchindex = SearchIndex.query.filter_by(
                name=name, index_name=index_name).first()

            if searchindex and searchindex.has_permission(
                    permission='write', user=current_user):
                return searchindex

        if extension and not data_label:
            data_label = extension

        if not data_label:
            data_label = 'generic'

        indices = [t.searchindex for t in sketch.active_timelines]
        for index in indices:
            if index.has_label(data_label) and sketch.has_permission(
                    permission='write', user=current_user):
                return index

        index_name = index_name or uuid.uuid4().hex
        searchindex = SearchIndex.get_or_create(
            name=name,
            index_name=index_name,
            description=description,
            user=current_user)

        searchindex.grant_permission(permission='read', user=current_user)
        searchindex.grant_permission(permission='write', user=current_user)
        searchindex.grant_permission(permission='delete', user=current_user)
        searchindex.set_status('processing')

        db_session.add(searchindex)
        db_session.commit()

        searchindex.add_label(data_label, user=current_user)

        return searchindex

    def _upload_and_index(
            self, file_extension, timeline_name, index_name, sketch,
            enable_stream, data_label='', file_path='', events='', meta=None):
        """Creates a full pipeline for an uploaded file and returns the results.

        Args:
            file_extension: the extension of the uploaded file.
            timeline_name: name the timeline will be stored under in the
                           datastore.
            index_name: the Elastic index name for the timeline.
            sketch: Instance of timesketch.models.sketch.Sketch
            enable_stream: boolean indicating whether this is file is part of a
                           stream or not.
            data_label: Optional string with a data label for the search index.
            file_path: the path to the file to be uploaded (optional).
            events: a string with events to upload (optional).
            meta: optional dict with additional meta fields that will be
                  included in the return.

        Returns:
            A timeline if created otherwise a search index in JSON (instance
            of flask.wrappers.Response)
        """
        searchindex = self._get_index(
            name=timeline_name,
            description=timeline_name,
            sketch=sketch,
            index_name=index_name,
            data_label=data_label,
            extension=file_extension)
        searchindex.set_status('processing')

        timelines = Timeline.query.filter_by(
            name=timeline_name, sketch=sketch).all()

        timeline = None
        for timeline_ in timelines:
            if timeline_.searchindex.index_name == searchindex.index_name:
                timeline = timeline_
                break

            abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                'There is a timeline in the sketch that has the same name '
                'but is stored in a different index, check the data_label '
                'on the uploaded data')

        if not timeline:
            timeline = Timeline.get_or_create(
                name=timeline_name,
                description=timeline_name,
                sketch=sketch,
                user=current_user,
                searchindex=searchindex)

        if not timeline:
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                'Unable to get or create a new Timeline object.')

        timeline.set_status('processing')
        sketch.timelines.append(timeline)

        labels_to_prevent_deletion = current_app.config.get(
            'LABELS_TO_PREVENT_DELETION', [])
        for sketch_label in sketch.get_labels:
            if sketch_label not in labels_to_prevent_deletion:
                continue
            timeline.add_label(sketch_label)
            searchindex.add_label(sketch_label)

        db_session.add(timeline)
        db_session.commit()

        sketch_id = sketch.id
        # Start Celery pipeline for indexing and analysis.
        # Import here to avoid circular imports.
        # pylint: disable=import-outside-toplevel
        from timesketch.lib import tasks
        pipeline = tasks.build_index_pipeline(
            file_path=file_path, events=events, timeline_name=timeline_name,
            index_name=searchindex.index_name, file_extension=file_extension,
            sketch_id=sketch_id, only_index=enable_stream,
            timeline_id=timeline.id)
        pipeline.apply_async()

        return self.to_json(
            timeline, status_code=HTTP_STATUS_CODE_CREATED, meta=meta)

    def _upload_events(self, events, form, sketch, index_name):
        """Upload a file like object.

        Args:
            events: string with all the events.
            form: a dict with the configuration for the upload.
            sketch: Instance of timesketch.models.sketch.Sketch
            index_name: the Elastic index name for the timeline.

        Returns:
            A timeline if created otherwise a search index in JSON (instance
            of flask.wrappers.Response)
        """
        timeline_name = form.get('name', 'unknown_events')
        file_extension = 'jsonl'
        data_label = form.get('data_label', '')

        return self._upload_and_index(
            events=events,
            file_extension=file_extension,
            timeline_name=timeline_name,
            index_name=index_name,
            sketch=sketch,
            data_label=data_label,
            enable_stream=form.get('enable_stream', False))

    def _upload_file(self, file_storage, form, sketch, index_name):
        """Upload a file.

        Args:
            file_storage: a FileStorage object.
            form: a dict with the configuration for the upload.
            sketch: Instance of timesketch.models.sketch.Sketch
            index_name: the Elastic index name for the timeline.

        Returns:
            A timeline if created otherwise a search index in JSON (instance
            of flask.wrappers.Response)
        """
        _filename, _extension = os.path.splitext(file_storage.filename)
        file_extension = _extension.lstrip('.')
        timeline_name = form.get('name', _filename.rstrip('.'))

        # We do not need a human readable filename or
        # datastore index name, so we use UUIDs here.
        filename = uuid.uuid4().hex
        if not isinstance(filename, str):
            filename = codecs.decode(filename, 'utf-8')

        upload_folder = current_app.config['UPLOAD_FOLDER']
        file_path = os.path.join(upload_folder, filename)

        chunk_index = form.get('chunk_index')
        if isinstance(chunk_index, str) and chunk_index.isdigit():
            chunk_index = int(chunk_index)
        chunk_byte_offset = form.get('chunk_byte_offset')
        if isinstance(
                chunk_byte_offset, str) and chunk_byte_offset.isdigit():
            chunk_byte_offset = int(chunk_byte_offset)
        chunk_total_chunks = form.get('chunk_total_chunks')
        if isinstance(
                chunk_total_chunks, str) and chunk_total_chunks.isdigit():
            chunk_total_chunks = int(chunk_total_chunks)
        file_size = form.get('total_file_size')
        if isinstance(file_size, str) and file_size.isdigit():
            file_size = int(file_size)
        enable_stream = form.get('enable_stream', False)

        data_label = form.get('data_label', '')

        if chunk_total_chunks is None:
            file_storage.save(file_path)
            return self._upload_and_index(
                file_path=file_path,
                file_extension=file_extension,
                timeline_name=timeline_name,
                index_name=index_name,
                sketch=sketch,
                data_label=data_label,
                enable_stream=enable_stream)

        # For file chunks we need the correct filepath, otherwise each chunk
        # will get their own UUID as a filename.
        file_path = os.path.join(upload_folder, index_name)
        try:
            with open(file_path, 'ab') as fh:
                fh.seek(chunk_byte_offset)
                fh.write(file_storage.read())
        except OSError as e:
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                'Unable to write data with error: {0!s}.'.format(e))

        if (chunk_index + 1) != chunk_total_chunks:
            schema = {
                'meta': {
                    'file_upload': True,
                    'upload_complete': False,
                    'total_chunks': chunk_total_chunks,
                    'chunk_index': chunk_index,
                    'file_size': file_size},
                'objects': []}
            response = jsonify(schema)
            response.status_code = HTTP_STATUS_CODE_CREATED
            return response

        if os.path.getsize(file_path) != file_size:
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                'Unable to save file correctly, inconsistent file size '
                '({0:d} but should have been {1:d})'.format(
                    os.path.getsize(file_path), file_size))

        meta = {
            'file_upload': True,
            'upload_complete': True,
            'file_size': file_size,
            'total_chunks': chunk_total_chunks,
        }

        return self._upload_and_index(
            file_path=file_path,
            file_extension=file_extension,
            timeline_name=timeline_name,
            index_name=index_name,
            sketch=sketch,
            data_label=data_label,
            enable_stream=enable_stream,
            meta=meta)

    @login_required
    def post(self):
        """Handles POST request to the resource.

        Returns:
            A view in JSON (instance of flask.wrappers.Response)
        """
        upload_enabled = current_app.config['UPLOAD_ENABLED']
        if not upload_enabled:
            abort(HTTP_STATUS_CODE_BAD_REQUEST, 'Upload not enabled')

        form = request.get_data(parse_form_data=True)
        if not form:
            form = request.form

        sketch_id = form.get('sketch_id', None)
        if not sketch_id:
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                'Unable to upload data without supplying a '
                'sketch to associated it with.')

        if not isinstance(sketch_id, int):
            sketch_id = int(sketch_id)

        sketch = Sketch.query.get_with_acl(sketch_id)
        if not sketch:
            abort(
                HTTP_STATUS_CODE_NOT_FOUND,
                'No sketch found with this ID.')

        if sketch.get_status.status == 'archived':
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                'Unable to upload a file to an archived sketch.')

        if not sketch.has_permission(current_user, 'write'):
            abort(
                HTTP_STATUS_CODE_FORBIDDEN,
                'Unable to upload data to a sketch, user does not have '
                'write access.')

        utils.update_sketch_last_activity(sketch)

        index_name = form.get('index_name', '')
        file_storage = request.files.get('file')
        if file_storage:
            return self._upload_file(
                file_storage=file_storage,
                form=form, sketch=sketch, index_name=index_name)

        events = form.get('events')
        if not events:
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                'Unable to upload data, no file uploaded nor any events.')

        return self._upload_events(
            events=events, form=form, sketch=sketch, index_name=index_name)
