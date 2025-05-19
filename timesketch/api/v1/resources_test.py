# Copyright 2015 Google Inc. All rights reserved.
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
"""Tests for v1 of the Timesketch API."""

import json
from unittest import mock

from timesketch.lib.definitions import HTTP_STATUS_CODE_BAD_REQUEST
from timesketch.lib.definitions import HTTP_STATUS_CODE_CREATED
from timesketch.lib.definitions import HTTP_STATUS_CODE_NOT_FOUND
from timesketch.lib.definitions import HTTP_STATUS_CODE_OK
from timesketch.lib.definitions import HTTP_STATUS_CODE_FORBIDDEN
from timesketch.lib.testlib import BaseTest
from timesketch.lib.testlib import MockDataStore
from timesketch.lib.dfiq import DFIQ
from timesketch.api.v1.resources import scenarios
from timesketch.models.sketch import Scenario
from timesketch.models.sketch import InvestigativeQuestion
from timesketch.models.sketch import InvestigativeQuestionApproach
from timesketch.models.sketch import Facet
from timesketch.api.v1.resources import ResourceMixin


class ResourceMixinTest(BaseTest):
    """Test ResourceMixin."""

    def test_to_json_empty_list(self):
        """Behavior of to_json when given an empty list."""
        response = ResourceMixin().to_json([])
        self.assertEqual(
            response.json,
            {
                "meta": {},
                "objects": [],
            },
        )


class InvalidResourceTest(BaseTest):
    """Test an Invalid Resource."""

    invalid_resource_url = "api/v1/invalidresource"

    def test_invalid_endpoint(self):
        """Authenticated request to get a non existent API endpoint"""
        self.login()
        response = self.client.get(self.invalid_resource_url)
        self.assert404(response)


class SketchListResourceTest(BaseTest):
    """Test SketchListResource."""

    resource_url = "/api/v1/sketches/"

    def test_sketch_list_resource(self):
        """Authenticated request to get list of sketches."""
        self.login()
        response = self.client.get(self.resource_url)
        self.assertEqual(len(response.json["objects"]), 2)
        result = sorted(i["name"] for i in response.json["objects"])
        self.assertEqual(result, ["Test 1", "Test 3"])
        self.assert200(response)

    def test_sketch_post_resource(self):
        """Authenticated request to create a sketch."""
        self.login()
        data = {"name": "test", "description": "test"}
        response = self.client.post(
            self.resource_url,
            data=json.dumps(data, ensure_ascii=False),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, HTTP_STATUS_CODE_CREATED)


class SketchResourceTest(BaseTest):
    """Test SketchResource."""

    resource_url = "/api/v1/sketches/1/"

    @mock.patch("timesketch.api.v1.resources.OpenSearchDataStore", MockDataStore)
    def test_sketch_resource(self):
        """Authenticated request to get a sketch."""
        self.login()
        response = self.client.get(self.resource_url)
        self.assertEqual(len(response.json["objects"]), 1)
        self.assertEqual(len(response.json["objects"][0]["timelines"]), 1)
        self.assertEqual(response.json["objects"][0]["name"], "Test 1")
        self.assertIsInstance(response.json["meta"]["emojis"], dict)
        self.assert200(response)

    def test_sketch_acl(self):
        """
        Authenticated request to get a sketch that the user do not have read
        permission on.
        """
        self.login()
        response = self.client.get("/api/v1/sketches/2/")
        self.assert403(response)

    def test_create_a_sketch(self):
        """Authenticated request to create a sketch."""
        self.login()
        data = {"name": "test_create_a_sketch", "description": "test_create_a_sketch"}
        response = self.client.post(
            "/api/v1/sketches/",
            data=json.dumps(data, ensure_ascii=False),
            content_type="application/json",
        )
        self.assertEqual(HTTP_STATUS_CODE_CREATED, response.status_code)

        # check the created sketch

        response = self.client.get("/api/v1/sketches/")
        self.assertEqual(len(response.json["objects"]), 3)
        self.assertIn(b"test_create_a_sketch", response.data)
        self.assert200(response)

    def test_append_label_to_sketch(self):
        """Authenticated request to append a label to a sketch."""
        self.login()

        data = {"labels": ["test_append_label_to_sketch"], "label_action": "add"}

        response = self.client.post(
            "/api/v1/sketches/3/",
            data=json.dumps(data, ensure_ascii=False),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, HTTP_STATUS_CODE_CREATED)

        # check the result in content
        response = self.client.get("/api/v1/sketches/3/")
        self.assertEqual(len(response.json["objects"]), 1)
        self.assertEqual(response.json["objects"][0]["name"], "Test 3")
        self.assertIn(
            "test_append_label_to_sketch", response.json["objects"][0]["label_string"]
        )
        self.assert200(response)

    def test_archive_sketch(self):
        """Authenticated request to archive a sketch."""
        self.login()

        # Create sketch to test with
        data = {"name": "test_archive_sketch", "description": "test_archive_sketch"}
        response = self.client.post(
            "/api/v1/sketches/",
            data=json.dumps(data, ensure_ascii=False),
            content_type="application/json",
        )
        created_id = response.json["objects"][0]["id"]

        self.assertEqual(HTTP_STATUS_CODE_CREATED, response.status_code)

        # Pull sketch
        response = self.client.get(f"/api/v1/sketches/{created_id}/")
        self.assertEqual(HTTP_STATUS_CODE_OK, response.status_code)
        self.assertEqual(len(response.json["objects"]), 1)
        self.assertEqual(response.json["objects"][0]["name"], "test_archive_sketch")

        # Archive sketch
        resource_url = f"/api/v1/sketches/{created_id}/archive/"
        data = {"action": "archive"}
        response = self.client.post(
            resource_url,
            data=json.dumps(data, ensure_ascii=False),
            content_type="application/json",
        )
        self.assert200(response)

        # Pull the sketch again to get the status
        response = self.client.get(f"/api/v1/sketches/{created_id}/")
        self.assertEqual(
            response.json["objects"][0]["name"],
            "test_archive_sketch",
        )
        self.assert200(response)
        self.assertIn("archived", response.json["objects"][0]["status"][0]["status"])

    def test_sketch_delete_not_existant_sketch(self):
        """Authenticated request to delete a sketch that does not exist."""
        self.login()
        response = self.client.delete("/api/v1/sketches/99/")
        self.assert404(response)

    def test_sketch_delete_no_acl(self):
        """Authenticated request to delete a sketch that the User has no read
        permission on.
        """
        self.login()
        response = self.client.delete("/api/v1/sketches/2/")
        self.assert403(response)

    def test_attempt_to_delete_protected_sketch(self):
        """Authenticated request to delete a protected sketch."""
        self.login()
        data = {
            "name": "test_attempt_to_delete_protected_sketch",
            "description": "test_attempt_to_delete_protected_sketch",
        }
        response = self.client.post(
            "/api/v1/sketches/",
            data=json.dumps(data, ensure_ascii=False),
            content_type="application/json",
        )
        self.assertEqual(HTTP_STATUS_CODE_CREATED, response.status_code)
        data = {"labels": ["protected"], "label_action": "add"}
        response = self.client.post(
            "/api/v1/sketches/4/",
            data=json.dumps(data, ensure_ascii=False),
            content_type="application/json",
        )

        self.assertEqual(
            response.json["objects"][0]["name"],
            "test_attempt_to_delete_protected_sketch",
        )
        self.assertIn("protected", response.json["objects"][0]["label_string"])

        response = self.client.delete("/api/v1/sketches/4/")
        self.assert403(response)

    def test_attempt_to_delete_archived_sketch(self):
        """Authenticated request to archive a sketch."""
        self.login()

        # Create sketch to test with
        data = {
            "name": "test_delete_archive_sketch",
            "description": "test_delete_archive_sketch",
        }
        response = self.client.post(
            "/api/v1/sketches/",
            data=json.dumps(data, ensure_ascii=False),
            content_type="application/json",
        )
        created_id = response.json["objects"][0]["id"]

        self.assertEqual(HTTP_STATUS_CODE_CREATED, response.status_code)
        response = self.client.get(f"/api/v1/sketches/{created_id}/")
        self.assertEqual(len(response.json["objects"]), 1)
        self.assertEqual(
            response.json["objects"][0]["name"], "test_delete_archive_sketch"
        )
        self.assertEqual(200, response.status_code)

        # Archive sketch
        resource_url = f"/api/v1/sketches/{created_id}/archive/"
        data = {"action": "archive"}
        response = self.client.post(
            resource_url,
            data=json.dumps(data, ensure_ascii=False),
            content_type="application/json",
        )
        self.assert200(response)

        # Pull the sketch again to get the status
        response = self.client.get(f"/api/v1/sketches/{created_id}/")
        self.assertEqual(
            response.json["objects"][0]["name"],
            "test_delete_archive_sketch",
        )
        self.assert200(response)
        self.assertIn("archived", response.json["objects"][0]["status"][0]["status"])

        # delete an archived sketch at the moment returns a 200
        response = self.client.delete(f"/api/v1/sketches/{created_id}/")
        self.assertEqual(200, response.status_code)


