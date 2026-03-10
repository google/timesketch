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
"""End to end tests for sketch export."""

import os
import uuid
import zipfile
import json
import time
import csv
import io

from . import interface
from . import manager


class ExportSketchTest(interface.BaseEndToEndTest):
    """End to end tests for sketch export."""

    NAME = "export_sketch_test"

    def test_export_sketch(self):
        """Test exporting a sketch (regular non-streamed)."""
        # 1. Create a sketch with some data
        sketch_name = f"test-export_{uuid.uuid4().hex}"
        sketch = self.api.create_sketch(name=sketch_name)

        # Import a timeline
        self.import_timeline("sigma_events.jsonl", sketch=sketch)

        # 2. Test Regular Export (Non-streamed)
        export_file = f"export_{uuid.uuid4().hex}.zip"
        sketch.export(export_file)

        self.assertions.assertTrue(os.path.isfile(export_file))
        self.assertions.assertTrue(zipfile.is_zipfile(export_file))

        with zipfile.ZipFile(export_file, "r") as z:
            # Check for metadata file which is always present in full export
            self.assertions.assertIn("METADATA", z.namelist())
            metadata = json.loads(z.read("METADATA").decode("utf-8"))
            self.assertions.assertEqual(metadata["sketch_name"], sketch_name)

        os.remove(export_file)

    def test_export_sketch_streamed(self):
        """Test exporting a sketch using streaming."""
        # 1. Create a sketch with some data
        sketch_name = f"test-export-stream_{uuid.uuid4().hex}"
        sketch = self.api.create_sketch(name=sketch_name)

        # Import a timeline
        self.import_timeline("sigma_events.jsonl", sketch=sketch)

        # 2. Test Streamed Export
        stream_export_file = f"export_stream_{uuid.uuid4().hex}.zip"
        sketch.export(stream_export_file, stream=True)

        self.assertions.assertTrue(os.path.isfile(stream_export_file))
        self.assertions.assertTrue(zipfile.is_zipfile(stream_export_file))

        with zipfile.ZipFile(stream_export_file, "r") as z:
            self.assertions.assertIn("METADATA", z.namelist())
            metadata = json.loads(z.read("METADATA").decode("utf-8"))
            self.assertions.assertEqual(metadata["sketch_name"], sketch_name)

        os.remove(stream_export_file)

    def test_export_sketch_count_integrity(self):
        """Verify that the exported event count matches the expected count.
        
        This test uses 20,000 events to trigger the scrolling logic (10k batches)
        and ensure that exactly 20,000 events are returned without duplicates
        or extra batches.
        """
        # 1. Setup: Create a sketch and import 20,000 events
        sketch_name = f"count-integrity-{uuid.uuid4().hex}"
        sketch = self.api.create_sketch(name=sketch_name)

        target_count = 20000
        print(f"  Importing {target_count} events into sketch {sketch.id}...")
        self.import_timeline("integrity_check.jsonl", sketch=sketch)

        # 2. Export via API
        export_file = f"integrity_{uuid.uuid4().hex}.zip"
        print("  Exporting sketch via API...")
        sketch.export(export_file)

        try:
            self.assertions.assertTrue(os.path.exists(export_file))
            with zipfile.ZipFile(export_file, "r") as z:
                # Find all event CSV files
                csv_files = [f for f in z.namelist() if f.endswith(".csv") and f != "METADATA"]
                self.assertions.assertTrue(len(csv_files) > 0, "No CSV files found in export archive")
                
                total_exported = 0
                for csv_file in csv_files:
                    content = z.read(csv_file).decode("utf-8")
                    reader = csv.reader(io.StringIO(content))
                    rows = list(reader)
                    # Subtract 1 for the header
                    if len(rows) > 1:
                        total_exported += (len(rows) - 1)
                
                self.assertions.assertEqual(
                    total_exported, target_count, 
                    f"Export count mismatch. Expected {target_count}, got {total_exported}"
                )
            print("  SUCCESS: Export count integrity verified.")
        finally:
            if os.path.exists(export_file):
                os.remove(export_file)


manager.EndToEndTestManager.register_test(ExportSketchTest)
