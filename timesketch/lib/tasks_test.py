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
from timesketch.models import db_session
from timesketch.models.sketch import DataSource, SearchIndex

_CREATE_STORAGE_READER = (
    "timesketch.lib.tasks.plaso_storage_factory.StorageFactory."
    "CreateStorageReaderForFile"
)


class TestTasks(BaseTest):
    """Tests for the tasks module."""

    def test_plaso_minimum_version_constant(self):
        """Test the PLASO_MINIMUM_VERSION constant."""
        self.assertEqual(tasks.PLASO_MINIMUM_VERSION, 20260720)

    @mock.patch("timesketch.lib.tasks.plaso", None)
    def test_run_plaso_not_installed_with_sketch(self):
        """Test run_plaso error contains sketch info when plaso is not installed."""
        file_path = "/tmp/fake_not_installed.plaso"
        datasource = DataSource(
            timeline=self.timeline,
            user=self.user1,
            file_on_disk=file_path,
            original_filename="fake_not_installed.plaso",
        )
        db_session.add(datasource)
        db_session.commit()

        with self.assertRaises(RuntimeError) as context:
            tasks.run_plaso(
                file_path=file_path,
                events="",
                timeline_name="test_timeline",
                index_name="test_index",
                source_type="plaso",
                timeline_id=self.timeline.id,
            )
        self.assertIn("Plaso isn't installed", str(context.exception))
        self.assertIn(f"[Sketch ID: {self.sketch1.id}]", str(context.exception))
        self.assertEqual(datasource.status[0].status, "fail")
        self.assertIn("Plaso isn't installed", datasource.error_message)

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

        file_path = "/tmp/fake_outdated.plaso"
        datasource = DataSource(
            timeline=self.timeline,
            user=self.user1,
            file_on_disk=file_path,
            original_filename="fake_outdated.plaso",
        )
        db_session.add(datasource)
        db_session.commit()

        with mock.patch("timesketch.lib.tasks.plaso", mock_plaso):
            with self.assertRaises(RuntimeError) as context:
                tasks.run_plaso(
                    file_path=file_path,
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
            self.assertEqual(datasource.status[0].status, "fail")
            self.assertIn("Plaso version is out of date", datasource.error_message)

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

    @mock.patch(_CREATE_STORAGE_READER)
    def test_run_plaso_storage_reader_none_raises(self, mock_create_reader):
        """Test run_plaso raises RuntimeError when storage reader is None."""
        mock_plaso = mock.MagicMock()
        mock_plaso.__version__ = "20260720"
        mock_create_reader.return_value = None

        file_path = "/tmp/reader_none.plaso"
        datasource = DataSource(
            timeline=self.timeline,
            user=self.user1,
            file_on_disk=file_path,
            original_filename="reader_none.plaso",
        )
        db_session.add(datasource)
        db_session.commit()

        with mock.patch("timesketch.lib.tasks.plaso", mock_plaso):
            with self.assertRaises(RuntimeError) as context:
                tasks.run_plaso(
                    file_path=file_path,
                    events="",
                    timeline_name="test_timeline",
                    index_name="test_index",
                    source_type="plaso",
                    timeline_id=self.timeline.id,
                )
            self.assertIn("Unable to open Plaso storage reader", str(context.exception))
            self.assertEqual(datasource.status[0].status, "fail")

    def test_set_datasource_status_success(self):
        """Test _set_datasource_status successfully updates status and error msg."""
        datasource = DataSource(
            timeline=self.timeline,
            user=self.user1,
            file_on_disk="/tmp/status_test.plaso",
            original_filename="status_test.plaso",
        )
        db_session.add(datasource)
        db_session.commit()

        tasks._set_datasource_status(  # pylint: disable=protected-access
            self.timeline.id,
            "/tmp/status_test.plaso",
            "fail",
            error_message="Test error message",
        )
        self.assertEqual(datasource.status[0].status, "fail")
        self.assertEqual(datasource.error_message, "Test error message")
        self.assertEqual(self.timeline.status[0].status, "fail")

    def test_set_datasource_status_missing_timeline(self):
        """Test _set_datasource_status gracefully returns when timeline is missing."""
        # Should not raise exception
        tasks._set_datasource_status(  # pylint: disable=protected-access
            99999, "/tmp/missing.plaso", "fail", error_message="Error"
        )

    def test_set_datasource_status_missing_datasource(self):
        """Test _set_datasource_status updates timeline status without datasource."""
        tasks._set_datasource_status(  # pylint: disable=protected-access
            self.timeline.id, "/tmp/nonexistent.plaso", "fail", error_message="Error"
        )
        self.assertEqual(self.timeline.status[0].status, "fail")

    def test_set_datasource_total_events_with_int(self):
        """Test _set_datasource_total_events with an integer value."""
        datasource = DataSource(
            timeline=self.timeline,
            user=self.user1,
            file_on_disk="/tmp/test1.plaso",
            original_filename="test1.plaso",
        )
        db_session.add(datasource)
        db_session.commit()

        file_path = datasource.get_file_on_disk
        tasks._set_datasource_total_events(  # pylint: disable=protected-access
            self.timeline.id, file_path, 42
        )
        self.assertEqual(datasource.get_total_file_events, 42)

    def test_set_datasource_total_events_not_found(self):
        """Test _set_datasource_total_events raises KeyError for missing file."""
        with self.assertRaises(KeyError):
            tasks._set_datasource_total_events(  # pylint: disable=protected-access
                self.timeline.id, "/nonexistent/path.plaso", 100
            )

    @mock.patch("timesketch.lib.tasks.subprocess.check_output")
    @mock.patch(_CREATE_STORAGE_READER)
    @mock.patch("timesketch.lib.tasks.OpenSearchDataStore")
    def test_run_plaso_success(
        self, mock_opensearch_cls, mock_create_reader, mock_check_output
    ):
        """Test run_plaso successfully processes and indexes plaso file."""
        mock_plaso = mock.MagicMock()
        mock_plaso.__version__ = "20260720"

        mock_storage_reader = mock.MagicMock()
        mock_storage_reader.GetNumberOfAttributeContainers.return_value = 3205
        mock_create_reader.return_value = mock_storage_reader

        mock_opensearch = mock.MagicMock()
        mock_connection = mock.MagicMock()
        mock_connection.host = "http://127.0.0.1"
        mock_connection.port = 9200
        mock_opensearch.client.transport.get_connection.return_value = mock_connection
        mock_opensearch.client.indices.exists.return_value = True
        mock_opensearch.create_index.return_value = "test_index"
        mock_opensearch_cls.return_value = mock_opensearch
        mock_check_output.return_value = "Done"

        file_path = "/tmp/test_success.plaso"
        datasource = DataSource(
            timeline=self.timeline,
            user=self.user1,
            file_on_disk=file_path,
            original_filename="test_success.plaso",
        )
        db_session.add(datasource)
        searchindex = SearchIndex(
            name="test_index",
            user=self.user1,
            index_name="test_index",
        )
        db_session.add(searchindex)
        db_session.commit()

        with mock.patch("timesketch.lib.tasks.plaso", mock_plaso):
            result = tasks.run_plaso(
                file_path=file_path,
                events="",
                timeline_name="test_timeline",
                index_name="test_index",
                source_type="plaso",
                timeline_id=self.timeline.id,
            )

        self.assertEqual(result, "test_index")
        self.assertEqual(datasource.get_total_file_events, 3205)
        mock_storage_reader.Close.assert_called_once()

    @mock.patch("timesketch.lib.tasks.subprocess.check_output")
    @mock.patch(_CREATE_STORAGE_READER)
    @mock.patch("timesketch.lib.tasks.OpenSearchDataStore")
    def test_run_plaso_success_event_data_fallback(
        self, mock_opensearch_cls, mock_create_reader, mock_check_output
    ):
        """Test run_plaso falls back to event_data count when event count is 0."""
        mock_plaso = mock.MagicMock()
        mock_plaso.__version__ = "20260720"

        mock_storage_reader = mock.MagicMock()
        # Returns 0 for "event" and 1602 for "event_data"
        mock_storage_reader.GetNumberOfAttributeContainers.side_effect = (
            lambda container_type: (1602 if container_type == "event_data" else 0)
        )
        mock_create_reader.return_value = mock_storage_reader

        mock_opensearch = mock.MagicMock()
        mock_connection = mock.MagicMock()
        mock_connection.host = "http://127.0.0.1"
        mock_connection.port = 9200
        mock_opensearch.client.transport.get_connection.return_value = mock_connection
        mock_opensearch.client.indices.exists.return_value = True
        mock_opensearch.create_index.return_value = "test_index"
        mock_opensearch_cls.return_value = mock_opensearch
        mock_check_output.return_value = "Done"

        file_path = "/tmp/test_event_data.plaso"
        datasource = DataSource(
            timeline=self.timeline,
            user=self.user1,
            file_on_disk=file_path,
            original_filename="test_event_data.plaso",
        )
        db_session.add(datasource)
        searchindex = SearchIndex(
            name="test_index_2",
            user=self.user1,
            index_name="test_index_2",
        )
        db_session.add(searchindex)
        db_session.commit()

        with mock.patch("timesketch.lib.tasks.plaso", mock_plaso):
            result = tasks.run_plaso(
                file_path=file_path,
                events="",
                timeline_name="test_timeline",
                index_name="test_index_2",
                source_type="plaso",
                timeline_id=self.timeline.id,
            )

        self.assertEqual(result, "test_index_2")
        self.assertEqual(datasource.get_total_file_events, 1602)
        mock_storage_reader.Close.assert_called_once()
