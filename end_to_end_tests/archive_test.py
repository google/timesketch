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
import os
import time
import opensearchpy

from . import interface
from . import manager


class ArchiveTest(interface.BaseEndToEndTest):
    """End to end tests for sketch archiving."""

    NAME = "archive_test"

    def test_archive_sketch_with_failed_timeline(self):
        """Test archiving a sketch with a failed timeline."""
        sketch = self.api.create_sketch(name="test-archive-failed")
        self.sketch = sketch
        self.assertions.assertIsNotNone(sketch)

        # This file is known to cause an import failure.
        file_path = os.path.join(
            os.path.dirname(__file__), "test_data", "invalid_jsonl.jsonl"
        )
        timeline = self.import_timeline(file_path, sketch=sketch)

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
        sketch = self.api.create_sketch(name="test-unarchive-failed")
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
        sketch = self.api.create_sketch(name="test-unarchive-missing-index")
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

        timeline = self.api.get_sketch(sketch.id).list_timelines()[0]

        # So ALL timelines in the sketch are set to 'ready', regardless of
        # index status! This is because timelines and searchindices are
        # separate. SearchIndex status is updated only if in
        # successfully_opened_indexes.

        self.assertions.assertEqual(timeline.status, "fail")

        # Check SearchIndex status
        index = self.api.get_searchindex(index_name)
        # Should be 'archived' because it wasn't successfully opened.
        self.assertions.assertEqual(index.status, "archived")


manager.EndToEndTestManager.register_test(ArchiveTest)
