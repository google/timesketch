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
"""User and Group resources for version 1 of the Timesketch API."""
import json

from flask import abort
from flask import request
from flask_restful import Resource
from flask_login import login_required
from flask_login import current_user

from timesketch.api.v1 import resources
from timesketch.lib.definitions import HTTP_STATUS_CODE_OK
from timesketch.lib.definitions import HTTP_STATUS_CODE_FORBIDDEN
from timesketch.lib.definitions import HTTP_STATUS_CODE_NOT_FOUND
from timesketch.models.sketch import Sketch
from timesketch.models.user import User
from timesketch.models.user import Group


class UserListResource(resources.ResourceMixin, Resource):
    """Resource to get list of users."""

    @login_required
    def get(self):
        """Handles GET request to the resource.

        Returns:
            List of usernames
        """
        return self.to_json(User.query.all())


class GroupListResource(resources.ResourceMixin, Resource):
    """Resource to get list of groups."""

    @login_required
    def get(self):
        """Handles GET request to the resource.

        Returns:
            List of group names
        """
        return self.to_json(Group.query.all())


class LoggedInUserResource(resources.ResourceMixin, Resource):
    """Resource to get the logged in user."""

    @login_required
    def get(self):
        """Handles GET request to the resource.

        Returns:
            User object
        """
        return self.to_json(current_user)


class CollaboratorResource(resources.ResourceMixin, Resource):
    """Resource to update sketch collaborators."""

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

        if not sketch.has_permission(user=current_user, permission='write'):
            abort(
                HTTP_STATUS_CODE_FORBIDDEN,
                'The user does not have write permission on the sketch.')

        permission_string = form.get('permissions', '')
        if permission_string:
            try:
                permissions = json.loads(permission_string)
            except json.JSONDecodeError:
                permissions = []
        else:
            permissions = []

        # You cannot grant a permission you don't have.
        for index, permission in enumerate(permissions):
            if not sketch.has_permission(
                    user=current_user, permission=permission):
                _ = permissions.pop(index)

        for username in form.get('users', []):
            # Try the username with any potential @domain preserved.
            user = User.query.filter_by(username=username).first()

            # If no hit, then try to strip the domain.
            if not user:
                base_username = username.split('@')[0]
                base_username = base_username.strip()
                user = User.query.filter_by(username=base_username).first()

            if user:
                user_permissions = permissions or ['read', 'write']
                for permission in user_permissions:
                    sketch.grant_permission(permission=permission, user=user)

        for group in form.get('groups', []):
            group = Group.query.filter_by(name=group).first()

            # Only add groups publicly visible or owned by the current user
            if not group.user or group.user == current_user:
                group_permissions = permissions or ['read', 'write']
                for permission in group_permissions:
                    sketch.grant_permission(permission=permission, group=group)

        all_permissions = sketch.get_all_permissions()
        for username in form.get('remove_users', []):
            user = User.query.filter_by(username=username).first()
            permission_list = permissions or all_permissions.get(
                'user/{0:s}'.format(username), [])
            for permission in permission_list:
                sketch.revoke_permission(permission=permission, user=user)

        for group in form.get('remove_groups', []):
            group = Group.query.filter_by(name=group).first()
            permission_list = permissions or all_permissions.get(
                'group/{0:s}'.format(username), [])
            for permission in permission_list:
                sketch.revoke_permission(permission=permission, user=user)

        public = form.get('public')
        if public == 'true':
            sketch.grant_permission(permission='read')
        else:
            sketch.revoke_permission(permission='read')

        return HTTP_STATUS_CODE_OK
