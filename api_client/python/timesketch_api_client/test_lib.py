# Copyright 2017 Google Inc. All rights reserved.
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
"""Tests for the Timesketch API client"""
from __future__ import unicode_literals

import json


def mock_session():
    """Mock HTTP requests session."""

    class MockHeaders(object):
        """Mock requests HTTP headers."""

        # pylint: disable=unused-argument
        @staticmethod
        def update(*args, **kwargs):
            """Mock header update method."""
            return

    class MockSession(object):
        """Mock HTTP requests session."""

        def __init__(self):
            """Initializes the mock Session object."""
            self.verify = False
            self.headers = MockHeaders()
            self._post_done = False

        # pylint: disable=unused-argument
        @staticmethod
        def get(*args, **kwargs):
            """Mock GET request handler."""
            return mock_response(*args, **kwargs)

        # pylint: disable=unused-argument
        def post(self, *args, **kwargs):
            """Mock POST request handler."""
            if self._post_done:
                return mock_response(*args, empty=True)
            return mock_response(*args, **kwargs)

    return MockSession()


# pylint: disable=unused-argument
def mock_response(*args, **kwargs):
    """Mocks HTTP response."""

    class MockResponse(object):
        """Mock HTTP response object."""

        def __init__(self, json_data=None, text_data=None, status_code=200):
            """Initializes mock object."""
            self.json_data = json_data
            self.text = text_data
            self.status_code = status_code

        def json(self):
            """Mock JSON response."""
            return self.json_data

    auth_text_data = '<input id="csrf_token" name="csrf_token" value="test">'

    archive_data = {
        'is_archived': False,
        'sketch_id': 1,
        'sketch_name': 'test',
    }

    sketch_data = {
        'meta': {
            'views': [{
                'id': 1,
                'name': 'test'
            }, {
                'id': 2,
                'name': 'test'
            }],
            'es_time': 41444,
        },
        'objects': [{
            'id':
            1,
            'name': 'test',
            'description': 'test',
            'timelines': [{
                'id': 1,
                'name': 'test',
                'searchindex': {
                    'index_name': 'test'
                }
            }, {
                'id': 2,
                'name': 'test',
                'searchindex': {
                    'index_name': 'test'
                }
            }]
        }]
    }

    sketch_list_data = {
        'meta': {'es_time': 324},
        'objects': sketch_data['objects']}

    timeline_data = {
        'meta': {
            'es_time': 12,
        },
        'objects': [{
            'id': 1,
            'name': 'test',
            'searchindex': {
                'index_name': 'test'
            }
        }]
    }

    empty_data = {
        'meta': {'es_time': 0},
        'objects': []
    }

    story_list_data = {
        'meta': {'es_time': 23},
        'objects': [[{'id': 1}]]
    }

    story_data = {
        'meta': {
            'es_time': 1,
        },
        'objects': [{
            'title': 'My First Story',
            'content': json.dumps([
                {
                    'componentName': '',
                    'componentProps': {},
                    'content': '# My Heading\nWith Some Text.',
                    'edit': False,
                    'showPanel': False,
                    'isActive': False
                },
                {
                    'componentName': 'TsViewEventList',
                    'componentProps': {
                        'view': {
                            'id': 1,
                            'name': 'Smoking Gun'}},
                    'content': '',
                    'edit': False,
                    'showPanel': False,
                    'isActive': False
                },
                {
                    'componentName': '',
                    'componentProps': {},
                    'content': '... and that was the true crime.',
                    'edit': False,
                    'showPanel': False,
                    'isActive': False
                }
            ])
        }]
    }

    # Register API endpoints to the correct mock response data.
    url_router = {
        'http://127.0.0.1':
        MockResponse(text_data=auth_text_data),
        'http://127.0.0.1/api/v1/sketches/':
        MockResponse(json_data=sketch_list_data),
        'http://127.0.0.1/api/v1/sketches/1':
        MockResponse(json_data=sketch_data),
        'http://127.0.0.1/api/v1/sketches/1/timelines/1':
        MockResponse(json_data=timeline_data),
        'http://127.0.0.1/api/v1/sketches/1/explore/':
        MockResponse(json_data=timeline_data),
        'http://127.0.0.1/api/v1/sketches/1/stories/':
        MockResponse(json_data=story_list_data),
        'http://127.0.0.1/api/v1/sketches/1/stories/1/':
        MockResponse(json_data=story_data),
        'http://127.0.0.1/api/v1/sketches/1/archive/':
        MockResponse(json_data=archive_data),
    }

    if kwargs.get('empty', False):
        return MockResponse(text_data=empty_data)

    return url_router.get(args[0], MockResponse(None, 404))
