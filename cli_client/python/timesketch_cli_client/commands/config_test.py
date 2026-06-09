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
"""Tests for config command."""

import unittest
import mock

from click.testing import CliRunner

from timesketch_api_client import test_lib as api_test_lib
from .. import test_lib
from .config import config_group


class ConfigTest(unittest.TestCase):
    """Test Config."""

    @mock.patch("requests.Session", api_test_lib.mock_session)
    def setUp(self):
        """Setup test case."""
        self.ctx = test_lib.get_cli_context()

    @mock.patch("requests.Session", api_test_lib.mock_session)
    def test_set_output(self):
        """Test the 'config set output' command."""
        runner = CliRunner()
        result = runner.invoke(config_group, ["set", "output", "json"], obj=self.ctx)
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(self.ctx.config_assistant.get_config("output_format"), "json")

    @mock.patch("requests.Session", api_test_lib.mock_session)
    def test_set_output_format(self):
        """Test the 'config set output-format' command."""
        runner = CliRunner()
        result = runner.invoke(config_group, ["set", "output-format", "csv"], obj=self.ctx)
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(self.ctx.config_assistant.get_config("output_format"), "csv")

    @mock.patch("requests.Session", api_test_lib.mock_session)
    def test_set_output_invalid(self):
        """Test the 'config set output' command with invalid format."""
        runner = CliRunner()
        result = runner.invoke(config_group, ["set", "output", "invalid_format"], obj=self.ctx)
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("Unsupported format", result.output)
