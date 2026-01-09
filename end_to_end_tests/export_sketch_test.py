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

from . import interface
from . import manager


class ExportSketchTest(interface.BaseEndToEndTest):
    """End to end tests for sketch export."""

    NAME = "export_sketch_test"

    def test_export_sketch(self):
        """Test exporting a sketch (both streamed and regular)."""
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

        # 3. Test Streamed Export
        stream_export_file = f"export_stream_{uuid.uuid4().hex}.zip"
        sketch.export(stream_export_file, stream=True)

        self.assertions.assertTrue(os.path.isfile(stream_export_file))
        self.assertions.assertTrue(zipfile.is_zipfile(stream_export_file))

        with zipfile.ZipFile(stream_export_file, "r") as z:
            self.assertions.assertIn("METADATA", z.namelist())
            metadata = json.loads(z.read("METADATA").decode("utf-8"))
            self.assertions.assertEqual(metadata["sketch_name"], sketch_name)

        os.remove(stream_export_file)


manager.EndToEndTestManager.register_test(ExportSketchTest)
