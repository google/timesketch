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
"""This collaborator API calls for version 1 of the Timesketch API."""

from __future__ import unicode_literals

import logging

from flask import abort
from flask import request
from flask_login import current_user
from flask_login import login_required
from flask_restful import Resource

from timesketch.api.v1 import resources
from timesketch.lib.definitions import HTTP_STATUS_CODE_FORBIDDEN
from timesketch.lib.definitions import HTTP_STATUS_CODE_NOT_FOUND
from timesketch.lib.definitions import HTTP_STATUS_CODE_OK
from timesketch.models.sketch import Sketch
from timesketch.models.user import User
from timesketch.models.user import Group


logger = logging.getLogger('api_collaborator_resource')


class CollaboratorResource(resources.ResourceMixin, Resource):
    """Resource to update sketch collaborators."""

    # A list of possible permissions that can be defined.
    POSSIBLE_PERMISSIONS = frozenset([
        'read',
        'write',
        'delete',
    ])

    @login_required
    def post(self, sketch_id):
        """Handles POST request to the resource.

        Args:
            sketch_id: Integer primary key for a sketch database model
        """
        sketch = Sketch.query.get_with_acl(sketch_id)
        if not sketch:
            abort(
                HTTP_STATUS_CODE_NOT_FOUND, 'No sketch found with this ID.')
        form = request.json

        # TODO: Add granular ACL controls.
        # https://github.com/google/timesketch/issues/1016

        if not sketch.has_permission(user=current_user, permission='write'):
            abort(
                HTTP_STATUS_CODE_FORBIDDEN,
                'The user does not have write permission on the sketch.')

        for username in form.get('users', []):
            # Try the username with any potential @domain preserved.
            user = User.query.filter_by(username=username).first()

            # If no hit, then try to strip the domain.
            if not user:
                base_username = username.split('@')[0]
                base_username = base_username.strip()
                user = User.query.filter_by(username=base_username).first()

            if user:
                sketch.grant_permission(permission='read', user=user)
                sketch.grant_permission(permission='write', user=user)

        for group in form.get('groups', []):
            group = Group.query.filter_by(name=group).first()
            # Only add groups publicly visible or owned by the current user
            if not group.user or group.user == current_user:
                sketch.grant_permission(permission='read', group=group)
                sketch.grant_permission(permission='write', group=group)

        for username in form.get('remove_users', []):
            user = User.query.filter_by(username=username).first()
            sketch.revoke_permission(permission='read', user=user)
            sketch.revoke_permission(permission='write', user=user)

        for group in form.get('remove_groups', []):
            group = Group.query.filter_by(name=group).first()
            sketch.revoke_permission(permission='read', group=group)
            sketch.revoke_permission(permission='write', group=group)

        public = form.get('public')
        if public == 'true':
            sketch.grant_permission(permission='read')
        else:
            sketch.revoke_permission(permission='read')

        return HTTP_STATUS_CODE_OK
