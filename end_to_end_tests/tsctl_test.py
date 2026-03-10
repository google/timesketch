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

    def test_annotated_only_export(self):
        """Test filtering events by annotations (labels, stars, comments, tags)."""
        # 1. Setup: Create sketch and import data
        sketch = self.api.create_sketch(name=f"annotated-test-{uuid.uuid4().hex}")
        self.import_timeline("sigma_events.jsonl", sketch=sketch)

        # 2. Annotate some events
        # We'll use the API to star one event and comment on another
        search_res = sketch.explore(query_string="*", max_entries=10)
        events = search_res["hits"]["hits"]
        self.assertions.assertTrue(
            len(events) >= 2, "Not enough events to test annotations"
        )

        event1 = events[0]
        event2 = events[1]

        # Star event1
        sketch.label_events([event1], "__ts_star")
        # Comment on event2
        sketch.comment_event(
            event2["_id"], event2["_index"], "Forensic E2E Test Comment"
        )

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
            self.assertions.assertIn(
                "Filtering for annotated events only", result.output
            )

            # 4. Verify filtered data
            with zipfile.ZipFile(export_file, "r") as z:
                # Our export logic should have only 2 events in events.csv
                # (header + 2 rows)
                events_raw = z.read("events.csv").decode("utf-8")
                events_data = events_raw.strip().split("\n")
                # actual event rows (excluding header)
                event_count = len(events_data) - 1
                self.assertions.assertEqual(
                    event_count, 2, f"Expected 2 annotated events, got {event_count}"
                )

        finally:
            if os.path.exists(export_file):
                os.remove(export_file)

    def test_export_stories_as_markdown(self):
        """Test that sketch stories are correctly exported as Markdown files."""
        # 1. Setup
        sketch = self.api.create_sketch(name=f"story-test-{uuid.uuid4().hex}")
        story_title = "Forensic Investigation Story"
        story_content = "# Summary\nEvidence found of lateral movement."
        new_story = sketch.create_story(title=story_title)
        new_story.add_text(story_content)

        sketch_id = str(sketch.id)
        export_file = f"story_export_{sketch_id}.zip"

        try:
            # 2. Run export
            result = self.runner.invoke(
                cli, ["export-sketch", sketch_id, "--filename", export_file]
            )
            self.assertions.assertEqual(result.exit_code, 0)

            # 3. Verify story file in ZIP
            with zipfile.ZipFile(export_file, "r") as z:
                stories = [f for f in z.namelist() if f.startswith("stories/")]
                self.assertions.assertTrue(
                    len(stories) > 0, "No stories found in export archive"
                )

                # Check content of one story
                story_path = stories[0]
                content = z.read(story_path).decode("utf-8")
                self.assertions.assertIn(story_title, content)
                self.assertions.assertIn("Evidence found", content)

        finally:
            if os.path.exists(export_file):
                os.remove(export_file)


manager.EndToEndTestManager.register_test(TestTsctl)
