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
"""End to end tests of Timesketch upload functionality with filter."""

import uuid
import os
import time
from timesketch_import_client import importer
from . import interface
from . import manager


class ImportPlasoFilterTest(interface.BaseEndToEndTest):
    """End to end tests for plaso upload functionality with filter."""

    NAME = "import_plaso_filter_test"

    def import_timeline(
        self, filename, index_name=None, sketch=None, filter_expression=None
    ):
        """Import a Plaso file with an optional filter.

        Args:
            filename (str): Filename of the file to be imported.
            index_name (str): The OpenSearch index to store the documents in.
            sketch (Sketch): Optional sketch object to add the timeline to.
            filter_expression (str): Plaso event filter expression.

        Returns:
            The created timeline object.
        """
        if not sketch:
            sketch = self.sketch

        file_path = os.path.join(interface.TEST_DATA_DIR, filename)
        if not index_name:
            index_name = uuid.uuid4().hex

        with importer.ImportStreamer() as streamer:
            streamer.set_sketch(sketch)
            streamer.set_timeline_name(f"{os.path.basename(file_path)}_filtered")
            streamer.set_index_name(index_name)
            streamer.set_provider("e2e test interface")
            if filter_expression:
                streamer.set_plaso_event_filter(filter_expression)
            streamer.add_file(file_path)
            timeline = streamer.timeline

        # Poll for readiness (simplified from base class for this specific test)
        max_retries = 30
        for _ in range(max_retries):
            try:
                if timeline:
                    timeline.lazyload_data(refresh_cache=True)
                    if timeline.status == "ready":
                        break
                    if timeline.status == "fail":
                        raise RuntimeError(
                            f"Timeline failed processing: {timeline.status}"
                        )
            except Exception as e:  # pylint: disable=broad-exception-caught
                print(f"An exception occurred while polling for timeline status: {e}")
            time.sleep(2)

        return timeline

    def test_plaso_import_with_filter(self):
        """Test the upload of a plaso file with a filter."""
        # create a new sketch
        rand = uuid.uuid4().hex
        sketch = self.api.create_sketch(name=f"test_plaso_filter_import_{rand}")
        self.sketch = sketch

        file_name = "evtx_20250918.plaso"

        # This filter should limit the number of events to 3.
        filter_expression = 'data_type is "fs:stat"'

        timeline = self.import_timeline(
            file_name, sketch=sketch, filter_expression=filter_expression
        )

        # check that timeline was uploaded correctly
        self.assertions.assertIsNotNone(timeline)
        self.assertions.assertEqual(timeline.index.status, "ready")

        events = sketch.explore("*", as_pandas=True)
        # Verify events are present and the filter worked.
        self.assertions.assertEqual(len(events), 3)


manager.EndToEndTestManager.register_test(ImportPlasoFilterTest)
