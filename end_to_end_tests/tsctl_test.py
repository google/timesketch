# -*- coding: utf-8 -*-
# Copyright 2024 Google Inc. All rights reserved.
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
"""Tests for tsctl command-line tool."""

from click.testing import CliRunner
from . import interface
from . import manager

from timesketch.tsctl import cli


class TestTsctl(interface.BaseEndToEndTest):  # Or inherit from BaseTest if applicable
    """Tests for tsctl commands."""

    NAME = "tsctl_test"

    def __init__(self):
        """Initialize the test class and the runner."""
        super().__init__()
        self.runner = CliRunner()

    def test_version_command(self):
        """Tests the 'tsctl version' command."""
        # Invoke 'tsctl version'
        result = self.runner.invoke(cli, ["version"])

        # Assertions
        self.assertions.assertEqual(result.exit_code, 0, f"CLI Error: {result.output}")
        self.assertions.assertIn("Timesketch version:", result.output)

    def test_list_users_command(self):
        """Tests the 'tsctl list-users' command."""
        # Invoke 'tsctl list-users'
        result = self.runner.invoke(cli, ["list-users"])

        self.assertions.assertEqual(result.exit_code, 0, f"CLI Error: {result.output}")
        self.assertions.assertIn(interface.USERNAME, result.output)

    def test_list_users_status_command(self):
        """Tests the 'tsctl list-users --status' command."""
        # Invoke 'tsctl list-users --status'
        result = self.runner.invoke(cli, ["list-users", "--status"])

        # Assertions
        self.assertions.assertEqual(result.exit_code, 0, f"CLI Error: {result.output}")
        self.assertions.assertIn(interface.USERNAME, result.output)
        # Check for the status indicator (active: True/False)
        self.assertions.assertIn("active: True)", result.output)

    def test_list_config_command(self):
        """Tests the 'tsctl list-config' command."""
        result = self.runner.invoke(cli, ["list-config"])

        # Use assertEqual for the exit code check
        self.assertions.assertEqual(result.exit_code, 0, f"CLI Error: {result.output}")

        # Use assertIn for checking substrings in the output
        self.assertions.assertIn("Timesketch Configuration Variables:", result.output)
        # Check for a known non-sensitive key
        self.assertions.assertIn("UPLOAD_ENABLED", result.output)
        # Check that a known sensitive key is redacted
        self.assertions.assertIn("SECRET_KEY", result.output)
        self.assertions.assertIn("******** (redacted)", result.output)


manager.EndToEndTestManager.register_test(TestTsctl)
