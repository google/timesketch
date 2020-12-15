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

    class MockHeaders:
        """Mock requests HTTP headers."""

        # pylint: disable=unused-argument
        @staticmethod
        def update(*args, **kwargs):
            """Mock header update method."""
            return

    class MockSession:
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

    class MockResponse:
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

    view_data_1 = {
        'objects': [{
            'id': 1,
            'name': 'test',
            'description': 'meant for testing purposes only.',
            'user': {'username': 'gisli'},
            'query_string': 'test:"foobar"',
            'query_dsl': '',
            'searchtemplate': '',
            'aggregation': '',
            'created_at': '2020-11-30T15:17:29',
            'updated_at': '2020-11-30T15:17:29',
        }],
    }

    view_data_2 = {
        'objects': [{
            'id': 2,
            'name': 'more test',
            'description': 'really meant for testing purposes only.',
            'user': {'username': 'eirikur'},
            'query_string': 'test:"bar"',
            'query_dsl': '',
            'searchtemplate': '',
            'aggregation': '',
            'created_at': '2020-11-30T15:17:29',
            'updated_at': '2020-11-30T15:17:29',
        }],
    }

    sketch_list_data = {
        'meta': {
            'es_time': 324,
            'total_pages': 1,
            'current_page': 1
        },
        'objects': sketch_data['objects']}

    timeline_data = {
        'meta': {
            'es_time': 12,
        },
        'objects': [{
            'id': 1,
            'name': 'test',
            'searchindex': {
                'id': 1234,
                'index_name': 'test'
            }
        }]
    }

    more_timeline_data = {
        'meta': {
            'es_time': 12,
        },
        'objects': [{
            'id': 2,
            'name': 'more_test',
            'searchindex': {
                'id': 42,
                'index_name': 'even_more_test'
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

    sigma_list = {
        'meta': {
            'current_user': 'dev',
            'rules_count': 2
        },
        'objects': [
            {
                'author': 'Alexander Jaeger',
                'date': '2020/06/26',
                'description': 'Detects suspicious installation of Zenmap',
                'detection': {
                    'condition': 'keywords',
                    'keywords': ['*apt-get install zmap*']
                    },
                'falsepositives': ['Unknown'],
                'id': '5266a592-b793-11ea-b3de-0242ac130004',
                'level': 'high',
                'logsource': {
                    'product': 'linux', 'service': 'shell'
                    },
                'es_query': '("*apt\\-get\\ install\\ zmap*")',
                'modified': '2020/06/26',
                'references': ['httpx://foobar.com'],
                'title': 'Suspicious Installation of Zenmap',
                'file_name': 'lnx_susp_zenmap',
                'file_relpath' : '/linux/syslog/foobar/'

            }, {
                'author': 'Alexander Jaeger',
                'date': '2020/11/10',
                'description': 'Detects suspicious installation of foobar',
                'detection': {
                    'condition': 'keywords',
                    'keywords': ['*apt-get install foobar*']
                    },
                'falsepositives': ['Unknown'],
                'id': '776bdd11-f3aa-436e-9d03-9d6159e9814e',
                'level': 'high',
                'logsource': {
                    'product': 'linux', 'service': 'shell'
                    },
                'es_query': '("*apt\\-get\\ install\\ foo*")',
                'modified': '2020/06/26',
                'references': ['httpx://foobar.com'],
                'title': 'Suspicious Installation of Zenmap',
                'file_name': 'lnx_susp_zenmap',
                'file_relpath' : '/windows/foobar/'
                }
        ]
    }

    sigma_rule = {
        'title': 'Suspicious Installation of Zenmap',
        'id': '5266a592-b793-11ea-b3de-0242ac130004',
        'description': 'Detects suspicious installation of Zenmap',
        'references': ['httpx://foobar.com'],
        'author': 'Alexander Jaeger',
        'date': '2020/06/26',
        'modified': '2020/06/26',
        'logsource': {
            'product': 'linux', 'service': 'shell'
            },
        'detection': {
            'keywords': ['*apt-get install zmap*'],
            'condition': 'keywords'
            },
        'falsepositives': ['Unknown'],
        'level': 'high',
        'es_query': '("*apt\\-get\\ install\\ zmap*")',
        'file_name': 'lnx_susp_zenmap',
        'file_relpath' : '/linux/syslog/foobar/'
    }

    # Register API endpoints to the correct mock response data.
    url_router = {
        'http://127.0.0.1':
        MockResponse(text_data=auth_text_data),
        'http://127.0.0.1/api/v1/sketches/':
        MockResponse(json_data=sketch_list_data),
        'http://127.0.0.1/api/v1/sketches/1':
        MockResponse(json_data=sketch_data),
        'http://127.0.0.1/api/v1/sketches/1/views/1/':
        MockResponse(json_data=view_data_1),
        'http://127.0.0.1/api/v1/sketches/1/views/2/':
        MockResponse(json_data=view_data_2),
        'http://127.0.0.1/api/v1/sketches/1/timelines/1/':
        MockResponse(json_data=timeline_data),
        'http://127.0.0.1/api/v1/sketches/1/timelines/2/':
        MockResponse(json_data=more_timeline_data),
        'http://127.0.0.1/api/v1/sketches/1/explore/':
        MockResponse(json_data=timeline_data),
        'http://127.0.0.1/api/v1/sketches/1/stories/':
        MockResponse(json_data=story_list_data),
        'http://127.0.0.1/api/v1/sketches/1/stories/1/':
        MockResponse(json_data=story_data),
        'http://127.0.0.1/api/v1/sketches/1/archive/':
        MockResponse(json_data=archive_data),
        'http://127.0.0.1/api/v1/sigma/5266a592-b793-11ea-b3de-0242ac130004':
        MockResponse(json_data=sigma_rule),
        'http://127.0.0.1/api/v1/sigma/':
        MockResponse(json_data=sigma_list),
    }

    if kwargs.get('empty', False):
        return MockResponse(text_data=empty_data)

    return url_router.get(args[0], MockResponse(None, 404))