class ViewListResourceTest(BaseTest):
    """Test ViewListResource."""

    resource_url = "/api/v1/sketches/1/views/"

    def test_post_view_list_resource(self):
        """Authenticated request to create a view."""
        self.login()
        data = {
            "name": "test",
            "new_searchtemplate": False,
            "query": "test",
            "filter": {},
            "dsl": {},
        }
        response = self.client.post(
            self.resource_url,
            data=json.dumps(data, ensure_ascii=False),
            content_type="application/json",
        )
        data["from_searchtemplate_id"] = 1
        response_with_searchtemplate = self.client.post(
            self.resource_url,
            data=json.dumps(data, ensure_ascii=False),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, HTTP_STATUS_CODE_CREATED)
        self.assertEqual(
            response_with_searchtemplate.status_code, HTTP_STATUS_CODE_CREATED
        )


class ViewResourceTest(BaseTest):
    """Test ViewResource."""

    resource_url = "/api/v1/sketches/1/views/1/"

    def test_view_resource(self):
        """Authenticated request to get a view."""
        self.login()
        response = self.client.get(self.resource_url)
        self.assertEqual(len(response.json["objects"]), 1)
        self.assertEqual(response.json["objects"][0]["name"], "View 1")
        self.assert200(response)

    def test_post_view_resource(self):
        """Authenticated request to update a view."""
        self.login()
        data = {"name": "test", "query": "test", "filter": "{}"}
        response = self.client.post(
            self.resource_url,
            data=json.dumps(data, ensure_ascii=False),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, HTTP_STATUS_CODE_CREATED)

    def test_invalid_user_in_view(self):
        """Authenticated request to get a view for another user."""
        self.login()
        response = self.client.get("/api/v1/sketches/1/views/3/")
        self.assert403(response)

    def test_invalid_view(self):
        """Authenticated request to get a view for non existing view."""
        self.login()
        response = self.client.get("/api/v1/sketches/1/views/2/")
        self.assert404(response)


class SearchTemplateResourceTest(BaseTest):
    """Test Search template resource."""

    resource_url = "/api/v1/searchtemplates/1/"

    def test_searchtemplate_resource(self):
        """Authenticated request to get a search template."""
        self.login()
        response = self.client.get(self.resource_url)
        self.assertEqual(len(response.json["objects"]), 1)
        self.assertEqual(response.json["objects"][0]["name"], "template")
        self.assert200(response)

    def test_invalid_searchtemplate(self):
        """Authenticated request to get a non existing search template."""
        self.login()
        response = self.client.get("/api/v1/searchtemplates/2/")
        self.assert404(response)


class ExploreResourceTest(BaseTest):
    """Test ExploreResource."""

    resource_url = "/api/v1/sketches/1/explore/"
    expected_response = {
        "meta": {
            "es_time": 5,
            "es_total_count": 1,
            "es_total_count_complete": 0,
            "timeline_colors": {"test": "FFFFFF"},
            "timeline_names": {"test": "Timeline 1"},
            "count_per_index": {},
            "count_per_timeline": {},
            "count_over_time": {"data": {}, "interval": ""},
            "scroll_id": "",
            "search_node": {
                "children": [],
                "description": None,
                "id": 1,
                "labels": [],
                "parent": None,
                "query_dsl": None,
                "query_filter": "{}",
                "query_result_count": 0,
                "query_string": "test",
                "scenario": None,
                "facet": None,
                "question": None,
            },
        },
        "objects": [
            {
                "sort": [1410593223000],
                "_type": "plaso_event",
                "_source": {
                    "timestamp": 1410593222543942,
                    "message": "Test event",
                    "label": ["__ts_star"],
                    "timestamp_desc": "Content Modification Time",
                    "datetime": "2014-09-13T07:27:03+00:00",
                    "__ts_timeline_id": 1,
                    "comment": ["test"],
                },
                "_score": "null",
                "selected": False,
                "_index": "test",
                "_id": "test",
            }
        ],
    }

    @mock.patch("timesketch.api.v1.resources.OpenSearchDataStore", MockDataStore)
    def test_search(self):
        """Authenticated request to query the datastore."""
        self.login()
        data = {"query": "test", "filter": {}}
        response = self.client.post(
            self.resource_url,
            data=json.dumps(data, ensure_ascii=False),
            content_type="application/json",
        )
        response_json = response.json
        # Remove flaky properties (dynamically generated)
        del response_json["meta"]["search_node"]["created_at"]
        del response_json["meta"]["search_node"]["query_time"]
        self.assertDictEqual(response_json, self.expected_response)
        self.assert200(response)


