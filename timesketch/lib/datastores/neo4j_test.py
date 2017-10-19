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
"""Tests for the Neo4j datastore."""

import mock

from timesketch.lib.datastores.neo4j import Neo4jDataStore
from timesketch.lib.testlib import MockGraphDatabase
from timesketch.lib.testlib import BaseTest


@mock.patch(u'timesketch.lib.datastores.neo4j.GraphDatabase', MockGraphDatabase)
class Neo4jTest(BaseTest):
    """Test Neo4j datastore."""

    def test_neo4j_output(self):
        """Test Neo4j output format."""
        expected_output = {
            u'graph': [{
                u'nodes': [{
                    u'id': u'1',
                    u'labels': [u'User'],
                    u'properties': {
                        u'username': u'test',
                        u'uid': u'123456'
                    }
                }, {
                    u'id': u'2',
                    u'labels': [u'Machine'],
                    u'properties': {
                        u'hostname': u'test'
                    }
                }],
                u'relationships': [{
                    u'endNode': u'2',
                    u'id': u'3',
                    u'startNode': u'1',
                    u'properties': {
                        u'method': u'Network'
                    },
                    u'type': u'ACCESS'
                }]
            }],
            u'rows':
            None,
            u'stats': {}
        }
        datastore = Neo4jDataStore(username=u'test', password=u'test')
        formatted_response = datastore.query(query=u'')
        self.assertIsInstance(formatted_response, dict)
        self.assertDictEqual(formatted_response, expected_output)

    def test_cytoscape_output(self):
        """Test Cytoscape output format."""
        expected_output = {
            u'graph': {
                u'nodes': [{
                    u'data': {
                        u'username': u'test',
                        u'type': u'User',
                        u'id': u'node1',
                        u'uid': u'123456',
                    }
                }, {
                    u'data': {
                        u'hostname': u'test',
                        u'type': u'Machine',
                        u'id': u'node2',
                    }
                }],
                u'edges': [{
                    u'data': {
                        u'target': u'node2',
                        u'method': u'Network',
                        u'source': u'node1',
                        u'type': u'ACCESS',
                        u'id': u'edge3',
                    }
                }],
            },
            u'rows': None,
            u'stats': {},
        }
        datastore = Neo4jDataStore(username=u'test', password=u'test')
        formatted_response = datastore.query(
            query=u'', output_format=u'cytoscape')
        self.assertIsInstance(formatted_response, dict)
        self.assertDictEqual(formatted_response, expected_output)

    def test_cytoscape_output_empty_graph(self):
        """Test Cytoscape output format for and empty graph."""
        expected_output = {
            u'graph': {
                u'nodes': [],
                u'edges': [],
            },
            u'rows': None,
            u'stats': {},
        }
        datastore = Neo4jDataStore(username=u'test', password=u'test')
        formatted_response = datastore.query(
            query=u'empty', output_format=u'cytoscape')
        self.assertIsInstance(formatted_response, dict)
        self.assertDictEqual(formatted_response, expected_output)
