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
"""End to end tests for export stream functionality."""

from . import interface
from . import manager


class ExportStreamTest(interface.BaseEndToEndTest):
    """End to end tests for export stream functionality."""

    NAME = "export_stream_test"
    TEST_PLASO_FILE = "evtx_20250918.plaso"

    def setup(self):
        """Import test timeline."""
        self.import_timeline(self.TEST_PLASO_FILE)

    def test_export_all(self):
        """Test streaming export of all events."""
        # Export all events
        events = self.sketch.export_events_stream()

        # Consume the generator to count events
        count = len(list(events))

        # 3205 is the known event count for evtx_20250918.plaso
        self.assertions.assertEqual(count, 3205)

    def test_export_subset(self):
        """Test streaming export of partial events."""
        # Export only events with data_type:"fs:stat"
        events = self.sketch.export_events_stream(query_string='data_type:"fs:stat"')

        # Consume the generator to count events
        count = len(list(events))

        # 3 is the known event count for data_type:"fs:stat" in evtx_20250918.plaso
        self.assertions.assertEqual(count, 3)

    def test_export_fields(self):
        """Test streaming export with field selection."""
        # Export only a few fields
        events = self.sketch.export_events_stream(
            query_string='data_type:"fs:stat"', return_fields=["data_type", "message"]
        )
        first_event = next(events)
        # 1. Assert required fields are present (and others are not)
        self.assertions.assertIn("data_type", first_event)
        self.assertions.assertIn("message", first_event)
        self.assertions.assertNotIn(
            "timestamp_desc", first_event
        )  # this field should not be present
        # 2. Assert total count is still correct
        count = len(list(events)) + 1  # +1 for the event consumed by next()
        self.assertions.assertEqual(count, 3)


manager.EndToEndTestManager.register_test(ExportStreamTest)
