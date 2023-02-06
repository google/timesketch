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

import json
import time

from timesketch_api_client import search

from . import interface, manager


class ClientTest(interface.BaseEndToEndTest):
    """End to end tests for client functionality."""

    NAME = "client_test"

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
        single_index_name = "direct_testing"
        multiple_index = "index-multiple"

        self.import_directly_to_opensearch(
            filename="evtx_direct.csv", index_name=single_index_name
        )
        self.import_directly_to_opensearch(
            filename="sigma_events_multiple.csv", index_name=multiple_index
        )

        new_sketch = self.api.create_sketch(
            name="Testing Direct", description="Adding data directly from ES"
        )

        context = "e2e - > test_direct_opensearch"
        timeline = new_sketch.generate_timeline_from_es_index(
            es_index_name=single_index_name,
            name="Ingested Via Mechanism",
            provider="end_to_end_testing_platform",
            context=context,
        )
        multi_timeline = []
        for i in range(0, 3):
            multi_timeline.append(
                new_sketch.generate_timeline_from_es_index(
                    es_index_name=multiple_index,
                    name=f"Ingested Via Mechanism - {i}",
                    provider="end_to_end_testing_platform",
                    context=context,
                    timeline_filter_id=i,
                )
            )

        _ = new_sketch.lazyload_data(refresh_cache=True)
        self.assertions.assertEqual(len(new_sketch.list_timelines()), 4)
        self.assertions.assertEqual(timeline.name, "Ingested Via Mechanism")

        for i in range(0, 3):
            self.assertions.assertEqual(
                multi_timeline[i].name, f"Ingested Via Mechanism - {i}"
            )
            # Verify amount of events in timeline
            search_obj = search.Search(new_sketch)
            search_obj.query_string = f"__ts_timeline_filter_id:{i}"
            self.assertions.assertEqual(len(search_obj.table), 1)

        data_sources = timeline.data_sources
        self.assertions.assertEqual(len(data_sources), 1)
        data_source = data_sources[0]
        self.assertions.assertEqual(data_source.get("context", ""), context)

    def test_create_sigma_rule(self):
        """Create a Sigma rule in database"""
        MOCK_SIGMA_RULE = """
title: Suspicious Installation of bbbbbb
id: 5266a592-b793-11ea-b3de-bbbbbb
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

    def test_sigma_list(self):
        """Client Sigma list tests."""
        rules = self.api.list_sigma_rules()
        self.assertions.assertGreaterEqual(len(rules), 1)
        rule = rules[0]
        self.assertions.assertIn("5266a592-b793-11ea-b3de-bbbbbb", rule.id)
        self.assertions.assertIn("5266a592-b793-11ea-b3de-bbbbbb", rule.rule_uuid)
        self.assertions.assertIn("Installation of bbbbbb", rule.title)
        self.assertions.assertIn("bbbbbb", rule.search_query)
        self.assertions.assertIn("Alexander", rule.author)
        self.assertions.assertIn("2020/06/26", rule.date)
        self.assertions.assertIn("installation of bbbbbb", rule.description)
        self.assertions.assertEqual(len(rule.detection), 2)
        self.assertions.assertEqual(
            '(data_type:("shell:zsh:history" OR "bash:history:command" OR "apt:history:line" OR "selinux:line") AND "apt-get install bbbbbb")',  # pylint: disable=line-too-long
            rule.search_query,
        )
        self.assertions.assertIn("shell:zsh:history", rule.search_query)
        self.assertions.assertIn("Unknown", rule.falsepositives[0])
        self.assertions.assertEqual(len(rule.logsource), 2)
        self.assertions.assertIn("2022/06/12", rule.modified)
        self.assertions.assertIn("high", rule.level)
        self.assertions.assertIn("rmusser.net", rule.references[0])

    def test_get_sigmarule(self):
        """Client Sigma object tests."""

        rule = self.api.create_sigmarule(
            rule_yaml="""
title: Suspicious Installation of eeeee
id: 5266a592-b793-11ea-b3de-eeeee
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

        rule = self.api.get_sigmarule(rule_uuid="5266a592-b793-11ea-b3de-eeeee")
        rule.from_rule_uuid("5266a592-b793-11ea-b3de-eeeee")
        self.assertions.assertGreater(len(rule.attributes), 5)
        self.assertions.assertIsNotNone(rule)
        self.assertions.assertIn("Alexander", rule.author)
        self.assertions.assertIn("Alexander", rule.get_attribute("author"))
        self.assertions.assertIn("b793-11ea-b3de-eeeee", rule.id)
        self.assertions.assertIn("Installation of eeeee", rule.title)
        self.assertions.assertIn("zmap", rule.search_query)
        self.assertions.assertIn("shell:zsh:history", rule.search_query)
        self.assertions.assertIn("sigmarule/5266a592", rule.resource_uri)
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
                "_type": old_event["_type"],
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
                "_type": old_event["_type"],
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


manager.EndToEndTestManager.register_test(ClientTest)