class AggregationExploreResourceTest(BaseTest):
    """Test AggregationExploreResource."""

    resource_url = "/api/v1/sketches/1/aggregation/explore/"

    @mock.patch("timesketch.api.v1.resources.OpenSearchDataStore", MockDataStore)
    def test_heatmap_aggregation(self):
        """Authenticated request to get aggregation requests."""
        self.login()
        data = {"aggregation_dsl": "test"}
        response = self.client.post(
            self.resource_url,
            data=json.dumps(data, ensure_ascii=False),
            content_type="application/json",
        )
        self.assert200(response)


class EventResourceTest(BaseTest):
    """Test EventResource."""

    resource_url = "/api/v1/sketches/1/event/"
    expected_response = {
        "objects": {
            "timestamp_desc": "",
            "timestamp": 1410895419859714,
            "label": "",
            "source_long": "",
            "source_short": "",
            "es_index": "",
            "es_id": "",
            "message": "",
            "datetime": "2014-09-16T19:23:40+00:00",
            "__ts_timeline_id": 1,
            "comment": ["test"],
        }
    }

    @mock.patch("timesketch.api.v1.resources.OpenSearchDataStore", MockDataStore)
    def test_get_event(self):
        """Authenticated request to get an event from the datastore."""
        self.login()
        response = self.client.get(
            self.resource_url + "?searchindex_id=test&event_id=test"
        )
        response_json = response.json
        del response_json["meta"]
        self.assertEqual(response.json, response.json | self.expected_response)
        self.assert200(response)

    @mock.patch("timesketch.api.v1.resources.OpenSearchDataStore", MockDataStore)
    def test_invalid_index(self):
        """
        Authenticated request to get an event from the datastore, but in the
        wrong index.
        """
        self.login()
        response_400 = self.client.get(
            self.resource_url + "?searchindex_id=wrong_index&event_id=test"
        )
        self.assert400(response_400)


class EventAddAttributeResourceTest(BaseTest):
    """Test EventAddAttributeResource."""

    resource_url = "/api/v1/sketches/1/event/attributes/"

    @mock.patch("timesketch.api.v1.resources.OpenSearchDataStore", MockDataStore)
    def test_add_attributes(self):
        """Test add attributes with a well formed request."""
        self.login()

        attrs = [{"attr_name": "foo", "attr_value": "bar"}]
        events = {
            "events": [
                {
                    "_id": "1",
                    "_type": "_doc",
                    "_index": "1",
                    "attributes": attrs,
                },
                {
                    "_id": "2",
                    "_type": "_doc",
                    "_index": "1",
                    "attributes": attrs,
                },
            ]
        }

        expected_response = {
            "meta": {
                "attributes_added": 2,
                "chunks_per_index": {"1": 1},
                "error_count": 0,
                "last_10_errors": [],
                "events_modified": 2,
            },
            "objects": [],
        }

        response = self.client.post(self.resource_url, json=events)
        self.assertEqual(expected_response, response.json)

    @mock.patch("timesketch.api.v1.resources.OpenSearchDataStore", MockDataStore)
    def test_incorrect_content_type(self):
        """Test that a content-type other than application/json is handled."""
        self.login()
        response = self.client.post(self.resource_url)
        self.assertEqual(400, response.status_code)
        self.assertIn(b"Request must be in JSON format.", response.data)

    @mock.patch("timesketch.api.v1.resources.OpenSearchDataStore", MockDataStore)
    def test_events_json_missing_events(self):
        """Test that a request without events is handled."""
        self.login()

        response = self.client.post(self.resource_url, json={"events": []})
        self.assertEqual(HTTP_STATUS_CODE_BAD_REQUEST, response.status_code)
        self.assertIn(b"Request must contain an events field.", response.data)

    @mock.patch("timesketch.api.v1.resources.OpenSearchDataStore", MockDataStore)
    def test_events_json_events_type(self):
        """Test that that the wrong type for events is handled."""
        self.login()

        response = self.client.post(self.resource_url, json={"events": "a string"})
        self.assertEqual(HTTP_STATUS_CODE_BAD_REQUEST, response.status_code)
        self.assertIn(b"Events field must be a list.", response.data)

    @mock.patch("timesketch.api.v1.resources.OpenSearchDataStore", MockDataStore)
    def test_events_json_max_events(self):
        """Test that an event list larger than max events is handled."""
        self.login()

        response = self.client.post(self.resource_url, json={"events": ["a"] * 100001})
        self.assertEqual(HTTP_STATUS_CODE_BAD_REQUEST, response.status_code)
        self.assertIn(b"Request exceeds maximum events", response.data)

    @mock.patch("timesketch.api.v1.resources.OpenSearchDataStore", MockDataStore)
    def test_events_json_missing_id(self):
        """Test that an event without an _id field is handled."""
        self.login()

        response = self.client.post(self.resource_url, json={"events": [{}]})
        self.assertEqual(HTTP_STATUS_CODE_BAD_REQUEST, response.status_code)
        self.assertIn(b"Event missing field _id.", response.data)

    @mock.patch("timesketch.api.v1.resources.OpenSearchDataStore", MockDataStore)
    def test_events_json_attributes_type(self):
        """Test that event attributes of the wrong type is handled."""
        self.login()

        response = self.client.post(
            self.resource_url,
            json={
                "events": [
                    {
                        "_id": "1",
                        "_index": "1",
                        "_type": "_doc",
                        "attributes": "a string",
                    }
                ]
            },
        )
        self.assertEqual(HTTP_STATUS_CODE_BAD_REQUEST, response.status_code)
        self.assertIn(b"Attributes must be a list.", response.data)

    @mock.patch("timesketch.api.v1.resources.OpenSearchDataStore", MockDataStore)
    def test_events_json_max_attributes(self):
        """Test that too many attributes is handled."""
        self.login()

        response = self.client.post(
            self.resource_url,
            json={
                "events": [
                    {
                        "_id": "1",
                        "_index": "1",
                        "_type": "_doc",
                        "attributes": ["a"] * 11,
                    }
                ]
            },
        )
        self.assertEqual(HTTP_STATUS_CODE_BAD_REQUEST, response.status_code)
        self.assertIn(b"Attributes for event exceeds maximum", response.data)

    @mock.patch("timesketch.api.v1.resources.OpenSearchDataStore", MockDataStore)
    def test_events_json_attribute_fields(self):
        """Test that an attribute with a missing field is handled."""
        self.login()

        response = self.client.post(
            self.resource_url,
            json={
                "events": [
                    {
                        "_id": "1",
                        "_index": "1",
                        "_type": "_doc",
                        "attributes": [{"attr_name": "abc"}],
                    }
                ]
            },
        )
        self.assertEqual(HTTP_STATUS_CODE_BAD_REQUEST, response.status_code)
        self.assertIn(b"Attribute missing field", response.data)

    @mock.patch("timesketch.api.v1.resources.OpenSearchDataStore", MockDataStore)
    def test_chunk_calculation(self):
        """Tests that chunks are properly calculated."""
        self.login()

        attrs = [{"attr_name": "foo", "attr_value": "bar"}]

        # One chunk when event count is the same as chunk size.
        response = self.client.post(
            self.resource_url,
            json={
                "events": [
                    {
                        "_id": "1",
                        "_type": "_doc",
                        "_index": "1",
                        "attributes": attrs,
                    }
                ]
                * 1000
            },
        )
        self.assertEqual({"1": 1}, response.json["meta"]["chunks_per_index"])

        # Two chunks when event count is chunk size + 1.
        response = self.client.post(
            self.resource_url,
            json={
                "events": [
                    {
                        "_id": "1",
                        "_type": "_doc",
                        "_index": "1",
                        "attributes": attrs,
                    }
                ]
                * 1001
            },
        )
        self.assertEqual({"1": 2}, response.json["meta"]["chunks_per_index"])

        # Chunk per index with multiple indexes.
        response = self.client.post(
            self.resource_url,
            json={
                "events": [
                    {
                        "_id": "1",
                        "_type": "_doc",
                        "_index": "1",
                        "attributes": attrs,
                    },
                    {
                        "_id": "1",
                        "_type": "_doc",
                        "_index": "2",
                        "attributes": attrs,
                    },
                ]
            },
        )
        self.assertEqual({"1": 1, "2": 1}, response.json["meta"]["chunks_per_index"])

    @mock.patch("timesketch.api.v1.resources.OpenSearchDataStore", MockDataStore)
    def test_add_existing_attributes(self):
        """Tests existing attributes cannot be overridden."""
        self.login()

        response = self.client.post(
            self.resource_url,
            json={
                "events": [
                    {
                        "_id": "1",
                        "_type": "_doc",
                        "_index": "1",
                        "attributes": [{"attr_name": "exists", "attr_value": "yes"}],
                    }
                ]
            },
        )
        self.assertIn(
            "Attribute 'exists' already exists for event_id '1'.",
            response.json["meta"]["last_10_errors"],
        )

    @mock.patch("timesketch.api.v1.resources.OpenSearchDataStore", MockDataStore)
    def test_add_invalid_attributes_underscore(self):
        """Tests attributes beginning with an underscore cannot be added."""
        self.login()

        response = self.client.post(
            self.resource_url,
            json={
                "events": [
                    {
                        "_id": "1",
                        "_type": "_doc",
                        "_index": "1",
                        "attributes": [{"attr_name": "_invalid", "attr_value": "yes"}],
                    }
                ]
            },
        )
        self.assertIn(
            "Attribute '_invalid' for event_id '1' invalid, cannot start with '_'",
            response.json["meta"]["last_10_errors"],
        )

    @mock.patch("timesketch.api.v1.resources.OpenSearchDataStore", MockDataStore)
    def test_add_invalid_attributes_disallowed_name(self):
        """Tests attributes cannot be added with a disallowed name."""
        self.login()

        response = self.client.post(
            self.resource_url,
            json={
                "events": [
                    {
                        "_id": "1",
                        "_type": "_doc",
                        "_index": "1",
                        "attributes": [{"attr_name": "message", "attr_value": "yes"}],
                    }
                ]
            },
        )
        self.assertIn(
            "Cannot add 'message' for event_id '1', name not allowed.",
            response.json["meta"]["last_10_errors"],
        )


