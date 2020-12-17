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
"""Explore resources for version 1 of the Timesketch API."""

import datetime
import io
import json
import zipfile

from flask import abort
from flask import jsonify
from flask import request
from flask import send_file
from flask_restful import Resource
from flask_login import login_required
from flask_login import current_user

from timesketch.api.v1 import export
from timesketch.api.v1 import resources
from timesketch.api.v1 import utils
from timesketch.lib import forms
from timesketch.lib.utils import get_validated_indices
from timesketch.lib.definitions import DEFAULT_SOURCE_FIELDS
from timesketch.lib.definitions import HTTP_STATUS_CODE_BAD_REQUEST
from timesketch.lib.definitions import HTTP_STATUS_CODE_FORBIDDEN
from timesketch.lib.definitions import HTTP_STATUS_CODE_NOT_FOUND
from timesketch.models import db_session
from timesketch.models.sketch import Sketch
from timesketch.models.sketch import View


class ExploreResource(resources.ResourceMixin, Resource):
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
        if not sketch:
            abort(
                HTTP_STATUS_CODE_NOT_FOUND, 'No sketch found with this ID.')

        if not sketch.has_permission(current_user, 'read'):
            abort(HTTP_STATUS_CODE_FORBIDDEN,
                  'User does not have read access controls on sketch.')

        if sketch.get_status.status == 'archived':
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                'Unable to query on an archived sketch.')

        form = forms.ExploreForm.build(request)

        if not form.validate_on_submit():
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                'Unable to explore data, unable to validate form data')

        # TODO: Remove form and use json instead.
        query_dsl = form.dsl.data
        enable_scroll = form.enable_scroll.data
        scroll_id = form.scroll_id.data
        file_name = form.file_name.data

        query_filter = request.json.get('filter', {})

        return_field_string = form.fields.data
        if return_field_string:
            return_fields = [x.strip() for x in return_field_string.split(',')]
        else:
            return_fields = query_filter.get('fields', [])
            return_fields = [field['field'] for field in return_fields]
            return_fields.extend(DEFAULT_SOURCE_FIELDS)

        sketch_indices = {
            t.searchindex.index_name
            for t in sketch.timelines
            if t.get_status.status.lower() == 'ready'
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
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                'The request needs a query string/DSL and or a star filter.')

        # Aggregate hit count per index.
        index_stats_agg = {
            "indices": {
                "terms": {
                    "field": "_index"
                }
            }
        }

        if file_name:
            file_object = io.BytesIO()

            form_data = {
                'created_at': datetime.datetime.utcnow().isoformat(),
                'created_by': current_user.username,
                'sketch': sketch_id,
                'query': form.query.data,
                'query_dsl': query_dsl,
                'query_filter': query_filter,
                'return_fields': return_fields,
            }
            with zipfile.ZipFile(file_object, mode='w') as zip_file:
                zip_file.writestr('METADATA', data=json.dumps(form_data))
                fh = export.query_to_filehandle(
                    query_string=form.query.data,
                    query_dsl=query_dsl,
                    query_filter=query_filter,
                    indices=indices,
                    sketch=sketch,
                    datastore=self.datastore)
                fh.seek(0)
                zip_file.writestr('query_results.csv', fh.read())
            file_object.seek(0)
            return send_file(
                file_object, mimetype='zip',
                attachment_filename=file_name)

        if scroll_id:
            # pylint: disable=unexpected-keyword-arg
            result = self.datastore.client.scroll(
                scroll_id=scroll_id, scroll='1m')
        else:
            try:
                result = self.datastore.search(
                    sketch_id,
                    form.query.data,
                    query_filter,
                    query_dsl,
                    indices,
                    aggregations=index_stats_agg,
                    return_fields=return_fields,
                    enable_scroll=enable_scroll)
            except ValueError as e:
                abort(
                    HTTP_STATUS_CODE_BAD_REQUEST, e)

        # Get number of matching documents per index.
        count_per_index = {}
        try:
            for bucket in result['aggregations']['indices']['buckets']:
                key = bucket.get('key')
                if key:
                    count_per_index[key] = bucket.get('doc_count')
        except KeyError:
            pass

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
        # TODO: Add a call to utils.update_sketch_last_activity once new
        # mechanism has been added, instead of relying on user views.
        view = View.get_or_create(
            user=current_user, sketch=sketch, name='')
        view.update_modification_time()
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
            'count_per_index': count_per_index,
            'scroll_id': result.get('_scroll_id', ''),
        }

        # Elasticsearch version 7.x returns total hits as a dictionary.
        # TODO: Refactor when version 6.x has been deprecated.
        if isinstance(meta['es_total_count'], dict):
            meta['es_total_count'] = meta['es_total_count'].get('value', 0)

        schema = {'meta': meta, 'objects': result['hits']['hits']}
        return jsonify(schema)


class QueryResource(resources.ResourceMixin, Resource):
    """Resource to get a query."""

    @login_required
    def post(self, sketch_id):
        """Handles GET request to the resource.

        Args:
            sketch_id: Integer primary key for a sketch database model

        Returns:
            A story in JSON (instance of flask.wrappers.Response)
        """
        form = forms.ExploreForm.build(request)
        if not form.validate_on_submit():
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST, 'Unable to validate form data.')
        sketch = Sketch.query.get_with_acl(sketch_id)
        if not sketch:
            abort(
                HTTP_STATUS_CODE_NOT_FOUND, 'No sketch found with this ID.')
        if not sketch.has_permission(current_user, 'read'):
            abort(HTTP_STATUS_CODE_FORBIDDEN,
                  'User does not have read access controls on sketch.')
        schema = {
            'objects': [],
            'meta': {}}
        query_string = form.query.data
        query_filter = form.filter.data
        query_dsl = form.dsl.data
        query = self.datastore.build_query(
            sketch.id, query_string, query_filter, query_dsl)
        schema['objects'].append(query)
        return jsonify(schema)
