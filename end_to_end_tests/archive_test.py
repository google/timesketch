# Copyright 2023 Google Inc. All rights reserved.
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
"""End to end tests for sketch archiving."""

import time
import uuid
import opensearchpy

from timesketch_api_client import search

from . import interface
from . import manager


class ArchiveTest(interface.BaseEndToEndTest):
    """End to end tests for sketch archiving."""

    NAME = "archive_test"

    def test_archive_sketch_with_failed_timeline(self):
        """Test archiving a sketch with a failed timeline."""
        sketch_name = f"test-archive-failed_{uuid.uuid4().hex}"
        sketch = self.api.create_sketch(name=sketch_name)
        self.sketch = sketch
        self.assertions.assertIsNotNone(sketch)

        # This file is known to cause an import failure.
        timeline = self.import_timeline("invalid_jsonl.jsonl", sketch=sketch)

        # Wait for the timeline to fail.
        for _ in range(20):
            time.sleep(1)
            if timeline.status == "fail":
                break
        self.assertions.assertEqual(timeline.status, "fail")

        sketch.archive()
        self.assertions.assertEqual(sketch.status, "archived")

        # Check that the index is closed.
        index_name = timeline.index_name
        index = self.api.get_searchindex(index_name)
        self.assertions.assertEqual(index.status, "closed")

    def test_unarchive_sketch_with_failed_timeline(self):
        """Test unarchiving a sketch with a failed timeline."""
        sketch_name = f"test-unarchive-failed_{uuid.uuid4().hex}"
        sketch = self.api.create_sketch(name=sketch_name)
        self.sketch = sketch

        # This file is known to cause an import failure.
        timeline = self.import_timeline("invalid_jsonl.jsonl", sketch=sketch)

        # Wait for the timeline to fail.
        for _ in range(20):
            time.sleep(1)
            if timeline.status == "fail":
                break

        self.assertions.assertEqual(timeline.status, "fail")
        sketch.archive()
        self.assertions.assertEqual(sketch.status, "archived")
        # Unarchive
        sketch.unarchive()
        self.assertions.assertEqual(sketch.status, "ready")
        self.assertions.assertEqual(timeline.status, "fail")

    def test_unarchive_sketch_with_missing_index(self):
        """Test unarchiving a sketch where the OpenSearch index is missing."""
        sketch_name = f"test-unarchive-missing-index_{uuid.uuid4().hex}"
        sketch = self.api.create_sketch(name=sketch_name)
        self.sketch = sketch

        # Import a valid timeline first
        timeline = self.import_timeline("sigma_events.jsonl", sketch=sketch)
        index_name = timeline.index_name

        sketch.archive()
        self.assertions.assertEqual(sketch.status, "archived")

        # Manually delete the index from OpenSearch
        es = opensearchpy.OpenSearch(
            [
                {
                    "host": interface.OPENSEARCH_HOST,
                    "port": interface.OPENSEARCH_PORT,
                }
            ],
            http_compress=True,
        )
        # Note: Index should be closed now, so delete might need it to be open?
        # Or we can delete a closed index.
        es.indices.delete(index=index_name)

        # Verify it's gone
        self.assertions.assertFalse(es.indices.exists(index=index_name))

        # Try to unarchive
        sketch.unarchive()

        # Should succeed (become ready) despite missing index
        self.assertions.assertEqual(sketch.status, "ready")

        timeline = sketch.list_timelines()[0]

        # So ALL timelines in the sketch are set to 'ready', regardless of
        # index status! This is because timelines and searchindices are
        # separate. SearchIndex status is updated only if in
        # successfully_opened_indexes.

        self.assertions.assertEqual(timeline.status, "fail")

        # Check SearchIndex status
        index = self.api.get_searchindex(index_name)
        # Should be 'archived' because it wasn't successfully opened.
        self.assertions.assertEqual(index.status, "archived")

    def test_unarchive_mixed_indices(self):
        """Test unarchiving a sketch with one good and one missing index.

        Logic:
        1. Create a sketch with two timelines: A (Good) and B (Bad).
        2. B's index is manually deleted to simulate failure.
        3. Archive the sketch.
        4. Unarchive the sketch.
        5. Verify that Timeline A remains READY and Timeline B is FAIL.
        6. Delete the failed Timeline B.
        7. Verify the sketch can be archived and unarchived again successfully.
        8. Verify Timeline A is still READY and searchable.
        """
        sketch_name = f"test-unarchive-mixed_{uuid.uuid4().hex}"
        sketch = self.api.create_sketch(name=sketch_name)

        # Import Timeline A (Good)
        tl_a = self.import_timeline("sigma_events.jsonl", sketch=sketch)

        # Import Timeline B (Bad - will be deleted)
        tl_b = self.import_timeline("evtx_part.csv", sketch=sketch)
        idx_b_name = tl_b.index_name

        sketch.archive()
        self.assertions.assertEqual(sketch.status, "archived")

        # Delete Index B
        es = opensearchpy.OpenSearch(
            [
                {
                    "host": interface.OPENSEARCH_HOST,
                    "port": interface.OPENSEARCH_PORT,
                }
            ],
            http_compress=True,
        )
        es.indices.delete(index=idx_b_name)

        # Unarchive
        sketch.unarchive()

        # Verify Sketch Ready
        self.assertions.assertEqual(sketch.status, "ready")

        # Refetch timelines
        timelines = {t.id: t for t in self.api.get_sketch(sketch.id).list_timelines()}

        # Timeline A should be ready
        self.assertions.assertEqual(timelines[tl_a.id].status, "ready")

        # Timeline B should be fail
        self.assertions.assertEqual(timelines[tl_b.id].status, "fail")

        # Verify we can search Timeline A
        search_client = search.Search(sketch)
        search_client.query_filter.update({"indices": [tl_a.id]})
        results = search_client.table
        self.assertions.assertEqual(len(results), 4)

        # Delete the failed timeline B
        timelines[tl_b.id].delete()

        # Archive again
        sketch.archive()
        self.assertions.assertEqual(sketch.status, "archived")

        # Unarchive again
        sketch.unarchive()
        self.assertions.assertEqual(sketch.status, "ready")

        # Verify Timeline A is still ready and working
        final_timelines = self.api.get_sketch(sketch.id).list_timelines()
        self.assertions.assertEqual(final_timelines[0].status, "ready")

        # Verify search still works
        results = search_client.table
        self.assertions.assertEqual(len(results), 4)

    def test_unarchive_shared_index_missing(self):
        """Test unarchiving when a shared index is missing."""
        sketch_name = f"test-unarchive-shared-missing_{uuid.uuid4().hex}"
        sketch = self.api.create_sketch(name=sketch_name)

        shared_index_name = uuid.uuid4().hex

        # Import Timeline A
        tl_a = self.import_timeline(
            "sigma_events.jsonl", sketch=sketch, index_name=shared_index_name
        )

        # Import Timeline B into same index
        tl_b = self.import_timeline(
            "evtx_part.csv", sketch=sketch, index_name=shared_index_name
        )

        # Verify they share the index
        self.assertions.assertEqual(tl_a.index_name, tl_b.index_name)

        sketch.archive()
        self.assertions.assertEqual(sketch.status, "archived")

        # Delete the shared index
        es = opensearchpy.OpenSearch(
            [
                {
                    "host": interface.OPENSEARCH_HOST,
                    "port": interface.OPENSEARCH_PORT,
                }
            ],
            http_compress=True,
        )
        es.indices.delete(index=shared_index_name)

        # Unarchive
        sketch.unarchive()

        # Both timelines should be 'fail' because their shared index is gone
        timelines = {t.id: t for t in self.api.get_sketch(sketch.id).list_timelines()}
        self.assertions.assertEqual(timelines[tl_a.id].status, "fail")
        self.assertions.assertEqual(timelines[tl_b.id].status, "fail")

    def test_archive_cycle_with_deletion(self):
        """Test archive -> unarchive -> delete timeline -> archive -> unarchive."""
        sketch_name = f"test-archive-cycle_{uuid.uuid4().hex}"
        sketch = self.api.create_sketch(name=sketch_name)

        # 1. Setup: Import Timeline
        timeline = self.import_timeline("sigma_events.jsonl", sketch=sketch)

        # 2. Cycle 1: Archive -> Unarchive
        sketch.archive()
        self.assertions.assertEqual(sketch.status, "archived")

        sketch.unarchive()
        self.assertions.assertEqual(sketch.status, "ready")

        # Verify timeline is ready
        timeline = sketch.list_timelines()[0]
        self.assertions.assertEqual(timeline.status, "ready")

        # 3. Delete Timeline
        timeline.delete()

        # Verify it's gone from list (or deleted status if list includes deleted?)
        # sketch.list_timelines() usually excludes deleted by default in client?
        # Let's check length.
        self.assertions.assertEqual(len(sketch.list_timelines()), 0)

        # 4. Cycle 2: Archive -> Unarchive (Empty sketch)
        sketch.archive()
        self.assertions.assertEqual(sketch.status, "archived")

        sketch.unarchive()
        self.assertions.assertEqual(sketch.status, "ready")


manager.EndToEndTestManager.register_test(ArchiveTest)
