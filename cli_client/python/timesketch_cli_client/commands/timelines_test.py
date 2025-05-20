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
"""Tests for timelines command."""

import unittest
import mock

from click.testing import CliRunner

from timesketch_api_client import test_lib as api_test_lib

from .. import test_lib
from .timelines import timelines_group


class TimelinesTest(unittest.TestCase):
    """Test Timelines."""

    @mock.patch("requests.Session", api_test_lib.mock_session)
    def setUp(self):
        """Setup test case."""
        self.ctx = test_lib.get_cli_context()

    def test_list_timelines(self):
        """Test to list timelines."""
        runner = CliRunner()
        result = runner.invoke(timelines_group, ["list"], obj=self.ctx)
        assert "1 test" in result.output
        assert "2 test\n" in result.output

    def test_describe_timeline(self):
        """Test to get detail for a timeline."""
        runner = CliRunner()
        result = runner.invoke(timelines_group, ["describe", "1"], obj=self.ctx)
        assert "Name: test" in result.output
        assert "Index: test" in result.output
        assert "Event count: 0" in result.output
