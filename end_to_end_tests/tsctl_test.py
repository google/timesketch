# -*- coding: utf-8 -*-
# Copyright 2025 Google Inc. All rights reserved.
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

import json
import os

from click.testing import CliRunner
from timesketch.tsctl import cli
from . import interface
from . import manager


class TestTsctl(interface.BaseEndToEndTest):
    """Tests for tsctl commands."""

    NAME = "tsctl_test"

    def __init__(self):
        """Initialize the test class and the runner."""
        super().__init__()
        self.runner = CliRunner()

    def _create_group_sync_file(self, content):
        """Helper to create a temporary group sync file."""
        file_path = "groups.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(content, f)
        return file_path

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

    def test_sync_group_memberships_file_not_found(self):
        """Tests sync-groups-from-json with a non-existent file."""
        result = self.runner.invoke(cli, ["sync-groups-from-json", "nonexistent.json"])
        self.assertions.assertNotEqual(result.exit_code, 0)
        self.assertions.assertIn("Error: File not found", result.output)

    def test_sync_group_memberships_invalid_json(self):
        """Tests sync-groups-from-json with an invalid JSON file."""
        file_path = "invalid.json"
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("{'invalid_json':}")
            result = self.runner.invoke(cli, ["sync-groups-from-json", file_path])
            self.assertions.assertNotEqual(result.exit_code, 0)
            self.assertions.assertIn("Error: Invalid JSON file", result.output)
        finally:
            os.remove(file_path)

    def test_sync_groups_dry_run(self):
        """Tests sync-groups-from-json with --dry-run."""
        group_data = {"new_group": ["user1", "user2"]}
        file_path = self._create_group_sync_file(group_data)

        try:
            result = self.runner.invoke(
                cli, ["sync-groups-from-json", file_path, "--dry-run"]
            )
            self.assertions.assertEqual(
                result.exit_code, 0, f"CLI Error: {result.output}"
            )
            self.assertions.assertIn("[DRY-RUN]", result.output)
            self.assertions.assertIn("Would create group new_group", result.output)
            self.assertions.assertIn("Would create user 'user1'", result.output)
            self.assertions.assertIn("No changes committed", result.output)
        finally:
            os.remove(file_path)

    def test_sync_groups_full_run(self):
        """Tests the full sync-groups-from-json command."""
        # 1. Initial setup: Create a new group with one user
        group_data = {"test_sync_group": ["user_a"]}
        file_path = self._create_group_sync_file(group_data)
        result = self.runner.invoke(cli, ["sync-groups-from-json", file_path])
        self.assertions.assertEqual(result.exit_code, 0, f"CLI Error: {result.output}")
        self.assertions.assertIn("Creating new group: 'test_sync_group'", result.output)
        self.assertions.assertIn("Creating new user: 'user_a'", result.output)
        self.assertions.assertIn(
            "Adding user 'user_a' to group 'test_sync_group'", result.output
        )
        self.assertions.assertIn("Sync complete", result.output)

        # 2. Update: Add a user, remove a user
        group_data = {"test_sync_group": ["user_b"]}
        file_path = self._create_group_sync_file(group_data)
        result = self.runner.invoke(cli, ["sync-groups-from-json", file_path])
        self.assertions.assertEqual(result.exit_code, 0, f"CLI Error: {result.output}")
        self.assertions.assertIn("Creating new user: 'user_b'", result.output)
        self.assertions.assertIn(
            "Adding user 'user_b' to group 'test_sync_group'", result.output
        )
        self.assertions.assertIn(
            "Removing user 'user_a' from group 'test_sync_group'", result.output
        )
        self.assertions.assertIn("Sync complete", result.output)

        # 3. Cleanup: Check ignored groups
        self.runner.invoke(cli, ["create-group", "unmanaged_group"])
        group_data = {"test_sync_group": []}
        file_path = self._create_group_sync_file(group_data)
        result = self.runner.invoke(cli, ["sync-groups-from-json", file_path])
        self.assertions.assertEqual(result.exit_code, 0, f"CLI Error: {result.output}")
        self.assertions.assertIn(
            "Removing user 'user_b' from group 'test_sync_group'", result.output
        )
        self.assertions.assertIn("unmanaged_group", result.output)

        os.remove(file_path)


manager.EndToEndTestManager.register_test(TestTsctl)
