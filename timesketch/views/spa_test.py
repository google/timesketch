# Copyright 2026 Google Inc. All rights reserved.
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
"""Tests for the SPA views."""

from timesketch.lib.definitions import HTTP_STATUS_CODE_REDIRECT
from timesketch.lib.testlib import BaseTest


class SpaViewTest(BaseTest):
    """Test the SPA views."""

    def test_redirect_view(self):
        """Test redirecting old view URLs to the new scheme."""
        self.login()
        response = self.client.get("/sketch/1/explore/view/2/")
        self.assertEqual(response.status_code, HTTP_STATUS_CODE_REDIRECT)
        self.assertTrue(
            response.headers.get("Location").endswith("/sketch/1/explore?view=2")
        )
