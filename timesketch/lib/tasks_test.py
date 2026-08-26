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
"""Tests for celery tasks."""

from unittest import mock

from timesketch.lib import tasks
from timesketch.lib.testlib import BaseTest


class TestTasks(BaseTest):
    """Tests for the tasks module."""

    def test_plaso_minimum_version_constant(self):
        """Test the PLASO_MINIMUM_VERSION constant."""
        self.assertEqual(tasks.PLASO_MINIMUM_VERSION, 20260720)

    @mock.patch("timesketch.lib.tasks.plaso", None)
    def test_run_plaso_not_installed_with_sketch(self):
        """Test run_plaso error contains sketch info when plaso is not installed."""
        with self.assertRaises(RuntimeError) as context:
            tasks.run_plaso(
                file_path="/tmp/fake.plaso",
                events="",
                timeline_name="test_timeline",
                index_name="test_index",
                source_type="plaso",
                timeline_id=self.timeline.id,
            )
        self.assertIn("Plaso isn't installed", str(context.exception))
        self.assertIn(f"[Sketch ID: {self.sketch1.id}]", str(context.exception))

    @mock.patch("timesketch.lib.tasks.plaso", None)
    def test_run_plaso_not_installed_without_sketch(self):
        """Test run_plaso error when plaso is not installed and timeline not found."""
        with self.assertRaises(RuntimeError) as context:
            tasks.run_plaso(
                file_path="/tmp/fake.plaso",
                events="",
                timeline_name="test_timeline",
                index_name="test_index",
                source_type="plaso",
                timeline_id=99999,
            )
        self.assertIn("Plaso isn't installed", str(context.exception))
        self.assertNotIn("[Sketch ID:", str(context.exception))

    def test_run_plaso_outdated_version_with_sketch(self):
        """Test run_plaso error contains sketch info for outdated plaso version."""
        mock_plaso = mock.MagicMock()
        mock_plaso.__version__ = "20260512"

        with mock.patch("timesketch.lib.tasks.plaso", mock_plaso):
            with self.assertRaises(RuntimeError) as context:
                tasks.run_plaso(
                    file_path="/tmp/fake.plaso",
                    events="",
                    timeline_name="test_timeline",
                    index_name="test_index",
                    source_type="plaso",
                    timeline_id=self.timeline.id,
                )
            self.assertIn("Plaso version is out of date", str(context.exception))
            self.assertIn("installed version: 20260512", str(context.exception))
            self.assertIn("20260720", str(context.exception))
            self.assertIn(f"[Sketch ID: {self.sketch1.id}]", str(context.exception))

    def test_run_plaso_outdated_version_without_sketch(self):
        """Test run_plaso error without sketch info when timeline is not found."""
        mock_plaso = mock.MagicMock()
        mock_plaso.__version__ = "20260512"

        with mock.patch("timesketch.lib.tasks.plaso", mock_plaso):
            with self.assertRaises(RuntimeError) as context:
                tasks.run_plaso(
                    file_path="/tmp/fake.plaso",
                    events="",
                    timeline_name="test_timeline",
                    index_name="test_index",
                    source_type="plaso",
                    timeline_id=99999,
                )
            self.assertIn("Plaso version is out of date", str(context.exception))
            self.assertIn("installed version: 20260512", str(context.exception))
            self.assertIn("20260720", str(context.exception))
            self.assertNotIn("[Sketch ID:", str(context.exception))

    def test_run_plaso_with_events_raises(self):
        """Test run_plaso raises RuntimeError when events string is provided."""
        mock_plaso = mock.MagicMock()
        mock_plaso.__version__ = "20260720"

        with mock.patch("timesketch.lib.tasks.plaso", mock_plaso):
            with self.assertRaises(RuntimeError) as context:
                tasks.run_plaso(
                    file_path="/tmp/fake.plaso",
                    events="some,events,data",
                    timeline_name="test_timeline",
                    index_name="test_index",
                    source_type="plaso",
                    timeline_id=self.timeline.id,
                )
            self.assertIn(
                "Plaso uploads need a file, not events", str(context.exception)
            )
