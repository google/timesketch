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
from __future__ import print_function
from __future__ import unicode_literals

import json
import mock

from timesketch.lib.definitions import HTTP_STATUS_CODE_BAD_REQUEST
from timesketch.lib.definitions import HTTP_STATUS_CODE_CREATED
from timesketch.lib.definitions import HTTP_STATUS_CODE_NOT_FOUND
from timesketch.lib.definitions import HTTP_STATUS_CODE_OK
from timesketch.lib.definitions import HTTP_STATUS_CODE_FORBIDDEN
from timesketch.lib.definitions import HTTP_STATUS_CODE_INTERNAL_SERVER_ERROR
from timesketch.lib.testlib import BaseTest
from timesketch.lib.testlib import MockDataStore

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
        """Authenticated request to get a non existant API endpoint"""
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
        data = dict(name="test", description="test")
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


class ViewListResourceTest(BaseTest):
    """Test ViewListResource."""

    resource_url = "/api/v1/sketches/1/views/"

    def test_post_view_list_resource(self):
        """Authenticated request to create a view."""
        self.login()
        data = dict(
            name="test",
            new_searchtemplate=False,
            query="test",
            filter={},
            dsl={},
        )
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
        data = dict(name="test", query="test", filter="{}")
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
        data = dict(query="test", filter={})
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
        data = dict(aggregation_dsl="test")
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
        self.assertDictContainsSubset(self.expected_response, response_json)
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
            "Attribute '_invalid' for event_id '1' invalid, cannot start with " "'_'",
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
            data = dict(
                annotation="test",
                annotation_type=annotation_type,
                events=[event],
            )
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
        data = dict(
            annotation="test",
            annotation_type="comment",
            event_id="test",
            searchindex_id="invalid_searchindex",
        )
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
        data = dict(searchindex_name="test3", es_index_name="test3", public=False)
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
        data = dict(timeline=1)
        response = self.client.post(
            self.resource_url,
            data=json.dumps(data, ensure_ascii=False),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, HTTP_STATUS_CODE_OK)

    def test_add_new_timeline_resource(self):
        """Authenticated request to add a timeline to a sketch."""
        self.login()
        data = dict(timeline=2)
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

        sigma = dict(
            rule_uuid="5266a592-b793-11ea-b3de-bbbbbb",
            title="Suspicious Installation of bbbbbb",
            description="Detects suspicious installation of bbbbbb",
            rule_yaml=MOCK_SIGMA_RULE,
        )

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

        sigma = dict(
            rule_uuid="5266a592-b793-11ea-b3de-bbbbbb",
            title="Suspicious Installation of bbbbbb",
            description="Detects suspicious installation of bbbbbb",
            rule_yaml="""
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
        )

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
                dict(
                    rule_uuid="5266a592-b793-11ea-b3de-bbbbbb",
                    title="Suspicious Installation of cccccc",
                    description="Detects suspicious installation of cccccc",
                    rule_yaml="""
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
                )
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

        data = dict(content=self.correct_rule)
        response = self.client.post(
            "/api/v1/sigmarules/text/",
            data=json.dumps(data, ensure_ascii=False),
            content_type="application/json",
        )
        self.assertIsNotNone(response)
        self.assertEqual(response.status_code, HTTP_STATUS_CODE_OK)
        self.assertDictContainsSubset(self.expected_response, response.json)
        self.assert200(response)

    def test_get_non_existing_rule_by_text(self):
        """Authenticated request to get an sigma rule by text with non parseable
        yaml text."""
        self.login()
        data = dict(content="foobar: asd")
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
            data=json.dumps(dict(action="post")),
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
            "default": {"class": "info", "weight": 0},
            "legit": {"class": "success", "weight": 10},
            "malware": {"class": "danger", "weight": 100},
            "suspicious": {"class": "warning", "weight": 50},
            "regexes": {"^GROUPNAME": {"class": "danger", "weight": 100}},
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

        data = dict(username="testuser", password="testpassword")
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

        data = dict(username="testuser", password="testpassword")
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

        data = dict(username="", password="testpassword")
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

        data = dict(username="testuser", password="")
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


