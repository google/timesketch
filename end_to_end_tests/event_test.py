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
import uuid
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
        rand = uuid.uuid4().hex
        sketch = self.api.create_sketch(name=f"test_annotate_event_{rand}")
        self.sketch = sketch

        # 1. Import a timeline with a known event.
        self.import_timeline("sigma_events.csv", sketch=sketch)
        _ = sketch.lazyload_data(refresh_cache=True)

        # 2. Get an event to annotate.
        search_client = search.Search(sketch)
        search_client.query_string = "zmap"
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
        sketch.comment_event(event_id, index_id, comment_text)

        events_to_label = [
            {"_id": event_id, "_index": index_id, "_type": "generic_event"}
        ]
        sketch.label_events(events_to_label, label_text)
        time.sleep(2)  # Added sleep

        # 4. Retrieve the event again to verify the annotations.
        # A short delay might be needed for the changes to be indexed.
        annotated_event_data = None
        # Verify comments (from SQL via get_event)
        for _ in range(20):
            time.sleep(1)
            annotated_event_data = sketch.get_event(event_id, index_id)
            comments = annotated_event_data.get("meta", {}).get("comments", [])
            if len(comments) > 0 and comments[0]["comment"] == comment_text:
                break

        self.assertions.assertEqual(len(comments), 1)
        self.assertions.assertEqual(comments[0]["comment"], comment_text)

        # Verify the label (from OpenSearch via Search, as get_event excludes it)
        found_label = False
        search_result_labels = []
        for _ in range(20):
            time.sleep(1)
            search_obj = search.Search(sketch)
            search_obj.query_string = f'_id:"{event_id}"'
            # Return all fields to be sure
            search_result = json.loads(search_obj.json)

            if search_result["objects"]:
                event_data = search_result["objects"][0]
                source_data = event_data.get("_source", event_data)

                ts_labels = source_data.get("timesketch_label", [])
                search_result_labels = [l.get("name") for l in ts_labels]
                search_result_labels.extend(source_data.get("label", []))

                if label_text in search_result_labels:
                    found_label = True
                    break

        self.assertions.assertTrue(
            found_label,
            (
                f"The test label '{label_text}' was not found on event {event_id} "
                f"in sketch {sketch.id} via search. Found labels: "
                f"{search_result_labels}"
            ),
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
        search_client.query_string = "*"
        search_response = json.loads(search_client.json)
        self.assertions.assertGreater(
            len(search_response["objects"]), 0, "No events found to annotate"
        )
        event_to_annotate = search_response["objects"][0]
        event_id = event_to_annotate["_id"]
        index_id = event_to_annotate["_index"]
        event_type = event_to_annotate.get("_type", "generic_event")
        label_to_toggle = "__ts_star"

        # 3. Add the label.
        events_to_label = [{"_id": event_id, "_index": index_id, "_type": event_type}]
        sketch.label_events(events_to_label, label_to_toggle)

        # 4. Verify the label was added.
        labels_after_add = []
        found_label_add = False
        for _ in range(20):
            time.sleep(1)
            search_obj = search.Search(sketch)
            search_obj.query_string = f'_id:"{event_id}"'
            search_result = json.loads(search_obj.json)

            if search_result["objects"]:
                event_data = search_result["objects"][0]
                source_data = event_data.get("_source", event_data)

                ts_labels = source_data.get("timesketch_label", [])
                labels_after_add = [l.get("name") for l in ts_labels]
                labels_after_add.extend(source_data.get("label", []))

                if label_to_toggle in labels_after_add:
                    found_label_add = True
                    break

        if not found_label_add:
            print(
                f"DEBUG (Add Label Failure): Sketch ID: {sketch.id}, "
                f"Name: {sketch.name}"
            )
            print(
                f"DEBUG (Add Label Failure): Event ID: {event_id}, "
                f"Index ID: {index_id}"
            )
            print(
                f"DEBUG (Add Label Failure): Expected label to add: "
                f"{label_to_toggle}"
            )
            print(
                "DEBUG (Add Label Failure): Labels found in OpenSearch after add: "
                f"{labels_after_add}"
            )
            if search_result["objects"]:
                print(
                    f"DEBUG (Add Label Failure): Full Event Data: "
                    f"{json.dumps(search_result['objects'][0], default=str)}"
                )

        self.assertions.assertTrue(
            found_label_add,
            (
                f"The star label '{label_to_toggle}' was not added to event {event_id} "
                f"in sketch {sketch.id}. Found labels: {labels_after_add}"
            ),
        )

        # 5. Remove the label.
        sketch.label_events(events_to_label, label_to_toggle, remove=True)

        # 6. Verify the label was removed.
        labels_after_remove = []
        label_removed = False
        for _ in range(20):
            time.sleep(1)
            search_obj = search.Search(sketch)
            search_obj.query_string = f'_id:"{event_id}"'
            search_result = json.loads(search_obj.json)

            if search_result["objects"]:
                event_data = search_result["objects"][0]
                source_data = event_data.get("_source", event_data)

                ts_labels = source_data.get("timesketch_label", [])
                labels_after_remove = [l.get("name") for l in ts_labels]
                labels_after_remove.extend(source_data.get("label", []))

                if label_to_toggle not in labels_after_remove:
                    label_removed = True
                    break

                if not label_removed:
                    if search_result["objects"]:
                        print(
                            f"DEBUG (Remove Label Failure): Full Event Data: "
                            f"{json.dumps(search_result['objects'][0], default=str)}"
                        )

        self.assertions.assertTrue(
            label_removed,
            (
                f"star '{label_to_toggle}' was not removed from event {event_id} "
                f"in sketch {sketch.id}. Found labels: "
                f"{labels_after_remove}"
            ),
        )

    def test_explore_with_comment(self):
        """Test exploring events and retrieving comments."""
        rand = uuid.uuid4().hex
        sketch = self.api.create_sketch(
            name=f"test_explore_with_comment_{rand}",
            description="A sketch for explore testing with comments",
        )

        # 1. Import a timeline with a known event.
        self.import_timeline("sigma_events.csv", sketch=sketch)
        _ = sketch.lazyload_data(refresh_cache=True)

        # 2. Get an event to annotate.
        search_client = search.Search(sketch)
        search_client.query_string = "*"
        search_response = json.loads(search_client.json)
        self.assertions.assertGreater(
            len(search_response["objects"]), 0, "No events found to annotate"
        )
        event_to_annotate = search_response["objects"][0]
        event_id = event_to_annotate["_id"]
        index_id = event_to_annotate["_index"]

        # 3. Add a comment.
        comment_text = "This is a test comment for explore."
        sketch.comment_event(event_id, index_id, comment_text)
        # 4. Explore for the event and request the comment field.
        comments = []
        for _ in range(20):
            time.sleep(1)
            explore_response = sketch.explore(
                query_string=f'_id:"{event_id}"',
                return_fields="comment",
            )

            explore_objects = explore_response.get("objects", [])
            if len(explore_objects) == 1:
                event_source = explore_objects[0].get("_source", {})
                comments = event_source.get("comment", [])
                if len(comments) == 1 and comments[0] == comment_text:
                    break

        self.assertions.assertEqual(len(explore_objects), 1)
        self.assertions.assertEqual(len(comments), 1)
        self.assertions.assertEqual(comments[0], comment_text)


manager.EndToEndTestManager.register_test(EventTest)
