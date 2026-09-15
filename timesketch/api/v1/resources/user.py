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
import logging
import typing
import functools

from flask import abort
from flask import current_app
from flask import jsonify
from flask import request
from flask_restful import Resource
from flask_login import login_required
from flask_login import current_user

from timesketch.api.v1 import resources
from timesketch.lib.definitions import HTTP_STATUS_CODE_OK
from timesketch.lib.definitions import HTTP_STATUS_CODE_FORBIDDEN
from timesketch.lib.definitions import HTTP_STATUS_CODE_NOT_FOUND
from timesketch.models import db_session
from timesketch.models.sketch import Sketch
from timesketch.models.user import User
from timesketch.models.user import UserProfile
from timesketch.models.user import Group

logger = logging.getLogger("timesketch.user_api")


class UserListResource(resources.ResourceMixin, Resource):
    """Resource to get list of users."""

    @login_required
    def get(self):
        """Handles GET request to the resource.

        Returns:
            List of usernames
        """
        return self.to_json(User.query.all())

    @login_required
    def post(self):
        """Handles POST request to the resource.

        Returns:
            User Object
        """

        if not current_user.admin:
            abort(
                HTTP_STATUS_CODE_FORBIDDEN,
                "The user has no permissions to create other users.",
            )
        form = request.json
        username = form.get("username", "")
        password = form.get("password", "")

        # Check provided username
        if not username:
            abort(
                HTTP_STATUS_CODE_NOT_FOUND,
                "No username provided, unable to create the user.",
            )
        if not isinstance(username, str):
            abort(HTTP_STATUS_CODE_FORBIDDEN, "Username needs to be a string.")
        # Check provided password
        if not password:
            abort(
                HTTP_STATUS_CODE_NOT_FOUND,
                "No password provided, unable to create the user.",
            )
        if not isinstance(password, str):
            abort(HTTP_STATUS_CODE_FORBIDDEN, "Password needs to be a string.")

        user = User.get_or_create(username=username, name=username)
        user.set_password(plaintext=password)
        # TODO: Take additional attributes of users into account
        db_session.add(user)
        db_session.commit()
        return self.to_json(user)


class UserResource(resources.ResourceMixin, Resource):
    """Resource to get list of users."""

    @login_required
    def get(self, user_id):
        """Handles GET request to the resource.

        Returns:
            Details of user
        """

        user = User.get_by_id(user_id)
        return self.to_json(user)


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

    @login_required
    def post(self):
        """Handles POST request to the resource.

        Returns:
            HTTP status code indicating whether operation was successful.
        """
        form = request.json
        if not form:
            form = request.data

        password = form.get("password", "")

        if not password:
            abort(
                HTTP_STATUS_CODE_NOT_FOUND,
                "No password supplied, unable to change the password.",
            )

        if not isinstance(password, str):
            abort(HTTP_STATUS_CODE_FORBIDDEN, "Password needs to be a string.")

        current_user.set_password(plaintext=password)
        db_session.add(current_user)
        db_session.commit()
        return HTTP_STATUS_CODE_OK


class UserSettingsResource(resources.ResourceMixin, Resource):
    """Settings for the logged in user."""

    def _format_settings(self, settings):
        """Format settings with global defaults and overrides applied.

        Args:
            settings (dict): Dictionary containing raw user settings.

        Returns:
            Dictionary containing formatted user settings.
        """
        default_method = (
            "wildcard"
            if current_app.config.get("OPENSEARCH_WILDCARD_DEFAULT", False)
            else "query_string"
        )
        settings.setdefault(
            "defaultSearchMethod",
            default_method,
        )
        settings.setdefault("showProcessingTimelineEvents", False)

        # If the value of SEARCH_PROCESSING_TIMELINES changes to false while the user
        # had the option enabled, it remains enabled without functioning.
        # Therefore, if SEARCH_PROCESSING_TIMELINES changes to false, we disable the
        # showProcessingTimelineEvents option in the user's settings for display
        # consistency.
        if not current_app.config.get("SEARCH_PROCESSING_TIMELINES", False):
            settings["showProcessingTimelineEvents"] = False

        return settings

    @login_required
    def get(self):
        """Get profile for the logged in user.

        Returns:
          User profile as json
        """
        profile = UserProfile.get_or_create(user=current_user)
        settings = json.loads(profile.settings)
        formatted_settings = self._format_settings(settings)
        schema = {"objects": [formatted_settings], "meta": {}}
        return jsonify(schema)

    @login_required
    def post(self):
        """Create or update the logged in user's settings.

        Returns:
            User settings as json
        """
        profile = UserProfile.get_or_create(user=current_user)
        settings = json.loads(profile.settings)
        form = request.json

        form_settings = form.get("settings", {})
        settings.update(form_settings)
        profile.settings = json.dumps(settings)

        db_session.add(profile)
        db_session.commit()

        # Return consistent formatted settings back to the client
        formatted_settings = self._format_settings(settings)
        schema = {"objects": [formatted_settings], "meta": {}}
        return jsonify(schema)


