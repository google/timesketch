# Copyright 2020 Google Inc. All rights reserved.
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
import unittest
import mock

from . import client
from . import search
from . import test_lib


class SearchTest(unittest.TestCase):
    """Test Search object."""

    @mock.patch('requests.Session', test_lib.mock_session)
    def setUp(self):
        """Setup test case."""
        self.api_client = client.TimesketchApi(
            'http://127.0.0.1', 'test', 'test')
        self.sketch = self.api_client.get_sketch(1)

    def test_from_saved(self):
        """Test fetching object from store."""
        search_obj = search.Search(sketch=self.sketch)
        search_obj.from_saved(1)

        self.assertIsInstance(search_obj, search.Search)
        self.assertEqual(search_obj.id, 1)
        self.assertEqual(search_obj.name, 'test')
        query_filter = search_obj.query_filter

        self.assertEqual(query_filter.get('chips'), [])
        self.assertIsNone(query_filter.get('time_start', 'AA'))

    def test_from_manual(self):
        """Test fetching data."""
        search_obj = search.Search(sketch=self.sketch)
        search_obj.query_string = '*'
        df = search_obj.table
        self.assertEqual(len(df), 1)
        search_dict = search_obj.to_dict()
        meta = search_dict.get('meta', {})
        es_time = meta.get('es_time', 0)
        self.assertEqual(es_time, 12)

        objects = search_dict.get('objects', [])
        self.assertEqual(len(objects), 1)

    def test_range_chip(self):
        """Test date range chip."""
        chip = search.DateRangeChip()
        chip.start_time = '2020-11-30T12:12:12'
        chip.end_time = '2020-11-30T12:45:12'

        self.assertEqual(
            chip.date_range, '2020-11-30T12:12:12,2020-11-30T12:45:12')

        with self.assertRaises(ValueError):
            chip.start_time = '20bar'

        expected_chip = {
            'active': True,
            'field': '',
            'type': 'datetime_range',
            'operator': 'must',
            'value': '2020-11-30T12:12:12,2020-11-30T12:45:12',
        }
        self.assertEqual(chip.chip, expected_chip)

    def test_label_chip(self):
        """Test label chip."""
        chip = search.LabelChip()
        chip.label = 'foobar'

        expected_chip = {
            'active': True,
            'field': '',
            'type': 'label',
            'operator': 'must',
            'value': 'foobar'
        }
        self.assertEqual(chip.chip, expected_chip)

    def test_term_chip(self):
        """Test term chip."""
        chip = search.TermChip()
        chip.field = 'foobar'
        chip.query = '2fold'

        expected_chip = {
            'active': True,
            'field': 'foobar',
            'type': 'term',
            'operator': 'must',
            'value': '2fold'
        }
        self.assertEqual(chip.chip, expected_chip)

    def test_date_interval(self):
        """Test date interval chip."""
        chip = search.DateIntervalChip()
        with self.assertRaises(ValueError):
            chip.date = '20 minutes'

        date_string = '2020-11-30T12:12:12'
        chip.date = date_string

        expected_chip = {
            'active': True,
            'field': '',
            'type': 'datetime_interval',
            'operator': 'must',
            'value': f'{date_string} -5m +5m'
        }
        self.assertEqual(chip.chip, expected_chip)

        chip.unit = 'h'
        chip.before = 1
        chip.after = 6
        expected_chip['value'] = f'{date_string} -1h +6h'

        self.assertEqual(chip.chip, expected_chip)
