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

from timesketch.lib.cypher.append_return_clause import \
    append_return_clause


class TestAppendReturnClause(unittest.TestCase):
    """Tests."""

    def extract_output(self, result):
        return ('RETURN' + result.split('RETURN')[1].split('LIMIT')[0]).strip()

    def test_nothing(self):
        input_query = 'MATCH ()--()'
        expected = 'RETURN [] AS nodes, ' \
            '[] AS edges, [] AS timestamps'
        result = self.extract_output(append_return_clause(input_query))
        self.assertEqual(result, expected)

    def test_node(self):
        input_query = 'MATCH (a)'
        expected = 'RETURN [id(a)] AS nodes, ' \
            '[] AS edges, [] AS timestamps'
        result = self.extract_output(append_return_clause(input_query))
        self.assertEqual(result, expected)

    def test_2_nodes(self):
        input_query = 'MATCH (a)-->(b)'
        expected = 'RETURN [id(a), id(b)] AS nodes, ' \
            '[] AS edges, [] AS timestamps'
        result = self.extract_output(append_return_clause(input_query))
        self.assertEqual(result, expected)

    def test_edge(self):
        input_query = 'MATCH ()-[e]->()'
        expected = 'RETURN [] AS nodes, ' \
            '[id(e)] AS edges, [e.timestamps] AS timestamps'
        result = self.extract_output(append_return_clause(input_query))
        self.assertEqual(result, expected)

    def test_2_edges(self):
        input_query = 'MATCH ()-[e1]->()-[e2]->()'
        expected = 'RETURN [] AS nodes, ' \
            '[id(e1), id(e2)] AS edges, ' \
            '[e1.timestamps, e2.timestamps] AS timestamps'
        result = self.extract_output(append_return_clause(input_query))
        self.assertEqual(result, expected)

    def test_varlength_edge(self):
        input_queries = (
            'MATCH ()-[e1]->()-[e2%s]->()' % length
            for length in ['*', '*..', '*0..', '*..1', '*0..1']
        )
        expected = 'RETURN [] AS nodes, ' \
            '[id(e1)] AS edges, [e1.timestamps] AS timestamps'
        for input_query in input_queries:
            result = self.extract_output(append_return_clause(input_query))
            self.assertEqual(result, expected)

    def test_local_binders(self):
        input_query = 'MATCH (a) WHERE size((b)-[c]-(d)) > 0'
        expected = 'RETURN [id(a)] AS nodes, [] AS edges, [] AS timestamps'
        result = self.extract_output(append_return_clause(input_query))
        self.assertEqual(result, expected)
