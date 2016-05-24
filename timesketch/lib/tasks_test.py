# Copyright 2014 Google Inc. All rights reserved.
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
"""Tests for tasks."""

from flask import current_app

from timesketch.lib.testlib import BaseTest
from timesketch.lib.tasks import get_data_location


class TestTasks(BaseTest):
    """Tests for the functionality on the tasks module."""
    def test_get_data_location(self):
        """Test to get data_location path."""
        current_app.config[u'PLASO_DATA_LOCATION'] = u'/tmp'
        data_location_exists = get_data_location()
        self.assertEqual(u'/tmp', data_location_exists)
