# /usr/local/google/home/jaegeral/dev/timesketch/utils/generate_sample_data_test.py
import unittest
import tempfile
import os
import csv
from datetime import datetime, timezone
from unittest import mock

# Assuming your script is importable or you adjust sys.path
from utils import generate_sample_data  # Or however you need to import it


class TestGenerateSampleData(unittest.TestCase):
    def test_generate_random_event_structure(self):
        start = datetime(2023, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        end = datetime(2023, 1, 1, 1, 0, 0, tzinfo=timezone.utc)
        event = generate_sample_data.generate_random_event(start, end)
        self.assertIsInstance(event, dict)
        for header in generate_sample_data.DUMMY_CSV_HEADERS:
            self.assertIn(header, event)
        self.assertEqual(
            event["ts_cli_generator"], generate_sample_data.GENERATOR_TAG_VALUE
        )

    @mock.patch("random.randint")
    def test_generate_random_event_time_range(self, mock_randint):
        # Mock randint to return 0, so the event time is exactly the start_time
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
        start = datetime(2023, 1, 2, tzinfo=timezone.utc)
        end = datetime(2023, 1, 1, tzinfo=timezone.utc)  # End before start
        with self.assertRaises(ValueError):
            generate_sample_data.generate_random_event(start, end)

    @mock.patch("builtins.print")  # To capture print to stderr for errors
    def test_main_successful_generation(self, mock_print):
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
                self.assertEqual(header, generate_sample_data.DUMMY_CSV_HEADERS)
                rows = list(reader)
                self.assertEqual(len(rows), 3)
        finally:
            if os.path.exists(output_filename):
                os.remove(output_filename)

    # Add more tests for argument parsing errors, file I/O errors, etc.


if __name__ == "__main__":
    unittest.main()
