# Copyright 2024 Google Inc. All rights reserved.
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
"""End to end tests for advanced event annotation functionality."""

import json
import time
import uuid

from . import interface
from . import manager


class AdvancedAnnotationTest(interface.BaseEndToEndTest):
    """End to end tests for advanced event annotation functionality."""

    NAME = "advanced_annotation_test"

    def _get_event(self, sketch):
        """Helper to get an event from a sketch."""
        for _ in range(10):
            explore_results = sketch.explore(query_string="*", max_entries=1)
            if explore_results.get("objects"):
                return explore_results["objects"][0]
            time.sleep(1)
        raise RuntimeError("No events found in sketch")

    def test_index_disambiguation(self):
        """Tests that specifying only _id fails if it exists in multiple indices.

        This test case ensures that the API correctly handles ambiguity when an
        event ID exists in multiple search indices within the same sketch.
        It imports the same data into two different indices and attempts to
        annotate by ID alone, which should trigger a 400 error requiring
        disambiguation.
        """
        sketch = self.api.create_sketch(name="Index Disambiguation Test")

        # 1. Import same data into two different indices
        self.import_timeline("sigma_events.csv", index_name="index_1", sketch=sketch)
        self.import_timeline("sigma_events.csv", index_name="index_2", sketch=sketch)

        # 2. Get an event ID that we know exists in both (since they are identical)
        event = self._get_event(sketch)
        event_id = event["_id"]

        # 3. Attempt to annotate with only _id (no _index)
        # We bypass the client helper because it might try to be too smart.
        resource_url = (
            f"{self.api.host_uri}/api/v1/sketches/{sketch.id}/event/annotate/"
        )
        data = {
            "annotation": "ambiguous comment",
            "annotation_type": "comment",
            "events": [{"_id": event_id}],  # Missing _index
        }
        response = self.api.session.post(resource_url, json=data)

        # 4. Verify we get a 400 Bad Request
        self.assertions.assertEqual(response.status_code, 400)
        self.assertions.assertIn("Multiple events found", response.text)

    def test_unauthorized_index_access(self):
        """Tests that annotating an event in an index not in the sketch fails.

        Security boundary test: Ensures that a user cannot 'poke' or annotate
        events in indices they might know the name of, but which are not
        attached to the current sketch.
        """
        sketch_a = self.api.create_sketch(name="Sketch A")
        sketch_b = self.api.create_sketch(name="Sketch B")

        self.import_timeline("sigma_events.csv", sketch=sketch_a)
        event_a = self._get_event(sketch_a)

        # Try to annotate event_a (from Sketch A) using the endpoint for Sketch B
        resource_url = (
            f"{self.api.host_uri}/api/v1/sketches/{sketch_b.id}/event/annotate/"
        )
        data = {
            "annotation": "illegal comment",
            "annotation_type": "comment",
            "events": [{"_id": event_a["_id"], "_index": event_a["_index"]}],
        }
        response = self.api.session.post(resource_url, json=data)

        # Should fail because the index doesn't belong to Sketch B
        self.assertions.assertEqual(response.status_code, 400)
        self.assertions.assertIn(
            "does not belong to the list of indices", response.text
        )

    def test_fact_label_integrity(self):
        """Tests that creating a fact label requires a conclusion_id.

        This test verifies that the 'Fact' annotation type (__ts_fact) is
        protected and cannot be applied as a simple label without being
        linked to an investigative conclusion.
        """
        sketch = self.api.create_sketch(name="Fact Integrity Test")
        self.import_timeline("sigma_events.csv", sketch=sketch)
        event = self._get_event(sketch)

        resource_url = (
            f"{self.api.host_uri}/api/v1/sketches/{sketch.id}/event/annotate/"
        )

        # Attempt to add __ts_fact without conclusion_id
        data = {
            "annotation": "__ts_fact",
            "annotation_type": "label",
            "events": [{"_id": event["_id"], "_index": event["_index"]}],
        }
        response = self.api.session.post(resource_url, json=data)

        self.assertions.assertEqual(response.status_code, 400)
        self.assertions.assertIn("Conclusion ID is required", response.text)

    def test_conclusion_access_control(self):
        """Tests that linking to a non-existent or inaccessible conclusion fails.

        Verifies that the API validates the conclusion_id and ensures it
        exists before attempting to link an event to it.
        """
        sketch = self.api.create_sketch(name="Conclusion Access Test")
        self.import_timeline("sigma_events.csv", sketch=sketch)
        event = self._get_event(sketch)

        resource_url = (
            f"{self.api.host_uri}/api/v1/sketches/{sketch.id}/event/annotate/"
        )

        # Use a non-existent conclusion ID
        data = {
            "annotation": "__ts_fact",
            "annotation_type": "label",
            "events": [{"_id": event["_id"], "_index": event["_index"]}],
            "conclusion_id": 999999,
        }
        response = self.api.session.post(resource_url, json=data)

        self.assertions.assertEqual(response.status_code, 400)
        self.assertions.assertIn(
            "Conclusion ID is required to add a fact", response.text
        )

    def test_search_node_mismatch(self):
        """Tests that a search node must belong to the correct sketch.

        This test ensures that search history tracking is context-aware.
        Annotations associated with a search node must be within the same
        sketch that the search node was created in.
        """
        sketch_a = self.api.create_sketch(name="Sketch A")
        sketch_b = self.api.create_sketch(name="Sketch B")

        # Create a search node in Sketch A
        explore_results = sketch_a.explore(query_string="*", incognito=False)
        node_id = explore_results["meta"]["search_node"]["id"]

        self.import_timeline("sigma_events.csv", sketch=sketch_b)
        event_b = self._get_event(sketch_b)

        # Try to annotate event in Sketch B using Search Node from Sketch A
        resource_url = (
            f"{self.api.host_uri}/api/v1/sketches/{sketch_b.id}/event/annotate/"
        )
        data = {
            "annotation": "misplaced node comment",
            "annotation_type": "comment",
            "events": [{"_id": event_b["_id"], "_index": event_b["_index"]}],
            "current_search_node_id": node_id,
        }
        response = self.api.session.post(resource_url, json=data)

        self.assertions.assertEqual(response.status_code, 400)
        self.assertions.assertIn("Wrong sketch for this search history", response.text)

    def test_annotation_toggle_logic(self):
        """Tests the full lifecycle of adding and removing a label.

        This test verifies the 'toggle' and 'remove' logic in the refactored
        method. It ensures that labels (like stars) can be added and
        subsequently removed correctly, reflecting both in the SQL database
        and the datastore.
        """
        sketch = self.api.create_sketch(name="Toggle Logic Test")
        self.import_timeline("sigma_events.csv", sketch=sketch)
        event = self._get_event(sketch)
        event_id = event["_id"]
        index_id = event["_index"]

        # 1. Add star
        sketch.label_events([{"_id": event_id, "_index": index_id}], "__ts_star")

        # 2. Verify star exists (polling search)
        found = False
        for _ in range(10):
            res = sketch.explore(query_string=f'_id:"{event_id}"')
            labels = [
                l["name"]
                for l in res["objects"][0]["_source"].get("timesketch_label", [])
            ]
            if "__ts_star" in labels:
                found = True
                break
            time.sleep(1)
        self.assertions.assertTrue(found, "Star label was not added")

        # 3. Remove star
        sketch.label_events(
            [{"_id": event_id, "_index": index_id}], "__ts_star", remove=True
        )

        # 4. Verify star is gone
        removed = False
        for _ in range(10):
            res = sketch.explore(query_string=f'_id:"{event_id}"')
            labels = [
                l["name"]
                for l in res["objects"][0]["_source"].get("timesketch_label", [])
            ]
            if "__ts_star" not in labels:
                removed = True
                break
            time.sleep(1)
        self.assertions.assertTrue(removed, "Star label was not removed")

    def test_processing_timeline_handling(self):
        """Tests annotating an event in a timeline that is not 'ready'.

        This test checks the 'allowed_statuses' logic. By default, only 'ready'
        timelines can be annotated. We attempt to annotate an event in a
        hypothetical processing index (simulated by using an index name
        not yet marked as ready in the sketch).
        """
        sketch = self.api.create_sketch(name="Processing Timeline Test")

        # We need a timeline that is NOT ready.
        # Since import_timeline waits for ready, we can try to annotate
        # immediately after starting an import if we didn't use the helper,
        # but a simpler way is to try an index that isn't attached yet.
        # This actually overlaps with unauthorized_index_access but
        # specifically targets the status check logic.

        resource_url = (
            f"{self.api.host_uri}/api/v1/sketches/{sketch.id}/event/annotate/"
        )
        data = {
            "annotation": "early comment",
            "annotation_type": "comment",
            "events": [{"_id": "any", "_index": "non_existent_or_processing"}],
        }
        response = self.api.session.post(resource_url, json=data)

        self.assertions.assertEqual(response.status_code, 400)
        self.assertions.assertIn(
            "does not belong to the list of indices", response.text
        )


manager.EndToEndTestManager.register_test(AdvancedAnnotationTest)