class EventAnnotationResourceTest(BaseTest):
    """Test EventAnnotationResource."""

    resource_url = "/api/v1/sketches/1/event/annotate/"

    @mock.patch("timesketch.api.v1.resources.OpenSearchDataStore", MockDataStore)
    def test_post_annotate_resource(self):
        """Authenticated request to create an annotation."""
        self.login()
        for annotation_type in ["comment", "label"]:
            event = {"_type": "test_event", "_index": "test", "_id": "test"}
            data = {
                "annotation": "test",
                "annotation_type": annotation_type,
                "events": [event],
            }
            response = self.client.post(
                self.resource_url,
                data=json.dumps(data),
                content_type="application/json",
            )
            self.assertIsInstance(response.json, dict)
            self.assertEqual(response.status_code, HTTP_STATUS_CODE_CREATED)

    def test_post_annotate_invalid_index_resource(self):
        """
        Authenticated request to create an annotation, but in the wrong index.
        """
        self.login()
        data = {
            "annotation": "test",
            "annotation_type": "comment",
            "event_id": "test",
            "searchindex_id": "invalid_searchindex",
        }
        response = self.client.post(
            self.resource_url,
            data=json.dumps(data),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, HTTP_STATUS_CODE_BAD_REQUEST)


class SearchIndexResourceTest(BaseTest):
    """Test SearchIndexResource."""

    resource_url = "/api/v1/searchindices/"

    @mock.patch("timesketch.api.v1.resources.OpenSearchDataStore", MockDataStore)
    def test_post_create_searchindex(self):
        """Authenticated request to create a searchindex."""
        self.login()
        data = {"searchindex_name": "test3", "es_index_name": "test3", "public": False}
        response = self.client.post(
            self.resource_url,
            data=json.dumps(data),
            content_type="application/json",
        )
        self.assertIsInstance(response.json, dict)
        self.assertEqual(response.status_code, HTTP_STATUS_CODE_CREATED)


class TimelineListResourceTest(BaseTest):
    """Test TimelineList resource."""

    resource_url = "/api/v1/sketches/1/timelines/"

    def test_add_existing_timeline_resource(self):
        """Authenticated request to add a timeline to a sketch."""
        self.login()
        data = {"timeline": 1}
        response = self.client.post(
            self.resource_url,
            data=json.dumps(data, ensure_ascii=False),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, HTTP_STATUS_CODE_OK)

    def test_add_new_timeline_resource(self):
        """Authenticated request to add a timeline to a sketch."""
        self.login()
        data = {"timeline": 2}
        response = self.client.post(
            self.resource_url,
            data=json.dumps(data, ensure_ascii=False),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, HTTP_STATUS_CODE_CREATED)


