# Copyright 2021 Google Inc. All rights reserved.
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
"""Tests for search command."""

import unittest
import mock

from click.testing import CliRunner

from timesketch_api_client import test_lib as api_test_lib

from .. import test_lib
from .search import saved_searches_group


EXPECTED_OUTPUT = """query_string: test:"foobar"
query_filter: {
  "size": 10000,
  "terminate_after": 10000,
  "indices": "_all",
  "order": "asc",
  "chips": []
}
"""


class SearchTest(unittest.TestCase):
    """Test Search."""

    @mock.patch('requests.Session', api_test_lib.mock_session)
    def setUp(self):
        """Setup test case."""
        self.ctx = test_lib.get_cli_context()

    def test_list_saved_searches(self):
        """Test to list saved searches."""
        runner = CliRunner()
        result = runner.invoke(saved_searches_group, ['list'], obj=self.ctx)
        assert result.output == '1 test\n2 more test\n'

    def test_describe_saved_search(self):
        """Test to get details for a saved search."""
        runner = CliRunner()
        result = runner.invoke(
            saved_searches_group, ['describe', '1'], obj=self.ctx)
        assert result.output == EXPECTED_OUTPUT
