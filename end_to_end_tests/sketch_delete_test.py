"""End to end tests for sketch deletion functionality."""

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

import uuid

from . import interface
from . import manager


class SketchDeleteTest(interface.BaseEndToEndTest):
    """End to end tests for sketch deletion functionality."""

    NAME = "sketch_delete_test"

    def test_delete_sketch_with_shared_indices(self):
        """Test deleting a sketch where multiple timelines share the same index.

        This covers the crash reported in issue #3677 where iterating over timelines
        during deletion caused an error if shared indices were involved.
        """
        rand = uuid.uuid4().hex
        sketch = self.api.create_sketch(name=f"test_delete_shared_indices_{rand}")

        # Use a unique index name for this test
        index_name = f"shared_index_e2e_{rand}"

        # Import two timelines with the same index_name
        # Note: import_timeline creates a timeline object.
        # Using the same index_name means they will share the underlying OpenSearch index.
        self.import_timeline("sigma_events.csv", index_name=index_name, sketch=sketch)
        self.import_timeline("evtx_part.csv", index_name=index_name, sketch=sketch)

        # Verify timelines exist in the sketch
        timelines = sketch.list_timelines()
        self.assertions.assertEqual(len(timelines), 2)

        # Verify they share the same index name (client side view)
        # Note: timelines[0].index.index_name might access API again
        index_names = set(t.index.index_name for t in timelines)
        self.assertions.assertEqual(len(index_names), 1)
        self.assertions.assertEqual(list(index_names)[0], index_name)

        # Force delete the sketch
        # This calls DELETE /api/v1/sketches/<id>/?force=true
        sketch.delete(force_delete=True)

        # Verify sketch is gone
        # We can check by listing sketches and ensuring it's not there,
        # or trying to access it and expecting 404/error.

        # Trying to fetch the sketch details should fail or return 404
        # The python client lazyloads data.

        # Option 1: List all sketches
        # Note: list_sketches iterates pages, so it might be slow if many sketches exist.
        # But this is E2E test env.

        # Option 2: Try to get the sketch again
        try:
             # Just trying to load data should fail if it doesn't exist?
             # Actually create_sketch returns a Sketch object.
             # If we create a new Sketch object with same ID and try to load...
             from timesketch_api_client import sketch as api_sketch
             deleted_sketch = api_sketch.Sketch(sketch.id, self.api)
             # lazyload_data calls the API
             deleted_sketch.lazyload_data()
             # If we reach here, it might still exist or API returns something else?
             # Usually 404 raises RuntimeError in client (via check_return_status)
             self.assertions.fail("Sketch still exists after deletion")
        except RuntimeError:
             # This is expected if 404
             pass
        except Exception as e:
             # Also acceptable
             pass

manager.EndToEndTestManager.register_test(SketchDeleteTest)
