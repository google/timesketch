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
"""Tests for the home view."""

from timesketch.lib.testlib import BaseTest


class HomeViewTest(BaseTest):
    """Class for the view handler tests."""
    resource_url = u'/'

    def test_home_view(self):
        """Test the home view handler."""
        self.login()
        response = self.client.get(self.resource_url)
        self.assert200(response)
        self.assert_template_used(u'home/home.html')
