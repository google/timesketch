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

from timesketch.lib.cypher.unwind_timestamps import \
    unwind_timestamps


class TestUnwindTimestamps(unittest.TestCase):
    """Tests."""

    def test_timestamp_not_referenced(self):
        input_query = 'MATCH (a) RETURN a'
        expected = 'MATCH (a) RETURN a'
        result = unwind_timestamps(input_query)
        self.assertEqual(result, expected)

    def test_timestamp_referenced_in_where(self):
        input_query = 'MATCH ()-[e]-() WHERE e.timestamp < 4'
        expected = 'MATCH ()-[e]-() ' \
            'UNWIND e.timestamps + ' \
            'filter(a IN [null] WHERE e.timestamps_incomplete) ' \
            'AS e_timestamp ' \
            'WITH *  ' \
            'WHERE  coalesce((e_timestamp < 4), e_timestamp IS NULL)'
        result = unwind_timestamps(input_query)
        self.assertEqual(result, expected)

    def test_timestamp_referenced_in_where_with_other_condition_1(self):
        input_query = 'MATCH ()-[e]-() WHERE e.timestamp < 4 ' \
            'AND e.foo = "foo"'
        expected = 'MATCH ()-[e]-() ' \
            'WHERE e.foo = "foo" ' \
            'UNWIND e.timestamps + ' \
            'filter(a IN [null] WHERE e.timestamps_incomplete) ' \
            'AS e_timestamp ' \
            'WITH *  ' \
            'WHERE  coalesce((e_timestamp < 4 AND e.foo = "foo"), ' \
            'e_timestamp IS NULL)'
        result = unwind_timestamps(input_query)
        self.assertEqual(result, expected)

    def test_timestamp_referenced_in_where_with_other_condition_2(self):
        input_query = 'MATCH ()-[e]-() WHERE e.foo = "foo" ' \
            'AND e.timestamp < 4'
        expected = 'MATCH ()-[e]-() ' \
            'WHERE e.foo = "foo" ' \
            'UNWIND e.timestamps + ' \
            'filter(a IN [null] WHERE e.timestamps_incomplete) ' \
            'AS e_timestamp ' \
            'WITH *  ' \
            'WHERE  coalesce((e.foo = "foo" AND e_timestamp < 4), ' \
            'e_timestamp IS NULL)'
        result = unwind_timestamps(input_query)
        self.assertEqual(result, expected)

    def test_timestamp_referenced_in_where_with_other_condition_3(self):
        input_query = 'MATCH ()-[e]-() WHERE e.foo = "foo" ' \
            'AND e.timestamp < 4 ' \
            'AND e.bar = "bar"'
        expected = 'MATCH ()-[e]-() ' \
            'WHERE e.foo = "foo" AND e.bar = "bar" ' \
            'UNWIND e.timestamps + ' \
            'filter(a IN [null] WHERE e.timestamps_incomplete) ' \
            'AS e_timestamp ' \
            'WITH *  ' \
            'WHERE  coalesce((' \
            'e.foo = "foo" AND e_timestamp < 4 AND e.bar = "bar"), ' \
            'e_timestamp IS NULL)'
        result = unwind_timestamps(input_query)
        self.assertEqual(result, expected)

    def test_2_timestamps_referenced_in_where(self):
        input_query = 'MATCH ()-[e1]-()-[e2]-() ' \
            'WHERE e1.timestamp < e2.timestamp < e1.timestamp + 10'
        expected = 'MATCH ()-[e1]-()-[e2]-() ' \
            'UNWIND e1.timestamps + ' \
            'filter(a IN [null] WHERE e1.timestamps_incomplete) ' \
            'AS e1_timestamp ' \
            'UNWIND e2.timestamps + ' \
            'filter(a IN [null] WHERE e2.timestamps_incomplete) ' \
            'AS e2_timestamp ' \
            'WITH *  ' \
            'WHERE  coalesce((' \
            'e1_timestamp < e2_timestamp < e1_timestamp + 10), ' \
            'e1_timestamp IS NULL OR e2_timestamp IS NULL)'
        result = unwind_timestamps(input_query)
        self.assertEqual(result, expected)

    def test_timestamp_referenced_after_where(self):
        input_query = 'MATCH ()-[e]-() WHERE e.foo = "foo" ' \
            'MATCH (a) WHERE e.timestamp < 4'
        expected = 'MATCH ()-[e]-() WHERE e.foo = "foo" ' \
            'UNWIND e.timestamps + ' \
            'filter(a IN [null] WHERE e.timestamps_incomplete) ' \
            'AS e_timestamp ' \
            'WITH *  ' \
            'WHERE e.foo = "foo" ' \
            'MATCH (a) ' \
            'WHERE  coalesce((e_timestamp < 4), e_timestamp IS NULL)'
        result = unwind_timestamps(input_query)
        self.assertEqual(result, expected)

    def test_return_clause_when_timestamp_not_referenced(self):
        input_query = 'MATCH ()-[e]-() RETURN [e.timestamps] AS timestamps'
        expected = 'RETURN [e.timestamps] AS timestamps'
        result = unwind_timestamps(input_query)
        result = 'RETURN' + result.split('RETURN')[1]
        self.assertEqual(result, expected)

    def test_return_clause_when_timestamp_referenced_in_where(self):
        input_query = 'MATCH ()-[e]-() WHERE e.timestamp > 4 ' \
            'RETURN [e.timestamps] AS timestamps'
        expected = 'RETURN [collect(e_timestamp)] AS timestamps'
        result = unwind_timestamps(input_query)
        result = 'RETURN' + result.split('RETURN')[1]
        self.assertEqual(result, expected)

    def test_return_clause_when_timestamp_referenced_after_where(self):
        input_query = 'MATCH ()-[e]-() MATCH (a) WHERE e.timestamp > 4 ' \
            'RETURN [e.timestamps] AS timestamps'
        expected = 'RETURN [collect(e_timestamp)] AS timestamps'
        result = unwind_timestamps(input_query)
        result = 'RETURN' + result.split('RETURN')[1]
        self.assertEqual(result, expected)
