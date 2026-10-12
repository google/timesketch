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
"""Tests for the Flask application factory."""

from unittest import mock

from timesketch.app import create_app
from timesketch.app import get_index_prefix_warning
from timesketch.lib.testlib import BaseTest
from timesketch.lib.testlib import TestConfig


class InvalidIndexPrefixConfig(TestConfig):
    """Test configuration with an invalid OpenSearch index prefix."""

    OPENSEARCH_INDEX_PREFIX = "Invalid Prefix"


class ValidIndexPrefixConfig(TestConfig):
    """Test configuration with a valid OpenSearch index prefix."""

    OPENSEARCH_INDEX_PREFIX = "timesketch-"


class CreateAppTest(BaseTest):
    """Tests for create_app."""

    def test_invalid_index_prefix(self):
        """Test that the app refuses to start with an invalid index prefix."""
        with mock.patch("timesketch.app.sys.stderr") as mock_stderr:
            with self.assertRaises(SystemExit):
                create_app(InvalidIndexPrefixConfig)
        self.assertIn("OPENSEARCH_INDEX_PREFIX", mock_stderr.write.call_args.args[0])

    def test_valid_index_prefix(self):
        """Test that the app starts with a valid index prefix."""
        app = create_app(ValidIndexPrefixConfig)
        self.assertEqual(app.config["OPENSEARCH_INDEX_PREFIX"], "timesketch-")


class IndexPrefixWarningTest(BaseTest):
    """Tests for get_index_prefix_warning."""

    def test_no_index_prefix(self):
        """Test that there is no warning and no query without a prefix."""
        with mock.patch("timesketch.app.SearchIndex") as mock_searchindex:
            self.assertEqual(get_index_prefix_warning(""), "")
            self.assertEqual(get_index_prefix_warning(None), "")
        mock_searchindex.query.filter.assert_not_called()

    def test_unprefixed_indices(self):
        """Test that search indices without the prefix are reported."""
        # The test database has the unprefixed indices "test" and "test2".
        self._create_searchindex(name="timesketch-0123", user=self.user1)
        warning = get_index_prefix_warning("timesketch-")
        self.assertIn("2 of 3 search indices", warning)
        self.assertIn("OPENSEARCH_INDEX_PREFIX 'timesketch-'", warning)

    def test_failed_indices_are_ignored(self):
        """Test that search indices that failed to be created are ignored."""
        self.searchindex.set_status("fail")
        self.searchindex2.set_status("fail")
        self.assertEqual(get_index_prefix_warning("timesketch-"), "")
