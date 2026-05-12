# Copyright 2026 Google Inc. All rights reserved.
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
"""End to end tests for status race condition."""

import time
import subprocess
import threading
from . import interface
from . import manager


class StatusRaceTest(interface.BaseEndToEndTest):
    """End to end tests for status race condition."""

    NAME = "status_race_test"

    def test_tsctl_status_race(self):
        """Test that multiple concurrent tsctl calls don't create duplicate statuses."""
        # 1. Create a sketch and a timeline to get a searchindex
        sketch = self.api.create_sketch(name="TSCTL Race Test")
        self.sketch = sketch

        file_path = (
            "/usr/local/src/timesketch/end_to_end_tests/test_data/sigma_events.csv"
        )
        print("Creating initial timeline...")
        timeline = self.import_timeline(file_path, sketch=sketch)
        self.wait_for_timeline_ready(timeline)
        searchindex_id = timeline.index.id

        # 2. Use multiple threads to call tsctl concurrently
        def call_tsctl():
            cmd = [
                "tsctl",
                "searchindex-status",
                "--action",
                "set",
                "--status",
                "ready",
                "--searchindex_id",
                str(searchindex_id),
            ]
            subprocess.run(cmd, capture_output=True, text=True, check=False)

        print("Triggering concurrent tsctl calls...")
        threads = []
        for _ in range(50):
            t = threading.Thread(target=call_tsctl)
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # 3. Verify the number of statuses
        print("Verifying status count...")
        cmd = [
            "tsctl",
            "searchindex-status",
            "--action",
            "get",
            "--searchindex_id",
            str(searchindex_id),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)

        status_section = result.stdout.split("Full Status Value")[1]
        lines = status_section.strip().splitlines()
        ready_rows = [
            l for l in lines if "ready" in l and not l.strip().startswith("ID")
        ]
        ready_count = len(ready_rows)

        print(
            f"DEBUG: Found {ready_count} ready status entries for searchindex {searchindex_id}"
        )

        # In a race condition, ready_count might be > 1 without the fix.
        # We want to assert it is exactly 1.
        self.assertions.assertEqual(
            ready_count, 1, f"Expected exactly 1 ready status, found {ready_count}"
        )

    def wait_for_timeline_ready(self, timeline, timeout=300):
        """Helper to wait for a timeline to be ready."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            timeline.lazyload_data(refresh_cache=True)
            if timeline.status == "ready" and timeline.index.status == "ready":
                return
            time.sleep(2)
        raise RuntimeError(f"Timeout waiting for timeline {timeline.id}")


manager.EndToEndTestManager.register_test(StatusRaceTest)
