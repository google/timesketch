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


manager.EndToEndTestManager.register_test(ArchiveTest)
