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
from timesketch_cli_client import test_lib
from timesketch_cli_client.commands.config import config_group


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
        result = runner.invoke(
            config_group, ["set", "output-format", "csv"], obj=self.ctx
        )
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(self.ctx.config_assistant.get_config("output_format"), "csv")

    @mock.patch("requests.Session", api_test_lib.mock_session)
    def test_set_output_invalid(self):
        """Test the 'config set output' command with invalid format."""
        runner = CliRunner()
        result = runner.invoke(
            config_group, ["set", "output", "invalid_format"], obj=self.ctx
        )
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("Unsupported format", result.output)

    @mock.patch("requests.Session", api_test_lib.mock_session)
    def test_set_sketch(self):
        """Test the 'config set sketch' command."""
        runner = CliRunner()
        result = runner.invoke(config_group, ["set", "sketch", "42"], obj=self.ctx)
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(self.ctx.config_assistant.get_config("sketch"), 42)

    @mock.patch("requests.Session", api_test_lib.mock_session)
    def test_set_sketch_invalid(self):
        """Test the 'config set sketch' command with non-digit ID."""
        runner = CliRunner()
        result = runner.invoke(
            config_group, ["set", "sketch", "invalid_id"], obj=self.ctx
        )
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("Sketch ID must be an integer", result.output)

    @mock.patch("requests.Session", api_test_lib.mock_session)
    def test_get_sketch(self):
        """Test the 'config get sketch' command."""
        runner = CliRunner()
        result = runner.invoke(config_group, ["get", "sketch"], obj=self.ctx)
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(result.output.strip(), "1")

    @mock.patch("requests.Session", api_test_lib.mock_session)
    def test_get_sketch_missing(self):
        """Test 'config get sketch' when sketch is missing in config."""
        ctx = test_lib.get_cli_context_no_output()
        runner = CliRunner()
        with mock.patch.object(
            ctx.config_assistant, "get_config", side_effect=KeyError("sketch")
        ):
            result = runner.invoke(config_group, ["get", "sketch"], obj=ctx)
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn(
            "No such configuration parameter: sketch (error: 'sketch')", result.output
        )

    @mock.patch("requests.Session", api_test_lib.mock_session)
    def test_get_output(self):
        """Test the 'config get output' command."""
        runner = CliRunner()
        result = runner.invoke(config_group, ["get", "output"], obj=self.ctx)
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(result.output.strip(), "tabular")

    @mock.patch("requests.Session", api_test_lib.mock_session)
    def test_get_output_format(self):
        """Test the 'config get output-format' command."""
        runner = CliRunner()
        result = runner.invoke(config_group, ["get", "output-format"], obj=self.ctx)
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(result.output.strip(), "tabular")

    @mock.patch("requests.Session", api_test_lib.mock_session)
    def test_get_output_missing(self):
        """Test 'config get output' when output format is missing in config."""
        ctx = test_lib.get_cli_context_no_output()
        runner = CliRunner()
        result = runner.invoke(config_group, ["get", "output"], obj=ctx)
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn(
            "No such configuration parameter: output_format (error: 'output_format')",
            result.output,
        )

    @mock.patch("requests.Session", api_test_lib.mock_session)
    def test_custom_config_section(self):
        """Test the TimesketchCli loads a custom config section."""
        import tempfile
        from timesketch_cli_client.cli import TimesketchCli
        
        custom_config = """
[timesketch]
host_uri = http://127.0.0.1
username = default_user

[custom_section]
host_uri = http://custom.example.com
username = custom_user

[cli]
output_format = tabular
"""
        with tempfile.NamedTemporaryFile(mode="w") as fw:
            fw.write(custom_config)
            fw.seek(0)
            
            cli_context = TimesketchCli(
                api_client=None,
                conf_file=fw.name,
                config_section="custom_section"
            )
            
            self.assertEqual(
                cli_context.config_assistant.get_config("host_uri"),
                "http://custom.example.com"
            )
            self.assertEqual(
                cli_context.config_assistant.get_config("username"),
                "custom_user"
            )