class SigmaRuleResourceTest(BaseTest):
    """Test Sigma Rule resource."""

    expected_response = {
        "objects": {
            "description": "Detects suspicious installation of bbbbbb",
            "id": "5266a592-b793-11ea-b3de-bbbbbb",
            "level": "high",
            "logsource": {"product": "linux", "service": "shell"},
            "title": "Suspicious Installation of bbbbbb",
        }
    }

    @mock.patch("timesketch.api.v1.resources.OpenSearchDataStore", MockDataStore)
    def test_post_sigma_resource(self):
        """Authenticated request to POST an sigma rule."""
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

        self.login()

        sigma = {
            "rule_uuid": "5266a592-b793-11ea-b3de-bbbbbb",
            "title": "Suspicious Installation of bbbbbb",
            "description": "Detects suspicious installation of bbbbbb",
            "rule_yaml": MOCK_SIGMA_RULE,
        }

        # Create a first rule
        response = self.client.post(
            "/api/v1/sigmarules/",
            data=json.dumps(sigma),
            content_type="application/json",
        )
        self.assertIn("bbbbbb", response.json["objects"][0]["rule_uuid"])
        self.assertIn(
            "bbbbbb",
            response.json["objects"][0]["description"],
        )
        self.assertIn(
            "shell",
            response.json["objects"][0]["rule_yaml"],
        )
        self.assertEqual(response.status_code, HTTP_STATUS_CODE_CREATED)
        # Now GET the resources
        response = self.client.get("/api/v1/sigmarules/5266a592-b793-11ea-b3de-bbbbbb/")

        self.assertIsNotNone(response)
        self.assertEqual(response.status_code, HTTP_STATUS_CODE_OK)
        self.assertIn("bbbbbb", response.json["objects"][0]["rule_uuid"])
        self.assertIn(
            "bbbbbb",
            response.json["objects"][0]["description"],
        )
        self.assertIn(
            "shell",
            response.json["objects"][0]["rule_yaml"],
        )

    def test_get_sigma_rule(self):
        """Authenticated request to get an sigma rule."""
        self.login()
        response = self.client.get(
            "/api/v1/sigmarules/5266a592-b793-11ea-b3de-0242ac130004"
        )
        self.assertIsNotNone(response)

    def test_get_sigma_rule_that_does_not_exist(self):
        """Fetch a Sigma rule that does not exist."""
        self.login()
        response = self.client.get("/api/v1/sigmarules/foobar/")
        self.assertEqual(response.status_code, HTTP_STATUS_CODE_NOT_FOUND)

    def test_put_sigma_rule(self):
        """Authenticated request to update sigma rule."""
        self.login()

        sigma = {
            "rule_uuid": "5266a592-b793-11ea-b3de-bbbbbb",
            "title": "Suspicious Installation of bbbbbb",
            "description": "Detects suspicious installation of bbbbbb",
            "rule_yaml": """
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
""",
        }

        # Create a first rule
        response = self.client.post(
            "/api/v1/sigmarules/",
            data=json.dumps(sigma),
            content_type="application/json",
        )
        self.assertIn("bbbbbb", response.json["objects"][0]["rule_uuid"])
        self.assertIn(
            "bbbbbb",
            response.json["objects"][0]["description"],
        )
        self.assertIn(
            "shell",
            response.json["objects"][0]["rule_yaml"],
        )
        self.assertEqual(response.status_code, HTTP_STATUS_CODE_CREATED)
        response = self.client.put(
            "/api/v1/sigmarules/5266a592-b793-11ea-b3de-bbbbbb/",
            data=json.dumps(
                {
                    "rule_uuid": "5266a592-b793-11ea-b3de-bbbbbb",
                    "title": "Suspicious Installation of cccccc",
                    "description": "Detects suspicious installation of cccccc",
                    "rule_yaml": """
title: Suspicious Installation of cccccc
id: 5266a592-b793-11ea-b3de-bbbbbb
description: Detects suspicious installation of cccccc
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
        - '*apt-get install cccccc*'
    condition: keywords
falsepositives:
    - Unknown
level: high
""",
                }
            ),
            content_type="application/json",
        )
        self.assertIsNotNone(response)
        self.assertEqual(response.status_code, HTTP_STATUS_CODE_OK)
        self.assertIn("bbbbbb", response.json["objects"][0]["rule_uuid"])
        self.assertIn(
            "cccccc",
            response.json["objects"][0]["rule_yaml"],
        )

        self.assertIn(
            "cccccc",
            response.json["objects"][0]["description"],
        )
        self.assertIn(
            "cccccc",
            response.json["objects"][0]["title"],
        )


class SigmaRuleListResourceTest(BaseTest):
    """Test Sigma resource."""

    def test_get_sigma_rule_list(self):
        self.login()
        response = self.client.get("/api/v1/sigmarules/")
        self.assertIsNotNone(response)
        self.assertEqual(
            len(response.json["objects"]), response.json["meta"]["rules_count"]
        )
        rule = response.json["objects"][0]
        self.assertIn("5266a592-b793-11ea-b3de-0242ac", rule["rule_uuid"])
        self.assertIsNotNone(rule["created_at"])


class SigmaRuleByTextResourceTest(BaseTest):
    """Test SigmaRule by text resource."""

    correct_rule = """
        title: Installation of foobar
        id: bb1e0d1d-cd13-4b65-bf7e-69b4e740266b
        description: Detects suspicious installation of foobar
        references:
            - https://sample.com/foobar
        author: Alexander Jaeger
        date: 2020/12/10
        modified: 2020/12/10
        tags:
            - attack.discovery
            - attack.t1046
        logsource:
            product: linux
            service: shell
        detection:
            keywords:
                # Generic suspicious commands
                - '*apt-get install foobar*'
            condition: keywords
        falsepositives:
            - Unknown
        level: high
        """
    expected_response = {
        "meta": {"parsed": True},
        "objects": [
            {
                "title": "Installation of foobar",
                "id": "bb1e0d1d-cd13-4b65-bf7e-69b4e740266b",
                "description": "Detects suspicious installation of foobar",
                "references": ["https://sample.com/foobar"],
                "author": "Alexander Jaeger",
                "date": "2020/12/10",
                "modified": "2020/12/10",
                "tags": ["attack.discovery", "attack.t1046"],
                "logsource": {"product": "linux", "service": "shell"},
                "detection": {
                    "keywords": ["*apt-get install foobar*"],
                    "condition": "keywords",
                },
                "falsepositives": ["Unknown"],
                "level": "high",
                "search_query": '(data_type:("shell:zsh:history" OR "bash:history:command" OR "apt:history:line" OR "selinux:line") AND "apt-get install foobar")',  # pylint: disable=line-too-long
                "file_name": "N/A",
            }
        ],
    }

    def test_get_sigma_rule(self):
        """Authenticated request to get an sigma rule by text."""
        self.login()

        data = {"content": self.correct_rule}
        response = self.client.post(
            "/api/v1/sigmarules/text/",
            data=json.dumps(data, ensure_ascii=False),
            content_type="application/json",
        )
        self.assertIsNotNone(response)
        self.assertEqual(response.status_code, HTTP_STATUS_CODE_OK)
        self.assertEqual(response.json, response.json | self.expected_response)
        self.assert200(response)

    def test_get_non_existing_rule_by_text(self):
        """Authenticated request to get an sigma rule by text with non parseable
        yaml text."""
        self.login()
        data = {"content": "foobar: asd"}
        response = self.client.post(
            "/api/v1/sigmarules/text/",
            data=json.dumps(data, ensure_ascii=False),
            content_type="application/json",
        )
        data = json.loads(response.get_data(as_text=True))

        self.assertIn("Sigma parsing error generating rule", data["message"])
        self.assertEqual(response.status_code, HTTP_STATUS_CODE_BAD_REQUEST)

    def test_get_rule_by_text_no_form_data(self):
        """Authenticated request to get an sigma rule by text with no form
        data"""
        self.login()
        response = self.client.post(
            "/api/v1/sigmarules/text/",
            data=json.dumps({"action": "post"}),
            content_type="application/json",
        )
        data = json.loads(response.get_data(as_text=True))

        self.assertIn("Missing value in the request", data["message"])
        self.assertEqual(response.status_code, HTTP_STATUS_CODE_BAD_REQUEST)


