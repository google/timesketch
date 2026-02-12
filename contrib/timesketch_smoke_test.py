#!/usr/bin/env python
#
# Copyright 2026 Google Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
A smoke test script for a Timesketch deployment.

This script tests the following core functionalities:
- Sketch creation
- CSV and JSONL file import
- Searching for events
- Commenting on events
- Tagging and un-tagging events
- Sketch deletion (for cleanup)

It is designed to be run after a new deployment to verify that the basic
API and backend functionalities are working as expected.
"""
import os
import sys
import time
import uuid
import json

from timesketch_api_client import config

# --- CONFIGURATION ---
# TODO: Update these values to match your Timesketch deployment.
# It is recommended to use environment variables for credentials.
TS_HOST = os.environ.get("TS_HOST", "http://127.0.0.1")
TS_USER = os.environ.get("TS_USER", "admin")
TS_PASSWORD = os.environ.get("TS_PASSWORD", "admin")
# --- END CONFIGURATION ---

# Constants
CSV_FILENAME = "smoke_test_data.csv"
JSONL_FILENAME = "smoke_test_data.jsonl"
SMOKE_TEST_TAG = "smoke_test_tag"


class TimesketchSmokeTest:
    """A class to encapsulate the Timesketch smoke test."""

    def __init__(self, host, user, password):
        """Initializes the smoke test class."""
        self.api = config.get_client(
            host=host, username=user, password=password, verify=False
        )
        self.sketch = None
        self.csv_search_string = str(uuid.uuid4())
        self.jsonl_search_string = str(uuid.uuid4())

    def _create_sample_files(self):
        """Creates temporary CSV and JSONL files for testing."""
        print(f"[INFO] Creating sample data files: {CSV_FILENAME}, {JSONL_FILENAME}")

        # Create CSV file
        with open(CSV_FILENAME, "w", encoding="utf-8") as f:
            f.write("timestamp,datetime,message,source_host\n")
            f.write(
                f"1672531200,2023-01-01T00:00:00Z,\n"
                f"Benign entry for context,workstation1\n"
            )
            f.write(
                f"1672531261,2023-01-01T00:01:01Z,\n"
                f"A unique event to find {self.csv_search_string},workstation2\n"
            )

        # Create JSONL file (simulating a simple Plaso-like format)
        with open(JSONL_FILENAME, "w", encoding="utf-8") as f:
            f.write(
                json.dumps(
                    {
                        "timestamp": 1672531322,
                        "datetime": "2023-01-01T00:02:02Z",
                        "message": "A JSONL event for context",
                        "source": "JSONL_IMPORTER",
                    }
                )
                + "\n"
            )
            f.write(
                json.dumps(
                    {
                        "timestamp": 1672531383,
                        "datetime": "2023-01-01T00:03:03Z",
                        "message": f"Another unique event {self.jsonl_search_string}",
                        "source": "JSONL_IMPORTER",
                    }
                )
                + "\n"
            )
        print("[SUCCESS] Sample data files created.")

    def _wait_for_timeline(self, timeline, timeout=120):
        """
        Waits for a timeline's indexing to complete.

        Args:
            timeline (timesketch_api_client.Timeline): The timeline object.
            timeout (int): Maximum seconds to wait.

        Raises:
            TimeoutError: If the timeline does not become ready in time.
        """
        for i in range(timeout):
            timeline.reload()
            status = timeline.status
            if status == "ready":
                print(f"[INFO] Timeline '{timeline.name}' is ready.")
                return
            if status == "fail":
                raise RuntimeError(f"Timeline '{timeline.name}' failed to import.")
            if i % 10 == 0:
                print(
                    f"[INFO] Waiting for timeline '{timeline.name}'..."
                    f" (status: {status}, {i}s elapsed)"
                )
            time.sleep(1)
        raise TimeoutError(
            f"Timeline '{timeline.name}' did not become ready within {timeout}s."
        )

    def run_tests(self):
        """Runs the sequence of API tests."""
        self._create_sample_files()

        # 1. Create Sketch
        sketch_name = f"Smoke Test Sketch {int(time.time())}"
        print(f"[INFO] Creating sketch: '{sketch_name}'")
        self.sketch = self.api.create_sketch(
            name=sketch_name, description="Automated smoke test"
        )
        assert self.sketch is not None, "Failed to create sketch"
        print(f"[SUCCESS] Sketch created (ID: {self.sketch.id})")

        # 2. Import CSV
        print(f"[INFO] Uploading and importing '{CSV_FILENAME}'...")
        csv_timeline = self.sketch.upload(CSV_FILENAME)
        self._wait_for_timeline(csv_timeline)
        print(f"[SUCCESS] '{CSV_FILENAME}' imported successfully.")

        # 3. Import JSONL
        print(f"[INFO] Uploading and importing '{JSONL_FILENAME}'...")
        jsonl_timeline = self.sketch.upload(JSONL_FILENAME)
        self._wait_for_timeline(jsonl_timeline)
        print(f"[SUCCESS] '{JSONL_FILENAME}' imported successfully.")

        # 4. Search for an event
        print(f"[INFO] Searching for unique event: '{self.csv_search_string}'")
        events_df = self.sketch.explore(query=f'"{self.csv_search_string}"')
        assert len(events_df) == 1, f"Expected 1 event, found {len(events_df)}"
        event_id = events_df.index[0]
        event_dict = events_df.iloc[0].to_dict()
        print(f"[SUCCESS] Found unique event (ID: {event_id})")

        # 5. Add a comment
        comment_text = f"Smoke test comment on event {event_id}"
        print(f"[INFO] Adding comment to event {event_id}: '{comment_text}'")
        self.sketch.add_comment(event_id, comment_text)
        # Verification
        events_df_commented = self.sketch.explore(query=f'_id:"{event_id}"')
        comments = events_df_commented.iloc[0].to_dict().get("__ts_comment", "")
        assert comment_text in comments, "Comment not found on event"
        print("[SUCCESS] Comment added and verified.")

        # 6. Add a tag
        print(f"[INFO] Adding tag '{SMOKE_TEST_TAG}' to event {event_id}")
        self.sketch.add_tags(event_ids=[event_id], tags=[SMOKE_TEST_TAG])
        # Verification
        events_df_tagged = self.sketch.explore(query=f'_id:"{event_id}"')
        tags = events_df_tagged.iloc[0].to_dict().get("tag", [])
        assert SMOKE_TEST_TAG in tags, "Tag not found on event"
        print("[SUCCESS] Tag added and verified.")

        # 7. Remove the tag
        print(f"[INFO] Removing tag '{SMOKE_TEST_TAG}' from event {event_id}")
        self.sketch.remove_tags(event_ids=[event_id], tags=[SMOKE_TEST_TAG])
        # Verification
        events_df_untagged = self.sketch.explore(query=f'_id:"{event_id}"')
        tags_after_removal = events_df_untagged.iloc[0].to_dict().get("tag", [])
        assert (
            SMOKE_TEST_TAG not in tags_after_removal
        ), "Tag was not removed from event"
        print("[SUCCESS] Tag removed and verified.")

    def cleanup(self):
        """Cleans up resources created during the test."""
        print("[INFO] --- Starting Cleanup ---")
        if self.sketch:
            try:
                self.sketch.delete()
                print(f"[INFO] Sketch '{self.sketch.name}' deleted.")
            except Exception as e:
                print(f"[ERROR] Failed to delete sketch: {e}", file=sys.stderr)

        for filename in [CSV_FILENAME, JSONL_FILENAME]:
            if os.path.exists(filename):
                os.remove(filename)
                print(f"[INFO] Deleted temporary file: {filename}")
        print("[INFO] --- Cleanup Complete ---")


def main():
    """Main function to run the smoke test."""
    print("--- Timesketch API Smoke Test ---")
    print(f"Host: {TS_HOST}")
    print(f"User: {TS_USER}")
    print("---------------------------------")

    tester = TimesketchSmokeTest(host=TS_HOST, user=TS_USER, password=TS_PASSWORD)
    try:
        tester.run_tests()
        print("\n[SUCCESS] All smoke tests passed!")
    except Exception as e:
        print(f"\n[ERROR] A test failed: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        sys.exit(1)
    finally:
        tester.cleanup()


if __name__ == "__main__":
    main()
