# Copyright 2020 Google Inc. All rights reserved.
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
"""End to end tests of Timesketch event functionality."""

import json
import time

from timesketch_api_client import search

from . import interface
from . import manager


class EventTest(interface.BaseEndToEndTest):
    """End to end tests for event functionality."""

    NAME = "event_test"

    def test_add_event_attributes(self):
        """Tests adding attributes to an event."""
        sketch = self.api.create_sketch(name="Add event attributes test")
        sketch.add_event("event message", "2020-01-01T00:00:00", "timestamp_desc")

        # Wait for new timeline and event to be created, retrying 5 times.
        for _ in range(5):
            search_client = search.Search(sketch)
            search_response = json.loads(search_client.json)
            objects = search_response.get("objects")
            if objects:
                old_event = search_response["objects"][0]
                break
            time.sleep(1)
        else:
            raise RuntimeError("Event creation failed for test.")

        events = [
            {
                "_id": old_event["_id"],
                "_index": old_event["_index"],
                "attributes": [{"attr_name": "foo", "attr_value": "bar"}],
            }
        ]

        response = sketch.add_event_attributes(events)
        new_event = sketch.get_event(old_event["_id"], old_event["_index"])
        self.assertions.assertEqual(
            response,
            {
                "meta": {
                    "attributes_added": 1,
                    "chunks_per_index": {old_event["_index"]: 1},
                    "error_count": 0,
                    "last_10_errors": [],
                    "events_modified": 1,
                },
                "objects": [],
            },
        )
        self.assertions.assertIn("foo", new_event["objects"])

    def test_add_event_attributes_invalid(self):
        """Tests adding invalid attributes to an event."""
        sketch = self.api.create_sketch(name="Add invalid attributes test")
        sketch.add_event(
            "original message",
            "2020-01-01T00:00:00",
            "timestamp_desc",
            attributes={"existing_attr": "original_value"},
        )

        # Wait for new timeline and event to be created, retrying 5 times.
        for _ in range(5):
            search_client = search.Search(sketch)
            search_response = json.loads(search_client.json)
            objects = search_response.get("objects")
            if objects:
                old_event = search_response["objects"][0]
                break
            time.sleep(1)
        else:
            raise RuntimeError("Event creation failed for test.")

        # Have to use search to get event_id
        search_client = search.Search(sketch)
        search_response = json.loads(search_client.json)
        old_event = search_response["objects"][0]

        events = [
            {
                "_id": old_event["_id"],
                "_index": old_event["_index"],
                "attributes": [
                    {"attr_name": "existing_attr", "attr_value": "new_value"},
                    {"attr_name": "message", "attr_value": "new message"},
                ],
            }
        ]

        response = sketch.add_event_attributes(events)
        # Confirm the error lines are generated for the invalid attributes.
        self.assertions.assertIn(
            f"Attribute 'existing_attr' already exists for event_id "
            f"'{old_event['_id']}'.",
            response["meta"]["last_10_errors"],
        )
        self.assertions.assertIn(
            f"Cannot add 'message' for event_id '{old_event['_id']}', name not "
            f"allowed.",
            response["meta"]["last_10_errors"],
        )

        new_event = sketch.get_event(old_event["_id"], old_event["_index"])
        # Confirm attributes have not been changed.
        self.assertions.assertEqual(new_event["objects"]["message"], "original message")
        self.assertions.assertEqual(
            new_event["objects"]["existing_attr"], "original_value"
        )

    def test_annotate_event(self):
        """Test annotating an event with a comment and a label."""
        sketch = self.api.create_sketch(
            name="test_annotate_event", description="A sketch for annotation testing"
        )

        # 1. Import a timeline with a known event.
        self.import_timeline("sigma_events.csv", sketch=sketch)
        _ = sketch.lazyload_data(refresh_cache=True)

        # 2. Get an event to annotate.
        search_client = search.Search(sketch)
        search_client.query_string = 'source_short:"LOG"'
        search_response = json.loads(search_client.json)
        self.assertions.assertGreater(
            len(search_response["objects"]), 0, "No events found to annotate"
        )
        event_to_annotate = search_response["objects"][0]
        event_id = event_to_annotate["_id"]
        index_id = event_to_annotate["_index"]

        # 3. Add a comment and a label.
        comment_text = "This is a test comment."
        label_text = "test_label"
        sketch.add_comment_to_event(event_id, index_id, comment_text)
        sketch.add_label_to_event(event_id, index_id, label_text)

        # 4. Retrieve the event again to verify the annotations.
        # A short delay might be needed for the changes to be indexed.
        time.sleep(2)
        annotated_event_data = sketch.get_event(event_id, index_id)

        # Verify the comment
        comments = annotated_event_data.get("meta", {}).get("comments", [])
        self.assertions.assertEqual(len(comments), 1)
        self.assertions.assertEqual(comments[0]["comment"], comment_text)

        # Verify the label
        labels = annotated_event_data.get("objects", {}).get("label", [])
        self.assertions.assertIn(
            label_text, labels, "The test label was not found on the event."
        )

    def test_toggle_event_label(self):
        """Test toggling a label on an event."""
        sketch = self.api.create_sketch(
            name="test_toggle_event_label",
            description="A sketch for label toggling",
        )

        # 1. Import a timeline with a known event.
        self.import_timeline("sigma_events.csv", sketch=sketch)
        _ = sketch.lazyload_data(refresh_cache=True)

        # 2. Get an event to annotate.
        search_client = search.Search(sketch)
        search_client.query_string = 'source_short:"LOG"'
        search_response = json.loads(search_client.json)
        self.assertions.assertGreater(
            len(search_response["objects"]), 0, "No events found to annotate"
        )
        event_to_annotate = search_response["objects"][0]
        event_id = event_to_annotate["_id"]
        index_id = event_to_annotate["_index"]
        label_to_toggle = "__ts_star"

        # 3. Add the label.
        sketch.add_label_to_event(event_id, index_id, label_to_toggle)

        # 4. Verify the label was added.
        time.sleep(2)  # Allow for indexing.
        event_after_add = sketch.get_event(event_id, index_id)
        labels_after_add = event_after_add.get("objects", {}).get("label", [])
        self.assertions.assertIn(
            label_to_toggle, labels_after_add, "The star label was not added."
        )

        # 5. Remove the label.
        sketch.add_label_to_event(event_id, index_id, label_to_toggle, remove=True)

        # 6. Verify the label was removed.
        time.sleep(2)  # Allow for indexing.
        event_after_remove = sketch.get_event(event_id, index_id)
        labels_after_remove = event_after_remove.get("objects", {}).get("label", [])
        self.assertions.assertNotIn(
            label_to_toggle,
            labels_after_remove,
            "The star label was not removed.",
        )


manager.EndToEndTestManager.register_test(EventTest)