class IntelligenceResourceTest(BaseTest):
    """Test Intelligence resource."""

    def test_get_intelligence_tag_metadata(self):
        """Authenticated request to get intelligence tag metadata."""
        expected_tag_metadata = {
            "malware": {"weight": 100, "type": "danger"},
            "bad": {"weight": 90, "type": "danger"},
            "suspicious": {"weight": 50, "type": "warning"},
            "good": {"weight": 10, "type": "legit"},
            "legit": {"weight": 10, "type": "legit"},
            "default": {"weight": 0, "type": "default"},
            "export": {"weight": 100, "type": "info"},
            "regexes": {
                "^GROUPNAME": {"type": "danger", "weight": 100},
                "^inv_": {"type": "warning", "weight": 80},
            },
        }
        self.login()
        response = self.client.get("/api/v1/intelligence/tagmetadata/")
        data = json.loads(response.get_data(as_text=True))
        self.assertIsNotNone(response)
        self.assertEqual(response.status_code, HTTP_STATUS_CODE_OK)
        self.assertDictEqual(data, expected_tag_metadata)


class ContextLinksResourceTest(BaseTest):
    """Test Context Links resources."""

    maxDiff = None

    def test_get_context_links_config(self):
        """Authenticated request to get the context links configuration."""

        expected_configuration = {
            "hash": [
                {
                    "context_link": "https://lookupone.local/q=<ATTR_VALUE>",
                    "redirect_warning": True,
                    "short_name": "LookupOne",
                    "type": "linked_services",
                    "validation_regex": "/^[0-9a-f]{40}$|^[0-9a-f]{32}$/i",
                },
                {
                    "context_link": "https://lookuptwo.local/q=<ATTR_VALUE>",
                    "redirect_warning": False,
                    "short_name": "LookupTwo",
                    "type": "linked_services",
                    "validation_regex": "/^[0-9a-f]{64}$/i",
                },
            ],
            "original_url": [
                {
                    "module": "module_two",
                    "short_name": "ModuleTwo",
                    "type": "hardcoded_modules",
                }
            ],
            "sha256_hash": [
                {
                    "context_link": "https://lookuptwo.local/q=<ATTR_VALUE>",
                    "redirect_warning": False,
                    "short_name": "LookupTwo",
                    "type": "linked_services",
                    "validation_regex": "/^[0-9a-f]{64}$/i",
                }
            ],
            "uri": [
                {
                    "module": "module_two",
                    "short_name": "ModuleTwo",
                    "type": "hardcoded_modules",
                }
            ],
            "url": [
                {
                    "module": "module_two",
                    "short_name": "ModuleTwo",
                    "type": "hardcoded_modules",
                },
                {
                    "context_link": "https://lookupthree.local/q=<ATTR_VALUE>",
                    "redirect_warning": True,
                    "short_name": "LookupThree",
                    "type": "linked_services",
                },
            ],
            "xml": [
                {
                    "module": "module_one",
                    "short_name": "ModuleOne",
                    "type": "hardcoded_modules",
                    "validation_regex": "/^[0-9a-f]{64}$/i",
                }
            ],
            "xml_string": [
                {
                    "module": "module_one",
                    "short_name": "ModuleOne",
                    "type": "hardcoded_modules",
                    "validation_regex": "/^[0-9a-f]{64}$/i",
                }
            ],
        }

        self.login()
        response = self.client.get("/api/v1/contextlinks/")
        data = json.loads(response.get_data(as_text=True))
        self.assertIsNotNone(response)
        self.assertEqual(response.status_code, HTTP_STATUS_CODE_OK)
        self.assertDictEqual(data, expected_configuration)


class UserListTest(BaseTest):
    """Test UserListResource."""

    def test_user_post_resource_admin(self):
        """Authenticated request (admin user) to create another user."""
        self.login_admin()

        data = {"username": "testuser", "password": "testpassword"}
        response = self.client.post(
            "/api/v1/users/",
            data=json.dumps(data),
            content_type="application/json",
        )
        self.assertIsNotNone(response)

    def test_user_post_resource_without_admin(self):
        """Authenticated request (no admin) to create another user,
        which should not work."""
        self.login()

        data = {"username": "testuser", "password": "testpassword"}
        response = self.client.post(
            "/api/v1/users/",
            data=json.dumps(data),
            content_type="application/json",
        )
        self.assertIsNotNone(response)
        self.assertEqual(response.status_code, HTTP_STATUS_CODE_FORBIDDEN)

    def test_user_post_resource_missing_username(self):
        """Authenticated request (admin user) to create another user,
        but with missing username, which should not work."""
        self.login_admin()

        data = {"username": "", "password": "testpassword"}
        response = self.client.post(
            "/api/v1/users/",
            data=json.dumps(data),
            content_type="application/json",
        )
        self.assertIsNotNone(response)
        self.assertEqual(response.status_code, HTTP_STATUS_CODE_NOT_FOUND)

    def test_user_post_resource_missing_password(self):
        """Authenticated request (admin user) to create another user,
        but with missing password, which should not work."""
        self.login_admin()

        data = {"username": "testuser", "password": ""}
        response = self.client.post(
            "/api/v1/users/",
            data=json.dumps(data),
            content_type="application/json",
        )
        self.assertIsNotNone(response)
        self.assertEqual(response.status_code, HTTP_STATUS_CODE_NOT_FOUND)


