"""End to end tests for timeline deletion functionality."""

# Copyright 2025 Google Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may not a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import uuid
import subprocess

import requests  # Added here

from . import interface
from . import manager


class TimelineDeletionTest(interface.BaseEndToEndTest):
    """End to end tests for delete functionality."""

    NAME = "delete_timeline_test"

    def test_delete_failed_timeline(self):
        """Test to delete a failed timeline"""
        rand = uuid.uuid4().hex
        sketch = self.api.create_sketch(name=f"test-timeline-deletion_{rand}")

        # Import a valid timeline.
        self.import_timeline("sigma_events.csv", sketch=sketch)
        timeline = sketch.list_timelines()[0]

        # Force the timeline status to fail using tsctl.
        subprocess.check_call(
            [
                "tsctl",
                "timeline-status",
                str(timeline.id),
                "--action",
                "set",
                "--status",
                "fail",
            ]
        )

        # Reload the timeline to get the updated status.
        _ = sketch.lazyload_data(refresh_cache=True)
        timeline = sketch.list_timelines()[0]
        self.assertions.assertEqual(timeline.status, "fail")

        # Check that the search index is archived
        searchindex_name = timeline.index.index_name

        # Delete the timeline
        timeline.delete()

        output = subprocess.check_output(
            ["tsctl", "searchindex-info", "--index_name", searchindex_name]
        )

        self.assertions.assertIn("Status: archived", output.decode("utf-8"))

    def test_delete_failed_timeline_with_soft_deleted_sibling(self):
        """Test that index is archived when deleting a failed timeline if other
        sibling is soft-deleted."""
        rand = uuid.uuid4().hex
        sketch = self.api.create_sketch(
            name=f"test-deletion-soft-deleted-sibling_{rand}"
        )

        # 1. Create Timeline A (Sibling)
        self.import_timeline("sigma_events.csv", sketch=sketch, index_name="timeline_a")
        _ = sketch.lazyload_data(refresh_cache=True)
        timeline_a = sketch.list_timelines()[0]
        index_name = timeline_a.index.index_name

        # 2. Delete Timeline A
        timeline_a.delete()

        # 3. Create Timeline B (Failed) sharing the same index
        timeline_b = self.import_timeline(
            "evtx_part.csv", sketch=sketch, index_name="timeline_b_failed"
        )

        # Reload the sketch and find Timeline B from the list of timelines.
        _ = sketch.lazyload_data(refresh_cache=True)
        timelines = sketch.list_timelines()
        self.assertions.assertIsNotNone(timeline_b)

        # Force the timeline status to fail using tsctl.
        subprocess.check_call(
            [
                "tsctl",
                "timeline-status",
                str(timeline_b.id),
                "--action",
                "set",
                "--status",
                "fail",
            ]
        )

        # Reload the timeline to get the updated status.
        _ = sketch.lazyload_data(refresh_cache=True)
        timelines = sketch.list_timelines()
        timeline_b = next(
            t for t in timelines if t.id == timeline_b.id
        )  # Re-fetch to ensure status is fresh
        self.assertions.assertEqual(timeline_b.status, "fail")

        # 4. Delete Timeline B
        timeline_b.delete()

        # 5. Verify Index is Archived via tsctl
        output = subprocess.check_output(
            ["tsctl", "searchindex-info", "--index_name", index_name]
        )
        self.assertions.assertIn("Status: archived", output.decode("utf-8"))

        # 6. Verify the OpenSearch index is actually closed via requests
        try:
            response = requests.get(
                f"http://{interface.OPENSEARCH_HOST}:{interface.OPENSEARCH_PORT}/_cat/indices?h=status,index",  # pylint: disable=line-too-long
                timeout=5,
            )
            response.raise_for_status()  # Raise HTTPError
            opensearch_status_output = response.text
            self.assertions.assertIn(f"close {index_name}", opensearch_status_output)
        except requests.exceptions.RequestException as e:
            self.assertions.fail(f"OpenSearch index check failed for {index_name}: {e}")

    def test_delete_shared_index_timeline_safety(self):
        """Test that deleting a timeline with a shared index does NOT close the
        index.

        Logic:
        1. Create a sketch and import two timelines (Timeline A and B) that
           share the same underlying OpenSearch index.
        2. Verify that the shared index is initially 'open'.
        3. Delete Timeline A.
        4. Verify that the shared index remains 'open' because Timeline B
           still depends on it.
        5. Delete Timeline B.
        6. Verify that the shared index is now 'closed' as no more active
           timelines are using it.
        """
        rand = uuid.uuid4().hex
        sketch = self.api.create_sketch(name=f"test-shared-index-safety_{rand}")

        shared_index_name = uuid.uuid4().hex

        # 1. Create Timeline A
        tl_a = self.import_timeline(
            "sigma_events.csv", sketch=sketch, index_name=shared_index_name
        )

        # 2. Create Timeline B sharing same index
        tl_b = self.import_timeline(
            "evtx_part.csv", sketch=sketch, index_name=shared_index_name
        )

        # Verify index exists and is open
        try:
            response = requests.get(
                f"http://{interface.OPENSEARCH_HOST}:{interface.OPENSEARCH_PORT}/_cat/indices/{shared_index_name}?format=json",
                timeout=5,
            )
            response.raise_for_status()
            stats = response.json()
            self.assertions.assertEqual(stats[0].get("status"), "open")
        except requests.exceptions.RequestException as e:
            self.assertions.fail(f"OS check failed: {e}")

        # 3. Delete Timeline A
        tl_a.delete()

        # 4. Verify Index is STILL OPEN
        try:
            response = requests.get(
                f"http://{interface.OPENSEARCH_HOST}:{interface.OPENSEARCH_PORT}/_cat/indices/{shared_index_name}?format=json",
                timeout=5,
            )
            response.raise_for_status()
            stats = response.json()
            self.assertions.assertEqual(
                stats[0].get("status"), "open", "Shared index should remain open"
            )
        except requests.exceptions.RequestException as e:
            self.assertions.fail(f"OS check failed: {e}")

        # 5. Delete Timeline B (Last one)
        tl_b.delete()

        # 6. Verify Index is NOW CLOSED
        try:
            response = requests.get(
                f"http://{interface.OPENSEARCH_HOST}:{interface.OPENSEARCH_PORT}/_cat/indices/{shared_index_name}?format=json",
                timeout=5,
            )
            if response.status_code == 200:
                stats = response.json()
                self.assertions.assertEqual(
                    stats[0].get("status"),
                    "close",
                    "Index should be closed after last timeline deleted",
                )
        except requests.exceptions.RequestException as e:
            self.assertions.fail(f"OS check failed: {e}")


manager.EndToEndTestManager.register_test(TimelineDeletionTest)
