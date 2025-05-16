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
"""Unit tests for the generate_sample_data.py script."""
import unittest
import tempfile
import os
import csv
from datetime import datetime, timezone
from unittest import mock

from utils import generate_sample_data
from utils.generate_sample_data import DUMMY_CSV_HEADERS, GENERATOR_TAG_VALUE


class TestGenerateSampleData(unittest.TestCase):
    """Tests for the sample data generation script."""

    def test_generate_random_event_structure(self):
        start = datetime(2023, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        end = datetime(2023, 1, 1, 1, 0, 0, tzinfo=timezone.utc)
        event = generate_sample_data.generate_random_event(start, end)
        self.assertIsInstance(event, dict)
        for header in generate_sample_data.DUMMY_CSV_HEADERS:
            self.assertIn(header, event)
        self.assertEqual(event["ts_cli_generator"], GENERATOR_TAG_VALUE)

    @mock.patch("random.randint")
    def test_generate_random_event_time_range(self, mock_randint):
        """Tests that generated event timestamps fall within the specified range."""
        mock_randint.return_value = 0
        start = datetime(2023, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
        end = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        event = generate_sample_data.generate_random_event(start, end)

        # Check datetime string
        event_dt = datetime.fromisoformat(event["datetime"])
        self.assertEqual(event_dt, start)

        # Check timestamp
        self.assertEqual(event["timestamp"], int(start.timestamp()))

    def test_generate_random_event_invalid_range(self):
        """Tests that an invalid date range raises a ValueError."""
        start = datetime(2023, 1, 2, tzinfo=timezone.utc)
        end = datetime(2023, 1, 1, tzinfo=timezone.utc)  # End before start
        with self.assertRaises(ValueError):
            generate_sample_data.generate_random_event(start, end)

    @mock.patch("builtins.print")  # To capture print to stderr for errors
    def test_main_successful_generation(self, mock_print):
        """Tests the main script execution for successful CSV generation."""
        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".csv"
        ) as tmp_output:
            output_filename = tmp_output.name

        try:
            # Arguments to pass to main, excluding the script name itself
            cli_args = [
                "--output",
                output_filename,
                "--count",
                "3",
                "--start-date",
                "2023-01-01T00:00:00+00:00",
                "--end-date",
                "2023-01-01T01:00:00+00:00",
            ]
            generate_sample_data.main(cli_args)

            with open(output_filename, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                header = next(reader)
                self.assertEqual(header, DUMMY_CSV_HEADERS)
                rows = list(reader)
                self.assertEqual(len(rows), 3)

            successful_generation_message_found = False
            for call_args in mock_print.call_args_list:
                if (
                    f"Successfully generated 3 events to {output_filename}"
                    in call_args[0][0]
                ):
                    successful_generation_message_found = True
                    break
            self.assertTrue(
                successful_generation_message_found,
                "Success message not found in print calls",
            )
        finally:
            if os.path.exists(output_filename):
                os.remove(output_filename)


if __name__ == "__main__":
    unittest.main()