class UserTest(BaseTest):
    """Test UserResource."""

    def test_user_get_resource_admin(self):
        """Authenticated request (admin user) to create another user."""
        self.login_admin()

        response = self.client.get("/api/v1/users/1/")
        data = json.loads(response.get_data(as_text=True))
        self.assertEqual(data["objects"][0]["username"], "test1")


class SystemSettingsResourceTest(BaseTest):
    """Test system settings resource."""

    resource_url = "/api/v1/settings/"

    def test_system_settings_resource(self):
        """Authenticated request to get system settings."""
        self.app.config["LLM_PROVIDER_CONFIGS"] = {"default": {"test": {}}}
        self.app.config["DFIQ_ENABLED"] = False
        self.login()
        response = self.client.get(self.resource_url)

        self.assertEqual(response.json["DFIQ_ENABLED"], False)
        self.assertEqual(response.json["SEARCH_PROCESSING_TIMELINES"], False)

        self.assertIn("LLM_FEATURES_AVAILABLE", response.json)
        self.assertIn("default", response.json["LLM_FEATURES_AVAILABLE"])

    def test_system_settings_invalid_llm_config(self):
        """Test with invalid LLM configuration."""
        self.app.config["LLM_PROVIDER_CONFIGS"] = "invalid_config"
        self.login()
        response = self.client.get(self.resource_url)

        expected_response = {
            "DFIQ_ENABLED": False,
            "SEARCH_PROCESSING_TIMELINES": False,
            "LLM_FEATURES_AVAILABLE": {"default": False},
        }

        self.assertDictEqual(response.json, expected_response)


class ScenariosResourceTest(BaseTest):
    """Tests the scenarios resource."""

    @mock.patch("timesketch.lib.analyzers.dfiq_plugins.manager.DFIQAnalyzerManager")
    def test_check_and_run_dfiq_analysis_steps(self, mock_analyzer_manager):
        """Test triggering analyzers for different DFIQ objects."""
        test_sketch = self.sketch1
        test_user = self.user1
        self.sketch1.set_status("ready")
        self._commit_to_database(test_sketch)

        # Load DFIQ objects
        dfiq_obj = DFIQ("./tests/test_data/dfiq/")

        scenario = dfiq_obj.scenarios[0]
        scenario_sql = Scenario(
            dfiq_identifier=scenario.id,
            uuid=scenario.uuid,
            name=scenario.name,
            display_name=scenario.name,
            description=scenario.description,
            spec_json=scenario.to_json(),
            sketch=test_sketch,
            user=test_user,
        )

        facet = dfiq_obj.facets[0]
        facet_sql = Facet(
            dfiq_identifier=facet.id,
            uuid=facet.uuid,
            name=facet.name,
            display_name=facet.name,
            description=facet.description,
            spec_json=facet.to_json(),
            sketch=test_sketch,
            user=test_user,
        )
        scenario_sql.facets = [facet_sql]

        question = dfiq_obj.questions[0]
        question_sql = InvestigativeQuestion(
            dfiq_identifier=question.id,
            uuid=question.uuid,
            name=question.name,
            display_name=question.name,
            description=question.description,
            spec_json=question.to_json(),
            sketch=test_sketch,
            scenario=scenario_sql,
            user=test_user,
        )
        facet_sql.questions = [question_sql]

        approach = question.approaches[0]
        approach_sql = InvestigativeQuestionApproach(
            name=approach.name,
            display_name=approach.name,
            description=approach.description,
            spec_json=approach.to_json(),
            user=test_user,
        )
        question_sql.approaches = [approach_sql]

        self._commit_to_database(approach_sql)
        self._commit_to_database(question_sql)
        self._commit_to_database(facet_sql)
        self._commit_to_database(scenario_sql)

        # Test without analysis step
        result = scenarios.check_and_run_dfiq_analysis_steps(scenario_sql, test_sketch)
        self.assertFalse(result)

        result = scenarios.check_and_run_dfiq_analysis_steps(facet_sql, test_sketch)
        self.assertFalse(result)

        result = scenarios.check_and_run_dfiq_analysis_steps(approach_sql, test_sketch)
        self.assertFalse(result)

        # Add analysis step to approach
        approach.steps.append(
            {
                "stage": "analysis",
                "type": "timesketch-analyzer",
                "value": "test_analyzer",
            }
        )
        approach_sql.spec_json = approach.to_json()

        # Mocking analyzer manager response.
        mock_analyzer_manager.trigger_analyzers_for_approach.return_value = [
            mock.MagicMock()
        ]

        # Test with analysis step
        result = scenarios.check_and_run_dfiq_analysis_steps(
            scenario_sql, test_sketch, mock_analyzer_manager
        )
        self.assertEqual(result, [mock.ANY, mock.ANY])
        mock_analyzer_manager.trigger_analyzers_for_approach.assert_called_with(
            approach=approach_sql
        )

        result = scenarios.check_and_run_dfiq_analysis_steps(
            facet_sql, test_sketch, mock_analyzer_manager
        )
        self.assertEqual(result, [mock.ANY])
        mock_analyzer_manager.trigger_analyzers_for_approach.assert_called_with(
            approach=approach_sql
        )

        result = scenarios.check_and_run_dfiq_analysis_steps(
            question_sql, test_sketch, mock_analyzer_manager
        )
        self.assertEqual(result, [mock.ANY])
        mock_analyzer_manager.trigger_analyzers_for_approach.assert_called_with(
            approach=approach_sql
        )

        # Test with invalid object
        result = scenarios.check_and_run_dfiq_analysis_steps("invalid", test_sketch)
        self.assertFalse(result)