class CollaboratorResource(resources.ResourceMixin, Resource):
    """Resource to update sketch collaborators."""

    def _verify_caller_authority(
        self, sketch: Sketch, permissions: typing.Iterable[str], error_message: str
    ) -> None:
        """Verifies if the current user has the given permissions on the sketch.

        Args:
            sketch: The sketch object to check permissions against.
            permissions: A list or set of permissions (e.g. 'read', 'write') to check.
            error_message: The error message to format and abort with if the user
                lacks the required permissions.
        """
        for permission in permissions:
            if not sketch.has_permission(user=current_user, permission=permission):
                abort(
                    HTTP_STATUS_CODE_FORBIDDEN,
                    error_message.format(permission=permission),
                )

    def _prepare_add_users(
        self, sketch: Sketch, users: list[str], permissions: list[str]
    ) -> typing.Iterator[typing.Callable[[], None]]:
        """Validates and yields user permission grants without committing to the database.

        Args:
            sketch: The sketch object to add collaborators to.
            users: A list of usernames to add as collaborators.
            permissions: A list of permissions to grant to the users.

        Yields:
            Callable actions to execute the grants.
        """
        for username in users:
            username = username.strip()
            if not username:
                continue

            # Try the username with any potential @domain preserved.
            user = User.query.filter_by(username=username).first()

            # If no hit, then try to strip the domain.
            if not user and "@" in username:
                base_username = username.split("@")[0].strip()
                user = User.query.filter_by(username=base_username).first()

            if user:
                user_permissions = permissions or ["read", "write"]
                for permission in user_permissions:
                    yield functools.partial(
                        sketch.grant_permission, permission=permission, user=user
                    )

    def _prepare_add_groups(
        self, sketch: Sketch, groups: list[str], permissions: list[str]
    ) -> typing.Iterator[typing.Callable[[], None]]:
        """Validates and yields group permission grants without committing to the database.

        Args:
            sketch: The sketch object to add group collaborators to.
            groups: A list of group names to add as collaborators.
            permissions: A list of permissions to grant to the groups.

        Yields:
            Callable actions to execute the grants.
        """
        for group_name in groups:
            group = Group.query.filter_by(name=group_name).first()

            if not group:
                logger.error("Group: %s not found", group_name)
                continue

            # Only add groups publicly visible or owned by the current user
            if not group.user or group.user == current_user:
                group_permissions = permissions or ["read", "write"]
                for permission in group_permissions:
                    yield functools.partial(
                        sketch.grant_permission, permission=permission, group=group
                    )

    def _prepare_remove_users(
        self, sketch: Sketch, users: list[str], permissions: list[str]
    ) -> typing.Iterator[typing.Callable[[], None]]:
        """Validates and yields user permission revocations without committing to the database.

        Args:
            sketch: The sketch object to remove user collaborators from.
            users: A list of usernames to revoke permissions from.
            permissions: A list of permissions to revoke from the users.

        Yields:
            Callable actions to execute the revocations.
        """
        for username in users:
            username = username.strip()
            if not username:
                continue

            # Try the username with any potential @domain preserved.
            user = User.query.filter_by(username=username).first()

            # If no hit, then try to strip the domain.
            if not user and "@" in username:
                base_username = username.split("@")[0].strip()
                user = User.query.filter_by(username=base_username).first()

            if not user:
                continue
            if user == sketch.user:
                abort(
                    HTTP_STATUS_CODE_FORBIDDEN,
                    "Cannot revoke permissions from the sketch owner.",
                )
            # Check effective permissions (including group inheritance) for parity
            target_permissions = []
            for p in ["read", "write", "delete"]:
                if sketch.has_permission(user, p):
                    target_permissions.append(p)
            permission_list = permissions or target_permissions
            self._verify_caller_authority(
                sketch,
                set(permission_list) | set(target_permissions),
                "The user does not have {permission:s} permission on the sketch "
                "and therefore can't revoke it from others",
            )
            for permission in permission_list:
                yield functools.partial(
                    sketch.revoke_permission, permission=permission, user=user
                )

    def _prepare_remove_groups(
        self, sketch: Sketch, groups: list[str], permissions: list[str]
    ) -> typing.Iterator[typing.Callable[[], None]]:
        """Validates and yields group permission revocations without committing to the database.

        Args:
            sketch: The sketch object to remove group collaborators from.
            groups: A list of group names to revoke permissions from.
            permissions: A list of permissions to revoke from the groups.

        Yields:
            Callable actions to execute the revocations.
        """
        all_permissions = sketch.get_all_permissions()
        for group_name in groups:
            if not group_name:
                continue
            group = Group.query.filter_by(name=group_name).first()
            if not group:
                continue

            # Asymmetric Group Ownership Boundary (groups vs. remove_groups):
            # As a feature, we intentionally allow any collaborator to remove any group
            # from the sketch.
            # This contrasts with adding groups, which restricts adding groups owned by others.
            target_permissions = all_permissions.get(f"group/{group.name:s}", [])
            permission_list = permissions or target_permissions
            self._verify_caller_authority(
                sketch,
                set(permission_list) | set(target_permissions),
                "The user does not have {permission:s} permission on the sketch "
                "and therefore can't revoke it from others",
            )
            for permission in permission_list:
                yield functools.partial(
                    sketch.revoke_permission, permission=permission, group=group
                )

    @login_required
    def post(self, sketch_id: int):
        """Handles POST request to manage sketch collaborators and permissions.

        The request JSON payload can contain the following fields:
        - users: List of usernames to grant permissions to.
        - groups: List of group names to grant permissions to.
        - remove_users: List of usernames to revoke permissions from.
        - remove_groups: List of group names to revoke permissions from.
        - permissions: A JSON-serialized list of permission strings to grant or
            revoke (e.g., '["read", "write"]'). If empty or not provided, defaults
            to ["read", "write"] for grants, and to all existing permissions for
            revocations.
        - public: Boolean (or string "true"/"false") to toggle public read access.

        Args:
            sketch_id: Integer primary key for a sketch database model.

        Returns:
            HTTP status code 200 (OK) on success, or HTTP_STATUS_CODE_FORBIDDEN if the
            user lacks permission to modify the sketch or grant/revoke the requested
            permissions.
        """
        sketch = Sketch.get_with_acl(sketch_id)
        if not sketch:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No sketch found with this ID.")

        form = request.json
        if not isinstance(form, dict):
            form = {}

        if not sketch.has_permission(user=current_user, permission="write"):
            abort(
                HTTP_STATUS_CODE_FORBIDDEN,
                "The user does not have write permission on the sketch.",
            )

        raw_permissions = form.get("permissions")
        permissions = []
        if isinstance(raw_permissions, str):
            try:
                parsed = json.loads(raw_permissions)
                if isinstance(parsed, list):
                    permissions = parsed
            except (json.JSONDecodeError, TypeError):
                pass
        elif isinstance(raw_permissions, list):
            permissions = raw_permissions

        # Ensure permissions is strictly a list of strings
        permissions = [p for p in permissions if isinstance(p, str)]

        # If we are adding users/groups, we must verify authority for the granted permissions
        if (
            isinstance(form.get("users"), list)
            or isinstance(form.get("groups"), list)
            or form.get("public") in (True, "true")
        ):
            grant_permissions = permissions or ["read", "write"]
            self._verify_caller_authority(
                sketch,
                grant_permissions,
                "The user does not have {permission:s} permission on the sketch "
                "and therefore can't grant it to others",
            )
        elif permissions:
            # For pure revokes, verify the explicit permissions array here.
            # (Target-specific inherited permissions will be checked in the helpers).
            self._verify_caller_authority(
                sketch,
                permissions,
                "The user does not have {permission:s} permission on the sketch "
                "and therefore can't grant/revoke it",
            )

        # PASS 1: Validation and Preparation
        # Gather all mutations before applying them to ensure atomicity and prevent
        # partial database mutations if a 403 Forbidden is triggered halfway through.
        pending_actions: list[typing.Callable[[], None]] = []

        users = form.get("users")
        if isinstance(users, list):
            users = [u for u in users if isinstance(u, str)]
            pending_actions.extend(self._prepare_add_users(sketch, users, permissions))

        groups = form.get("groups")
        if isinstance(groups, list):
            groups = [g for g in groups if isinstance(g, str)]
            pending_actions.extend(
                self._prepare_add_groups(sketch, groups, permissions)
            )

        remove_users = form.get("remove_users")
        if isinstance(remove_users, list):
            remove_users = [u for u in remove_users if isinstance(u, str)]
            pending_actions.extend(
                self._prepare_remove_users(sketch, remove_users, permissions)
            )

        remove_groups = form.get("remove_groups")
        if isinstance(remove_groups, list):
            remove_groups = [g for g in remove_groups if isinstance(g, str)]
            pending_actions.extend(
                self._prepare_remove_groups(sketch, remove_groups, permissions)
            )

        if "public" in form:
            public = form.get("public")
            # TODO: Remove string check. Non-pythonic check is needed because the old UI
            # returns a string of true or false and not a boolean.
            if public is True or public == "true":
                pending_actions.append(
                    functools.partial(sketch.grant_permission, permission="read")
                )
            else:
                pending_actions.append(
                    functools.partial(sketch.revoke_permission, permission="read")
                )

        # PASS 2: Execution
        # If we reached this point, no abort() was called. All checks passed.
        # Now we apply the configured mutations to the database.
        for action in pending_actions:
            action()

        return HTTP_STATUS_CODE_OK
