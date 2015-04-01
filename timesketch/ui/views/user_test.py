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
"""Tests for the user views."""

from flask_login import current_app
from flask_login import current_user

from timesketch.lib.definitions import HTTP_STATUS_CODE_REDIRECT
from timesketch.lib.testlib import BaseTest


class UserViewTest(BaseTest):
    """Test the user view."""
    def test_login_view_unauthenticated(self):
        """Test the login view handler with an unauthenticated session."""
        response = self.client.get(u'/login/')
        self.assert200(response)
        self.assert_template_used(u'user/login.html')

    def test_login_view_form_authenticated(self):
        """Test the login view handler with an authenticated session."""
        self.login()
        response = self.client.get(u'/login/')
        self.assertEquals(response.status_code, HTTP_STATUS_CODE_REDIRECT)

    def test_login_view_sso_authenticated(self):
        """Test the login view handler with an SSO authenticated session."""
        current_app.config[u'SSO_ENABLED'] = True
        with self.client:
            response = self.client.get(
                u'/login/', environ_base={u'REMOTE_USER': u'test1'})
            self.assertEqual(current_user.username, u'test1')
            self.assertEquals(response.status_code, HTTP_STATUS_CODE_REDIRECT)

    def test_logout_view(self):
        """Test the logout view handler."""
        self.login()
        response = self.client.get(u'/logout/')
        self.assertEquals(response.status_code, HTTP_STATUS_CODE_REDIRECT)
