# Copyright 2022 Google Inc. All rights reserved.
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
"""Tests for API utils."""
from timesketch.api.v1 import utils
from timesketch.lib.testlib import BaseTest


class TestApiUtils(BaseTest):
    """Tests for the functionality of the API utils."""

    def test_escape_query_string(self):
        """Test escaping a search query string."""
        query_string_to_test = r"/foo/bar/test.txt c:\foo\bar"
        expected_output = r"\/foo\/bar\/test\.txt c:\\foo\\bar"
        escaped_query_string = utils.escape_query_string(query_string_to_test)
        self.assertEqual(escaped_query_string, expected_output)
