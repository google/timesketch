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

        # pylint: disable=unused-argument
        @staticmethod
        def get(*args, **kwargs):
            """Mock GET request handler."""
            return mock_response(*args, **kwargs)

        # pylint: disable=unused-argument
        @staticmethod
        def post(*args, **kwargs):
            """Mock POST request handler."""
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

    auth_text_data = u'<input id="csrf_token" name="csrf_token" value="test">'
    sketch_data = {
        u'meta': {
            u'views': [{
                u'id': 1,
                u'name': u'test'
            }, {
                u'id': 2,
                u'name': u'test'
            }]
        },
        u'objects': [{
            u'id':
            1,
            u'name': u'test',
            u'description': u'test',
            u'timelines': [{
                u'id': 1,
                u'name': u'test',
                u'searchindex': {
                    u'index_name': u'test'
                }
            }, {
                u'id': 2,
                u'name': u'test',
                u'searchindex': {
                    u'index_name': u'test'
                }
            }]
        }]
    }

    sketch_list_data = {u'objects': [sketch_data[u'objects']]}

    timeline_data = {
        u'objects': [{
            u'id': 1,
            u'name': u'test',
            u'searchindex': {
                u'index_name': u'test'
            }
        }]
    }

    # Register API endpoints to the correct mock response data.
    url_router = {
        u'http://127.0.0.1':
        MockResponse(text_data=auth_text_data),
        u'http://127.0.0.1/api/v1/sketches/':
        MockResponse(json_data=sketch_list_data),
        u'http://127.0.0.1/api/v1/sketches/1':
        MockResponse(json_data=sketch_data),
        u'http://127.0.0.1/api/v1/sketches/1/timelines/1':
        MockResponse(json_data=timeline_data),
        u'http://127.0.0.1/api/v1/sketches/1/explore/':
        MockResponse(json_data=timeline_data),
    }
    return url_router.get(args[0], MockResponse(None, 404))
