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
"""This module contains common test utilities for Timesketch."""

from __future__ import unicode_literals

import codecs
import json
import six

from flask_testing import TestCase

from timesketch.app import create_app
from timesketch.lib.definitions import HTTP_STATUS_CODE_REDIRECT
from timesketch.models import init_db
from timesketch.models import drop_all
from timesketch.models import db_session
from timesketch.models.user import Group
from timesketch.models.user import User
from timesketch.models.sketch import Sketch
from timesketch.models.sketch import Timeline
from timesketch.models.sketch import SearchIndex
from timesketch.models.sketch import SearchTemplate
from timesketch.models.sketch import View
from timesketch.models.sketch import Event
from timesketch.models.sketch import Story
from timesketch.models.sigma import SigmaRule

SIGMA_RULE = """
title: Suspicious Installation of Zenmap
id: 5266a592-b793-11ea-b3de-0242ac130004
description: Detects suspicious installation of Zenmap
references:
    - https://rmusser.net/docs/ATT&CK-Stuff/ATT&CK/Discovery.html
author: Alexander Jaeger
date: 2020/06/26
modified: 2021/01/01
logsource:
    product: linux
    service: shell
detection:
    keywords:
        # Generic suspicious commands
        - '*apt-get install zmap*'
    condition: keywords
falsepositives:
    - Unknown
level: high
"""


class TestConfig(object):
    """Config for the test environment."""

    DEBUG = True
    SECRET_KEY = "testing"
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    WTF_CSRF_ENABLED = False
    OPENSEARCH_HOST = "noserver"
    OPENSEARCH_PORT = 4711
    OPENSEARCH_USER = None
    OPENSEARCH_PASSWORD = None
    OPENSEARCH_SSL = False
    OPENSEARCH_VERIFY_CERTS = True
    LABELS_TO_PREVENT_DELETION = ["protected", "magic"]
    UPLOAD_ENABLED = False
    AUTO_SKETCH_ANALYZERS = []
    SIMILARITY_DATA_TYPES = []
    SIGMA_RULES_FOLDERS = ["./data/sigma/rules/"]
    INTELLIGENCE_TAG_METADATA = "./data/intelligence_tag_metadata.yaml"
    CONTEXT_LINKS_CONFIG_PATH = "./test_tools/test_events/mock_context_links.yaml"
    LLM_PROVIDER = "test"
    DFIQ_ENABLED = False
    DATA_TYPES_PATH = "./test_data/nl2q/test_data_types.csv"
    PROMPT_NL2Q = "./test_data/nl2q/test_prompt_nl2q"
    EXAMPLES_NL2Q = "./test_data/nl2q/test_examples_nl2q"


class MockOpenSearchClient(object):
    """A mock implementation of a OpenSearch client."""

    def __init__(self):
        """Initialize the client."""
        self.indices = MockOpenSearchIndices()

    def search(
        self, index, body, size=0, search_type=None
    ):  # pylint: disable=unused-argument
        """Mock a client search.

        Used for testing both aggregations and adding event attributes.

        """
        # pylint: disable=line-too-long
        aggregation_search_result = {
            "meta": {
                "es_time": 23,
                "es_total_count": 5621,
                "timed_out": False,
                "max_score": 0.0,
            },
            "objects": [
                {
                    "my_aggregation": {
                        "buckets": [
                            {"foobar": 1, "second": "foobar"},
                            {"foobar": 4, "second": "more stuff"},
                            {"foobar": 532, "second": "hvernig hefurdu thad"},
                        ]
                    },
                    "my_second_aggregation": {
                        "buckets": [
                            {
                                "foobar": 54,
                                "second": "faranlegt",
                                "third": "other text",
                            },
                            {"foobar": 42, "second": "asnalegt"},
                        ]
                    },
                }
            ],
        }
        # pylint: enable=line-too-long

        add_attributes_search_result = {
            "hits": {
                "hits": [
                    {
                        "_id": "1",
                        "_type": "_doc",
                        "_index": "1",
                        "_source": {"exists": "yes"},
                    },
                    {
                        "_id": "2",
                        "_type": "_doc",
                        "_index": "2",
                        "_source": {"exists": "yes"},
                    },
                ]
            }
        }

        if search_type == "query_then_fetch":
            return add_attributes_search_result
        return aggregation_search_result


