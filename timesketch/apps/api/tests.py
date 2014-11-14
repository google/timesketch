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
"""Tests for the resources exposed by Timesketch API version 1."""

import json
import mock

from django.contrib.auth.models import User
from tastypie.test import TestApiClient
from tastypie.test import ResourceTestCase

from timesketch.lib.datastore import DataStore
from timesketch.apps.sketch.models import EventComment
from timesketch.apps.sketch.models import SavedView
from timesketch.apps.sketch.models import Sketch


class MockDataStore(DataStore):
    """A mock implementation of a Datastore."""
    get_event_dict = {
        "_index": [],
        "_id": "adc123",
        "_source": {
            "es_index": "",
            "es_id": "",
            "label": "",
            "timestamp": 1410895419859714,
            "timestamp_desc": "",
            "datetime": "2014-09-16T19:23:40+00:00",
            "source_short": "",
            "source_long": "",
            "message": "",
            }
    }

    search_result_dict = {
        "hits": {
            "hits": [
                {
                    "sort": [
                        1410900180000
                    ],
                    "_type": "plaso_event",
                    "_source": {
                        "timestamp_desc": "A timestamp",
                        "timestamp": 1410900180184000,
                        "tag": [],
                        "timesketch_label": [
                            {
                                "sketch": "1",
                                "name": "__ts_star",
                                "user": 1
                            }
                        ],
                        "message": "Test event",
                        "datetime": "2014-09-16T20:43:00+00:00",
                        },
                    "_score": "null",
                    "_index": "abc123",
                    "_id": "def345"
                }
            ],
            "total": 1,
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

    def __init__(self, _):
        self.index_list = []

    def get_single_event(self, unused_event_id):
        """Mock returning a single event from the datastore.

        Returns:
            A dictionary with event data.
        """
        return self.get_event_dict

    def add_label_to_event(
            self, unused_event, unused_sketch, unused_user, unused_label,
            toggle=False):
        """Mock adding a label to an event."""
        return

    def search(self, unused_sketch, unused_query, unused_filters):
        """Mock a search query.

        Returns:
            A dictionary with search result.
        """
        return self.search_result_dict


class BaseResourceTest(ResourceTestCase):
    """Base class that creates common objects and handles authentication."""
    def setUp(self):
        super(BaseResourceTest, self).setUp()
        self.user, self.password = self._create_user()
        self.sketch = self._create_sketch(self.user)
        self.api_client = TestApiClient()

    def _create_user(self):
        """Creates a user to be used in the tests.

        Returns:
            User object (instance of django.contrib.auth.models.User)
            Password string
        """
        username = 'john'
        password = 'pass'
        email = 'john@example.com'
        user = User.objects.create_user(username, email, password)
        return user, password

    def _create_sketch(self, user):
        """Creates a sketch, comment and saved view to be used in the tests.

        Returns:
            Sketch object (instance of timesketch.apps.sketch.models.Sketch)
        """
        sketch = Sketch.objects.create(user=user, title='Test')
        EventComment.objects.create(
            user=user, body='test', sketch=sketch, datastore_id='test',
            datastore_index='test')
        SavedView.objects.create(
            user=user, sketch=sketch, query="Test",
            filter=json.dumps({'foo': 'bar'}), name="Test")
        return sketch

    @mock.patch(
        'timesketch.lib.datastores.elasticsearch_datastore.ElasticSearchDataStore',
        MockDataStore)
    def api_request(self, method='get', data=None, auth=True):
        """Make a HTTP request to the api."""
        resource_url = '/api/v1/%s/' % self.resource_name
        test_api_client = TestApiClient()
        if auth:
            # Authenticate this session
            test_api_client.client.login(
                username=self.user.username, password=self.password)
        # Default method is GET
        api_client = test_api_client.get
        if method == 'post':
            api_client = test_api_client.post
        response = api_client(resource_url, format='json', data=data)
        return response

    def test_get_unauthenticated(self):
        """Access the resource with an unauthenticated session.

        There should not be any resource reachable without authentication so
        run this test on all resources by default.
        """
        # Prevent this test to run on any class that does not have a
        # resource_name set, e.g. the base class it self.
        if not getattr(self, 'resource_name', False):
            return
        self.assertHttpUnauthorized(self.api_request(auth=False))

    def _test_get_resources(self, request_data=None, expected_keys=None):
        """Send a request to the API to retrieve a list of resources."""
        response = self.api_request(method='get', data=request_data)
        self.assertHttpOK(response)
        if expected_keys:
            response_dict = self.deserialize(response)
            self.assertValidJSONResponse(response)
            self.assertKeys(response_dict['objects'][0], expected_keys)
        return response_dict

    def _test_post_resources(self, request_data=None, expected_keys=None):
        """Send a request to the API to create a resource."""
        response = self.api_request(method='post', data=request_data)
        self.assertHttpCreated(response)
        if expected_keys:
            response_dict = self.deserialize(response)
            self.assertKeys(response_dict['data'], expected_keys)


class CommentResourceTest(BaseResourceTest):
    """Test the comment API resource."""

    resource_name = 'comment'
    request_post_data = {
        'data': {
            'id': 'test',
            'index': 'test',
            'sketch': 1,
            'body': 'test'
        }
    }
    request_get_data = {
        'id': 'test',
        'index': 'test',
        'sketch': 1
    }
    expected_post_keys = frozenset([
        u'body',
        u'index',
        u'sketch',
        u'created',
        u'user',
        u'id'])
    expected_get_keys = frozenset([
        u'body',
        u'updated',
        u'created',
        u'user',
        u'datastore_id',
        u'datastore_index',
        u'resource_uri'])

    def test_get_resources(self):
        response = self._test_get_resources(
            request_data=self.request_get_data,
            expected_keys=self.expected_get_keys)
        self.assertTrue(response['objects'][0]['created'].endswith("+0000"))

    def test_post_resources(self):
        self._test_post_resources(
            request_data=self.request_post_data,
            expected_keys=self.expected_post_keys)


class EventResourceTest(BaseResourceTest):
    """Test the event API resource."""

    resource_name = 'event'
    request_get_data = {
        'id': 'test',
        'index': 'test'
    }
    expected_get_keys = frozenset([
        u'parser',
        u'datetime',
        u'tag',
        u'allocated',
        u'filename',
        u'inode',
        u'message',
        #u'size',
        u'display_name',
        u'uuid',
        u'hostname',
        u'label',
        u'source_short',
        u'username',
        u'store_number',
        u'data_type',
        u'timestamp',
        u'store_index',
        u'source_long',
        u'es_index',
        u'offset',
        u'timestamp_desc',
        u'fs_type',
        u'es_id',
        u'resource_uri'])

    def test_get_resources(self):
        self._test_get_resources(
            request_data=self.request_get_data,
            expected_keys=self.expected_get_keys)


class SearchResourceTest(BaseResourceTest):
    """Test the search API resource."""

    resource_name = 'search'
    request_get_data = {
        'q': 'test',
        'filter': json.dumps({'foo': 'bar'}),
        'indexes': 'test',
        'sketch': 1
    }
    expected_get_keys = frozenset([
        u'timestamp_desc',
        u'timestamp',
        u'label',
        u'tag',
        u'es_index',
        u'es_id',
        u'message',
        u'datetime',
        u'resource_uri'])

    def test_get_resources(self):
        self._test_get_resources(
            request_data=self.request_get_data,
            expected_keys=self.expected_get_keys)


class UserProfileResourceTest(BaseResourceTest):
    """Test the user profile API resource."""

    resource_name = 'userprofile'
    expected_get_keys = frozenset([
        u'avatar',
        u'resource_uri'])

    def test_get_resources(self):
        self._test_get_resources(expected_keys=self.expected_get_keys)


class UserResourceTest(BaseResourceTest):
    """Test the user API resource."""

    resource_name = 'user'
    expected_get_keys = frozenset([
        u'profile',
        u'username',
        u'first_name',
        u'last_name',
        u'resource_uri'])

    def test_get_resources(self):
        self._test_get_resources(expected_keys=self.expected_get_keys)


class SketchAclResourceTest(BaseResourceTest):
    """Test the sketch ACL API resource."""

    resource_name = 'sketch_acl'
    request_post_data = {
        'data': {
            'sketch': 1,
            'sketch_acl': 'public'
        }
    }

    def test_post_resources(self):
        self._test_post_resources(request_data=self.request_post_data)


class ViewResourceTest(BaseResourceTest):
    """Test the view API resource."""

    resource_name = 'view'
    request_post_data = {
        'data': {
            'sketch': 1,
            'name': 'test',
            'query': 'test query',
            'query_filter': json.dumps({'foo': 'bar'})
        }
    }
    request_get_data = {
        'sketch': 1,
        'view': 1
    }
    expected_get_keys = frozenset([
        u'updated',
        u'name',
        u'created',
        u'filter',
        u'query',
        u'id',
        u'resource_uri'])

    def test_get_resources(self):
        self._test_get_resources(
            request_data=self.request_get_data,
            expected_keys=self.expected_get_keys)

    def test_post_resources(self):
        self._test_post_resources(request_data=self.request_post_data)


class LabelResourceTest(BaseResourceTest):
    """Test the label API resource."""

    resource_name = 'label'
    request_post_data = {
        'data': {
            'sketch': 1,
            'id': 'test',
            'index': 'test',
            'label': 'test',
        }
    }
    expected_post_keys = frozenset([
        u'index',
        u'sketch',
        u'id',
        u'label'])

    def test_post_resources(self):
        self._test_post_resources(
            request_data=self.request_post_data,
            expected_keys=self.expected_post_keys)
