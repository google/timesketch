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

from timesketch.lib.testlib import BaseTest


class UserViewTest(BaseTest):
    """Test the user view."""
    def test_login_view(self):
        """Test the login view handler."""
        self.login()
        response = self.client.get('/login/')
        self.assert200(response)
        self.assert_template_used('user/login.html')

    def test_logout_view(self):
        """Test the logout view handler."""
        self.login()
        response = self.client.get('/logout/')
        self.assertEquals(response.status_code, 302)