class MockOpenSearchIndices(object):
    # pylint: disable=unused-argument
    def get_mapping(self, *args, **kwargs):
        """Mock get mapping call."""
        return {}

    def stats(self, *args, **kwargs):
        return {"indices": {}}

    def refresh(self, *args, **kwargs):
        return

    def exists(self, *args, **kwargs):
        return True


class MockDataStore(object):
    """A mock implementation of a Datastore."""

    event_dict = {
        "_index": [],
        "_id": "adc123",
        "_type": "plaso_event",
        "_source": {
            "__ts_timeline_id": 1,
            "comment": ["test"],
            "es_index": "",
            "es_id": "",
            "label": "",
            "timestamp": 1410895419859714,
            "timestamp_desc": "",
            "datetime": "2014-09-16T19:23:40+00:00",
            "source_short": "",
            "source_long": "",
            "message": "",
        },
    }
    search_result_dict = {
        "hits": {
            "hits": [
                {
                    "sort": [1410593223000],
                    "_type": "plaso_event",
                    "_source": {
                        "timestamp": 1410593222543942,
                        "message": "Test event",
                        "timesketch_label": [
                            {"user_id": 1, "name": "__ts_star", "sketch_id": 1},
                            {"user_id": 2, "name": "__ts_star", "sketch_id": 99},
                        ],
                        "timestamp_desc": "Content Modification Time",
                        "datetime": "2014-09-13T07:27:03+00:00",
                        "__ts_timeline_id": 1,
                    },
                    "_score": "null",
                    "_index": "test",
                    "_id": "test",
                }
            ],
            "total": 1,
            "max_score": "null",
        },
        "_shards": {"successful": 10, "failed": 0, "total": 10},
        "took": 5,
        "timed_out": False,
    }

    def __init__(self, host, port):
        """Initialize the datastore.
        Args:
            host: Hostname or IP address to the datastore
            port: The port used by the datastore
        """
        self.client = MockOpenSearchClient()
        self.host = host
        self.port = port
        # Dictionary containing event dictionaries.
        self.event_store = {}

    # pylint: disable=arguments-differ,unused-argument
    def search(self, *args, **kwargs):
        """Mock a search query.
        Returns:
            A dictionary with search result or integer if count is requested.
        """
        if kwargs.get("count"):
            # 4711 is sometimes used instead of 17, on occasions when you want
            # to denote a slightly larger number. Probably comes from the name
            # of 'genuine' Eau-de-cologne, 'No. 4711 ".
            # Ref: https://hack.org/mc/writings/hackerswe/hackerswe.html
            return 4711
        return self.search_result_dict

    def get_event(self, searchindex_id, event_id):
        """Mock returning a single event from the datastore.

        Args:
            searchindex_id: String of OpenSearch index id
            event_id: String of OpenSearch event id

        Returns:
            A dictionary with event data.
        """
        return self.event_dict

    @staticmethod
    def count(indices):
        """Mock returning a single event from the datastore.

        Args:
            indices: List of indices.

        Returns:
            A tuple with count and bytes.
        """
        return 1, 1

    @staticmethod
    def get_filter_labels(sketch_id, indices):
        """Mock returning a single event from the datastore.

        Returns:
            A list with label.
        """
        return []

    def set_label(
        self,
        searchindex_id,
        event_id,
        sketch_id,
        user_id,
        label,
        toggle=False,
        single_update=True,
    ):
        """Mock adding a label to an event."""
        return

    # pylint: disable=unused-argument
    def create_index(self, *args, **kwargs):
        """Mock creating an index."""
        return

    def import_event(self, index_name, event=None, event_id=None, flush_interval=None):
        """Mock adding the event to OpenSearch, instead add the event
        to event_store.
        Args:
            flush_interval: Number of events to queue up before indexing. (This
            functionality is not supported.)
            index_name: Name of the index in MockOpenSearchIndices
            event: Event dictionary
            event_id: Event MockOpenSearchIndices ID
        """

        if event_id in self.event_store:
            self.event_store[event_id]["_source"].update(event)
            return

        new_event = {
            "_index": index_name,
            "_id": event_id,
            "_source": event,
        }
        self.event_store[event_id] = new_event

    @property
    def version(self):
        """Get MockOpenSearch version.

        Returns:
          Version number as a string.
        """
        return "6.0"

    # pylint: disable=unused-argument
    def search_stream(
        self,
        query_string,
        query_filter,
        query_dsl,
        indices,
        return_fields,
        enable_scroll=True,
        timeline_ids=None,
    ):
        for i in range(len(self.event_store)):
            yield self.event_store[str(i)]

    def flush_queued_events(self):
        """No-op mock to flush_queued_events for the datastore."""