class TestNl2qResource(BaseTest):
    """Test Nl2qResource."""

    resource_url = "/api/v1/sketches/1/nl2q/"

    @mock.patch("timesketch.lib.llms.manager.LLMManager")
    @mock.patch("timesketch.api.v1.utils.run_aggregator")
    @mock.patch("timesketch.api.v1.resources.OpenSearchDataStore", MockDataStore)
    def test_nl2q_prompt(self, mock_aggregator, mock_llm_manager):
        """Test the prompt is created correctly."""

        self.login()
        data = dict(question="Question for LLM?")
        mock_AggregationResult = mock.MagicMock()
        mock_AggregationResult.values = [
            {"data_type": "test:data_type:1"},
            {"data_type": "test:data_type:2"},
        ]
        mock_aggregator.return_value = (mock_AggregationResult, {})
        mock_llm = mock.Mock()
        mock_llm.generate.return_value = "LLM generated query"
        mock_llm_manager.return_value.get_provider.return_value = lambda: mock_llm
        response = self.client.post(
            self.resource_url,
            data=json.dumps(data),
            content_type="application/json",
        )
        expected_input = (
            "Examples:\n"
            "example 1\n"
            "\n"
            "example 2\n"
            "Types:\n"
            '* "test:data_type:1" -> "field_test_1", "field_test_2"\n'
            '* "test:data_type:2" -> "field_test_3", "field_test_4"\n'
            "Question:\n"
            "Question for LLM?"
        )
        mock_llm.generate.assert_called_once_with(expected_input)
        self.assertEqual(response.status_code, HTTP_STATUS_CODE_OK)
        self.assertDictEqual(
            response.json,
            {
                "name": "AI generated search query",
                "query_string": "LLM generated query",
                "error": None,
            },
        )

    @mock.patch("timesketch.api.v1.utils.run_aggregator")
    @mock.patch("timesketch.api.v1.resources.OpenSearchDataStore", MockDataStore)
    def test_nl2q_no_prompt(self, mock_aggregator):
        """Test error when the prompt file is missing or not configured."""

        self.app.config["PROMPT_NL2Q"] = "/file_does_not_exist.txt"
        self.login()
        data = dict(question="Question for LLM?")
        mock_AggregationResult = mock.MagicMock()
        mock_AggregationResult.values = [
            {"data_type": "test:data_type:1"},
            {"data_type": "test:data_type:2"},
        ]
        mock_aggregator.return_value = (mock_AggregationResult, {})
        response = self.client.post(
            self.resource_url,
            data=json.dumps(data),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, HTTP_STATUS_CODE_INTERNAL_SERVER_ERROR)

        del self.app.config["PROMPT_NL2Q"]
        response = self.client.post(
            self.resource_url,
            data=json.dumps(data),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, HTTP_STATUS_CODE_INTERNAL_SERVER_ERROR)
        # data = json.loads(response.get_data(as_text=True))
        # self.assertIsNotNone(data.get("error"))

    @mock.patch("timesketch.api.v1.utils.run_aggregator")
    @mock.patch("timesketch.api.v1.resources.OpenSearchDataStore", MockDataStore)
    def test_nl2q_no_examples(self, mock_aggregator):
        """Test error when the prompt file is missing or not configured."""

        self.app.config["EXAMPLES_NL2Q"] = "/file_does_not_exist.txt"
        self.login()
        data = dict(question="Question for LLM?")
        mock_AggregationResult = mock.MagicMock()
        mock_AggregationResult.values = [
            {"data_type": "test:data_type:1"},
            {"data_type": "test:data_type:2"},
        ]
        mock_aggregator.return_value = (mock_AggregationResult, {})
        response = self.client.post(
            self.resource_url,
            data=json.dumps(data),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, HTTP_STATUS_CODE_INTERNAL_SERVER_ERROR)

        del self.app.config["EXAMPLES_NL2Q"]
        response = self.client.post(
            self.resource_url,
            data=json.dumps(data),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, HTTP_STATUS_CODE_INTERNAL_SERVER_ERROR)

    @mock.patch("timesketch.api.v1.resources.OpenSearchDataStore", MockDataStore)
    def test_nl2q_no_question(self):
        """Test nl2q without submitting a question."""

        self.login()
        data = dict()
        response = self.client.post(
            self.resource_url,
            data=json.dumps(data),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, HTTP_STATUS_CODE_BAD_REQUEST)

    @mock.patch("timesketch.api.v1.utils.run_aggregator")
    @mock.patch("timesketch.api.v1.resources.OpenSearchDataStore", MockDataStore)
    def test_nl2q_wrong_llm_provider(self, mock_aggregator):
        """Test nl2q with llm provider that does not exist."""

        self.app.config["LLM_PROVIDER"] = "DoesNotExists"
        self.login()
        data = dict(question="Question for LLM?")
        mock_AggregationResult = mock.MagicMock()
        mock_AggregationResult.values = [
            {"data_type": "test:data_type:1"},
            {"data_type": "test:data_type:2"},
        ]
        mock_aggregator.return_value = (mock_AggregationResult, {})
        response = self.client.post(
            self.resource_url,
            data=json.dumps(data),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, HTTP_STATUS_CODE_OK)
        data = json.loads(response.get_data(as_text=True))
        self.assertIsNotNone(data.get("error"))

    @mock.patch("timesketch.api.v1.resources.OpenSearchDataStore", MockDataStore)
    def test_nl2q_no_llm_provider(self):
        """Test nl2q with no llm provider configured."""

        del self.app.config["LLM_PROVIDER"]
        self.login()
        data = dict(question="Question for LLM?")
        response = self.client.post(
            self.resource_url,
            data=json.dumps(data),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, HTTP_STATUS_CODE_INTERNAL_SERVER_ERROR)

    @mock.patch("timesketch.api.v1.resources.OpenSearchDataStore", MockDataStore)
    def test_nl2q_no_sketch(self):
        """Test the nl2q with non existing sketch."""

        self.login()
        data = dict(question="Question for LLM?")
        response = self.client.post(
            "/api/v1/sketches/9999/nl2q/",
            data=json.dumps(data),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, HTTP_STATUS_CODE_NOT_FOUND)

    @mock.patch("timesketch.api.v1.resources.OpenSearchDataStore", MockDataStore)
    def test_nl2q_no_permission(self):
        """Test the nl2q with no permission on the sketch."""

        self.login()
        data = dict(question="Question for LLM?")
        response = self.client.post(
            "/api/v1/sketches/2/nl2q/",
            data=json.dumps(data),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, HTTP_STATUS_CODE_FORBIDDEN)

    @mock.patch("timesketch.lib.llms.manager.LLMManager")
    @mock.patch("timesketch.api.v1.utils.run_aggregator")
    @mock.patch("timesketch.api.v1.resources.OpenSearchDataStore", MockDataStore)
    def test_nl2q_llm_error(self, mock_aggregator, mock_llm_manager):
        """Test nl2q with llm error."""

        self.login()
        data = dict(question="Question for LLM?")
        mock_AggregationResult = mock.MagicMock()
        mock_AggregationResult.values = [
            {"data_type": "test:data_type:1"},
            {"data_type": "test:data_type:2"},
        ]
        mock_aggregator.return_value = (mock_AggregationResult, {})
        mock_llm = mock.Mock()
        mock_llm.generate.side_effect = Exception("Test exception")
        mock_llm_manager.return_value.get_provider.return_value = lambda: mock_llm
        response = self.client.post(
            self.resource_url,
            data=json.dumps(data),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, HTTP_STATUS_CODE_OK)
        data = json.loads(response.get_data(as_text=True))
        self.assertIsNotNone(data.get("error"))


class SystemSettingsResourceTest(BaseTest):
    """Test system settings resource."""

    resource_url = "/api/v1/settings/"

    def test_system_settings_resource(self):
        """Authenticated request to get system settings."""
        self.login()
        response = self.client.get(self.resource_url)
        expected_response = {"DFIQ_ENABLED": False, "LLM_PROVIDER": "test"}
        self.assertEqual(response.json, expected_response)
