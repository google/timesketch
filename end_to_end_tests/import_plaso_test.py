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
"""End to end tests of Timesketch upload functionality."""
import random

from . import interface
from . import manager


class ImportPlasoTest(interface.BaseEndToEndTest):
    """End to end tests for plaso upload functionality."""

    NAME = "import_plaso_test"

    def test_plaso_import(self):
        """Test the upload of a plaso file with a few events."""
        # create a new sketch
        rand = random.randint(0, 10000)
        sketch = self.api.create_sketch(name=f"test_plaso_import_{rand}")
        self.sketch = sketch

        file_path = (
            "/usr/local/src/timesketch/end_to_end_tests/test_data/evtx_20250918.plaso"
        )
        self.import_timeline(file_path, sketch=sketch)
        timeline = sketch.list_timelines()[0]
        # check that timeline was uploaded correctly
        self.assertions.assertEqual(timeline.name, file_path)
        self.assertions.assertEqual(timeline.index.status, "ready")

        events = sketch.explore("*", as_pandas=True)
        self.assertions.assertEqual(len(events), 3205)


manager.EndToEndTestManager.register_test(ImportPlasoTest)