class MockGraphDatabase(object):
    """A mock implementation of a Datastore."""

    def __init__(self, host, username, password):
        """Initialize the datastore.
        Args:
            host: Neo4j host
            username: Neo4j username
            password: Neo4j password
        """
        self.host = host
        self.username = username
        self.password = password

    class MockQuerySequence(object):
        """A mock implementation of a QuerySequence."""

        MOCK_GRAPH = [
            {
                "nodes": [
                    {
                        "id": "1",
                        "labels": ["User"],
                        "properties": {"username": "test", "uid": "123456"},
                    },
                    {
                        "id": "2",
                        "labels": ["Machine"],
                        "properties": {"hostname": "test"},
                    },
                ],
                "relationships": [
                    {
                        "endNode": "2",
                        "id": "3",
                        "startNode": "1",
                        "properties": {"method": "Network"},
                        "type": "ACCESS",
                    }
                ],
            }
        ]
        MOCK_ROWS = {}
        MOCK_STATS = {}

        def __init__(self):
            self.graph = self.MOCK_GRAPH
            self.rows = self.MOCK_ROWS
            self.stats = self.MOCK_ROWS

    class MockEmptyQuerySequence(object):
        def __init__(self):
            self.graph = None
            self.rows = {}
            self.stats = {}

    # pylint: disable=unused-argument
    def query(self, *args, **kwargs):
        """Mock a search query.
        Returns:
            A MockQuerySequence instance.
        """
        query = args[0]
        if query == "empty":
            return self.MockEmptyQuerySequence()
        return self.MockQuerySequence()


