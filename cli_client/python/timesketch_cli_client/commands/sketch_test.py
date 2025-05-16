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
"""Tests for sketch command."""

import unittest
import mock

from click.testing import CliRunner

from timesketch_api_client import test_lib as api_test_lib

from .. import test_lib
from .sketch import sketch_group


class SketchTest(unittest.TestCase):
    """Test Sketch."""

    @mock.patch("requests.Session", api_test_lib.mock_session)
    def setUp(self):
        """Setup test case."""
        self.ctx = test_lib.get_cli_context()

    def test_list_sketches(self):
        """Test the 'sketch list' command.

        Verifies that the command executes successfully and that the output
        contains the expected sketch information in text format.
        """
        runner = CliRunner()
        self.ctx.output_format_from_flag = "text"
        result = runner.invoke(sketch_group, ["list"], obj=self.ctx)
        self.assertIn("1 test", result.output)

    def test_describe_sketch(self):
        """Test the 'sketch describe' command.

        Verifies that the command executes successfully and that the output
        contains the expected sketch name and description in text format.
        """
        runner = CliRunner()
        self.ctx.output_format_from_flag = "text"
        result = runner.invoke(sketch_group, ["describe"], obj=self.ctx)
        self.assertIn("Name: test", result.output)
        self.assertIn("Description: test", result.output)
