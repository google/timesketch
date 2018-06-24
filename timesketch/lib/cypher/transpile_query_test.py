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
"""Tests."""
import unittest

from timesketch.lib.cypher.transpile_query import \
    transpile_query


class TestTranspileQuery(unittest.TestCase):
    """Tests."""

    def test_simple(self):
        input_query = 'MATCH (a)-[e]->(b)'
        expected_output = 'MATCH ' \
            '(a{sketch_id: 42})-[e{sketch_id: 42}]->(b{sketch_id: 42}) ' \
            'RETURN [id(a), id(b)] AS nodes, ' \
            '[id(e)] AS edges, [e.timestamps] AS timestamps ' \
            'LIMIT 10000'
        transpiled = transpile_query(input_query, sketch_id=42)
        self.assertEqual(transpiled, expected_output)

    def test_union(self):
        input_query = 'MATCH (a) UNION MATCH (b)'
        expected_output = \
            'MATCH (a{sketch_id: 42}) ' \
            'RETURN [id(a)] AS nodes, ' \
            '[] AS edges, [] AS timestamps ' \
            'LIMIT 10000 ' \
            'UNION ' \
            'MATCH (b{sketch_id: 42}) ' \
            'RETURN [id(b)] AS nodes, ' \
            '[] AS edges, [] AS timestamps ' \
            'LIMIT 10000'
        transpiled = transpile_query(input_query, sketch_id=42)
        self.assertEqual(transpiled, expected_output)

    def test_union_all(self):
        input_query = 'MATCH (a) UNION ALL MATCH (b)'
        expected_output = \
            'MATCH (a{sketch_id: 42}) ' \
            'RETURN [id(a)] AS nodes, ' \
            '[] AS edges, [] AS timestamps ' \
            'LIMIT 10000 ' \
            'UNION ALL ' \
            'MATCH (b{sketch_id: 42}) ' \
            'RETURN [id(b)] AS nodes, ' \
            '[] AS edges, [] AS timestamps ' \
            'LIMIT 10000'
        transpiled = transpile_query(input_query, sketch_id=42)
        self.assertEqual(transpiled, expected_output)
