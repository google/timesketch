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
import uuid
import zipfile
import time
import pandas as pd

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

    def _wait_for_events(self, sketch, expected_count):
        """Wait for events to be indexed."""
        for _ in range(30):
            res = sketch.explore(
                query_string="*", max_entries=expected_count, as_pandas=True
            )
            if isinstance(res, list):
                res = res[0]

            if isinstance(res, pd.DataFrame):
                if len(res) >= expected_count:
                    return True
            time.sleep(2)
        return False

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
        unique_group = f"group-{uuid.uuid4().hex}"
        user_a = f"user-{uuid.uuid4().hex}"
        user_b = f"user-{uuid.uuid4().hex}"

        group_data = {unique_group: [user_a]}
        file_path = self._create_group_sync_file(group_data)
        result = self.runner.invoke(cli, ["sync-groups-from-json", file_path])
        self.assertions.assertEqual(result.exit_code, 0, f"CLI Error: {result.output}")
        self.assertions.assertIn(f"Creating new group: '{unique_group}'", result.output)
        self.assertions.assertIn(f"Creating new user: '{user_a}'", result.output)
        self.assertions.assertIn(
            f"Adding user '{user_a}' to group '{unique_group}'", result.output
        )
        self.assertions.assertIn("Sync complete", result.output)

        # 2. Update: Add a user, remove a user
        group_data = {unique_group: [user_b]}
        file_path = self._create_group_sync_file(group_data)
        result = self.runner.invoke(cli, ["sync-groups-from-json", file_path])
        self.assertions.assertEqual(result.exit_code, 0, f"CLI Error: {result.output}")
        self.assertions.assertIn(f"Creating new user: '{user_b}'", result.output)
        self.assertions.assertIn(
            f"Adding user '{user_b}' to group '{unique_group}'", result.output
        )
        self.assertions.assertIn(
            f"Removing user '{user_a}' from group '{unique_group}'", result.output
        )
        self.assertions.assertIn("Sync complete", result.output)

        # 3. Cleanup: Check ignored groups
        self.runner.invoke(cli, ["create-group", "unmanaged_group"])
        group_data = {unique_group: []}
        file_path = self._create_group_sync_file(group_data)
        result = self.runner.invoke(cli, ["sync-groups-from-json", file_path])
        self.assertions.assertEqual(result.exit_code, 0, f"CLI Error: {result.output}")
        self.assertions.assertIn(
            f"Removing user '{user_b}' from group '{unique_group}'", result.output
        )
        self.assertions.assertIn("unmanaged_group", result.output)

        os.remove(file_path)

    def test_export_sketch_api_method(self):
        """Tests the 'tsctl export-sketch' command using the API method."""
        # 1. Import a small timeline to ensure we have events to export
        self.import_timeline("sigma_events.csv")

        # 2. Invoke 'tsctl export-sketch'
        # We use the sketch created by the base class
        sketch_id = str(self.sketch.id)
        output_filename = f"sketch_{sketch_id}_csv_export.zip"

        try:
            result = self.runner.invoke(cli, ["export-sketch", sketch_id])

            # 3. Assertions on command execution
            self.assertions.assertEqual(
                result.exit_code, 0, f"CLI Error: {result.output}"
            )
            self.assertions.assertIn(
                f"Starting API export of Sketch [{sketch_id}]", result.output
            )
            self.assertions.assertIn("Sketch exported successfully", result.output)

            # 4. Verify the export file exists and contains expected files
            self.assertions.assertTrue(
                os.path.exists(output_filename), "Export ZIP file not found"
            )

        finally:
            if os.path.exists(output_filename):
                os.remove(output_filename)

    def test_export_sketch_direct_method(self):
        """Test high-speed direct export method and forensic manifest."""
        # 1. Setup: Create sketch and import data
        sketch_name = f"forensic-export-{uuid.uuid4().hex}"
        sketch = self.api.create_sketch(name=sketch_name)
        self.import_timeline("sigma_events.jsonl", sketch=sketch)

        sketch_id = str(sketch.id)
        export_file = f"forensic_direct_{sketch_id}.zip"

        try:
            # 2. Run export-sketch with --method direct
            result = self.runner.invoke(
                cli,
                [
                    "export-sketch",
                    sketch_id,
                    "--method",
                    "direct",
                    "--filename",
                    export_file,
                ],
            )
            self.assertions.assertEqual(
                result.exit_code, 0, f"CLI Error: {result.output}"
            )
            self.assertions.assertIn(
                f"Starting DIRECT export of Sketch [{sketch_id}]", result.output
            )
            self.assertions.assertIn("Sketch exported successfully", result.output)

            # 3. Verify Forensic Integrity
            with zipfile.ZipFile(export_file, "r") as z:
                file_list = z.namelist()
                self.assertions.assertIn("manifest.txt", file_list)
                self.assertions.assertIn("metadata.json", file_list)
                self.assertions.assertIn("events.jsonl", file_list)

                # Check if mappings folder exists and has at least one file
                mappings = [f for f in file_list if f.startswith("mappings/")]
                self.assertions.assertTrue(
                    len(mappings) > 0, "No index mappings found in export"
                )

                # Verify manifest content
                manifest_content = z.read("manifest.txt").decode("utf-8")
                self.assertions.assertIn("File Hashes (SHA256):", manifest_content)
                self.assertions.assertIn("events.jsonl", manifest_content)

        finally:
            if os.path.exists(export_file):
                os.remove(export_file)

    def test_tsctl_multi_line_csv_count(self):
        """Reproduce and verify the fix for multi-line CSV over-counting in tsctl."""
        # 1. Setup: Create a sketch and add 3 events with newlines
        sketch_name = f"multi-line-test-{uuid.uuid4().hex}"
        sketch = self.api.create_sketch(name=sketch_name)

        for i in range(3):
            sketch.add_event(
                message=f"Event {i}\nLine 2\nLine 3",
                date="2026-03-10T12:00:00",
                timestamp_desc="Multi-line Event",
            )

        # Wait for indexing
        self.assertions.assertTrue(self._wait_for_events(sketch, 3))

        sketch_id = str(sketch.id)

        # 2. Run tsctl export-sketch
        result = self.runner.invoke(cli, ["export-sketch", sketch_id])
        self.assertions.assertEqual(result.exit_code, 0)

        # 3. Verify the output count in the console
        self.assertions.assertIn("3/3", result.output)
        self.assertions.assertNotIn("WARNING: Event count mismatch!", result.output)

    def test_tsctl_annotated_only_export(self):
        """Test tsctl filtering events by annotations."""
        # 1. Setup: Create sketch and import data
        sketch = self.api.create_sketch(name=f"annotated-test-{uuid.uuid4().hex}")
        self.import_timeline("sigma_events.jsonl", sketch=sketch)

        # Wait for import
        self.assertions.assertTrue(self._wait_for_events(sketch, 1))

        # 2. Annotate some events
        df = sketch.explore(query_string="*", max_entries=10, as_pandas=True)
        if isinstance(df, list):
            df = df[0]

        self.assertions.assertTrue(len(df) >= 2)

        # Star first event
        event1_id = df.iloc[0]["_id"]
        event1_index = df.iloc[0]["_index"]
        sketch.label_events([{"_id": event1_id, "_index": event1_index}], "__ts_star")

        # Comment on second event
        event2_id = df.iloc[1]["_id"]
        event2_index = df.iloc[1]["_index"]
        sketch.comment_event(event2_id, event2_index, "Forensic E2E Test Comment")

        # Wait for annotations to be searchable
        time.sleep(5)

        sketch_id = str(sketch.id)
        export_file = f"annotated_only_{sketch_id}.zip"

        try:
            # 3. Run export-sketch with --annotated-only
            result = self.runner.invoke(
                cli,
                [
                    "export-sketch",
                    sketch_id,
                    "--annotated-only",
                    "--filename",
                    export_file,
                ],
            )
            self.assertions.assertEqual(
                result.exit_code, 0, f"CLI Error: {result.output}"
            )
            # The refactored code prints processing status
            self.assertions.assertIn(
                "Processing comments for 2 event(s)...", result.output
            )

            # 4. Verify filtered data
            with zipfile.ZipFile(export_file, "r") as z:
                csv_files = [f for f in z.namelist() if f.endswith(".csv")]
                self.assertions.assertTrue(len(csv_files) > 0)

                import csv
                import io

                content = z.read(csv_files[0]).decode("utf-8")
                reader = csv.reader(io.StringIO(content))
                rows = list(reader)
                # actual event rows (excluding header)
                event_count = len(rows) - 1
                self.assertions.assertEqual(
                    event_count, 2, f"Expected 2 annotated events, got {event_count}"
                )

        finally:
            if os.path.exists(export_file):
                os.remove(export_file)

    def test_tsctl_export_api_jsonl(self):
        """Test API-based export using JSONL format."""
        sketch = self.api.create_sketch(name=f"api-jsonl-{uuid.uuid4().hex}")
        sketch.add_event(
            message="JSONL API Test", date="2026-03-10T12:00:00", timestamp_desc="Test"
        )

        # Wait for indexing
        self.assertions.assertTrue(self._wait_for_events(sketch, 1))

        sketch_id = str(sketch.id)
        export_file = f"api_jsonl_{sketch_id}.zip"

        try:
            result = self.runner.invoke(
                cli,
                [
                    "export-sketch",
                    sketch_id,
                    "--method",
                    "api",
                    "--output-format",
                    "jsonl",
                    "--filename",
                    export_file,
                ],
            )
            self.assertions.assertEqual(result.exit_code, 0)
            self.assertions.assertIn("Starting API export", result.output)

            with zipfile.ZipFile(export_file, "r") as z:
                self.assertions.assertIn("events.jsonl", z.namelist())
                content = z.read("events.jsonl").decode("utf-8").strip().split("\n")
                self.assertions.assertEqual(len(content), 1)
        finally:
            if os.path.exists(export_file):
                os.remove(export_file)

    def test_tsctl_annotated_only_zero_results(self):
        """Test tsctl export with --annotated-only when NO events are annotated."""
        # 1. Setup: Create sketch and import data, but don't annotate anything
        sketch = self.api.create_sketch(name=f"no-annotations-{uuid.uuid4().hex}")
        self.import_timeline("sigma_events.jsonl", sketch=sketch)

        # Wait for import
        self.assertions.assertTrue(self._wait_for_events(sketch, 1))

        sketch_id = str(sketch.id)
        export_file = f"empty_annotated_{sketch_id}.zip"

        try:
            # 2. Run export-sketch with --annotated-only
            result = self.runner.invoke(
                cli,
                [
                    "export-sketch",
                    sketch_id,
                    "--annotated-only",
                    "--filename",
                    export_file,
                ],
            )
            self.assertions.assertEqual(result.exit_code, 0)
            self.assertions.assertIn("Total events expected: 0", result.output)

            # 3. Verify filtered data (should only have header)
            with zipfile.ZipFile(export_file, "r") as z:
                csv_files = [f for f in z.namelist() if f.endswith(".csv")]
                self.assertions.assertTrue(len(csv_files) > 0)

                content = z.read(csv_files[0]).decode("utf-8").strip().split("\n")
                # Only header should exist
                event_count = len(content) - 1
                self.assertions.assertEqual(
                    event_count, 0, f"Expected 0 events, got {event_count}"
                )
        finally:
            if os.path.exists(export_file):
                os.remove(export_file)


manager.EndToEndTestManager.register_test(TestTsctl)
