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
"""Standalone script to generate dummy data for Timesketch."""

import argparse
import csv
import datetime
import random
import string
import sys
from datetime import timezone

# Define standard fields for the dummy CSV
DUMMY_CSV_HEADERS = [
    "message",
    "datetime",
    "timestamp_desc",
    "timestamp",
    "hostname",
    "username",
    "source_short",
    "custom_field_1",
    "numeric_field",
    "ts_cli_generator",
]

GENERATOR_TAG_VALUE = "ts_cli_client_generate_dummy_csv"

_MESSAGE_VERBS = ["Accessed", "Modified", "Created", "Deleted", "Logged", "Failed"]
_MESSAGE_NOUNS = ["file.txt", "registry key", "process", "user account", "config"]
_TIMESTAMP_DESCRIPTIONS = [
    "File Creation Time",
    "Last Access Time",
    "Metadata Change Time",
    "Event Logged Time",
    "Session Start",
]
_USERNAMES = ["alice", "bob", "charlie", "eve", "system", "admin"]
_SOURCE_SHORTS = ["LOG", "WEBHIST", "REG", "FILE", "AUTH"]


def generate_random_event(
    start_time: datetime.datetime, end_time: datetime.datetime
) -> dict:
    """Generates a dictionary representing a single random event.

    Args:
        start_time: The start of the time range (datetime object, UTC).
        end_time: The end of the time range (datetime object, UTC).

    Returns:
        A dictionary representing a single random event.

    Raises:
        ValueError: If end_time is earlier than start_time.
    """
    if end_time < start_time:
        raise ValueError("End time cannot be earlier than start time.")

    # Calculate total seconds in the range
    # Ensure total_seconds is not negative.
    total_seconds = max(0, int((end_time - start_time).total_seconds()))

    # Add a random number of seconds to the start time
    dt_object_utc = start_time + datetime.timedelta(
        seconds=random.randint(0, total_seconds)
    )

    iso_datetime = dt_object_utc.isoformat()
    unix_timestamp = int(dt_object_utc.timestamp())

    message = (
        f"{random.choice(_MESSAGE_VERBS)} {random.choice(_MESSAGE_NOUNS)} by user."
    )
    timestamp_desc = random.choice(_TIMESTAMP_DESCRIPTIONS)
    hostname = f"host-{random.randint(100, 999)}.example.com"
    username = random.choice(_USERNAMES)
    source_short = random.choice(_SOURCE_SHORTS)
    custom_field_1 = "".join(
        random.choices(string.ascii_lowercase + string.digits, k=8)
    )
    numeric_field = random.randint(0, 10000)

    return {
        "message": message,
        "datetime": iso_datetime,
        "timestamp_desc": timestamp_desc,
        "timestamp": unix_timestamp,
        "hostname": hostname,
        "username": username,
        "source_short": source_short,
        "custom_field_1": custom_field_1,
        "numeric_field": numeric_field,
        "ts_cli_generator": GENERATOR_TAG_VALUE,
    }


def main(cli_args=None):
    """Main function for the standalone script."""
    parser = argparse.ArgumentParser(
        prog="generate_sample_data.py",
        description="Generate a CSV file with random dummy event data for Timesketch.",
    )
    parser.add_argument(
        "-o",
        "--output",
        required=True,
        type=argparse.FileType("w", encoding="utf-8"),
        help="Path to the output CSV file.",
    )
    parser.add_argument(
        "-c",
        "--count",
        required=True,
        type=int,
        help="Number of dummy events to generate.",
    )
    parser.add_argument(
        "--start-date",
        required=True,
        type=lambda s: datetime.datetime.fromisoformat(s).replace(tzinfo=timezone.utc),
        help="Start date/time for event generation (ISO 8601). E.g., "
        "'2023-10-26T10:00:00+00:00'. Assumed UTC if no timezone specified.",
    )
    parser.add_argument(
        "--end-date",
        required=True,
        type=lambda s: datetime.datetime.fromisoformat(s).replace(tzinfo=timezone.utc),
        help="End date/time for event generation (ISO 8601). E.g., "
        "'2023-10-27T18:30:00+00:00'. Assumed UTC if no timezone specified.",
    )

    args_to_parse = cli_args if cli_args is not None else sys.argv[1:]
    args = parser.parse_args(args_to_parse)

    if args.count <= 0:
        print("Error: Count must be a positive integer.", file=sys.stderr)
        sys.exit(1)

    try:
        # Ensure dates are timezone-aware UTC (handled by type=lambda in argparse)
        start_time_utc = args.start_date
        end_time_utc = args.end_date

        if end_time_utc < start_time_utc:
            print("Error: End date cannot be earlier than start date.", file=sys.stderr)
            sys.exit(1)

        print(f"Generating {args.count} events to {args.output.name}")
        print(f"Time range: {start_time_utc.isoformat()} to {end_time_utc.isoformat()}")

        writer = csv.DictWriter(args.output, fieldnames=DUMMY_CSV_HEADERS)
        writer.writeheader()

        for i in range(args.count):
            event_data = generate_random_event(start_time_utc, end_time_utc)
            writer.writerow(event_data)

        print(f"\nSuccessfully generated {args.count} events to {args.output.name}")

    except ValueError as e:
        print(f"Error parsing date: {e}. Please use ISO 8601 format.", file=sys.stderr)
        sys.exit(1)
    except IOError as e:
        print(f"Error writing to file {args.output.name}: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:  # pylint: disable=broad-except
        print(
            f"An unexpected error occurred: {type(e).__name__} - {e}", file=sys.stderr
        )
        sys.exit(1)
    finally:
        if args.output and not args.output.closed:
            args.output.close()


if __name__ == "__main__":
    main()
