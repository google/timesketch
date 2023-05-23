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

    def test_valid_index_name(self):
        """Test valid index name."""
        valid_index_name = "a89933473b2a48948beee2c7e870209f"
        self.assertTrue(utils.is_valid_index_name(valid_index_name))

    def test_invalid_index_name(self):
        """Test invalid index name."""
        invalid_index_name = "/invalid/index/name"
        self.assertFalse(utils.is_valid_index_name(invalid_index_name))

    def test_invalid_upload_path(self):
        """Test invalid upload path.

        Resulting path should be a concatenation of the two paths anchored at the
        base path.
        """
        base_path = "/tmp"
        user_supplied_index_name = "/foo/bar/test.txt"
        expected_path = "/tmp/foo/bar/test.txt"
        resulting_path = utils.format_upload_path(base_path, user_supplied_index_name)
        self.assertEqual(resulting_path, expected_path)

    def test_valid_upload_path(self):
        """Test valid upload path.

        Resulting path should be a concatenation of the two paths anchored at the
        base path.
        """
        base_path = "/tmp"
        user_supplied_index_name = "a89933473b2a48948beee2c7e870209f"
        expected_path = "/tmp/a89933473b2a48948beee2c7e870209f"
        resulting_path = utils.format_upload_path(base_path, user_supplied_index_name)
        self.assertEqual(resulting_path, expected_path)

    def test_relative_base_upload_path(self):
        """Test invalid base upload path."""
        base_path = "tmp"
        user_supplied_index_name = "a89933473b2a48948beee2c7e870209f"
        with self.assertRaises(ValueError):
            utils.format_upload_path(base_path, user_supplied_index_name)
