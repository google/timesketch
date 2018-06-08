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

from parameterized import parameterized

from timesketch.lib.cypher.restrict_query_to_sketch import \
    restrict_query_to_sketch
from timesketch.lib.cypher.invalid_query import InvalidQuery
# pylint: disable=bad-continuation


def edge_names():
    return (
        name + type + length + space
        for name in ['', 'e']
        for type in ['', ':TYPE']
        for length in ['', '*', '*..', '*0..', '*..0', '*0..1']
        for space in ['', ' ']
    )


def node_names():
    return (
        name + labels + space
        for name in ['', 'a']
        for labels in ['', ':Label', ':Label1:Label2']
        for space in ['', ' ']
    )


def valid_properties():
    return ['', ' ', 'int: 3', 'int: 3, string: "bla"', 'list: [1, 2]']


def invalid_properties():
    return [
        'sketch_id: 10', 'sketch_id: null', 'string: "bla", sketch_id: 10',
        'sketch_id: 10, sketch_id: 10', 'sketch_id: 10, sketch_id: null',
    ]


def edge_directions():
    return [('-', '-'), ('-', '->'), ('<-', '-')]


queries = [
    ('in match clause', 'MATCH %s'),
    ('in pattern comprehension', 'WITH [p = %s | p] AS ps'),
    ('in pattern comprehension nested inside list comprehension',
        'WITH [x IN [1, 2] | size([%s | 1])] AS xs',
    ),
    ('in pattern expression', 'WITH size(%s) AS s'),
]


invalid_queries = [
    'CALL db.labels()', 'CALL db.propertyKeys()', 'MERGE (a:Label)',
    'CREATE (a:Label)', 'MATCH (a) SET a.x = 3', 'RETURN 1',
    'MATCH (a) DETACH DELETE (a)', 'MATCH (a:Label) REMOVE a:Label',
    'MATCH p = ()--() FOREACH (r IN nodes(p) | SET r.marked = true)',
    'MATCH p = ()--() FOREACH (r IN nodes(p) | CREATE (a {x: r.x}))',
    'MATCH (a) REMOVE a.property',
    'CREATE INDEX ON :Label(property)',
    'DROP INDEX ON :Label(property)',
    'CREATE CONSTRAINT ON (n:Label) ASSERT n.property IS UNIQUE',
    'DROP CONSTRAINT ON (n:Label) ASSERT n.property IS UNIQUE',
    'LOAD CSV WITH HEADERS FROM "a.csv" AS l WITH l MATCH (a {x: l.x})',
    'LOAD CSV FROM "a.csv" AS l WITH l MATCH (a {x: l.x})',
    'START a=node(5) MATCH (a)--(b)',
]


class TestRestrictQueryToSketch(unittest.TestCase):
    """Tests."""

    @parameterized.expand(queries)
    def test_node_with_properties(self, test_name, query):
        if 'pattern' in test_name:
            return
        patterns = ((
            '(%s{%s})' % (name, props),
            '(%s{sketch_id: 42, %s})' % (name, props))
            for name in node_names()
            for props in valid_properties()
        )
        for input_pattern, expected_pattern in patterns:
            output = restrict_query_to_sketch(query % input_pattern, 42)
            self.assertEqual(output, ((query % expected_pattern)
                .replace(', }', '}')
                .replace(',  }', ' }')
            ))

    @parameterized.expand(queries)
    def test_node_without_properties(self, test_name, query):
        if 'pattern' in test_name:
            return
        patterns = ((
            '(%s)' % name,
            '(%s{sketch_id: 42})' % name)
            for name in node_names()
        )
        for input_pattern, expected_pattern in patterns:
            output = restrict_query_to_sketch(query % input_pattern, 42)
            self.assertEqual(output, ((query % expected_pattern)
                .replace(', }', '}')
                .replace(',  }', ' }')
            ))

    @parameterized.expand(queries)
    def test_node_with_invalid_properties(self, test_name, query):
        if 'pattern' in test_name:
            return
        patterns = (
            '(%s{%s})' % (name, props)
            for name in node_names()
            for props in invalid_properties()
        )
        for input_pattern in patterns:
            with self.assertRaises(InvalidQuery):
                restrict_query_to_sketch(query % input_pattern, 42)

    @parameterized.expand(queries)
    def test_edge_with_properties(self, _, query):
        patterns = ((
            '()%s[%s{%s}]%s()' % (left, name, props, right),
            '({sketch_id: 42})%s[%s{sketch_id: 42, %s}]%s({sketch_id: 42})'
            % (left, name, props, right))
            for name in edge_names()
            for left, right in edge_directions()
            for props in valid_properties()
        )
        for input_pattern, expected_pattern in patterns:
            output = restrict_query_to_sketch(query % input_pattern, 42)
            self.assertEqual(output, ((query % expected_pattern)
                .replace(', }', '}')
                .replace(',  }', ' }')
            ))

    @parameterized.expand(queries)
    def test_edge_without_properties(self, _, query):
        patterns = ((
            '()%s[%s]%s()' % (left, name, right),
            '({sketch_id: 42})%s[%s{sketch_id: 42}]%s({sketch_id: 42})'
            % (left, name, right),
            ) for name in edge_names()
            for left, right in edge_directions()
        )
        for input_pattern, expected_pattern in patterns:
            output = restrict_query_to_sketch(query % input_pattern, 42)
            self.assertEqual(output, ((query % expected_pattern)
                .replace(', }', '}')
                .replace(',  }', ' }')
            ))

    @parameterized.expand(queries)
    def test_edge_with_invalid_properties(self, _, query):
        patterns = (
            '()%s[%s{%s}]%s()' % (left, name, props, right)
            for name in edge_names()
            for left, right in edge_directions()
            for props in invalid_properties()
        )
        for input_pattern in patterns:
            with self.assertRaises(InvalidQuery):
                restrict_query_to_sketch(query % input_pattern, 42)

    @parameterized.expand(queries)
    def test_edge_without_bracket(self, _, query):
        patterns = ((
            '()%s%s()' % (left, right),
            '({sketch_id: 42})%s[{sketch_id: 42}]%s({sketch_id: 42})'
            % (left, right),
            ) for left, right in edge_directions()
        )
        for input_pattern, expected_pattern in patterns:
            output = restrict_query_to_sketch(query % input_pattern, 42)
            self.assertEqual(output, ((query % expected_pattern)
                .replace(', }', '}')
                .replace(',  }', ' }')
            ))

    def test_invalid_queries(self):
        for query in invalid_queries:
            try:
                with self.assertRaises(InvalidQuery):
                    restrict_query_to_sketch(query, 42)
            except AssertionError as e:
                raise self.failureException('%s for %s' % (e.message, query))

    def test_spaces_in_rel_pattern(self):
        queries_with_spaces_int_rel_pattern = [
            'MATCH () -    - ()',
            'MATCH () -- >()',
            'MATCH ()< --()',
            'MATCH ()<- -()',
            'MATCH ()<- - ()',
        ]
        for query in queries_with_spaces_int_rel_pattern:
            try:
                with self.assertRaises(InvalidQuery):
                    print restrict_query_to_sketch(query, 42)
            except AssertionError as e:
                raise self.failureException('%s for %s' % (e.message, query))
