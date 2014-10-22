# Copyright 2014 Google Inc. All rights reserved.
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
"""Tests for version 1 of the Timesketch API."""

from django.contrib.auth.models import User
from timesketch.apps.sketch.models import Sketch, EventComment, SavedView
from tastypie.test import ResourceTestCase, TestApiClient
import mock
import json


class MockDataStore(object):
    def __init__(self, _):
        self.index_list = []

    def get_single_event(self, event_id):
        result_dict = {
            "_index": self.index_list,
            "_id": event_id,
            "_source": {
                "xml_string": "",
                "event_level": 1,
                "parser": "",
                "datetime": "2014-09-16T19:23:40+00:00",
                "source_name": "",
                "message": "",
                "label": [],
                "inode": 1,
                "display_name": "",
                "uuid": "",
                "hostname": "",
                "filename": "",
                "source_short": "",
                "event_identifier": 1,
                "recovered": "false",
                "username": "",
                "store_number": 1,
                "data_type": "",
                "user_sid": "",
                "timestamp": 1410895419859714,
                "req_user": 1,
                "store_index": 1,
                "source_long": "",
                "record_number": 1,
                "es_index": "",
                "computer_name": "",
                "offset": 0,
                "timestamp_desc": "",
                "es_id": "",
                "strings": []
            }
        }
        return result_dict

    @staticmethod
    def add_label_to_event(datastore_id, sketch_id, user_id, label, toggle=False):
        return

    @staticmethod
    def search(sketch, query, filter):
        result = {
            "hits": {
                "hits": [
                    {
                        "sort": [
                            1410900180000
                        ],
                        "_type": "plaso_event",
                        "_source": {"username": "SYSTEM",
                                    "comment": "Created by NetScheduleJobAdd.",
                                    "parser": "winjob",
                                    "display_name": "OS:/media/disk/Windows/Tasks/At2.job",
                                    "uuid": "6c0beea72f32400297b8d9514c260d8a",
                                    "timestamp_desc": "Last Time Executed",
                                    "store_number": 2,
                                    "timestamp": 1410900180184000,
                                    "hostname": "STUDENT-PC2",
                                    "tag": [],
                                    "filename": "/media/disk/Windows/Tasks/At2.job",
                                    "data_type": "windows:tasks:job",
                                    "application": "C:\\windows\\temp\\exploder.exe",
                                    "store_index": 423074,
                                    "source_long": "Windows Scheduled Task Job",
                                    "source_short": "JOB",
                                    "timesketch_label": [
                                        {
                                            "sketch": "1",
                                            "name": "__ts_star",
                                            "user": 1
                                        }
                                    ],
                                    "message": "Application: C:\\windows\\temp\\exploder.exe Scheduled by: SYSTEM Run Iteration: ONCE",
                                    "datetime": "2014-09-16T20:43:00+00:00",
                                    "inode": 148551,
                                    "trigger": "ONCE"
                        },
                        "_score": "null",
                        "_index": "abff427e72d44dd7bd1bc981d41fd98d",
                        "_id": "itdKmmP9RdWiOB1Enj4QBA"
                    }
                ],
                "total": 2,
                "max_score": "null"
            },
            "_shards": {
                "successful": 15,
                "failed": 0,
                "total": 15
            },
            "took": 24,
            "timed_out": "false"
        }
        return result


class BaseResourceTest(ResourceTestCase):
    def setUp(self):
        super(BaseResourceTest, self).setUp()
        # Create a user.
        self.username = 'john'
        self.password = 'pass'
        self.user = User.objects.create_user(
            self.username, 'john@example.com', self.password)
        self.api_client = TestApiClient()
        self.sketch = Sketch.objects.create(user=self.user, title="Test")
        self.comment = EventComment.objects.create(
            user=self.user, body="test", sketch=self.sketch,
            datastore_id="test", datastore_index="test")
        self.view = SavedView.objects.create(
            user=self.user, sketch=self.sketch, query="Test",
            filter=json.dumps({'foo': 'bar'}), name="Test")

    def auth(self):
        return self.api_client.client.login(
            username=self.username, password=self.password)


class CommentResourceTest(BaseResourceTest):
    """Test to create and get comment."""
    @mock.patch(
        'timesketch.lib.datastores.elasticsearch_datastore.ElasticSearchDataStore',
        MockDataStore)
    def test_create(self):
        data = {
            'data': {
                'sketch': 1,
                'id': 'test',
                'index': 'test',
                'body': 'test'
            }
        }
        response = self.api_client.post(
            '/api/v1/comment/', format='json', authentication=self.auth(),
            data=data)
        self.assertEqual(len(self.deserialize(response)['data']), 6)
        self.assertEqual(self.deserialize(response)['data']['body'], 'test')
        self.assertEqual(self.deserialize(response)['datastore_id'], 'test')
        self.assertEqual(self.deserialize(response)['datastore_index'], 'test')
        self.assertEqual(self.deserialize(response)['body'], 'test')

    def test_get_list_unauthorized(self):
        self.assertHttpUnauthorized(
            self.api_client.get('/api/v1/comment/', format='json'))

    def test_get_list_json(self):
        data = {
            'id': 'test',
            'index': "test",
            "sketch": 1
        }
        response = self.api_client.get(
            '/api/v1/comment/', format='json', authentication=self.auth(),
            data=data)
        self.assertValidJSONResponse(response)
        self.assertEqual(len(self.deserialize(response)['objects']), 1)
        self.assertEqual(
            self.deserialize(response)['objects'][0]['body'], 'test')
        self.assertEqual(
            self.deserialize(response)['objects'][0]['datastore_id'], 'test')
        self.assertEqual(
            self.deserialize(response)['objects'][0]['datastore_index'], 'test')