class BaseTest(TestCase):
    """Base class for tests."""

    COLOR_WHITE = "FFFFFF"

    def create_app(self):
        """Setup the Flask application.
        Returns:
            Flask application (instance of flask.app.Flask)
        """
        app = create_app(TestConfig)
        return app

    def _commit_to_database(self, model):
        """Add object to the database session and commit.
        Args:
            model: Instance of timesketch.models.[model] object
        """
        db_session.add(model)
        db_session.commit()

    def _create_user(self, username, set_password=False, set_admin=False):
        """Create a user in the database.
        Args:
            username: Username (string)
            set_password: Boolean value to decide if a password should be set
            set_admin: Boolean value to decide if the user should be an admin
        Returns:
            A user (instance of timesketch.models.user.User)
        """
        user = User.get_or_create(username=username, name=username)
        if set_password:
            user.set_password(plaintext="test", rounds=4)
        if set_admin:
            user.admin = True
        self._commit_to_database(user)
        return user

    def _create_group(self, name, user):
        """Create a user in the database.
        Args:
            name: Group name
            user: A user (instance of timesketch.models.user.User)
        Returns:
            A group (instance of timesketch.models.user.Group)
        """
        group = Group.get_or_create(name=name, display_name=name, description=name)
        user.groups.append(group)
        self._commit_to_database(group)
        return group

    def _create_sketch(self, name, user, acl=False):
        """Create a sketch in the database.
        Args:
            name: Name of the sketch (string)
            user: A user (instance of timesketch.models.user.User)
            acl: Boolean value to decide if ACL permissions should be set
        Returns:
            A sketch (instance of timesketch.models.sketch.Sketch)
        """
        sketch = Sketch.get_or_create(name=name, description=name, user=user)
        if acl:
            for permission in ["read", "write", "delete"]:
                sketch.grant_permission(permission=permission, user=user)
        label = sketch.Label(label="Test label", user=user)
        status = sketch.Status(status="Test status", user=user)
        sketch.labels.append(label)
        sketch.status.append(status)
        self._commit_to_database(sketch)
        return sketch

    def _create_searchindex(self, name, user, acl=False):
        """Create a searchindex in the database.
        Args:
            name: Name of the searchindex (string)
            user: A user (instance of timesketch.models.user.User)
            acl: Boolean value to decide if ACL permissions should be set
        Returns:
            A searchindex (instance of timesketch.models.sketch.SearchIndex)
        """
        searchindex = SearchIndex.get_or_create(
            name=name, description=name, index_name=name, user=user
        )
        if acl:
            for permission in ["read", "write", "delete"]:
                searchindex.grant_permission(permission=permission, user=user)
        searchindex.set_status(status="ready")
        self._commit_to_database(searchindex)
        return searchindex

    def _create_event(self, sketch, searchindex, user):
        """Create an event in the database.
        Args:
            sketch: A sketch (instance of timesketch.models.sketch.Sketch)
            searchindex:
                A searchindex (instance of timesketch.models.sketch.SearchIndex)
            user: A user (instance of timesketch.models.user.User)
        Returns:
            An event (instance of timesketch.models.sketch.Event)
        """
        event = Event.get_or_create(
            sketch=sketch, searchindex=searchindex, document_id="test"
        )
        comment = event.Comment(comment="test", user=user)
        event.comments.append(comment)
        self._commit_to_database(event)
        return event

    def _create_story(self, sketch, user):
        """Create a story in the database.
        Args:
            sketch: A sketch (instance of timesketch.models.sketch.Sketch)
            user: A user (instance of timesketch.models.user.User)
        Returns:
            A story (instance of timesketch.models.story.Story)
        """
        story = Story.get_or_create(
            title="Test", content="Test", sketch=sketch, user=user
        )
        self._commit_to_database(story)
        return story

    def _create_timeline(self, name, sketch, searchindex, user):
        """Create a timeline in the database.
        Args:
            name: Name of the timeline (string)
            sketch: A sketch (instance of timesketch.models.sketch.Sketch)
            searchindex:
                A searchindex (instance of timesketch.models.sketch.SearchIndex)
            user: A user (instance of timesketch.models.user.User)
        Returns:
            A timeline (instance of timesketch.models.sketch.Timeline)
        """
        timeline = Timeline(
            name=name,
            description=name,
            user=user,
            sketch=sketch,
            searchindex=searchindex,
            color=self.COLOR_WHITE,
        )
        timeline.set_status(status="ready")
        self._commit_to_database(timeline)
        return timeline

    def _create_view(self, name, sketch, user):
        """Create a view in the database.
        Args:
            name: Name of the view (string)
            sketch: A sketch (instance of timesketch.models.sketch.Sketch)
            user: A user (instance of timesketch.models.user.User)
        Returns:
            A view (instance of timesketch.models.sketch.View)
        """
        view = View(
            name=name,
            query_string=name,
            query_filter=json.dumps(dict()),
            user=user,
            sketch=sketch,
        )
        self._commit_to_database(view)
        return view

    def _create_searchtemplate(self, name, user):
        """Create a search template in the database.
        Args:
            name: Name of the view (string)
            user: A user (instance of timesketch.models.user.User)
        Returns:
            A search template (timesketch.models.sketch.SearchTemplate)
        """
        searchtemplate = SearchTemplate(
            name=name, query_string=name, query_filter=json.dumps(dict()), user=user
        )
        self._commit_to_database(searchtemplate)
        return searchtemplate

    def _create_sigma(self, user, rule_yaml, rule_uuid, title, description):
        """Create a sigma rule in the database.
        Args:
            user: A user (instance of timesketch.models.user.User)
            rule_yaml: yaml content of the rule
            rule_uuid: rule uuid of the rule
            title: Title for the rule
            description: description of the rule
        Returns:
            A Sigma Rule (timesketch.models.sigma.SigmaRule)
        """
        sigma = SigmaRule(
            user=user,
            rule_yaml=rule_yaml,
            rule_uuid=rule_uuid,
            title=title,
            description=description,
        )
        self._commit_to_database(sigma)
        return sigma

    def setUp(self):
        """Setup the test database."""
        init_db()

        self.user1 = self._create_user(username="test1", set_password=True)
        self.user2 = self._create_user(username="test2", set_password=False)
        self.useradmin = self._create_user(
            username="testadmin", set_password=True, set_admin=True
        )

        self.group1 = self._create_group(name="test_group1", user=self.user1)
        self.group2 = self._create_group(name="test_group2", user=self.user1)

        self.sketch1 = self._create_sketch(name="Test 1", user=self.user1, acl=True)
        self.sketch2 = self._create_sketch(name="Test 2", user=self.user1, acl=False)
        self.sketch3 = self._create_sketch(name="Test 3", user=self.user1, acl=True)

        self.searchindex = self._create_searchindex(
            name="test", user=self.user1, acl=True
        )
        self.searchindex2 = self._create_searchindex(
            name="test2", user=self.user1, acl=True
        )

        self.timeline = self._create_timeline(
            name="Timeline 1",
            sketch=self.sketch1,
            searchindex=self.searchindex,
            user=self.user1,
        )

        self.view1 = self._create_view(
            name="View 1", sketch=self.sketch1, user=self.user1
        )
        self.view2 = self._create_view(
            name="View 2", sketch=self.sketch2, user=self.user1
        )
        self.view3 = self._create_view(name="", sketch=self.sketch1, user=self.user2)

        self.searchtemplate = self._create_searchtemplate(
            name="template", user=self.user1
        )

        self.event = self._create_event(
            sketch=self.sketch1, searchindex=self.searchindex, user=self.user1
        )

        self.story = self._create_story(sketch=self.sketch1, user=self.user1)

        self.sigma1 = self._create_sigma(
            user=self.user1,
            rule_uuid="5266a592-b793-11ea-b3de-0242ac130004",
            rule_yaml=SIGMA_RULE,
            title="Suspicious Installation of Zenmap",
            description="Detects suspicious installation of Zenmap",
        )

    def tearDown(self):
        """Tear down the test database."""
        db_session.remove()
        drop_all()

    def login(self):
        """Authenticate the test user."""
        self.client.post(
            "/login/",
            data=dict(username="test1", password="test"),
            follow_redirects=True,
        )

    def login_admin(self):
        """Authenticate the test user with admin privileges."""
        self.client.post(
            "/login/",
            data=dict(username="testadmin", password="test"),
            follow_redirects=True,
        )

    def test_unauthenticated(self):
        """
        Generic test for all resources. It tests that no
        unauthenticated request are accepted.
        """
        if not getattr(self, "resource_url", False):
            self.skipTest(self)

        response = self.client.get(self.resource_url)
        if response.status_code == 405:
            response = self.client.post(self.resource_url)
        if isinstance(response.data, six.binary_type):
            response_data = codecs.decode(response.data, "utf-8")
        else:
            response_data = response.data
        self.assertIn("/login/", response_data)
        self.assertEqual(response.status_code, HTTP_STATUS_CODE_REDIRECT)


class ModelBaseTest(BaseTest):
    """Base class for database model tests."""

    def _test_db_object(self, expected_result=None, model_cls=None):
        """Generic test that checks if the stored data is correct."""
        db_obj = model_cls.get_by_id(1)
        for x in expected_result:
            k, v = x[0], x[1]
            self.assertEqual(db_obj.__getattribute__(k), v)
