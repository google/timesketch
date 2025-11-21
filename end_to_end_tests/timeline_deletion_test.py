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
import subprocess
import random

from . import interface
from . import manager


class TimelineDeletionTest(interface.BaseEndToEndTest):
    """End to end tests for delete functionality."""

    NAME = "delete_timeline_test"

    def test_delete_failed_timeline(self):
        rand = random.randint(0, 10000)
        sketch = self.api.create_sketch(name=f"test-timeline-deletion_{rand}")
        timeline_name = "test-timeline"
        timeline = sketch.upload(
            file_path="test_data/sigma_events.csv", timeline_name=timeline_name
        )
        timeline.set_status("fail")

        # Delete the timeline
        sketch.delete_timeline(timeline)

        # Check that the search index is archived
        searchindex_name = timeline.searchindex.index_name
        output = subprocess.check_output(
            ["tsctl", "searchindex-info", "--index_name", searchindex_name]
        )
        self.assertIn("Status: archived", output.decode("utf-8"))


manager.EndToEndTestManager.register_test(TimelineDeletionTest)