class EventResourceTest(BaseResourceTest):
    def test_get_list_unauthorized(self):
        self.assertHttpUnauthorized(
            self.api_client.get('/api/v1/event/', format='json'))

    def test_get_list_json(self):
        data = {
            'id': 'test_id',
            'index': 'test_index'
        }
        resp = self.api_client.get(
            '/api/v1/event/', format='json', authentication=self.auth(),
            data=data)
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)['objects']), 1)
        self.assertEqual(len(self.deserialize(resp)['objects'][0]), 25)


class SearchResourceTest(BaseResourceTest):
    def test_get_list_unauthorized(self):
        self.assertHttpUnauthorized(
            self.api_client.get('/api/v1/search/', format='json'))

    def test_get_list_json(self):
        data = {
            'q': 'test',
            'filter': json.dumps({'foo': 'bar'}),
            'indexes': 'test',
            'sketch': 1
        }
        response = self.api_client.get(
            '/api/v1/search/', format='json', authentication=self.auth(),
            data=data)
        self.assertValidJSONResponse(response)
        # ToDo: Add more assertions


class UserProfileResourceTest(BaseResourceTest):
    def test_get_list_unauthorized(self):
        self.assertHttpUnauthorized(
            self.api_client.get('/api/v1/userprofile/', format='json'))

    def test_get_list_json(self):
        resp = self.api_client.get(
            '/api/v1/userprofile/', format='json', authentication=self.auth())
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)['objects']), 1)
        expected_result = {
            u'avatar': u'/static/img/avatar_unknown.jpg',
            u'resource_uri': u'/api/v1/userprofile/1/'
        }
        self.assertEqual(self.deserialize(resp)['objects'][0], expected_result)


class UserResourceTest(BaseResourceTest):
    def test_get_list_unauthorized(self):
        self.assertHttpUnauthorized(
            self.api_client.get('/api/v1/user/', format='json'))

    def test_get_list_json(self):
        resp = self.api_client.get(
            '/api/v1/user/', format='json', authentication=self.auth())
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)['objects']), 1)
        expected_result = {
            u'profile': {
                u'avatar': u'/static/img/avatar_unknown.jpg',
                u'resource_uri': u'/api/v1/userprofile/1/'
            },
            u'username': u'john',
            u'first_name': u'',
            u'last_name': u'',
            u'resource_uri': u'/api/v1/user/1/'
        }
        self.assertEqual(self.deserialize(resp)['objects'][0], expected_result)


class SketchAclResourceTest(BaseResourceTest):
    def test_create(self):
        data = {
            'data': {
                'sketch': 1,
                'sketch_acl': 'public'
            }
        }
        response = self.api_client.post(
            '/api/v1/sketch_acl/', format='json', authentication=self.auth(),
            data=data)
        self.assertHttpCreated(response)

    def test_get_list_unauthorized(self):
        self.assertHttpUnauthorized(
            self.api_client.get('/api/v1/sketch_acl/', format='json'))


class ViewResourceTest(BaseResourceTest):
    def test_create(self):
        data = {
            'data': {
                'sketch': 1,
                'name': 'test',
                'query': "test query",
                'query_filter': json.dumps({'foo': 'bar'})
            }
        }
        response = self.api_client.post(
            '/api/v1/view/', format='json', authentication=self.auth(),
            data=data)
        self.assertHttpCreated(response)

    def test_get_list_unauthorized(self):
        self.assertHttpUnauthorized(
            self.api_client.get('/api/v1/view/', format='json'))

    def test_get_view_json(self):
        data = {
            'sketch': 1,
            'view': 1
        }
        response = self.api_client.get(
            '/api/v1/view/', format='json', authentication=self.auth(),
            data=data)
        self.assertValidJSONResponse(response)
        self.assertHttpOK(response)


class LabelResourceTest(BaseResourceTest):
    def test_create(self):
        data = {
            'data': {
                'sketch': 1,
                'id': 'test',
                'index': 'test',
                'label': "test",
            }
        }
        response = self.api_client.post(
            '/api/v1/label/', format='json', authentication=self.auth(),
            data=data)
        self.assertHttpCreated(response)
        self.assertEqual(data['data'], json.loads(response.content)['data'])

    def test_get_list_unauthorized(self):
        self.assertHttpUnauthorized(
            self.api_client.get('/api/v1/label/', format='json'))
