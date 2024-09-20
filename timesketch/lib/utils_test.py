# Copyright 2014 Google Inc. All rights reserved.
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
"""Tests for utils."""

from __future__ import unicode_literals

import re
import pandas as pd

from timesketch.lib.testlib import BaseTest
from timesketch.lib.utils import get_validated_indices
from timesketch.lib.utils import random_color
from timesketch.lib.utils import read_and_validate_csv
from timesketch.lib.utils import check_mapping_errors
from timesketch.lib.utils import _validate_csv_fields
from timesketch.lib.utils import rename_jsonl_headers


TEST_CSV = "tests/test_events/sigma_events.csv"
ISO8601_REGEX = (
    r"^(-?(?:[1-9][0-9]*)?[0-9]{4})-(1[0-2]|0[1-9])-(3[01]|0["
    r"1-9]|[12][0-9])T(2[0-3]|[01][0-9]):([0-5][0-9]):([0-5]["
    r"0-9])(\.[0-9]+)?(Z|[+-](?:2[0-3]|[01][0-9]):[0-5][0-9])?$"
)


class TestUtils(BaseTest):
    """Tests for the functionality on the utils module."""

    def test_random_color(self):
        """Test to generate a random color."""
        color = random_color()
        self.assertTrue(re.match("^[0-9a-fA-F]{6}$", color))

    def test_get_validated_indices(self):
        """Test for validating indices."""
        sketch = self.sketch1
        sketch_indices = [t.searchindex.index_name for t in sketch.timelines]

        valid_indices = ["test"]
        invalid_indices = ["test", "fail"]
        test_indices, _ = get_validated_indices(valid_indices, sketch)
        self.assertListEqual(sketch_indices, test_indices)

        test_indices, _ = get_validated_indices(invalid_indices, sketch)
        self.assertFalse("fail" in test_indices)

    def test_header_validation(self):
        """Test for Timesketch header validation."""
        mandatory_fields = ["message", "datetime", "fortytwo"]
        with self.assertRaises(RuntimeError):
            # Call next to work around lazy generators.
            next(read_and_validate_csv(TEST_CSV, ",", mandatory_fields))

    def test_date_normalisation(self):
        """Test for ISO date compliance."""
        data_generator = read_and_validate_csv(TEST_CSV)
        for row in data_generator:
            self.assertRegex(row["datetime"], ISO8601_REGEX)

    def test_invalid_headers_mapping(self):
        """Test for invalid headers mapping"""
        current_headers = ["DT", "message", "TD"]

        invalid_mapping_1 = [
            {"target": "datetime", "source": ["DT"], "default_value": None},
            {
                "target": "timestamp_desc",
                "source": ["No."],
                "default_value": None,
            },
            {"target": "message", "source": ["Source"], "default_value": None},
        ]
        # column message already exists
        with self.assertRaises(RuntimeError):
            # Call next to work around lazy generators.
            next(check_mapping_errors(current_headers, invalid_mapping_1))

        invalid_mapping_2 = [
            {"target": "datetime", "source": ["DT"], "default_value": None},
            {
                "target": "timestamp_desc",
                "source": ["TD", "nope"],
                "default_value": None,
            },
        ]
        # nope columns does not exists
        with self.assertRaises(RuntimeError):
            # Call next to work around lazy generators.
            next(check_mapping_errors(current_headers, invalid_mapping_2))

        invalid_mapping_3 = [
            {"target": "datetime", "source": ["DT"], "default_value": None},
            {
                "target": "timestamp_desc",
                "source": ["DT"],
                "default_value": None,
            },
        ]
        # 2 mandatory headers point to the same existing one
        with self.assertRaises(RuntimeError):
            # Call next to work around lazy generators.
            next(check_mapping_errors(current_headers, invalid_mapping_3))

    def test_valid_headers_mapping(self):
        """Test for valid headers mapping"""
        current_headers = ["DT", "message", "TD"]

        valid_mapping_1 = [
            {"target": "datetime", "source": ["DT"], "default_value": None},
            {
                "target": "timestamp_desc",
                "source": ["TD"],
                "default_value": None,
            },
        ]
        self.assertIs(check_mapping_errors(current_headers, valid_mapping_1), None)

        valid_mapping_2 = [
            {"target": "datetime", "source": ["DT"], "default_value": None},
            {"target": "timestamp_desc", "source": None, "default_value": "a"},
        ]
        self.assertIs(check_mapping_errors(current_headers, valid_mapping_2), None)

        current_headers = ["DT", "last_access", "TD", "file_path"]
        valid_mapping_3 = [
            {"target": "datetime", "source": ["DT"], "default_value": None},
            {"target": "timestamp_desc", "source": None, "default_value": "a"},
            {
                "target": "message",
                "source": ["TD", "file_path"],
                "default_value": None,
            },
        ]
        self.assertIs(check_mapping_errors(current_headers, valid_mapping_3), None)

        current_headers = ["DT", "last_access", "TD", "file_path", "T_desc"]
        valid_mapping_4 = [
            {"target": "datetime", "source": ["DT"], "default_value": None},
            {
                "target": "timestamp_desc",
                "source": ["T_desc"],
                "default_value": None,
            },
            {
                "target": "message",
                "source": ["T_desc", "file_path"],
                "default_value": None,
            },
        ]
        self.assertIs(check_mapping_errors(current_headers, valid_mapping_4), None)

    def test_invalid_CSV_file(self):
        """Test for CSV with missing mandatory headers without mapping"""
        mandatory_fields = ["message", "datetime", "timestamp_desc"]

        df_01 = pd.DataFrame({"DT": ["test"], "MSG": ["test"], "TD": ["test"]})

        with self.assertRaises(RuntimeError):
            # Call next to work around lazy generators.
            next(_validate_csv_fields(mandatory_fields, df_01))

        df_02 = pd.DataFrame({"datetime": ["test"], "MSG": ["test"], "TD": ["test"]})
        with self.assertRaises(RuntimeError):
            # Call next to work around lazy generators.
            next(_validate_csv_fields(mandatory_fields, df_02))

    def test_missing_timestamp_csv_file(self):
        """Test for parsing datetime values in CSV file"""

        # Test that a timestamp is generated if missing.

        expected_output = {
            "message": "No timestamp",
            "datetime": "2022-07-24T19:01:01+00:00",
            "timestamp_desc": "Time Logged",
            "data_type": "This event has no timestamp",
            "timestamp": 1658689261000000,
        }
        self.assertDictEqual(
            next(
                read_and_validate_csv(
                    "tests/test_events/validate_date_events_missing_timestamp.csv"
                )
            ),
            expected_output,
        )

    def test_timestamp_is_ISOformat(self):
        """Test that timestamp values in CSV file are not altered"""

        # Make sure timestamp is processed correctly, and the format is not altered
        expected_outputs = [
            {
                "message": "Checking timestamp conversion",
                "timestamp": 1331698658000000,
                "datetime": "2012-03-14T04:17:38+00:00",
                "timestamp_desc": "Time Logged",
                "data_type": "This event has timestamp",
            },
            {
                "message": "Checking timestamp conversion",
                "timestamp": 1658689261000000,
                "datetime": "2022-07-24T19:01:01+00:00",
                "timestamp_desc": "Time Logged",
                "data_type": "This event has timestamp",
            },
            {
                "message": "Make sure message is same",
                "timestamp": 1437789661000000,
                "datetime": "2015-07-25T02:01:01+00:00",
                "timestamp_desc": "Logging",
                "data_type": "This data_type should stay the same",
            },
        ]
        results = iter(
            read_and_validate_csv("tests/test_events/validate_timestamp_conversion.csv")
        )
        for output in expected_outputs:
            self.assertDictEqual(next(results), output)

    def test_missing_datetime_in_CSV(self):
        """Test for parsing a file with missing datetime field does attempt
        to get it from timestamp or fail"""
        results = iter(
            read_and_validate_csv(
                "tests/test_events/validate_no_datetime_timestamps.csv"
            )
        )

        n = 1
        for item in results:
            n = n + 1
            if item["data_type"] == "No timestamp1":
                self.assertIsNotNone(item["timestamp"])
                self.assertEqual(item["timestamp"], 1437789661000000)
                self.assertIsNotNone(item["datetime"])
                self.assertEqual(item["datetime"], "2015-07-25T02:01:01+00:00")

            elif item["data_type"] == "No timestamp2":
                self.assertIsNotNone(item["timestamp"])
                self.assertEqual(item["timestamp"], 1406253661000000)
                self.assertIsNotNone(item["datetime"])
                self.assertEqual(item["datetime"], "2014-07-25T02:01:01+00:00")
            elif item["data_type"] == "Whitespace datetime":
                self.assertIsNotNone(item["timestamp"])
                self.assertEqual(item["datetime"], "2016-07-25T02:01:01+00:00")
                self.assertIsNotNone(item["datetime"])

        self.assertGreaterEqual(n, 3)

    def test_time_datetime_valueerror(self):
        """Test for parsing a file with time precision

        The file is currently parsed as:
        {'message': 'Missing timezone info', 'timestamp': 123456,
            'datetime': '2017-09-24T19:01:01',
            'timestamp_desc': 'Write time',
            'data_type': 'Missing_timezone_info'}
        {'message': 'Wrong epoch', 'timestamp': 123456,
            'datetime': '2017-07-24T19:01:01',
            'timestamp_desc': 'Write time',
            'data_type': 'wrong_timestamp'}
        {'message': 'Wrong epoch', 'timestamp': 9999999999999,
            'datetime': '2017-10-24T19:01:01',
            'timestamp_desc': 'Write time',
            'data_type': 'long_timestamp'}

        """

        results = iter(read_and_validate_csv("tests/test_events/invalid_datetime.csv"))
        results_list = []
        for item in results:
            results_list.append(item)
            self.assertIsNotNone(item)
        # check that certain values are not present in results_list
        self.assertNotIn(
            "wrong_datetime_1",
            str(results_list),
            "Parsed line is in results but should be skipped",
        )
        self.assertIn("long_timestamp", str(results_list))

    def test_datetime_out_of_normal_range_in_csv(self):
        """Test for parsing a file with datetimes that are way out of range for
        normal usage
        One of the reasons to create this is:
        https://github.com/google/timesketch/issues/1617
        """
        results = iter(
            read_and_validate_csv("tests/test_events/validate_time_out_of_range.csv")
        )
        results_list = []
        for item in results:
            results_list.append(item)
            self.assertIsNotNone(item["timestamp"])

        self.assertIn("csv_very_future_event", str(results_list))
        self.assertIn("2227-12-31T23:01:01+00:00", str(results_list))
        self.assertNotIn("1601-01-01", str(results_list))

    def test_time_precision_in_csv(self):
        """Test for parsing a file with time precision"""
        results = iter(
            read_and_validate_csv("tests/test_events/validate_time_precision.csv")
        )
        results_list = []
        for item in results:
            results_list.append(item)
            self.assertIsNotNone(item["timestamp"])

        self.assertIn("timestamptest1", str(results_list))
        self.assertIn("2024-07-24T10:57:02.877297+00:00", str(results_list))
        self.assertIn("timestamptest2", str(results_list))

    def test_invalid_JSONL_file(self):
        """Test for JSONL with missing keys in the dictionary wrt headers mapping"""
        linedict = {"DT": "2011-11-11", "MSG": "this is a test"}
        headers_mapping = [
            {"target": "datetime", "source": ["DT"], "default_value": None},
            {
                "target": "timestamp_desc",
                "source": None,
                "default_value": "test time",
            },
            {"target": "message", "source": ["msg"], "default_value": None},
        ]
        lineno = 0
        with self.assertRaises(RuntimeError):
            # Call next to work around lazy generators.
            next(rename_jsonl_headers(linedict, headers_mapping, lineno))

        linedict = {
            "DT": "2011-11-11",
            "MSG": "this is a test",
            "ANOTHERMSG": "test2",
        }
        headers_mapping = [
            {"target": "datetime", "source": ["DT"], "default_value": None},
            {
                "target": "timestamp_desc",
                "source": None,
                "default_value": "test time",
            },
            {
                "target": "message",
                "source": ["MSG", "anothermsg"],
                "default_value": None,
            },
        ]
        lineno = 0
        with self.assertRaises(RuntimeError):
            # Call next to work around lazy generators.
            next(rename_jsonl_headers(linedict, headers_mapping, lineno))

    def test_valid_JSONL_file(self):
        """Test valid JSONL with valid headers mapping"""
        linedict = {
            "DT": "2011-11-11",
            "MSG": "this is a test",
            "ANOTHERMSG": "test2",
        }
        lineno = 0
        headers_mapping = [
            {"target": "datetime", "source": ["DT"], "default_value": None},
            {
                "target": "timestamp_desc",
                "source": None,
                "default_value": "test time",
            },
            {
                "target": "message",
                "source": ["MSG", "ANOTHERMSG"],
                "default_value": None,
            },
        ]
        self.assertTrue(
            isinstance(rename_jsonl_headers(linedict, headers_mapping, lineno), dict)
        )
