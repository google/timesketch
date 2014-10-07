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
"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.contrib.auth.models import User
from timesketch.apps.sketch.models import Sketch, EventComment
from tastypie.test import ResourceTestCase, TestApiClient
import mock


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

    def add_label_to_event(self, datastore_id, sketch_id, user_id, label):
        return


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

    def auth(self):
        return self.api_client.client.login(
            username=self.username, password=self.password)


class UserProfileResourceTest(BaseResourceTest):
    def test_get_list_unauthorized(self):
        self.assertHttpUnauthorized(self.api_client.get(
            '/api/v1/userprofile/', format='json'))

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
        self.assertHttpUnauthorized(self.api_client.get(
            '/api/v1/user/', format='json'))

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


class EventResourceTest(BaseResourceTest):
    def test_get_list_unauthorized(self):
        self.assertHttpUnauthorized(
            self.api_client.get('/api/v1/event/', format='json'))

    @mock.patch('timesketch.lib.datastores.elasticsearch_datastore.ElasticSearchDataStore', MockDataStore)
    def test_get_list_json(self):
        data = {'id': 'test_id', 'index': "test_index"}
        resp = self.api_client.get(
            '/api/v1/event/', format='json', authentication=self.auth(),
            data=data)
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)['objects']), 1)
        self.assertEqual(len(self.deserialize(resp)['objects'][0]), 25)


class CommentResourceTest(BaseResourceTest):
    def test_get_list_unauthorized(self):
        self.assertHttpUnauthorized(
            self.api_client.get('/api/v1/comment/', format='json'))

    @mock.patch('timesketch.lib.datastores.elasticsearch_datastore.ElasticSearchDataStore', MockDataStore)
    def test_get_list_json(self):
        data = {'id': 'test', 'index': "test", "sketch": 1}
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

    @mock.patch('timesketch.lib.datastores.elasticsearch_datastore.ElasticSearchDataStore', MockDataStore)
    def test_create(self):
        data = {'data': {'id': 'test', 'index': 'test', 'sketch': 1, 'body': 'test'}}
        response = self.api_client.post(
            '/api/v1/comment/', format='json', authentication=self.auth(),
            data=data)
        self.assertEqual(len(self.deserialize(response)['data']), 6)
        self.assertEqual(self.deserialize(response)['data']['body'], 'test')
        self.assertEqual( self.deserialize(response)['datastore_id'], 'test')
        self.assertEqual(self.deserialize(response)['datastore_index'], 'test')
        self.assertEqual(self.deserialize(response)['body'], 'test')


class SearchResourceTest(BaseResourceTest):
    def test_get_list_unauthorized(self):
        self.assertHttpUnauthorized(
            self.api_client.get('/api/v1/search/', format='json'))

    def test_get_list_json(self):
        data = {'q': 'test', '"filter"': 'test', 'indexes': "test", "sketch": 1}
        response = self.api_client.get(
            '/api/v1/search/', format='json', authentication=self.auth(),
            data=data)
        print response
