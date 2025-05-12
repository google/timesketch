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
"""Commands to generate dummy data for testing."""

from datetime import timezone  # Import timezone specifically
import datetime
import random
import string
import csv
import traceback
import click

from tqdm import tqdm

# Define standard fields for the dummy CSV
DUMMY_CSV_HEADERS = [
    "message",
    "datetime",
    "timestamp_desc",
    "timestamp",  # Often derived, but good to include
    "hostname",
    "username",
    "source_short",
    "custom_field_1",
    "numeric_field",
    "tsctl_generator",
]

GENERATOR_TAG_VALUE = "ts_cli_client_generate_dummy_csv"

# Constants for random data generation
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


# Helper function to generate random data
def _generate_random_event(start_time, end_time):
    """Generates a dictionary representing a single random event."""
    # Generate random datetime and timestamp
    dt_object = start_time + datetime.timedelta(
        seconds=random.randint(0, int((end_time - start_time).total_seconds()))
    )
    # Ensure timezone-aware datetime in UTC
    dt_object_utc = dt_object.replace(tzinfo=timezone.utc)
    iso_datetime = dt_object_utc.isoformat()
    unix_timestamp = int(dt_object_utc.timestamp())

    # Generate other random fields
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
        "tsctl_generator": GENERATOR_TAG_VALUE,
    }


SAMPLE_DATA_GROUP_EPILOG = """\b
Example Usage:
  timesketch sample-data generate-dummy-csv --output /tmp/dummy_events.csv \\
    --count 1000 --start-date "2025-01-01T00:00:00" \\
    --end-date "2025-01-02T23:59:59"
"""


@click.group("sample-data", epilog=SAMPLE_DATA_GROUP_EPILOG)
def sample_data_group():
    """Commands for generating sample or test data."""


@sample_data_group.command(name="generate-dummy-csv")
@click.option(
    "--output",
    "-o",
    required=True,
    type=click.Path(dir_okay=False, writable=True),
    help="Path to the output CSV file.",
)
@click.option(
    "--count",
    "-c",
    required=True,
    type=click.IntRange(min=1),  # Ensure at least 1 event
    help="Number of dummy events to generate.",
)
@click.option(
    "--start-date",
    required=True,
    type=click.DateTime(),  # Accepts formats like YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS
    help="Start date/time for event generation (inclusive). E.g., '2023-10-26' or '2023-10-26T10:00:00'. Assumed UTC if no timezone specified.",
)
@click.option(
    "--end-date",
    required=True,
    type=click.DateTime(),
    help="End date/time for event generation (inclusive). E.g., '2023-10-27' or '2023-10-27T18:30:00'. Assumed UTC if no timezone specified.",
)
def generate_dummy_csv(
    output: str, count: int, start_date: datetime.datetime, end_date: datetime.datetime
):
    """Generates a CSV file with random dummy event data within a specified timeframe.
    This command creates a CSV file suitable for testing Timesketch imports.
    It includes standard fields like 'datetime', 'timestamp_desc', and 'message',
    along with other common fields populated with random but valid data.
    The timestamps generated will be randomly distributed between the specified
    --start-date and --end-date (inclusive). Dates are interpreted as UTC.
    """

    # Ensure dates are timezone-aware UTC
    if start_date.tzinfo is None:
        start_time_utc = start_date.replace(tzinfo=timezone.utc)
    else:
        start_time_utc = start_date.astimezone(timezone.utc)

    if end_date.tzinfo is None:
        end_time_utc = end_date.replace(tzinfo=timezone.utc)
    else:
        end_time_utc = end_date.astimezone(timezone.utc)

    # Validate date range
    if end_time_utc < start_time_utc:
        raise click.UsageError("End date cannot be earlier than start date.")

    click.echo(f"\nSuccessfully generated {count} events to {output}")
    click.echo(
        f"Time range: {start_time_utc.isoformat()} to {end_time_utc.isoformat()}"
    )

    try:
        with open(output, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=DUMMY_CSV_HEADERS)
            writer.writeheader()

            for _ in tqdm(range(count), desc="Generating Events", unit="event"):
                # Pass the timezone-aware UTC dates to the helper
                event_data = _generate_random_event(start_time_utc, end_time_utc)
                writer.writerow(event_data)

        click.echo(f"\nSuccessfully generated {count} events to {output}")

    except IOError as e:
        raise click.ClickException(f"Could not write to file {output}: {e}")
    except Exception as e:
        click.echo(traceback.format_exc(), err=True)
        raise click.ClickException(
            f"An unexpected error occurred: {type(e).__name__} - {e}"
        )
