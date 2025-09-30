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

import logging
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
        # make the index name something random
        rand = random.randint(0, 10000)

        timeline_name = f"test_direct_opensearch_{rand}"
        self.import_directly_to_opensearch(
            filename="evtx_direct_without_label.csv", index_name=timeline_name
        )

        new_sketch = self.api.create_sketch(
            name="Testing Direct", description="Adding data directly from ES"
        )

        context = "e2e - > test_direct_opensearch"

        timeline = new_sketch.generate_timeline_from_es_index(
            es_index_name=timeline_name,
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
        sketch = self.api.create_sketch(name="test_sigmarule_create_get")
        sketch.add_event("event message", "2021-01-01T00:00:00", "timestamp_desc")
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

    def test_do_users_exist(self):
        """Tests if the essential 'test' and 'admin' users exist in Timesketch.

        This end-to-end test verifies the presence of two fundamental user accounts,
        'test' and 'admin', which are typically part of a default Timesketch e2e
        setup.
        """
        users = self.api.list_users()
        found_test_user = False
        found_admin_user = False

        # Convert the iterable of user objects into a set of usernames
        # for efficient lookup
        user_usernames = {user.username for user in users}

        if "test" in user_usernames:
            found_test_user = True
        if "admin" in user_usernames:
            found_admin_user = True
        self.assertions.assertTrue(
            found_test_user, "User 'test' was not found in Timesketch."
        )
        self.assertions.assertTrue(
            found_admin_user, "User 'admin' was not found in Timesketch."
        )

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

        sketch_name = f"test_delete_sketch_{uuid.uuid4().hex}"
        sketch = self.api.create_sketch(
            name=sketch_name, description="test_delete_sketch"
        )

        sketches = list(self.api.list_sketches())
        self.assertions.assertEqual(len(sketches), number_of_sketches + 1)

        # store sketch_id of the newly created sketch
        sketch_id = sketch.id

        # check that sketch is in the sketch list
        sketches = self.api.list_sketches()
        found = False
        for s in sketches:
            if s.name == sketch_name:
                found = True

        self.assertions.assertEqual(found, True)
        # Check the current user
        expected_user = "test"
        user = self.api.current_user
        self.assertions.assertEqual(user.username, expected_user)
        self.assertions.assertEqual(user.is_admin, False)
        self.assertions.assertEqual(user.is_active, True)

        # switch to a different user
        expected_admin_user = "admin"
        user = self.admin_api.current_user
        self.assertions.assertEqual(user.username, expected_admin_user)
        self.assertions.assertEqual(user.is_admin, True)
        self.assertions.assertEqual(user.is_active, True)

        # allow the admin user to read, write and delete the sketch
        sketch.add_to_acl(user_list=["admin"], permissions=["read", "write", "delete"])
        admin_sketch_instance = self.admin_api.get_sketch(sketch.id)

        admin_sketch_instance.delete(force_delete=True)

        sketches = list(self.api.list_sketches())
        self.assertions.assertEqual(len(sketches), number_of_sketches)
        with self.assertions.assertRaises(RuntimeError):
            print(
                "Expted that this sketch is not found - "
                "so API error (RuntimeError) for request is expected"
            )
            self.api.get_sketch(sketch_id).name  # pylint: disable=W0106
            print("End of expected RuntimeError")
        self.assertions.assertEqual(
            len(sketches),
            number_of_sketches,
            "Sketch count should decrease after deletion",
        )

        # disable logging for a bit to avoid flooding
        api_client_logger = logging.getLogger("timesketch_api_client")
        # Store the current level
        original_level = api_client_logger.level
        api_client_logger.setLevel(logging.CRITICAL)

        try:
            # attempt to pull sketch it is expected that this will cause
            # some 404 in the stdout
            with self.assertions.assertRaises(RuntimeError):
                # The .name attribute access will trigger the API call
                # that then fails with 404 and raises RuntimeError.
                self.api.get_sketch(sketch_id).name  # pylint: disable=W0106
        finally:
            # Restore the original logging level regardless of test outcome
            api_client_logger.setLevel(original_level)

    def test_delete_sketch_without_acls(self):
        """Test to attempt to delete a sketch where the admin user has no ACLs,
        and the deletion should fail."""
        sketch_name_prefix = "test_sketch_no_admin_acls_fail_"
        # Sketch created by the regular user (self.api)
        initial_sketch_count_regular_user = len(list(self.api.list_sketches()))

        sketch_by_regular_user = self.api.create_sketch(
            name=f"{sketch_name_prefix}{uuid.uuid4().hex}",
            description="Sketch created by regular user, admin will fail to delete.",
        )
        self.assertions.assertIsNotNone(sketch_by_regular_user)
        sketch_id_to_delete = sketch_by_regular_user.id

        # Verify sketch count increased for the regular user
        current_sketch_count_regular_user = len(list(self.api.list_sketches()))
        self.assertions.assertEqual(
            current_sketch_count_regular_user, initial_sketch_count_regular_user + 1
        )

        # Check that admin is not explicitly part of the sketch's ACLs initially.
        # The sketch is owned by the regular 'test' user.
        acl = sketch_by_regular_user.acl
        admin_username = self.admin_api.current_user.username  # Should be "admin"

        admin_user = self.admin_api.current_user
        self.assertions.assertEqual(admin_user.username, "admin")
        self.assertions.assertEqual(admin_user.is_admin, True)
        self.assertions.assertEqual(admin_user.is_active, True)

        admin_has_direct_permission = any(
            user_perm.get("username") == admin_username
            for user_perm in acl.get("users", [])
        )

        self.assertions.assertFalse(
            admin_has_direct_permission,
            f"Admin user '{admin_username}' should not have explicit user ACLs "
            "on this sketch initially as it was created by another user.",
        )

        # Admin user (self.admin_api) attempts to get the sketch.
        # This might succeed if admins have global read by default.
        admin_sketch_instance = None
        try:
            admin_sketch_instance = self.admin_api.get_sketch(sketch_id_to_delete)
            self.assertions.assertIsNotNone(
                admin_sketch_instance,
                "Admin should generally be able to get/read any sketch.",
            )
        except RuntimeError as e:
            self.assertions.fail(
                f"Admin failed to even GET sketch {sketch_id_to_delete} "
                f"which they did not own and had no explicit ACLs for. Error: {e}. "
                "This might indicate admins don't have global read by default, "
                "or the sketch was not found."
            )

        with self.assertions.assertRaises(RuntimeError) as context_delete:
            admin_sketch_instance.delete(force_delete=True)  # type: ignore

        self.assertions.assertIn(
            "have the permission to access the requested resource",
            str(context_delete.exception),
        )

        # Verify the sketch is actually still there (checked by regular user)
        still_exists_sketch = self.api.get_sketch(sketch_id_to_delete)
        self.assertions.assertIsNotNone(
            still_exists_sketch,
            "Sketch should still exist after failed admin deletion attempt.",
        )
        self.assertions.assertEqual(still_exists_sketch.id, sketch_id_to_delete)

    def test_delete_sketch_without_force_delete(self):
        """This test will attempt to delete a sketch
        without passing the force_delete argument"""
        sketch_n = f"test_delete_sketch_without_force_delete_{uuid.uuid4().hex}"
        sketch = self.api.create_sketch(
            name=sketch_n,
            description="test_delete_sketch_without_force_delete",
        )
        self.assertions.assertIsNotNone(sketch)
        sketch_id = sketch.id

        # switch to a different user
        expected_admin_user = "admin"
        user = self.admin_api.current_user
        self.assertions.assertEqual(user.username, expected_admin_user)
        self.assertions.assertEqual(user.is_admin, True)
        self.assertions.assertEqual(user.is_active, True)

        # allow the admin user to read, write and delete the sketch
        sketch.add_to_acl(user_list=["admin"], permissions=["read", "write", "delete"])
        admin_sketch_instance = self.admin_api.get_sketch(sketch_id)

        # Perform a soft delete (force_delete=False is the default)
        try:
            admin_sketch_instance.delete(force_delete=False)
        except RuntimeError as e:
            self.assertions.fail(f"Soft delete failed unexpectedly: {e}")

        # Verify the sketch status is 'deleted'
        # We need to fetch the sketch again to get its updated status from the server.
        # Depending on the API, a soft-deleted sketch might still be fetchable
        # or might require admin privileges / specific flags.
        # For this test, we assume it's fetchable by the owner to check status.
        try:
            updated_sketch = self.admin_api.get_sketch(sketch_id)
            self.assertions.assertEqual(
                updated_sketch.status,
                "deleted",
                "Sketch status should be 'deleted' after a soft delete.",
            )
        except RuntimeError as e:
            self.assertions.fail(f"Failed to get sketch after soft delete: {e}")

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
        self.import_timeline("sigma_events.csv", sketch=sketch)

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

        self.import_timeline(file_path, sketch=sketch)
        timeline = sketch.list_timelines()[0]
        # check that timeline was uploaded correctly
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
