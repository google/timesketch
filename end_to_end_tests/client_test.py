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
"""End to end tests of Timesketch client functionality."""

import uuid
import json
import random
import os
import time

from timesketch_api_client import search

from . import interface
from . import manager


class ClientTest(interface.BaseEndToEndTest):
    """End to end tests for client functionality."""

    NAME = "client_test"
    RULEID1 = str(uuid.uuid4())
    RULEID2 = str(uuid.uuid4())

    def test_client(self):
        """Client tests."""
        expected_user = "test"
        user = self.api.current_user
        self.assertions.assertEqual(user.username, expected_user)
        self.assertions.assertEqual(user.is_admin, False)
        self.assertions.assertEqual(user.is_active, True)

        sketches = list(self.api.list_sketches())
        number_of_sketches = len(sketches)

        sketch_name = "Testing"
        sketch_description = "This is truly a foobar"
        new_sketch = self.api.create_sketch(
            name=sketch_name, description=sketch_description
        )

        self.assertions.assertEqual(new_sketch.name, sketch_name)
        self.assertions.assertEqual(new_sketch.description, sketch_description)

        sketches = list(self.api.list_sketches())
        self.assertions.assertEqual(len(sketches), number_of_sketches + 1)

        for index in self.api.list_searchindices():
            if index is None:
                continue
            self.assertions.assertTrue(bool(index.index_name))

    def test_direct_opensearch(self):
        """Test injecting data into OpenSearch directly."""
        index_name = "direct_testing"

        self.import_directly_to_opensearch(
            filename="evtx_direct.csv", index_name=index_name
        )

        new_sketch = self.api.create_sketch(
            name="Testing Direct", description="Adding data directly from ES"
        )

        context = "e2e - > test_direct_opensearch"
        timeline_name = "Ingested Via Mechanism"
        timeline = new_sketch.generate_timeline_from_es_index(
            es_index_name=index_name,
            name=timeline_name,
            provider="end_to_end_testing_platform",
            context=context,
        )

        _ = new_sketch.lazyload_data(refresh_cache=True)
        self.assertions.assertEqual(len(new_sketch.list_timelines()), 1)
        self.assertions.assertEqual(timeline.name, timeline_name)

        data_sources = timeline.data_sources
        self.assertions.assertEqual(len(data_sources), 1)
        data_source = data_sources[0]
        self.assertions.assertEqual(data_source.get("context", ""), context)

    def test_sigmarule_create(self):
        """Create a Sigma rule in database"""

        MOCK_SIGMA_RULE = f"""
title: Suspicious Installation of bbbbbb
id: {self.RULEID1}
description: Detects suspicious installation of bbbbbb
references:
    - https://rmusser.net/docs/ATT&CK-Stuff/ATT&CK/Discovery.html
author: Alexander Jaeger
date: 2020/06/26
modified: 2022/06/12
logsource:
    product: linux
    service: shell
detection:
    keywords:
        # Generic suspicious commands
        - '*apt-get install bbbbbb*'
    condition: keywords
falsepositives:
    - Unknown
level: high
"""
        rule = self.api.create_sigmarule(rule_yaml=MOCK_SIGMA_RULE)
        self.assertions.assertIsNotNone(rule)

    def test_sigmarule_list(self):
        """Client Sigma list tests."""
        rules = self.api.list_sigmarules()
        self.assertions.assertGreaterEqual(len(rules), 1)
        rule = rules[0]
        self.assertions.assertIn("Installation of bbbbbb", rule.title)

        self.assertions.assertIn("installation of bbbbbb", rule.description)

    def test_sigmarule_create_get(self):
        """Client Sigma object tests."""

        rule = self.api.create_sigmarule(
            rule_yaml=f"""
title: Suspicious Installation of eeeee
id: {self.RULEID2}
description: Detects suspicious installation of eeeee
references:
    - https://rmusser.net/docs/ATT&CK-Stuff/ATT&CK/Discovery.html
author: Alexander Jaeger
date: 2020/06/26
modified: 2022/06/12
logsource:
    product: linux
    service: shell
detection:
    keywords:
        # Generic suspicious commands
        - '*apt-get install zmap*'
    condition: keywords
falsepositives:
    - Unknown
level: high
"""
        )
        self.assertions.assertIsNotNone(rule)

        rule = self.api.get_sigmarule(rule_uuid=self.RULEID2)
        rule.from_rule_uuid(self.RULEID2)
        self.assertions.assertGreater(len(rule.attributes), 5)
        self.assertions.assertIsNotNone(rule)
        self.assertions.assertIn("Alexander", rule.author)
        self.assertions.assertIn("Alexander", rule.get_attribute("author"))
        self.assertions.assertIn(self.RULEID2, rule.id)
        self.assertions.assertIn("Installation of eeeee", rule.title)
        self.assertions.assertIn("zmap", rule.search_query)
        self.assertions.assertIn("shell:zsh:history", rule.search_query)
        self.assertions.assertIn(self.RULEID2, rule.resource_uri)
        self.assertions.assertIn("installation of eeeee", rule.description)
        self.assertions.assertIn("high", rule.level)
        self.assertions.assertEqual(len(rule.falsepositives), 1)
        self.assertions.assertIn("Unknown", rule.falsepositives[0])
        self.assertions.assertIn("2020/06/26", rule.date)
        self.assertions.assertIn("2022/06/12", rule.modified)
        self.assertions.assertIn("high", rule.level)
        self.assertions.assertIn("rmusser.net", rule.references[0])
        self.assertions.assertEqual(len(rule.detection), 2)
        self.assertions.assertEqual(len(rule.logsource), 2)

        # Test an actual query
        self.import_timeline("sigma_events.csv")
        search_obj = search.Search(self.sketch)
        search_obj.query_string = rule.search_query
        data_frame = search_obj.table
        count = len(data_frame)
        self.assertions.assertEqual(count, 1)

    def test_sigmarule_remove(self):
        """Client Sigma delete tests.
        The test is called remove to avoid running it before the create test.
        """
        rule = self.api.get_sigmarule(rule_uuid=self.RULEID1)
        self.assertions.assertGreater(len(rule.attributes), 5)
        rule.delete()

        rules = self.api.list_sigmarules()
        self.assertions.assertGreaterEqual(len(rules), 1)

        rule = self.api.get_sigmarule(rule_uuid=self.RULEID2)
        self.assertions.assertGreater(len(rule.attributes), 5)
        rule.delete()
        rules = self.api.list_sigmarules()
        self.assertions.assertGreaterEqual(len(rules), 0)

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

    def test_create_sketch_empty_name(self):
        """Test creating a sketch with an empty name."""
        with self.assertions.assertRaises(ValueError) as context:
            self.api.create_sketch(name="", description="test_create_sketch")
        self.assertions.assertIn("Sketch name cannot be empty", str(context.exception))

    def test_archive_sketch(self):
        """Test archiving and unarchiving a sketch."""
        sketch = self.api.create_sketch(
            name="test_archive_sketch", description="test_archive_sketch"
        )
        # check status before archiving
        self.assertions.assertEqual(sketch.status, "new")
        sketch.archive()
        self.assertions.assertEqual(sketch.status, "archived")
        sketch.unarchive()
        self.assertions.assertEqual(sketch.status, "ready")

    def test_delete_sketch(self):
        """Test deleting a sketch."""
        sketches = list(self.api.list_sketches())
        number_of_sketches = len(sketches)

        sketch = self.api.create_sketch(
            name="test_delete_sketch", description="test_delete_sketch"
        )

        sketches = list(self.api.list_sketches())
        self.assertions.assertEqual(len(sketches), number_of_sketches + 1)

        # store sketch_id of the newly created sketch
        sketch_id = sketch.id

        # check that sketch is in the sketch list
        sketches = self.api.list_sketches()
        found = False
        for s in sketches:
            if s.name == "test_delete_sketch":
                found = True

        self.assertions.assertEqual(found, True)

        # delete sketch
        sketch.delete()

        sketches = list(self.api.list_sketches())
        self.assertions.assertEqual(len(sketches), number_of_sketches)
        # attempt to pull sketch
        # breakpoint()
        with self.assertions.assertRaises(RuntimeError):
            self.api.get_sketch(sketch_id).name  # pylint: disable=W0106

    # test to delete a sketch that is archived
    def test_delete_archived_sketch(self):
        """Test deleting an archived sketch."""
        sketch = self.api.create_sketch(
            name="test_delete_archived_sketch",
            description="test_delete_archived_sketch",
        )
        sketch.archive()
        with self.assertions.assertRaises(RuntimeError) as context:
            sketch.delete()
        self.assertions.assertIn(
            "Unable to delete an archived sketch, first unarchive then delete.",
            str(context.exception),
        )

    def test_modify_sketch_name_description(self):
        """Test modifying a sketch's name and description."""
        sketch = self.api.create_sketch(
            name="test_modify_sletch_name_description",
            description="test_modify_sletch_name_description",
        )
        sketch.name = "new_name"
        sketch.description = "new_description"
        self.assertions.assertEqual(sketch.name, "new_name")
        self.assertions.assertEqual(sketch.description, "new_description")
        # check in the sketch list
        sketches = self.api.list_sketches()
        # find the right one in the sketch list
        for s in sketches:
            if s.name == "new_name":
                sketch2 = s
                break
        else:
            raise RuntimeError("Sketch not found")

        self.assertions.assertEqual(sketch2.name, "new_name")
        self.assertions.assertEqual(sketch2.description, "new_description")

    def test_modify_sketch_with_empty_name(self):
        """Test modifying a sketch with an empty name.
        They should not be used, thus keeping the old names.
        """
        sketch = self.api.create_sketch(
            name="test_modify_sketch_with_empty_name",
            description="test_modify_sketch_with_empty_name",
        )
        sketch.name = ""
        sketch.description = ""

        # values should not be changed
        self.assertions.assertEqual(sketch.name, "test_modify_sketch_with_empty_name")
        self.assertions.assertEqual(
            sketch.description, "test_modify_sketch_with_empty_name"
        )

    def test_list_timelines(self):
        """Test listing timelines in a sketch."""
        # Create a new sketch
        sketch = self.api.create_sketch(
            name="test_list_timelines", description="test_list_timelines"
        )

        # Import a timeline into the sketch
        self.import_timeline("evtx.plaso", sketch=sketch)

        # List the timelines in the sketch
        timelines = sketch.list_timelines()

        # Check that there is at least one timeline
        self.assertions.assertGreaterEqual(len(timelines), 1)

        # Check that the timeline has a name
        for timeline in timelines:
            self.assertions.assertTrue(timeline.name)

        # Check that the timeline has an index name
        for timeline in timelines:
            self.assertions.assertTrue(timeline.index_name)

        # Check that the timeline has an ID
        for timeline in timelines:
            self.assertions.assertTrue(timeline.id)

        # Import a second timeline into the sketch
        self.import_timeline("evtx_part.csv", sketch=sketch)

        _ = sketch.lazyload_data(refresh_cache=True)

        # List the timelines in the sketch
        timelines = sketch.list_timelines()

        # Check that there are two timelines
        self.assertions.assertEqual(len(timelines), 2)

    def test_delete_timeline(self):
        """Test deleting a timeline.
        This test verifies the following:
            - A new sketch can be created.
            - A timeline can be imported into the sketch.
            - The timeline's name, index name, and index status are correct.
            - The number of events in the sketch is correct
                after importing the timeline.
            - A second timeline can be imported into the sketch.
            - The total number of events in the sketch is correct after
                importing the second timeline.
            - A timeline can be deleted.
            - The number of events in the sketch is correct after deleting
                 a timeline.
            - The number of timelines in the sketch is correct after
                deleting a timeline.
        Raises:
            AssertionError: If any of the assertions fail.
            RuntimeError: If the event creation fails.
            RuntimeError: If the sketch is not found.
        """

        # create a new sketch
        rand = random.randint(0, 10000)
        sketch = self.api.create_sketch(
            name=f"test_delete_timeline {rand}", description="test_delete_timeline"
        )
        self.sketch = sketch

        file_path = (
            "/usr/local/src/timesketch/end_to_end_tests/test_data/sigma_events.jsonl"
        )

        self.import_timeline(file_path, index_name=rand, sketch=sketch)
        timeline = sketch.list_timelines()[0]
        # check that timeline was uploaded correctly
        self.assertions.assertEqual(timeline.name, file_path)
        self.assertions.assertEqual(timeline.index.name, str(rand))
        self.assertions.assertEqual(timeline.index.status, "ready")
        self.assertions.assertEqual(len(sketch.list_timelines()), 1)

        events = sketch.explore("*", as_pandas=True)
        self.assertions.assertEqual(len(events), 4)

        # second import

        file_path = "/tmp/second.csv"

        with open(file_path, "w", encoding="utf-8") as file_object:
            file_object.write(
                '"message","timestamp","datetime","timestamp_desc","data_type"\n'
            )

            for i in range(5):
                # write a line with random values for message
                string = (
                    f'"CSV Count: {i} {rand}","123456789",'
                    '"2015-07-24T19:01:01+00:00","Write time","foobarcsv"\n'
                )
                file_object.write(string)

        self.import_timeline("/tmp/second.csv", index_name="second", sketch=sketch)
        os.remove(file_path)
        # refresh data after import
        _ = sketch.lazyload_data(refresh_cache=True)

        timeline = sketch.list_timelines()[0]
        self.assertions.assertEqual(len(sketch.list_timelines()), 2)

        # Check that there are 9 (5+4) events in total
        search_client = search.Search(sketch)
        search_response = json.loads(search_client.json)
        self.assertions.assertEqual(len(search_response["objects"]), 9)

        events = sketch.explore("*", as_pandas=True)
        self.assertions.assertEqual(len(events), 9)

        # delete timeline 1
        # now it should be 5 events in one timeline
        timeline.delete()
        events = sketch.explore("*", as_pandas=True)
        self.assertions.assertEqual(len(events), 5)

        # check number of timelines
        _ = sketch.lazyload_data(refresh_cache=True)
        self.assertions.assertEqual(len(sketch.list_timelines()), 1)


manager.EndToEndTestManager.register_test(ClientTest)
