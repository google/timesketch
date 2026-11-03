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
"""Tests for timelines command."""

import unittest
from unittest import mock

from click.testing import CliRunner

from timesketch_api_client import error as api_error
from timesketch_api_client import test_lib as api_test_lib

from timesketch_cli_client import test_lib
from timesketch_cli_client.commands.timelines import timelines_group


class TimelinesTest(unittest.TestCase):
    """Test Timelines."""

    @mock.patch("requests.Session", api_test_lib.mock_session)
    def setUp(self):
        """Setup test case."""
        self.ctx = test_lib.get_cli_context()

    def test_list_timelines(self):
        """Test to list timelines."""
        runner = CliRunner()
        result = runner.invoke(timelines_group, ["list"], obj=self.ctx)
        assert "1 test" in result.output
        assert "2 test\n" in result.output

    def test_describe_timeline(self):
        """Test to get detail for a timeline."""
        runner = CliRunner()
        result = runner.invoke(timelines_group, ["describe", "1"], obj=self.ctx)
        assert "Name: test" in result.output
        assert "Index: test" in result.output
        assert "Event count: 0" in result.output

    def _create_mock_timeline(self, meta=None, status="ready", error_message=None):
        """Creates a mocked Timeline object for describe command tests."""
        timeline_data = {
            "meta": meta if meta is not None else {"lines_indexed": 42},
            "objects": [
                {
                    "id": 1,
                    "name": "evtx_timeline",
                    "color": "FFFFFF",
                    "created_at": "2026-11-02T00:00:00",
                    "status": [{"status": status}],
                    "searchindex": {"id": 10, "index_name": "idx_10"},
                    "datasources": [
                        {
                            "original_filename": "evtx_part.csv",
                            "file_on_disk": "/tmp/evtx_part.csv",
                            "error_message": error_message,
                        }
                    ],
                }
            ],
        }
        mock_tl = mock.MagicMock()
        mock_tl.name = "evtx_timeline"
        mock_tl.index_name = "idx_10"
        mock_tl.status = status
        mock_tl.color = "FFFFFF"
        mock_tl.resource_data = timeline_data
        mock_tl.lazyload_data.return_value = timeline_data
        return mock_tl

    def test_describe_timeline_with_meta_fields_count(self):
        """Test describe uses meta.fields_count without querying SearchIndex."""
        self.ctx.output_format_from_flag = "text"
        for count, expected in ((15, "15"), (0, "0"), (None, "N/A")):
            with self.subTest(fields_count=count):
                mock_tl = self._create_mock_timeline(
                    meta={"lines_indexed": 42, "fields_count": count}
                )
                type(mock_tl).index = mock.PropertyMock(
                    side_effect=AssertionError("SearchIndex should not be accessed")
                )
                with mock.patch(
                    "timesketch_api_client.sketch.Sketch.get_timeline",
                    return_value=mock_tl,
                ):
                    runner = CliRunner()
                    result = runner.invoke(
                        timelines_group, ["describe", "1"], obj=self.ctx
                    )

                self.assertEqual(result.exit_code, 0, msg=result.output)
                self.assertIn("Event count: 42", result.output)
                self.assertIn(f"Number of fields: {expected}", result.output)
                self.assertIn("Datasources:", result.output)
                self.assertIn("Original filename: evtx_part.csv", result.output)

    def test_describe_timeline_legacy_not_found_and_null_index_id(self):
        """Test legacy fallback handles missing SearchIndex id and NotFoundError."""
        self.ctx.output_format_from_flag = "text"

        mock_null_id = self._create_mock_timeline(meta={"lines_indexed": 5})
        mock_null_id.index.id = None
        type(mock_null_id.index).fields = mock.PropertyMock(
            side_effect=AssertionError("SearchIndex.fields should not be queried")
        )
        with mock.patch(
            "timesketch_api_client.sketch.Sketch.get_timeline",
            return_value=mock_null_id,
        ):
            runner = CliRunner()
            res_null = runner.invoke(timelines_group, ["describe", "1"], obj=self.ctx)
        self.assertEqual(res_null.exit_code, 0, msg=res_null.output)
        self.assertIn("Number of fields: 0", res_null.output)

        mock_404 = self._create_mock_timeline(meta={"lines_indexed": 5})
        mock_404.index.id = 10
        type(mock_404.index).fields = mock.PropertyMock(
            side_effect=api_error.NotFoundError("Not Found")
        )
        with mock.patch(
            "timesketch_api_client.sketch.Sketch.get_timeline",
            return_value=mock_404,
        ):
            runner = CliRunner()
            res_404 = runner.invoke(timelines_group, ["describe", "1"], obj=self.ctx)
        self.assertEqual(res_404.exit_code, 0, msg=res_404.output)
        self.assertIn("Number of fields: 0", res_404.output)
        self.assertIn("Datasources:", res_404.output)

    def test_describe_timeline_collaborator_403_fallback(self):
        """Test describe degrades cleanly on SearchIndex 403 and prints datasources."""
        mock_tl = self._create_mock_timeline(
            meta={"lines_indexed": 10},
            error_message="Sample import warning",
        )
        type(mock_tl.index).fields = mock.PropertyMock(
            side_effect=RuntimeError(
                "Failed to get a valid response json from Timesketch API, "
                "with error [403] FORBIDDEN (http://127.0.0.1/api/v1/searchindices/10/)"
            )
        )
        self.ctx.output_format_from_flag = "text"
        with mock.patch(
            "timesketch_api_client.sketch.Sketch.get_timeline",
            return_value=mock_tl,
        ):
            runner = CliRunner()
            result = runner.invoke(timelines_group, ["describe", "1"], obj=self.ctx)

        self.assertEqual(result.exit_code, 0, msg=result.output)
        self.assertIn(
            "Number of fields: N/A (no direct SearchIndex read permission)",
            result.output,
        )
        self.assertIn("Datasources:", result.output)
        self.assertIn("Original filename: evtx_part.csv", result.output)
        self.assertIn("Error: Sample import warning", result.output)

    def test_describe_timeline_legacy_owner_fields(self):
        """Test describe falls back to SearchIndex.fields without fields_count."""
        mock_tl = self._create_mock_timeline(meta={"lines_indexed": 10})
        mock_tl.index.fields = ["datetime", "message", "timestamp"]
        self.ctx.output_format_from_flag = "text"
        with mock.patch(
            "timesketch_api_client.sketch.Sketch.get_timeline",
            return_value=mock_tl,
        ):
            runner = CliRunner()
            result = runner.invoke(timelines_group, ["describe", "1"], obj=self.ctx)

        self.assertEqual(result.exit_code, 0, msg=result.output)
        self.assertIn("Number of fields: 3", result.output)
        self.assertIn("Datasources:", result.output)

    def test_describe_timeline_non_403_error_propagates(self):
        """Test describe re-raises non-403 RuntimeErrors from SearchIndex."""
        mock_tl = self._create_mock_timeline(meta={"lines_indexed": 10})
        type(mock_tl.index).fields = mock.PropertyMock(
            side_effect=RuntimeError(
                "Failed to get a valid response json from Timesketch API, "
                "with error [500] INTERNAL SERVER ERROR"
            )
        )
        self.ctx.output_format_from_flag = "text"
        with mock.patch(
            "timesketch_api_client.sketch.Sketch.get_timeline",
            return_value=mock_tl,
        ):
            runner = CliRunner()
            result = runner.invoke(timelines_group, ["describe", "1"], obj=self.ctx)

        self.assertEqual(result.exit_code, 1)
        self.assertIsInstance(result.exception, RuntimeError)

    def test_describe_timeline_failed_status_skips_searchindex(self):
        """Test describe skips SearchIndex lookup when timeline status is fail."""
        mock_tl = self._create_mock_timeline(
            meta={"lines_indexed": None},
            status="fail",
            error_message="Plaso version out of date",
        )
        type(mock_tl.index).fields = mock.PropertyMock(
            side_effect=AssertionError("SearchIndex should not be queried on fail")
        )
        self.ctx.output_format_from_flag = "text"
        with mock.patch(
            "timesketch_api_client.sketch.Sketch.get_timeline",
            return_value=mock_tl,
        ):
            runner = CliRunner()
            result = runner.invoke(timelines_group, ["describe", "1"], obj=self.ctx)

        self.assertEqual(result.exit_code, 0, msg=result.output)
        self.assertIn("Status: fail", result.output)
        self.assertIn("Event count: 0", result.output)
        self.assertIn("Number of fields: 0", result.output)
        self.assertIn("Error: Plaso version out of date", result.output)
