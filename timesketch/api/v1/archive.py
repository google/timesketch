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
"""This module holds version 1 of the Timesketch API, archive API."""

from __future__ import unicode_literals

import datetime
import io
import json
import logging
import zipfile

import pandas as pd

from flask import abort
from flask import current_app
from flask import jsonify
from flask import request
from flask import send_file
from flask_login import current_user
from flask_login import login_required
from flask_restful import Resource

from timesketch import version
from timesketch.api.v1 import resources
from timesketch.api.v1 import utils
from timesketch.lib.definitions import HTTP_STATUS_CODE_BAD_REQUEST
from timesketch.lib.definitions import HTTP_STATUS_CODE_FORBIDDEN
from timesketch.lib.definitions import HTTP_STATUS_CODE_NOT_FOUND
from timesketch.lib.definitions import HTTP_STATUS_CODE_OK
from timesketch.lib.stories import api_fetcher as story_api_fetcher
from timesketch.lib.stories import manager as story_export_manager
from timesketch.models.sketch import Sketch


logger = logging.getLogger('api_archive_resource')


class SketchArchiveResource(resources.ResourceMixin, Resource):
    """Resource to archive a sketch."""

    @login_required
    def get(self, sketch_id):
        """Handles GET request to the resource.

        Returns:
            A sketch in JSON (instance of flask.wrappers.Response)
        """
        sketch = Sketch.query.get_with_acl(sketch_id)
        if not sketch:
            abort(
                HTTP_STATUS_CODE_NOT_FOUND, 'No sketch found with this ID.')

        if not sketch.has_permission(current_user, 'read'):
            abort(
                HTTP_STATUS_CODE_FORBIDDEN, (
                    'User does not have sufficient access rights to '
                    'read the sketch.'))
        meta = {
            'is_archived': sketch.get_status.status == 'archived',
            'sketch_id': sketch.id,
            'sketch_name': sketch.name,
        }
        schema = {
            'meta': meta,
            'objects': []
        }
        return jsonify(schema)

    @login_required
    def post(self, sketch_id):
        """Handles POST request to the resource.

        Returns:
            A sketch in JSON (instance of flask.wrappers.Response)
        """
        sketch = Sketch.query.get_with_acl(sketch_id)
        if not sketch:
            abort(
                HTTP_STATUS_CODE_NOT_FOUND, 'No sketch found with this ID.')

        if not sketch.has_permission(current_user, 'delete'):
            abort(
                HTTP_STATUS_CODE_FORBIDDEN, (
                    'User does not have sufficient access rights to '
                    'delete a sketch.'))

        form = request.json
        if not form:
            form = request.data

        action = form.get('action', '')
        if action == 'archive':
            return self._archive_sketch(sketch)

        if action == 'export':
            return self._export_sketch(sketch)

        if action == 'unarchive':
            return self._unarchive_sketch(sketch)

        return abort(
            HTTP_STATUS_CODE_NOT_FOUND,
            'The action: [{0:s}] is not supported.'.format(action))

    def _export_sketch(self, sketch):
        """Returns a ZIP file with the exported content of a sketch."""
        file_object = io.BytesIO()
        sketch_is_archived = sketch.get_status.status == 'archived'

        if sketch_is_archived:
            _ = self._unarchive_sketch(sketch)

        story_exporter = story_export_manager.StoryExportManager.get_exporter(
            'html')

        meta = {
            'user': current_user.username,
            'time': datetime.datetime.utcnow().isoformat(),
            'sketch_id': sketch.id,
            'sketch_name': sketch.name,
            'sketch_description': sketch.description,
            'timesketch_version': version.get_version(),
        }

        with zipfile.ZipFile(file_object, mode='w') as zip_file:
            zip_file.writestr('METADATA', data=json.dumps(meta))

            for story in sketch.stories:
                with story_exporter() as exporter:
                    data_fetcher = story_api_fetcher.ApiDataFetcher()
                    data_fetcher.set_sketch_id(sketch.id)

                    exporter.set_data_fetcher(data_fetcher)
                    exporter.from_string(story.content)
                    zip_file.writestr(
                        'stories/{0:04d}_{1:s}.html'.format(
                            story.id, story.title),
                        data=exporter.export_story())

            for aggregation in sketch.aggregations:
                name = '{0:04d}_{1:s}'.format(aggregation.id, aggregation.name)
                parameters = json.loads(aggregation.parameters)
                result_obj, meta = utils.run_aggregator(
                    sketch.id, aggregator_name=aggregation.agg_type,
                    aggregator_parameters=parameters)

                zip_file.writestr(
                    'aggregations/{0:s}.meta'.format(name),
                    data=json.dumps(meta))

                html = result_obj.to_chart(
                    chart_name=meta.get('chart_type'),
                    chart_title=aggregation.name,
                    color=meta.get('chart_color'),
                    interactive=True, as_html=True)
                zip_file.writestr(
                    'aggregations/{0:s}.html'.format(name),
                    data=html)

                string_io = io.StringIO()
                data_frame = result_obj.to_pandas()
                data_frame.to_csv(string_io, index=False)
                string_io.seek(0)
                zip_file.writestr(
                    'aggregations/{0:s}.csv'.format(name),
                    data=string_io.read())

            for view in sketch.views:
                name = '{0:04d}_{1:s}'.format(view.id, view.name)
                sketch_indices = {
                    t.searchindex.index_name
                    for t in sketch.timelines
                    if t.get_status.status.lower() == 'ready'
                }
                query_filter = json.loads(view.query_filter)
                if not query_filter:
                    query_filter = {}
                indices = query_filter.get('indices', sketch_indices)
                if not indices or '_all' in indices:
                    indices = sketch_indices

                query_dsl = view.query_dsl
                if query_dsl:
                    query_dict = json.loads(query_dsl)
                    if not query_dict:
                        query_dsl = None

                # TODO (kiddi): Include all fields, not just the default one.
                # TODO (kiddi): Enable scrolling support.
                result = self.datastore.search(
                    sketch_id=sketch.id,
                    query_string=view.query_string,
                    query_filter=query_filter,
                    query_dsl=query_dsl,
                    indices=indices)

                fh = io.StringIO()
                lines = []
                for event in result['hits']['hits']:
                    line = event['_source']
                    line.setdefault('label', [])
                    line['_id'] = event['_id']
                    line['_type'] = event['_type']
                    line['_index'] = event['_index']
                    try:
                        for label in line['timesketch_label']:
                            if sketch.id != label['sketch_id']:
                                continue
                            line['label'].append(label['name'])
                        del line['timesketch_label']
                    except KeyError:
                        pass

                    lines.append(line)
                data_frame = pd.DataFrame(lines)
                del lines
                data_frame.to_csv(fh, index=False)
                fh.seek(0)
                zip_file.writestr(
                    'views/{0:s}.csv'.format(name), data=fh.read())

                if not view.user:
                    username = 'System'
                else:
                    username = view.user.username
                meta = {
                    'name': view.name,
                    'view_id': view.id,
                    'description': view.description,
                    'query_string': view.query_string,
                    'query_filter': view.query_filter,
                    'query_dsl': view.query_dsl,
                    'username': username,
                    'sketch_id': view.sketch_id,
                }
                zip_file.writestr(
                    'views/{0:s}.meta'.format(name), data=json.dumps(meta))

            # TODO (kiddi): Add in aggregation group support.
            # TODO (kiddi): Add in support for comments/stars/labels.
            # TODO (kiddi): Add in support for all tagged events (includes
            # a metadata file with a list of all tags and their count).

        if sketch_is_archived:
            _ = self._archive_sketch(sketch)

        file_object.seek(0)
        return send_file(
            file_object, mimetype='zip',
            attachment_filename='timesketch_export.zip')

    def _unarchive_sketch(self, sketch):
        """Unarchives a sketch by opening up all indices and removing labels.

        Args:
            sketch: Instance of timesketch.models.sketch.Sketch
        """
        if sketch.get_status.status != 'archived':
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                'Unable to unarchive a sketch that wasn\'t already archived '
                '(sketch: {0:d})'.format(sketch.id))

        sketch.set_status(status='ready')

        indexes_to_open = []
        for timeline in sketch.timelines:
            if timeline.get_status.status != 'archived':
                continue
            timeline.set_status(status='ready')
            search_index = timeline.searchindex
            search_index.set_status(status='ready')
            indexes_to_open.append(search_index.index_name)

        # TODO (kiddi): Move this to lib/datastores/elastic.py.
        self.datastore.client.indices.open(','.join(indexes_to_open))
        return HTTP_STATUS_CODE_OK

    def _archive_sketch(self, sketch):
        """Unarchives a sketch by opening up all indices and removing labels.

        Args:
            sketch: Instance of timesketch.models.sketch.Sketch
        """
        if sketch.get_status.status == 'archived':
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                'Unable to archive a sketch that was already archived '
                '(sketch: {0:d})'.format(sketch.id))

        labels_to_prevent_deletion = current_app.config.get(
            'LABELS_TO_PREVENT_DELETION', [])

        for label in labels_to_prevent_deletion:
            if sketch.has_label(label):
                abort(
                    HTTP_STATUS_CODE_FORBIDDEN,
                    'A sketch with the label {0:s} cannot be '
                    'archived.'.format(label))

        sketch.set_status(status='archived')

        # Go through all timelines in a sketch.
        #    Each timeline has only a single search index, however
        #    each search index can be part of multiple timelines.
        #    Only archive a search index if all of it's timelines
        #    are archived.
        indexes_to_close = []
        for timeline in sketch.timelines:
            if timeline.get_status.status != 'ready':
                continue
            timeline.set_status(status='archived')
            search_index = timeline.searchindex

            if not all([
                    x.get_status.status == 'archived'
                    for x in search_index.timelines]):
                continue
            search_index.set_status(status='archived')
            indexes_to_close.append(search_index.index_name)

        # TODO (kiddi): Move this to lib/datastores/elastic.py.
        self.datastore.client.indices.close(','.join(indexes_to_close))
        return HTTP_STATUS_CODE_OK
