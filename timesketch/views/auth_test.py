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
"""Tests for the auth views."""

from __future__ import unicode_literals

from flask import current_app
from flask_login import current_user

from timesketch.lib.definitions import HTTP_STATUS_CODE_REDIRECT
from timesketch.lib.testlib import BaseTest


class AuthViewTest(BaseTest):
    """Test the auth view."""

    def test_login_view_unauthenticated(self):
        """Test the login view handler with an unauthenticated session."""
        response = self.client.get("/login/")
        self.assert200(response)

    def test_login_view_form_authenticated(self):
        """Test the login view handler with an authenticated session."""
        self.login()
        response = self.client.get("/login/")
        self.assertEqual(response.status_code, HTTP_STATUS_CODE_REDIRECT)

    def test_login_view_sso_authenticated(self):
        """Test the login view handler with an SSO authenticated session."""
        current_app.config["SSO_ENABLED"] = True
        current_app.config["SSO_GROUP_ENV_VARIABLE"] = "SSO_GROUP"
        current_app.config["SSO_GROUP_SEPARATOR"] = ";"
        current_app.config["SSO_GROUP_NOT_MEMBER_SIGN"] = "-"
        with self.client:
            response = self.client.get(
                "/login/",
                environ_base={
                    "REMOTE_USER": "test1",
                    "SSO_GROUP": "test_group1;-test_group2",
                },
            )
            self.assertEqual(current_user.username, "test1")
            self.assertIn(self.group1, current_user.groups)
            self.assertNotIn(self.group2, current_user.groups)
            self.assertEqual(response.status_code, HTTP_STATUS_CODE_REDIRECT)

    def test_logout_view(self):
        """Test the logout view handler."""
        self.login()
        response = self.client.get("/logout/")
        self.assertEqual(response.status_code, HTTP_STATUS_CODE_REDIRECT)
