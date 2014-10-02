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
from tastypie.test import ResourceTestCase, TestApiClient


class BaseResourceTest(ResourceTestCase):
    def setUp(self):
        super(BaseResourceTest, self).setUp()
        # Create a user.
        self.username = 'john'
        self.password = 'pass'
        self.user = User.objects.create_user(
            self.username, 'john@example.com', self.password)
        self.api_client = TestApiClient()

    def get_credentials(self):
        return self.api_client.client.login(
            username=self.username, password=self.password)


class UserResourceTest(BaseResourceTest):
    def test_get_list_unauthorzied(self):
        self.assertHttpUnauthorized(self.api_client.get(
            '/api/v1/user/', format='json'))

    def test_get_list_json(self):
        resp = self.api_client.get(
            '/api/v1/user/', format='json',
            authentication=self.get_credentials())
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


class UserProfileResourceTest(BaseResourceTest):
    def test_get_list_unauthorzied(self):
        self.assertHttpUnauthorized(self.api_client.get(
            '/api/v1/userprofile/', format='json'))

    def test_get_list_json(self):
        resp = self.api_client.get(
            '/api/v1/userprofile/', format='json',
            authentication=self.get_credentials())
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)['objects']), 1)
        expected_result = {
            u'avatar': u'/static/img/avatar_unknown.jpg',
            u'resource_uri': u'/api/v1/userprofile/1/'
        }
        self.assertEqual(self.deserialize(resp)['objects'][0], expected_result)

