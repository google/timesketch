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
"""Timesketch API client library."""
import logging

from . import error
from . import resource


logger = logging.getLogger("timesketch_api.user")


class User(resource.BaseResource):
    """User object."""

    def __init__(self, api, user_id=None):
        """Initializes the user object."""
        self._object_data = None
        if not user_id:
            resource_uri = "users/me/"
            super().__init__(api, resource_uri)
        else:
            self.id = user_id
            self.api = api
            super().__init__(api=api, resource_uri=f"users/{self.id}")

    def _get_data(self):
        """Returns dict from the first object of the resource data."""
        if self._object_data:
            return self._object_data

        data = self.data
        objects = data.get("objects")
        if objects:
            self._object_data = objects[0]
        else:
            self._object_data = {}

        return self._object_data

    def change_password(self, new_password):
        """Change the password for the user.

        Args:
            new_password (str): String with the password.

        Raises:
            ValueError: If there was an error.

        Returns:
            Boolean: Whether the password was successfully modified.
        """
        if not new_password:
            raise ValueError("No new password supplied.")

        if not isinstance(new_password, str):
            raise ValueError("Password needs to be a string value.")

        data = {"password": new_password}
        resource_url = f"{self.api.api_root}/{self.resource_uri}"
        response = self.api.session.post(resource_url, json=data)
        return error.check_return_status(response, logger)

    @property
    def groups(self):
        """Property that returns the groups the user belongs to."""
        data = self._get_data()
        groups = data.get("groups", [])
        return [x.get("name", "") for x in groups]

    @property
    def is_active(self):
        """Property that returns bool indicating whether the user is active."""
        data = self._get_data()
        return data.get("active", True)

    @property
    def is_admin(self):
        """Property that returns bool indicating whether the user is admin."""
        data = self._get_data()
        return data.get("admin", False)

    @property
    def username(self):
        """Property that returns back the username of the current user."""
        data = self._get_data()
        return data.get("username", "Unknown")

    def __str__(self):
        """Returns a string representation of the username."""
        user_strings = [self.username]

        if self.is_active:
            user_strings.append("[active]")
        else:
            user_strings.append("[inactive]")

        if self.is_admin:
            user_strings.append("<is admin>")

        return " ".join(user_strings)
