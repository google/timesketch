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

import os
import zipfile
import json
import csv
from click.testing import CliRunner
from timesketch.tsctl import cli
from . import interface
from . import manager


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

    def test_export_sketch_command(self):
        """Tests the 'tsctl export-sketch' command."""
        # Ensure the default sketch for the test has some data
        # Using 'sigma_events.csv' which is known to have 4 events + header
        self.import_timeline("sigma_events.csv")

        sketch_id = self.sketch.id
        sketch_name = self.sketch.name
        output_filename = f"test_sketch_{sketch_id}_export.zip"

        # Invoke 'tsctl export-sketch <sketch_id> --filename <output_filename>'
        result = self.runner.invoke(
            cli, ["export-sketch", str(sketch_id), "--filename", output_filename]
        )

        # Assertions for command execution
        self.assertions.assertEqual(result.exit_code, 0, f"CLI Error: {result.output}")
        self.assertions.assertTrue(
            os.path.exists(output_filename), f"Export file {output_filename} not found"
        )

        # Assertions for zip file content
        with zipfile.ZipFile(output_filename, "r") as zipf:
            self.assertions.assertIn("metadata.json", zipf.namelist())
            self.assertions.assertIn("events.csv", zipf.namelist())

            with zipf.open("metadata.json") as meta_file:
                metadata = json.load(meta_file)
                self.assertions.assertEqual(metadata.get("sketch_id"), sketch_id)
                self.assertions.assertEqual(metadata.get("name"), sketch_name)

            with zipf.open("events.csv") as events_file:
                # Read CSV content (decode bytes to string for csv.reader)
                csv_content = events_file.read().decode("utf-8")
                reader = csv.reader(csv_content.splitlines())
                rows = list(reader)
                self.assertions.assertEqual(len(rows), 5)  # 1 header + 4 events

        # Clean up
        if os.path.exists(output_filename):
            os.remove(output_filename)


manager.EndToEndTestManager.register_test(TestTsctl)
