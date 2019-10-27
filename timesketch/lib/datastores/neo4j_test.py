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

from __future__ import unicode_literals

import mock

from timesketch.lib.datastores.neo4j import Neo4jDataStore
from timesketch.lib.testlib import MockGraphDatabase
from timesketch.lib.testlib import BaseTest


@mock.patch('timesketch.lib.datastores.neo4j.GraphDatabase', MockGraphDatabase)
class Neo4jTest(BaseTest):
    """Test Neo4j datastore."""

    def test_neo4j_output(self):
        """Test Neo4j output format."""
        expected_output = {
            'graph': [{
                'nodes': [{
                    'id': '1',
                    'labels': ['User'],
                    'properties': {
                        'username': 'test',
                        'uid': '123456'
                    }
                }, {
                    'id': '2',
                    'labels': ['Machine'],
                    'properties': {
                        'hostname': 'test'
                    }
                }],
                'relationships': [{
                    'endNode': '2',
                    'id': '3',
                    'startNode': '1',
                    'properties': {
                        'method': 'Network'
                    },
                    'type': 'ACCESS'
                }]
            }],
            'rows':
            None,
            'stats': {}
        }
        datastore = Neo4jDataStore(username='test', password='test')
        formatted_response = datastore.query(query='')
        self.assertIsInstance(formatted_response, dict)
        self.assertDictEqual(formatted_response, expected_output)

    def test_cytoscape_output(self):
        """Test Cytoscape output format."""
        expected_output = {
            'graph': {
                'nodes': [{
                    'data': {
                        'username': 'test',
                        'type': 'User',
                        'id': 'node1',
                        'uid': '123456',
                    }
                }, {
                    'data': {
                        'hostname': 'test',
                        'type': 'Machine',
                        'id': 'node2',
                    }
                }],
                'edges': [{
                    'data': {
                        'target': 'node2',
                        'method': 'Network',
                        'source': 'node1',
                        'type': 'ACCESS',
                        'id': 'edge3',
                    }
                }],
            },
            'rows': None,
            'stats': {},
        }
        datastore = Neo4jDataStore(username='test', password='test')
        formatted_response = datastore.query(
            query='', output_format='cytoscape')
        self.assertIsInstance(formatted_response, dict)
        self.assertDictEqual(formatted_response, expected_output)

    def test_cytoscape_output_empty_graph(self):
        """Test Cytoscape output format for and empty graph."""
        expected_output = {
            'graph': {
                'nodes': [],
                'edges': [],
            },
            'rows': None,
            'stats': {},
        }
        datastore = Neo4jDataStore(username='test', password='test')
        formatted_response = datastore.query(
            query='empty', output_format='cytoscape')
        self.assertIsInstance(formatted_response, dict)
        self.assertDictEqual(formatted_response, expected_output)