@mock.patch("timesketch.api.v1.resources.OpenSearchDataStore", MockDataStore)
class LLMResourceTest(BaseTest):
    """Test LLMResource."""

    resource_url = "/api/v1/sketches/1/llm/"

    @mock.patch("timesketch.models.sketch.Sketch.get_with_acl")
    @mock.patch(
        "timesketch.lib.llms.features.manager.FeatureManager.get_feature_instance"
    )
    @mock.patch("timesketch.lib.utils.get_validated_indices")
    @mock.patch("timesketch.api.v1.resources.llm.LLMResource._execute_llm_call")
    def test_post_success(
        self,
        mock_execute_llm,
        mock_get_validated_indices,
        mock_get_feature,
        mock_get_with_acl,
    ):
        """Test a successful POST request to the LLM endpoint."""
        mock_sketch = mock.MagicMock()
        mock_sketch.has_permission.return_value = True
        mock_sketch.id = 1
        mock_get_with_acl.return_value = mock_sketch

        mock_feature = mock.MagicMock()
        mock_feature.NAME = "test_feature"
        mock_feature.generate_prompt.return_value = "test prompt"
        mock_feature.process_response.return_value = {"result": "test result"}
        mock_get_feature.return_value = mock_feature

        mock_get_validated_indices.return_value = (["index1"], [1])
        mock_execute_llm.return_value = {"response": "mock response"}

        self.login()
        response = self.client.post(
            self.resource_url,
            data=json.dumps({"feature": "test_feature", "filter": {}}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, HTTP_STATUS_CODE_OK)
        response_data = json.loads(response.get_data(as_text=True))
        self.assertEqual(response_data, {"result": "test result"})

    def test_post_missing_data(self):
        """Test POST request with missing data."""
        self.login()
        response = self.client.post(
            self.resource_url,
            data=json.dumps({"some_param": "some_value"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, HTTP_STATUS_CODE_BAD_REQUEST)
        response_data = json.loads(response.get_data(as_text=True))
        self.assertIn("The 'feature' parameter is required", response_data["message"])

    @mock.patch("timesketch.models.sketch.Sketch.get_with_acl")
    def test_post_missing_feature(self, mock_get_with_acl):
        """Test POST request with no feature parameter."""
        mock_sketch = mock.MagicMock()
        mock_sketch.has_permission.return_value = True
        mock_get_with_acl.return_value = mock_sketch

        self.login()
        response = self.client.post(
            self.resource_url,
            data=json.dumps({"filter": {}}),  # No 'feature' key
            content_type="application/json",
        )
        self.assertEqual(response.status_code, HTTP_STATUS_CODE_BAD_REQUEST)
        response_data = json.loads(response.get_data(as_text=True))
        self.assertIn("The 'feature' parameter is required", response_data["message"])

    @mock.patch("timesketch.models.sketch.Sketch.get_with_acl")
    def test_post_invalid_sketch(self, mock_get_with_acl):
        """Test POST request with an invalid sketch ID."""
        mock_get_with_acl.return_value = None

        self.login()
        response = self.client.post(
            self.resource_url,
            data=json.dumps({"feature": "test_feature", "filter": {}}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, HTTP_STATUS_CODE_NOT_FOUND)
        response_data = json.loads(response.get_data(as_text=True))
        self.assertIn("No sketch found with this ID", response_data["message"])

    @mock.patch("timesketch.models.sketch.Sketch.get_with_acl")
    def test_post_no_permission(self, mock_get_with_acl):
        """Test POST request when user lacks read permission."""
        mock_sketch = mock.MagicMock()
        mock_sketch.has_permission.return_value = False
        mock_get_with_acl.return_value = mock_sketch

        self.login()
        response = self.client.post(
            self.resource_url,
            data=json.dumps({"feature": "test_feature", "filter": {}}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, HTTP_STATUS_CODE_FORBIDDEN)
        response_data = json.loads(response.get_data(as_text=True))
        self.assertIn(
            "User does not have read access to the sketch", response_data["message"]
        )

    @mock.patch("timesketch.models.sketch.Sketch.get_with_acl")
    @mock.patch(
        "timesketch.lib.llms.features.manager.FeatureManager.get_feature_instance"
    )
    def test_post_invalid_feature(self, mock_get_feature, mock_get_with_acl):
        """Test POST request with an invalid feature name."""
        mock_sketch = mock.MagicMock()
        mock_sketch.has_permission.return_value = True
        mock_get_with_acl.return_value = mock_sketch

        mock_get_feature.side_effect = KeyError("Invalid feature")

        self.login()
        response = self.client.post(
            self.resource_url,
            data=json.dumps({"feature": "invalid_feature", "filter": {}}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, HTTP_STATUS_CODE_BAD_REQUEST)
        response_data = json.loads(response.get_data(as_text=True))
        self.assertIn("Invalid LLM feature: invalid_feature", response_data["message"])

    @mock.patch("timesketch.models.sketch.Sketch.get_with_acl")
    @mock.patch(
        "timesketch.lib.llms.features.manager.FeatureManager.get_feature_instance"
    )
    @mock.patch("timesketch.lib.utils.get_validated_indices")
    def test_post_prompt_generation_error(
        self,
        mock_get_validated_indices,
        mock_get_feature,
        mock_get_with_acl,
    ):
        """Test handling of errors during prompt generation."""
        mock_sketch = mock.MagicMock()
        mock_sketch.has_permission.return_value = True
        mock_sketch.id = 1
        mock_get_with_acl.return_value = mock_sketch

        mock_feature = mock.MagicMock()
        mock_feature.NAME = "test_feature"
        mock_feature.generate_prompt.side_effect = ValueError(
            "Prompt generation failed"
        )
        mock_get_feature.return_value = mock_feature

        mock_get_validated_indices.return_value = (["index1"], [1])

        self.login()
        response = self.client.post(
            self.resource_url,
            data=json.dumps({"feature": "test_feature", "filter": {}}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, HTTP_STATUS_CODE_BAD_REQUEST)
        response_data = json.loads(response.get_data(as_text=True))
        self.assertIn("Prompt generation failed", response_data["message"])

        mock_feature.generate_prompt.assert_called_once()

    @mock.patch("timesketch.models.sketch.Sketch.get_with_acl")
    @mock.patch(
        "timesketch.lib.llms.features.manager.FeatureManager.get_feature_instance"
    )
    @mock.patch("timesketch.lib.utils.get_validated_indices")
    @mock.patch("multiprocessing.Process")
    def test_post_llm_execution_timeout(
        self,
        mock_process,
        mock_get_validated_indices,
        mock_get_feature,
        mock_get_with_acl,
    ):
        """Test handling of LLM execution timeouts."""
        # Setup mocks
        mock_sketch = mock.MagicMock()
        mock_sketch.has_permission.return_value = True
        mock_sketch.id = 1
        mock_get_with_acl.return_value = mock_sketch

        mock_feature = mock.MagicMock()
        mock_feature.NAME = "test_feature"
        mock_feature.generate_prompt.return_value = "test prompt"
        mock_get_feature.return_value = mock_feature

        mock_get_validated_indices.return_value = (["index1"], [1])

        process_instance = mock.MagicMock()
        process_instance.is_alive.return_value = True
        mock_process.return_value = process_instance

        self.login()
        response = self.client.post(
            self.resource_url,
            data=json.dumps({"feature": "test_feature", "filter": {}}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, HTTP_STATUS_CODE_BAD_REQUEST)
        response_data = json.loads(response.get_data(as_text=True))
        self.assertIn("LLM call timed out", response_data["message"])

        process_instance.terminate.assert_called_once()
