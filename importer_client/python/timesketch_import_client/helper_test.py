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
"""Tests for the Timesketch importer."""
from __future__ import unicode_literals

import unittest
import tempfile

from . import helper


MOCK_CONFIG = """
foobar:
        message: 'The {cA} went bananas with {cC}, but without letting {cD} know.'
        timestamp_desc: 'Event Logged'
        datetime: 'cB'
        columns_subset: 'cA,cB,cC,cD'

bar:
        message: 'Some people {stuff}, with {other}'
        timestamp_desc: 'Stuff Happened'
        separator: '>'
        encoding: 'secret-formula'
        data_type: 'data:secret:message'

vindur:
        message: 'Vedrid i dag er: {vedur}, med typiskri {auka}'
        timestamp_desc: 'Thu Veist Thad'
        columns: 'vedur,magn,auka,rigning'
"""

class MockStreamer:
    """Mock streamer object for testing."""

    def __init__(self):
        """Initialize."""
        self.format_string = ''
        self.timestamp_description = ''
        self.csv_delimiter = ''
        self.text_encoding = ''
        self.datetime_column = ''

    def set_message_format_string(self, message):
        self.format_string = message

    def set_timestamp_description(self, timestamp_desc):
        self.timestamp_description = timestamp_desc

    def set_csv_delimiter(self, separator):
        self.csv_delimiter = separator

    def set_text_encoding(self, encoding):
        self.text_encoding = encoding

    def set_datetime_column(self, datetime_string):
        self.datetime_column = datetime_string


class TimesketchHelperTest(unittest.TestCase):
    """Test Timesketch import helper."""

    def setUp(self):
        """Set up the test."""
        self._helper = helper.ImportHelper()
        with tempfile.NamedTemporaryFile('w', suffix='.yaml') as fw:
            fw.write(MOCK_CONFIG)
            fw.seek(0)
            self._helper.add_config(fw.name)

    def test_not_config(self):
        """Test a helper that does not match."""
        streamer = MockStreamer()
        self._helper.configure_streamer(streamer, data_type='foo:no')

        self.assertEqual(streamer.format_string, '')
        self.assertEqual(streamer.timestamp_description, '')
        self.assertEqual(streamer.csv_delimiter, '')
        self.assertEqual(streamer.text_encoding, '')
        self.assertEqual(streamer.datetime_column, '')

    def test_sub_column(self):
        """Test a helper that matches on sub columns."""
        streamer = MockStreamer()
        self._helper.configure_streamer(
            streamer, data_type='foo:no',
            columns=['cA', 'cB', 'cC', 'cD', 'cE', 'cF', 'cG'])

        self.assertEqual(
            streamer.format_string,
            'The {cA} went bananas with {cC}, but without letting {cD} know.')
        self.assertEqual(streamer.timestamp_description, 'Event Logged')
        self.assertEqual(streamer.csv_delimiter, '')
        self.assertEqual(streamer.text_encoding, '')
        self.assertEqual(streamer.datetime_column, 'cB')

    def test_columns(self):
        """Test a helper that matches on columns."""
        streamer = MockStreamer()
        self._helper.configure_streamer(
            streamer, data_type='foo:no',
            columns=['vedur', 'magn', 'auka', 'rigning'])

        self.assertEqual(
            streamer.format_string,
            'Vedrid i dag er: {vedur}, med typiskri {auka}')
        self.assertEqual(streamer.timestamp_description, 'Thu Veist Thad')
        self.assertEqual(streamer.csv_delimiter, '')
        self.assertEqual(streamer.text_encoding, '')
        self.assertEqual(streamer.datetime_column, '')

    def test_data_type(self):
        """Test a helper that matches on data_type."""
        streamer = MockStreamer()
        self._helper.configure_streamer(
            streamer, data_type='data:secret:message',
            columns=['vedur', 'auka', 'rigning'])

        self.assertEqual(
            streamer.format_string,
            'Some people {stuff}, with {other}')
        self.assertEqual(streamer.timestamp_description, 'Stuff Happened')
        self.assertEqual(streamer.csv_delimiter, '>')
        self.assertEqual(streamer.text_encoding, 'secret-formula')
        self.assertEqual(streamer.datetime_column, '')
