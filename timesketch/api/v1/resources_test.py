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


import mock
import json

from timesketch.lib.definitions import HTTP_STATUS_CODE_CREATED
from timesketch.lib.definitions import HTTP_STATUS_CODE_BAD_REQUEST
from timesketch.lib.testlib import BaseTest
from timesketch.lib.testlib import MockDataStore


class SketchListResourceTest(BaseTest):
    """Test SketchListResource."""
    resource_url = u'/api/v1/sketches/'

    def test_sketch_list_resource(self):
        """Authenticated request to get list of sketches."""
        self.login()
        response = self.client.get(self.resource_url)
        self.assertEqual(len(response.json[u'objects']), 1)
        self.assertEqual(
            response.json[u'objects'][0][0][u'name'], u'Test 1')
        self.assert200(response)


class SketchResourceTest(BaseTest):
    """Test SketchResource."""
    resource_url = u'/api/v1/sketches/1/'

    def test_sketch_resource(self):
        """Authenticated request to get a sketch."""
        self.login()
        response = self.client.get(self.resource_url)
        self.assertEqual(len(response.json[u'objects']), 1)
        self.assertEqual(len(response.json[u'objects'][0][u'timelines']), 1)
        self.assertEqual(response.json[u'objects'][0][u'name'], u'Test 1')
        self.assert200(response)

    def test_sketch_acl(self):
        """
        Authenticated request to get a sketch that the user do not have read
        permission on.
        """
        self.login()
        response = self.client.get(u'/api/v1/sketches/2/')
        self.assert403(response)


class ViewListResourceTest(BaseTest):
    """Test ViewListResource."""
    resource_url = u'/api/v1/sketches/1/views/'

    def test_post_view_resource(self):
        """Authenticated request to create a view."""
        self.login()
        data = dict(name=u'test', query=u'test', filter=u'{}')
        response = self.client.post(
            self.resource_url, data=json.dumps(data, ensure_ascii=False),
            content_type=u'application/json')
        self.assertEquals(response.status_code, HTTP_STATUS_CODE_CREATED)


class ViewResourceTest(BaseTest):
    """Test ViewResource."""
    resource_url = u'/api/v1/sketches/1/views/1/'

    def test_view_resource(self):
        """Authenticated request to get a view."""
        self.login()
        response = self.client.get(self.resource_url)
        self.assertEqual(len(response.json[u'objects']), 1)
        self.assertEqual(response.json[u'objects'][0][u'name'], u'View 1')
        self.assert200(response)

    def test_invalid_user_in_view(self):
        """Authenticated request to get a view for another user."""
        self.login()
        response = self.client.get(u'/api/v1/sketches/1/views/3/')
        self.assert403(response)

    def test_invalid_view(self):
        """Authenticated request to get a view for non existing view."""
        self.login()
        response = self.client.get(u'/api/v1/sketches/1/views/2/')
        self.assert404(response)


class ExploreResourceTest(BaseTest):
    """Test ExploreResource."""
    resource_url = u'/api/v1/sketches/1/explore/'
    expected_response = {
        u'meta': {
            u'timeline_names': {
                u'test': u'Timeline 1'
            },
            u'timeline_colors': {
                u'test': u'FFFFFF'
            },
            u'es_total_count': 1,
            u'es_total_count_unfiltered': 0,
            u'histogram': None,
            u'es_time': 5
        },
        u'objects': [
            {
                u'sort': [
                    1410593223000
                ],
                u'_type': u'plaso_event',
                u'_source': {
                    u'timestamp': 1410593222543942,
                    u'message': u'Test event',
                    u'label': [
                        u'__ts_star'
                    ],
                    u'timestamp_desc': u'Content Modification Time',
                    u'datetime': u'2014-09-13T07:27:03+00:00'
                },
                u'_score': u'null',
                u'selected': False,
                u'_index': u'test',
                u'_id': u'test'
            }
        ]
    }

    @mock.patch(
        u'timesketch.api.v1.resources.ElasticSearchDataStore', MockDataStore)
    def test_search(self):
        """Authenticated request to query the datastore."""
        self.login()
        data = dict(query=u'test', filter={})
        response = self.client.post(
            self.resource_url, data=json.dumps(data, ensure_ascii=False),
            content_type=u'application/json')
        print response.json
        self.assertDictEqual(response.json, self.expected_response)
        self.assert200(response)


class EventResourceTest(BaseTest):
    """Test EventResource."""
    resource_url = u'/api/v1/sketches/1/event/'
    expected_response = {
        u'objects': {
            u'timestamp_desc': u'',
            u'timestamp': 1410895419859714,
            u'label': u'',
            u'source_long': u'',
            u'source_short': u'',
            u'es_index': u'',
            u'es_id': u'',
            u'message': u'',
            u'datetime': u'2014-09-16T19:23:40+00:00'
        }
    }

    @mock.patch(
        u'timesketch.api.v1.resources.ElasticSearchDataStore', MockDataStore)
    def test_get_event(self):
        """Authenticated request to get an event from the datastore."""
        self.login()
        response = self.client.get(
            self.resource_url + u'?searchindex_id=test&event_id=test')
        self.assertDictContainsSubset(self.expected_response, response.json)
        self.assert200(response)

    @mock.patch(
        u'timesketch.api.v1.resources.ElasticSearchDataStore', MockDataStore)
    def test_invalid_index(self):
        """
        Authenticated request to get an event from the datastore, but in the
        wrong index.
        """
        self.login()
        response_400 = self.client.get(
            self.resource_url + u'?searchindex_id=wrong_index&event_id=test')
        self.assert400(response_400)


class EventAnnotationResourceTest(BaseTest):
    """Test EventAnnotationResource."""
    resource_url = u'/api/v1/sketches/1/event/annotate/'

    @mock.patch(
        u'timesketch.api.v1.resources.ElasticSearchDataStore', MockDataStore)
    def test_post_annotate_resource(self):
        """Authenticated request to create an annotation."""
        self.login()
        for annotation_type in [u'comment', u'label']:
            event = {
                u'_type': u'test_event',
                u'_index': u'test',
                u'_id': u'test'}
            data = dict(
                annotation=u'test', annotation_type=annotation_type,
                events=[event])
            response = self.client.post(
                self.resource_url, data=json.dumps(data),
                content_type=u'application/json')
            self.assertIsInstance(response.json, dict)
            self.assertEquals(response.status_code, HTTP_STATUS_CODE_CREATED)

    def test_post_annotate_invalid_index_resource(self):
        """
        Authenticated request to create an annotation, but in the wrong index.
        """
        self.login()
        data = dict(
            annotation=u'test', annotation_type=u'comment',
            event_id=u'test', searchindex_id=u'invalid_searchindex')
        response = self.client.post(
            self.resource_url, data=json.dumps(data),
            content_type=u'application/json')
        self.assertEquals(response.status_code, HTTP_STATUS_CODE_BAD_REQUEST)
