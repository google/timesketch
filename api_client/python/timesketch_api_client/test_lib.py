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
            kwargs["method"] = "POST"
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
        "is_archived": False,
        "sketch_id": 1,
        "sketch_name": "test",
    }

    event_data_1 = {
        "meta": {
            "comments": [
                {
                    "comment": "test comment",
                    "created_at": "Wed, 18 May 2022 01:23:45 GMT",
                    "id": 1,
                    "updated_at": "Wed, 18 May 2022 01:23:45 GMT",
                    "user": {"username": "testuser"},
                }
            ]
        },
        "objects": {},
    }

    add_event_attribute_data = {
        "meta": {
            "attributes_added": 2,
            "chunks_per_index": {"1": 1},
            "error_count": 0,
            "errors": [],
            "events_modified": 2,
        },
        "objects": [],
    }

    add_event_tag_data = {
        "meta": {},
        "objects": [
            [
                {
                    "created_at": "2023-03-09T08:52:10.595285",
                    "name": None,
                    "updated_at": "2023-03-09T08:52:10.623554",
                    "user": {
                        "active": True,
                        "admin": True,
                        "groups": [],
                        "username": "testuser",
                    },
                }
            ]
        ],
    }

    add_event_comment_data = {
        "meta": {},
        "objects": [
            [
                {
                    "comment": "comment1 foobar",
                    "created_at": "2023-03-09T13:37:58.395855",
                    "id": 1,
                    "updated_at": "2023-03-09T13:37:58.395855",
                    "user": {
                        "active": True,
                        "admin": True,
                        "groups": [],
                        "username": "testuser",
                    },
                }
            ]
        ],
    }

    sketch_data = {
        "meta": {
            "views": [{"id": 1, "name": "test"}, {"id": 2, "name": "test"}],
            "es_time": 41444,
        },
        "objects": [
            {
                "id": 1,
                "name": "test",
                "description": "test",
                "timelines": [
                    {
                        "id": 1,
                        "name": "test",
                        "searchindex": {"index_name": "test"},
                    },
                    {
                        "id": 2,
                        "name": "test",
                        "searchindex": {"index_name": "test"},
                    },
                ],
            }
        ],
    }

    view_data_1 = {
        "objects": [
            {
                "id": 1,
                "name": "test",
                "description": "meant for testing purposes only.",
                "user": {"username": "gisli"},
                "query_string": 'test:"foobar"',
                "query_dsl": "",
                "searchtemplate": "",
                "aggregation": "",
                "created_at": "2020-11-30T15:17:29",
                "updated_at": "2020-11-30T15:17:29",
            }
        ],
    }

    view_data_2 = {
        "objects": [
            {
                "id": 2,
                "name": "more test",
                "description": "really meant for testing purposes only.",
                "user": {"username": "eirikur"},
                "query_string": 'test:"bar"',
                "query_dsl": "",
                "searchtemplate": "",
                "aggregation": "",
                "created_at": "2020-11-30T15:17:29",
                "updated_at": "2020-11-30T15:17:29",
            }
        ],
    }

    sketch_list_data = {
        "meta": {"es_time": 324, "total_pages": 1, "current_page": 1},
        "objects": sketch_data["objects"],
    }

    timeline_data = {
        "meta": {
            "es_time": 12,
        },
        "objects": [
            {
                "id": 1,
                "name": "test",
                "searchindex": {"id": 1234, "index_name": "test"},
            }
        ],
    }

    more_timeline_data = {
        "meta": {
            "es_time": 12,
        },
        "objects": [
            {
                "id": 2,
                "name": "more_test",
                "searchindex": {"id": 42, "index_name": "even_more_test"},
            }
        ],
    }

    empty_data = {"meta": {"es_time": 0}, "objects": []}

    story_list_data = {"meta": {"es_time": 23}, "objects": [[{"id": 1}]]}

    story_data = {
        "meta": {
            "es_time": 1,
        },
        "objects": [
            {
                "title": "My First Story",
                "content": json.dumps(
                    [
                        {
                            "componentName": "",
                            "componentProps": {},
                            "content": "# My Heading\nWith Some Text.",
                            "edit": False,
                            "showPanel": False,
                            "isActive": False,
                        },
                        {
                            "componentName": "TsViewEventList",
                            "componentProps": {
                                "view": {"id": 1, "name": "Smoking Gun"}
                            },
                            "content": "",
                            "edit": False,
                            "showPanel": False,
                            "isActive": False,
                        },
                        {
                            "componentName": "",
                            "componentProps": {},
                            "content": "... and that was the true crime.",
                            "edit": False,
                            "showPanel": False,
                            "isActive": False,
                        },
                    ]
                ),
            }
        ],
    }

    sigma_list = {
        "meta": {"current_user": "dev", "rules_count": 2},
        "objects": [
            {
                "author": "Alexander Jaeger",
                "date": "2020/06/26",
                "description": "Detects suspicious installation of ZMap",
                "detection": {
                    "condition": "keywords",
                    "keywords": ["*apt-get install zmap*"],
                },
                "falsepositives": ["Unknown"],
                "id": "5266a592-b793-11ea-b3de-0242ac130004",
                "level": "high",
                "logsource": {"product": "linux", "service": "shell"},
                "search_query": '("*apt\\-get\\ install\\ zmap*")',
                "modified": "2020/06/26",
                "references": ["httpx://foobar.com"],
                "title": "Suspicious Installation of ZMap",
                "file_name": "lnx_susp_zmap",
                "file_relpath": "/linux/syslog/foobar/",
            },
            {
                "author": "Alexander Jaeger",
                "date": "2020/11/10",
                "description": "Detects suspicious installation of foobar",
                "detection": {
                    "condition": "keywords",
                    "keywords": ["*apt-get install foobar*"],
                },
                "falsepositives": ["Unknown"],
                "id": "776bdd11-f3aa-436e-9d03-9d6159e9814e",
                "level": "high",
                "logsource": {"product": "linux", "service": "shell"},
                "search_query": '("*apt\\-get\\ install\\ foo*")',
                "modified": "2020/06/26",
                "references": ["httpx://foobar.com"],
                "title": "Suspicious Installation of ZMap",
                "file_name": "lnx_susp_foobar",
                "file_relpath": "/windows/foobar/",
            },
        ],
    }

    sigma_rule = {
        "meta": {"parsed": True},
        "objects": [
            {
                "title": "Suspicious Installation of ZMap",
                "id": "5266a592-b793-11ea-b3de-0242ac130004",
                "description": "Detects suspicious installation of ZMap",
                "references": ["httpx://foobar.com"],
                "author": "Alexander Jaeger",
                "date": "2020/06/26",
                "modified": "2021/01/01",
                "logsource": {"product": "linux", "service": "shell"},
                "detection": {
                    "keywords": ["*apt-get install zmap*"],
                    "condition": "keywords",
                },
                "falsepositives": ["Unknown"],
                "level": "high",
                "search_query": '("*apt\\-get\\ install\\ zmap*")',
                "file_name": "lnx_susp_zmap",
                "file_relpath": "/linux/syslog/foobar/",
            }
        ],
    }
    sigma_rule_text_mock = {
        "meta": {"parsed": True},
        "objects": [
            {
                "title": "Installation of foobar",
                "id": "bb1e0d1d-cd13-4b65-bf7e-69b4e740266b",
                "description": "Detects suspicious installation of foobar",
                "references": ["https://sample.com/foobar"],
                "author": "Alexander Jaeger",
                "date": "2020/12/10",
                "modified": "2021/01/01",
                "logsource": {"product": "linux", "service": "shell"},
                "detection": {
                    "keywords": ["*apt-get install foobar*"],
                    "condition": "keywords",
                },
                "falsepositives": ["Unknown"],
                "level": "high",
                "search_query": '(data_type:("shell\\:zsh\\:history" OR "bash\\:history\\:command" OR "apt\\:history\\:line" OR "selinux\\:line") AND "*apt\\-get\\ install\\ foobar*")',  # pylint: disable=line-too-long
                "file_name": "N/A",
                "file_relpath": "N/A",
            }
        ],
    }

    sigmarule_list = {
        "meta": {"current_user": "dev", "rules_count": 2},
        "objects": [
            {
                "author": "Alexander Jaeger",
                "date": "2020/06/26",
                "description": "Detects suspicious installation of ZMap",
                "detection": {
                    "condition": "keywords",
                    "keywords": ["*apt-get install zmap*"],
                },
                "falsepositives": ["Unknown"],
                "id": "5266a592-b793-11ea-b3de-0242ac130004",
                "level": "high",
                "logsource": {"product": "linux", "service": "shell"},
                "search_query": '("*apt\\-get\\ install\\ zmap*")',
                "modified": "2020/06/26",
                "references": ["httpx://foobar.com"],
                "title": "Suspicious Installation of ZMap",
            },
            {
                "author": "Alexander Jaeger",
                "date": "2020/11/10",
                "description": "Detects suspicious installation of foobar",
                "detection": {
                    "condition": "keywords",
                    "keywords": ["*apt-get install foobar*"],
                },
                "falsepositives": ["Unknown"],
                "id": "776bdd11-f3aa-436e-9d03-9d6159e9814e",
                "level": "high",
                "logsource": {"product": "linux", "service": "shell"},
                "search_query": '("*apt\\-get\\ install\\ foo*")',
                "modified": "2020/06/26",
                "references": ["httpx://foobar.com"],
                "title": "Suspicious Installation of ZMap",
            },
        ],
    }

    sigmarule_individual = {
        "meta": {"parsed": True},
        "objects": [
            {
                "title": "Suspicious Installation of ZMap",
                "id": "5266a592-b793-11ea-b3de-0242ac130004",
                "description": "Detects suspicious installation of ZMap",
                "references": ["httpx://foobar.com"],
                "author": "Alexander Jaeger",
                "date": "2020/06/26",
                "modified": "2021/01/01",
                "logsource": {"product": "linux", "service": "shell"},
                "detection": {
                    "keywords": ["*apt-get install zmap*"],
                    "condition": "keywords",
                },
                "falsepositives": ["Unknown"],
                "level": "high",
                "search_query": '("*apt\\-get\\ install\\ zmap*")',
            }
        ],
    }
    sigmarule_text = {
        "meta": {"parsed": True},
        "objects": [
            {
                "title": "Installation of foobar",
                "id": "bb1e0d1d-cd13-4b65-bf7e-69b4e740266b",
                "description": "Detects suspicious installation of foobar",
                "references": ["https://sample.com/foobar"],
                "author": "Alexander Jaeger",
                "date": "2020/12/10",
                "modified": "2021/01/01",
                "logsource": {"product": "linux", "service": "shell"},
                "detection": {
                    "keywords": ["*apt-get install foobar*"],
                    "condition": "keywords",
                },
                "falsepositives": ["Unknown"],
                "level": "high",
                "search_query": '(data_type:("shell\\:zsh\\:history" OR "bash\\:history\\:command" OR "apt\\:history\\:line" OR "selinux\\:line") AND "*apt\\-get\\ install\\ foobar*")',  # pylint: disable=line-too-long
            }
        ],
    }

    aggregation_data = {
        "meta": {},
        "objects": [
            [
                {
                    "agg_type": "field_bucket",
                    "aggregationgroup_id": 0,
                    "chart_type": "barchart",
                    "created_at": "2023-01-08T08:45:23.113454",
                    "description": "Aggregating values of a particular field",
                    "id": 1,
                    "label_string": "",
                    "name": "ip barchart",
                    "parameters": (
                        '{"supported_charts": "barchart", '
                        '"field": "ip", "start_time": "", "end_time": "", '
                        '"limit": "10", "index": [1, 2]}'
                    ),
                    "updated_at": "2023-01-08T08:45:23.113454",
                    "user": {
                        "active": True,
                        "admin": False,
                        "groups": [],
                        "username": "dev",
                    },
                },
                {
                    "agg_type": "field_bucket",
                    "aggregationgroup_id": 0,
                    "chart_type": "table",
                    "created_at": "2023-01-08T08:46:24.871292",
                    "description": "Aggregating values of a particular field",
                    "id": 2,
                    "label_string": "",
                    "name": "domain table",
                    "parameters": (
                        '{"supported_charts": "table", "field": "domain", '
                        '"start_time": "", "end_time": "", "limit": "10", '
                        '"index": [1, 2]}'
                    ),
                    "updated_at": "2023-01-08T08:46:24.871292",
                    "user": {
                        "active": True,
                        "admin": False,
                        "groups": [],
                        "username": "dev",
                    },
                },
            ]
        ],
    }

    aggregation_1_data = {
        "meta": {},
        "objects": [
            {
                "agg_type": "field_bucket",
                "aggregationgroup_id": 0,
                "chart_type": "barchart",
                "created_at": "2023-01-08T08:45:23.113454",
                "description": "Aggregating values of a particular field",
                "id": 1,
                "label_string": "",
                "name": "ip barchart",
                "parameters": (
                    '{"supported_charts": "barchart", "field": "ip", '
                    '"start_time": "", "end_time": "", "limit": "10", '
                    '"index": [1, 2]}'
                ),
                "updated_at": "2023-01-08T08:45:23.113454",
                "user": {
                    "active": True,
                    "admin": False,
                    "groups": [],
                    "username": "dev",
                },
            }
        ],
    }

    aggregation_2_data = {
        "meta": {},
        "objects": [
            {
                "agg_type": "field_bucket",
                "aggregationgroup_id": 0,
                "chart_type": "table",
                "created_at": "2023-01-08T08:46:24.871292",
                "description": "Aggregating values of a particular field",
                "id": 2,
                "label_string": "",
                "name": "domain table",
                "parameters": (
                    '{"supported_charts": "table", "field": "domain", '
                    '"start_time": "", "end_time": "", "limit": "10", '
                    '"index": [1, 2]}'
                ),
                "updated_at": "2023-01-08T08:46:24.871292",
                "user": {
                    "active": True,
                    "admin": False,
                    "groups": [],
                    "username": "dev",
                },
            }
        ],
    }

    aggregation_chart_data = {
        "meta": {
            "chart_type": "barchart",
            "description": "Aggregating values of a particular field",
            "es_time": 0.01930856704711914,
            "method": "aggregator_run",
            "name": "field_bucket",
            "vega_chart_title": "Top results for an unknown field",
            "vega_spec": {
                "$schema": "https://vega.github.io/schema/vega-lite/v4.8.1.json",
                "config": {"view": {"continuousHeight": 300, "continuousWidth": 400}},
                "data": {"name": "data-4e004a0d2e426361c7096c1d456fe9f0"},
                "datasets": {
                    "data-4e004a0d2e426361c7096c1d456fe9f0": [
                        {"count": 125, "ip": "1.1.1.1"},
                        {"count": 108, "ip": "1.1.1.2"},
                        {"count": 97, "ip": "1.1.1.3"},
                        {"count": 95, "ip": "1.1.1.4"},
                        {"count": 87, "ip": "1.1.1.5"},
                        {"count": 84, "ip": "1.1.1.6"},
                        {"count": 82, "ip": "1.1.1.7"},
                        {"count": 82, "ip": "1.1.1.8"},
                        {"count": 51, "ip": "1.1.1.9"},
                        {"count": 51, "ip": "1.1.1.10"},
                    ]
                },
                "encoding": {
                    "href": {"field": "url", "type": "nominal"},
                    "tooltip": [
                        {"field": "ip", "type": "nominal"},
                        {"field": "count", "type": "quantitative"},
                    ],
                    "x": {
                        "field": "ip",
                        "sort": {"field": "count", "op": "sum", "order": "descending"},
                        "type": "nominal",
                    },
                    "y": {"field": "count", "type": "quantitative"},
                },
                "mark": {"strokeWidth": 0.3, "type": "bar"},
                "title": "Top results for an unknown field",
                "transform": [
                    {
                        "as": "url",
                        "calculate": (
                            "((('/sketch/1/explore?q=ip:\"' + datum.ip) + "
                            "'\" ') + '')"
                        ),
                    }
                ],
            },
        },
        "objects": [
            {
                "field_bucket": {
                    "buckets": [
                        {"count": 125, "ip": "1.1.1.1"},
                        {"count": 108, "ip": "1.1.1.2"},
                        {"count": 97, "ip": "1.1.1.3"},
                        {"count": 95, "ip": "1.1.1.4"},
                        {"count": 87, "ip": "1.1.1.5"},
                        {"count": 84, "ip": "1.1.1.6"},
                        {"count": 82, "ip": "1.1.1.7"},
                        {"count": 82, "ip": "1.1.1.8"},
                        {"count": 51, "ip": "1.1.1.9"},
                        {"count": 51, "ip": "1.1.1.10"},
                    ]
                }
            }
        ],
    }

    aggregation_group = {"meta": {"command": "list_groups"}, "objects": []}

    mock_sketch_scenario_response = {
        "meta": {},
        "objects": [
            [
                {
                    "uuid": "1234a567-b89c-123d-e45f-g6h7ijk8l910",
                    "description": "Scenario description!",
                    "dfiq_identifier": "S0001",
                    "display_name": "Test Scenario",
                    "id": 1,
                    "name": "Test Scenario",
                }
            ]
        ],
    }

    mock_scenario_response = {
        "meta": {},
        "objects": [
            {
                "uuid": "1234a567-b89c-123d-e45f-g6h7ijk8l910",
                "description": "Scenario description!",
                "dfiq_identifier": "S0001",
                "display_name": "Test Scenario",
                "id": 1,
                "name": "Test Scenario",
            }
        ],
    }

    mock_scenario_templates_response = {
        "objects": [
            {
                "uuid": "1234a567-b89c-123d-e45f-g6h7ijk8l910",
                "child_ids": ["F0001", "F0002"],
                "description": "Scenario description!",
                "id": "S0001",
                "name": "Test Scenario",
                "parent_ids": [],
                "tags": ["test"],
            },
            {
                "uuid": "1234a567-123d-b89c-e45f-g6h7ijk8l910",
                "child_ids": ["F1007"],
                "description": "Scenario description 2!",
                "id": "S0002",
                "name": "Test Scenario 2",
                "parent_ids": [],
                "tags": [],
            },
        ]
    }

    mock_sketch_questions_response = {
        "meta": {},
        "objects": [
            [
                {
                    "approaches": [
                        {
                            "description": "Test Approach Description",
                            "display_name": "Test Approach",
                            "id": 26,
                            "name": "Test Approach",
                            "search_templates": [],
                        }
                    ],
                    "uuid": "1234a567-b89c-123d-e45f-g6h7ijk8l910",
                    "conclusions": [],
                    "description": "Test Question Description",
                    "dfiq_identifier": "Q0001",
                    "display_name": "Test Question?",
                    "id": 1,
                    "name": "Test Question?",
                }
            ]
        ],
    }

    mock_question_response = {
        "meta": {},
        "objects": [
            {
                "approaches": [
                    {
                        "description": "Test Approach Description",
                        "display_name": "Test Approach",
                        "id": 26,
                        "name": "Test Approach",
                        "search_templates": [],
                    }
                ],
                "uuid": "1234a567-b89c-123d-e45f-g6h7ijk8l910",
                "conclusions": [],
                "description": "Test Question Description",
                "dfiq_identifier": "Q0001",
                "display_name": "Test Question?",
                "id": 1,
                "name": "Test Question?",
            }
        ],
    }

    mock_question_templates_response = {
        "objects": [
            {
                "uuid": "1234a567-b89c-123d-e45f-g6h7ijk8l910",
                "child_ids": ["Q0001.01"],
                "description": "Test Question Description",
                "id": "Q0001",
                "name": "Test question?",
                "parent_ids": ["F0001"],
                "tags": ["test"],
            },
            {
                "uuid": "1234a567-123d-b89c-e45f-g6h7ijk8l910",
                "child_ids": ["Q0002.01"],
                "description": "Second Test Question Description",
                "id": "Q0002",
                "name": "Second question?",
                "parent_ids": ["F0001"],
                "tags": ["test"],
            },
        ]
    }

    # Register API endpoints to the correct mock response data for GET requests.
    url_router = {
        "http://127.0.0.1": MockResponse(text_data=auth_text_data),
        "http://127.0.0.1/api/v1/sketches/": MockResponse(json_data=sketch_list_data),
        "http://127.0.0.1/api/v1/sketches/1": MockResponse(json_data=sketch_data),
        "http://127.0.0.1/api/v1/sketches/1/event/?searchindex_id=test_index&event_id=test_event": MockResponse(  # pylint: disable=line-too-long
            json_data=event_data_1
        ),
        "http://127.0.0.1/api/v1/sketches/1/event/attributes/": MockResponse(
            json_data=add_event_attribute_data
        ),
        "http://127.0.0.1/api/v1/sketches/1/event/tagging/": MockResponse(
            json_data=add_event_tag_data
        ),
        "http://127.0.0.1/api/v1/sketches/1/event/annotate/": MockResponse(
            json_data=add_event_comment_data
        ),
        "http://127.0.0.1/api/v1/sketches/1/views/1/": MockResponse(
            json_data=view_data_1
        ),
        "http://127.0.0.1/api/v1/sketches/1/views/2/": MockResponse(
            json_data=view_data_2
        ),
        "http://127.0.0.1/api/v1/sketches/1/timelines/1/": MockResponse(
            json_data=timeline_data
        ),
        "http://127.0.0.1/api/v1/sketches/1/timelines/2/": MockResponse(
            json_data=more_timeline_data
        ),
        "http://127.0.0.1/api/v1/sketches/1/explore/": MockResponse(
            json_data=timeline_data
        ),
        "http://127.0.0.1/api/v1/sketches/1/stories/": MockResponse(
            json_data=story_list_data
        ),
        "http://127.0.0.1/api/v1/sketches/1/stories/1/": MockResponse(
            json_data=story_data
        ),
        "http://127.0.0.1/api/v1/sketches/1/archive/": MockResponse(
            json_data=archive_data
        ),
        "http://127.0.0.1/api/v1/sigma/rule/5266a592-b793-11ea-b3de-0242ac130004": MockResponse(  # pylint: disable=line-too-long
            json_data=sigma_rule
        ),
        "http://127.0.0.1/api/v1/sigma/": MockResponse(json_data=sigma_list),
        "http://127.0.0.1/api/v1/sigma/text/": MockResponse(
            json_data=sigma_rule_text_mock
        ),
        "http://127.0.0.1/api/v1/sigmarules/5266a592-b793-11ea-b3de-0242ac130004": MockResponse(  # pylint: disable=line-too-long
            json_data=sigmarule_individual
        ),
        "http://127.0.0.1/api/v1/sigmarules/": MockResponse(json_data=sigmarule_list),
        "http://127.0.0.1/api/v1/sigmarules/text/": MockResponse(
            json_data=sigmarule_text
        ),
        "http://127.0.0.1/api/v1/sketches/1/aggregation/": MockResponse(
            json_data=aggregation_data
        ),
        "http://127.0.0.1/api/v1/sketches/1/aggregation/1/": MockResponse(
            json_data=aggregation_1_data
        ),
        "http://127.0.0.1/api/v1/sketches/1/aggregation/2/": MockResponse(
            json_data=aggregation_2_data
        ),
        "http://127.0.0.1/api/v1/sketches/1/aggregation/group/": MockResponse(
            json_data=aggregation_group
        ),
        "http://127.0.0.1/api/v1/sketches/1/aggregation/explore/": MockResponse(
            json_data=aggregation_chart_data
        ),
        "http://127.0.0.1/api/v1/sketches/1/scenarios/": MockResponse(
            json_data=mock_sketch_scenario_response
        ),
        "http://127.0.0.1/api/v1/sketches/1/scenarios/1/": MockResponse(
            json_data=mock_scenario_response
        ),
        "http://127.0.0.1/api/v1/scenarios/": MockResponse(
            json_data=mock_scenario_templates_response
        ),
        "http://127.0.0.1/api/v1/sketches/1/questions/": MockResponse(
            json_data=mock_sketch_questions_response
        ),
        "http://127.0.0.1/api/v1/questions/": MockResponse(
            json_data=mock_question_templates_response
        ),
        "http://127.0.0.1/api/v1/sketches/1/questions/1/": MockResponse(
            json_data=mock_question_response
        ),
    }

    # Register API endpoints to the correct mock response data for POST requests.
    post_url_router = {
        "http://127.0.0.1/api/v1/sketches/1/event/attributes/": MockResponse(
            json_data=add_event_attribute_data
        ),
        "http://127.0.0.1/api/v1/sketches/1/aggregation/explore/": MockResponse(
            json_data=aggregation_chart_data
        ),
        "http://127.0.0.1/api/v1/sketches/1/scenarios/": MockResponse(
            json_data=mock_scenario_response
        ),
        "http://127.0.0.1/api/v1/sketches/1/questions/": MockResponse(
            json_data=mock_question_response
        ),
        "http://127.0.0.1/api/v1/sketches/1/explore/": MockResponse(
            json_data=timeline_data
        ),
    }

    if kwargs.get("empty", False):
        return MockResponse(text_data=empty_data)

    if kwargs.get("method", "").upper() == "POST":
        return post_url_router.get(args[0], MockResponse(None, 404))

    return url_router.get(args[0], MockResponse(None, 404))
