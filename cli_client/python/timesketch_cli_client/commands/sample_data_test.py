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
"""Tests for sample-data command."""

import unittest
import tempfile
import os
import csv
import mock


from click.testing import CliRunner

from timesketch_api_client import test_lib as api_test_lib
from timesketch_cli_client.commands.sample_data import (
    DUMMY_CSV_HEADERS,
    GENERATOR_TAG_VALUE,
)

from .. import test_lib
from .sample_data import sample_data_group


class SampleDataTest(unittest.TestCase):
    """Test Events."""

    @mock.patch("requests.Session", api_test_lib.mock_session)
    def setUp(self):
        """Setup test case."""
        self.ctx = test_lib.get_cli_context()

    def test_generate_dummy_csv(self):
        """Test generate_dummy_csv command."""
        runner = CliRunner()
        expected_event_count = 10
        output_file_name = ""
        try:
            # Create a temporary file that is not deleted on close
            # so we can read it after the command has written to it.
            with tempfile.NamedTemporaryFile(mode="w", delete=False) as tmp_file:
                output_file_name = tmp_file.name
            # The file needs to be closed before the CLI command can write to it.

            result = runner.invoke(
                sample_data_group,
                [
                    "generate-dummy-csv",
                    "--output",
                    output_file_name,
                    "--count",
                    str(expected_event_count),
                    "--start-date",
                    "2023-01-01T00:00:00",
                    "--end-date",
                    "2023-01-01T23:59:59",
                ],
                obj=self.ctx,
            )
            self.assertEqual(result.exit_code, 0)
            self.assertIn(
                f"Successfully generated {expected_event_count} events to"
                f" {output_file_name}",
                result.output,
            )

            # Verify the content of the CSV file
            with open(output_file_name, "r", encoding="utf-8") as csvfile:
                reader = csv.reader(csvfile)
                header = next(reader)
                self.assertEqual(header, DUMMY_CSV_HEADERS)

                rows = list(reader)
                self.assertEqual(len(rows), expected_event_count)

                for row in rows:
                    row_dict = dict(zip(header, row))
                    self.assertEqual(row_dict["tsctl_generator"], GENERATOR_TAG_VALUE)
        finally:
            if output_file_name and os.path.exists(output_file_name):
                os.remove(output_file_name)

    def test_generate_dummy_csv_invalid_dates(self):
        """Test generate_dummy_csv command with invalid date range."""
        runner = CliRunner()
        output_file_name = ""
        try:
            with tempfile.NamedTemporaryFile(mode="w", delete=False) as tmp_file:
                output_file_name = tmp_file.name

            result = runner.invoke(
                sample_data_group,
                [
                    "generate-dummy-csv",
                    "--output",
                    output_file_name,
                    "--count",
                    "10",
                    "--start-date",
                    "2023-01-02T00:00:00",  # Start date is after end date
                    "--end-date",
                    "2023-01-01T23:59:59",
                ],
                obj=self.ctx,
            )
            self.assertEqual(
                result.exit_code, 2
            )  # click.UsageError typically exits with 2
            self.assertIn(
                "Error: End date cannot be earlier than start date.", result.output
            )
        finally:
            if output_file_name and os.path.exists(output_file_name):
                os.remove(output_file_name)
