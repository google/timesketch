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
"""End to end tests for export functionality."""

from . import interface
from . import manager


class ExportStreamTest(interface.BaseEndToEndTest):
    """End to end tests for export functionality."""

    NAME = "export_stream_test"

    def setUp(self):
        """Import test timeline."""
        super().setUp()
        self.import_timeline("evtx_20250918.plaso")

    def test_export(self):
        """Test streaming export of events."""
        events = self.sketch.export_events_stream(
            query_string="*", return_fields=["message", "timestamp"]
        )
        count = len(list(events))
        self.assertions.assertEqual(count, 3205)


manager.EndToEndTestManager.register_test(ExportStreamTest)
