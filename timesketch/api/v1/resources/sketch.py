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
"""Sketch resources for version 1 of the Timesketch API."""

import six

from flask import jsonify
from flask import request
from flask import abort
from flask import current_app
from flask_restful import Resource
from flask_restful import reqparse
from flask_login import login_required
from flask_login import current_user
from sqlalchemy import not_

from timesketch.api.v1 import resources
from timesketch.lib import forms
from timesketch.lib.definitions import HTTP_STATUS_CODE_OK
from timesketch.lib.definitions import HTTP_STATUS_CODE_CREATED
from timesketch.lib.definitions import HTTP_STATUS_CODE_BAD_REQUEST
from timesketch.lib.definitions import HTTP_STATUS_CODE_FORBIDDEN
from timesketch.lib.definitions import HTTP_STATUS_CODE_NOT_FOUND
from timesketch.lib.analyzers import manager as analyzer_manager
from timesketch.lib.aggregators import manager as aggregator_manager
from timesketch.lib.emojis import get_emojis_as_dict
from timesketch.models import db_session
from timesketch.models.sketch import Sketch
from timesketch.models.sketch import SearchTemplate


class SketchListResource(resources.ResourceMixin, Resource):
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
        filtered_sketches = Sketch.all_with_acl().filter(
            not_(Sketch.Status.status == 'deleted'),
            Sketch.Status.parent).order_by(Sketch.updated_at.desc()).all()

        # Just return a subset of the sketch objects to reduce the amount of
        # data returned.
        sketches = []
        for sketch in filtered_sketches:
            sketches.append({
                'name': sketch.name,
                'updated_at': str(sketch.updated_at),
                'user': sketch.user.username,
                'id': sketch.id
            })
        meta = {'current_user': current_user.username}
        return jsonify({'objects': sketches, 'meta': meta})

    @login_required
    def post(self):
        """Handles POST request to the resource.

        Returns:
            A sketch in JSON (instance of flask.wrappers.Response)
        """
        form = forms.NameDescriptionForm.build(request)
        if not form.validate_on_submit():
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST, 'Unable to validate form data.')
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


class SketchResource(resources.ResourceMixin, Resource):
    """Resource to get a sketch."""

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

        aggregators = {}
        for _, cls in aggregator_manager.AggregatorManager.get_aggregators():
            aggregators[cls.NAME] = {
                'form_fields': cls.FORM_FIELDS,
                'display_name': cls.DISPLAY_NAME,
                'description': cls.DESCRIPTION
            }

        # Get mappings for all indices in the sketch. This is used to set
        # columns shown in the event list.
        sketch_indices = [
            t.searchindex.index_name
            for t in sketch.active_timelines
            if t.get_status.status != 'archived'
        ]

        # Get event count and size on disk for each index in the sketch.
        stats_per_index = {}
        for timeline in sketch.active_timelines:
            if timeline.get_status.status != 'archived':
                continue
            stats_per_index[timeline.searchindex.index_name] = {
                'count': 0,
                'bytes': 0
            }

        es_stats = self.datastore.client.indices.stats(
            index=sketch_indices, metric='docs, store')
        for index_name, stats in es_stats.get('indices', {}).items():
            stats_per_index[index_name] = {
                'count': stats.get('total', {}).get('docs', {}).get('count', 0),
                'bytes': stats.get(
                    'total', {}).get('store', {}).get('size_in_bytes', 0)
            }

        if not sketch_indices:
            mappings_settings = {}
        else:
            mappings_settings = self.datastore.client.indices.get_mapping(
                index=sketch_indices)

        mappings = []

        for _, value in mappings_settings.items():
            # The structure is different in ES version 6.x and lower. This check
            # makes sure we support both old and new versions.
            properties = value['mappings'].get('properties')
            if not properties:
                properties = next(
                    iter(value['mappings'].values())).get('properties')

            for field, value_dict in properties.items():
                mapping_dict = {}
                # Exclude internal fields
                if field.startswith('__'):
                    continue
                if field == 'timesketch_label':
                    continue
                mapping_dict['field'] = field
                mapping_dict['type'] = value_dict.get('type', 'n/a')
                mappings.append(mapping_dict)

        # Make the list of dicts unique
        mappings = {v['field']: v for v in mappings}.values()

        views = []
        for view in sketch.get_named_views:
            if not view.user:
                username = 'System'
            else:
                username = view.user.username
            view = {
                'name': view.name,
                'description': view.description,
                'id': view.id,
                'query': view.query_string,
                'user': username,
                'created_at': view.created_at,
                'updated_at': view.updated_at
            }
            views.append(view)

        meta = dict(
            aggregators=aggregators,
            views=views,
            searchtemplates=[{
                'name': searchtemplate.name,
                'id': searchtemplate.id
            } for searchtemplate in SearchTemplate.query.all()],
            emojis=get_emojis_as_dict(),
            permissions={
                'public': bool(sketch.is_public),
                'read': bool(sketch.has_permission(current_user, 'read')),
                'write': bool(sketch.has_permission(current_user, 'write')),
                'delete': bool(sketch.has_permission(current_user, 'delete')),
            },
            collaborators={
                'users': [user.username for user in sketch.collaborators],
                'groups': [group.name for group in sketch.groups],
            },
            analyzers=[
                x for x, y in analyzer_manager.AnalysisManager.get_analyzers()
            ],
            mappings=list(mappings),
            stats=stats_per_index
        )
        return self.to_json(sketch, meta=meta)

    @login_required
    def delete(self, sketch_id):
        """Handles DELETE request to the resource."""
        sketch = Sketch.query.get_with_acl(sketch_id)
        if not sketch:
            abort(
                HTTP_STATUS_CODE_NOT_FOUND, 'No sketch found with this ID.')
        if not sketch.has_permission(current_user, 'delete'):
            abort(
                HTTP_STATUS_CODE_FORBIDDEN, (
                    'User does not have sufficient access rights to '
                    'delete a sketch.'))
        not_delete_labels = current_app.config.get(
            'LABELS_TO_PREVENT_DELETION', [])
        for label in not_delete_labels:
            if sketch.has_label(label):
                abort(
                    HTTP_STATUS_CODE_FORBIDDEN,
                    'Sketch with the label [{0:s}] cannot be deleted.'.format(
                        label))
        sketch.set_status(status='deleted')
        return HTTP_STATUS_CODE_OK

    @login_required
    def post(self, sketch_id):
        """Handles POST request to the resource.

        Returns:
            A sketch in JSON (instance of flask.wrappers.Response)
        """
        form = forms.NameDescriptionForm.build(request)
        sketch = Sketch.query.get_with_acl(sketch_id)
        if not sketch:
            abort(
                HTTP_STATUS_CODE_NOT_FOUND, 'No sketch found with this ID.')

        if not form.validate_on_submit():
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST, (
                    'Unable to rename sketch, '
                    'unable to validate form data'))

        if not sketch.has_permission(current_user, 'write'):
            abort(HTTP_STATUS_CODE_FORBIDDEN,
                  'User does not have write access controls on sketch.')

        sketch.name = form.name.data
        sketch.description = form.description.data
        db_session.add(sketch)
        db_session.commit()
        return self.to_json(sketch, status_code=HTTP_STATUS_CODE_CREATED)
