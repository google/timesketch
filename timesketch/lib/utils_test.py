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


import io
import re
import pandas as pd

from timesketch.lib.testlib import BaseTest
from timesketch.lib.utils import get_validated_indices
from timesketch.lib.utils import random_color
from timesketch.lib.utils import read_and_validate_csv
from timesketch.lib.utils import check_mapping_errors
from timesketch.lib.utils import _convert_timestamp_to_datetime
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

    def test_datetime_parsing_six_digit_microseconds(self):
        """Test parsing a datetime string with 6-digit microseconds."""
        datetime_string = "2021-07-30T18:32:26.975000+00:00"
        csv_data = (
            "message,datetime,timestamp_desc\n" f'test_event,"{datetime_string}",test'
        )
        file_handle = io.StringIO(csv_data)
        data_generator = read_and_validate_csv(file_handle)
        result = next(data_generator)

        self.assertEqual(result["datetime"], datetime_string)
        # This timestamp is in microseconds.
        self.assertEqual(result["timestamp"], 1627669946975000)

    def test_csv_with_timestamp_in_datetime_field(self):
        """Test parsing a CSV where the datetime column contains a timestamp."""
        data_generator = read_and_validate_csv(
            "tests/test_events/csv_timestamp_as_datetime.csv"
        )
        results = list(data_generator)

        expected_output_1 = {
            "datetime": "2024-08-12T15:03:14.349345+00:00",
            "uid": "mustermann",
            "tool": "exampletool",
            "message": "PageView",
            "event_type": "foobar",
            "organization_name": "example.my.org.com",
            "timestamp_desc": "<URL placeholder>",
            "unique_id": "DETAILED DATA",
            "timestamp": 1723474994349345,
        }

        expected_output_2 = {
            "datetime": "2025-06-30T19:50:29.117113+00:00",
            "uid": "jondoe",
            "tool": "exampletool",
            "message": "PageView",
            "event_type": "foobar",
            "organization_name": "example.my.org.com",
            "timestamp_desc": "<URL placeholder>",
            "unique_id": "DETAILED DATA",
            "timestamp": 1751313029117113,
        }

        self.assertEqual(len(results), 4)
        self.assertDictEqual(results[0], expected_output_1)
        self.assertDictEqual(results[1], expected_output_2)

    def test_csv_with_timestamp_and_no_datetime(self):
        """Test parsing a CSV with a timestamp column but no datetime."""
        data_generator = read_and_validate_csv(
            "tests/test_events/csv_timestamp_no_datetime.csv"
        )
        results = list(data_generator)

        self.assertEqual(len(results), 3)

        expected_output_1 = {
            "datetime": "2022-07-24T19:01:01+00:00",
            "message": "seconds_timestamp",
            "timestamp_desc": "test",
            "timestamp": 1658689261000000,
        }
        expected_output_2 = {
            "datetime": "2022-07-24T19:01:01.123000+00:00",
            "message": "milliseconds_timestamp",
            "timestamp_desc": "test",
            "timestamp": 1658689261123000,
        }
        expected_output_3 = {
            "datetime": "2022-07-24T19:01:01.123456+00:00",
            "message": "microseconds_timestamp",
            "timestamp_desc": "test",
            "timestamp": 1658689261123456,
        }

        self.assertDictEqual(results[0], expected_output_1)
        self.assertDictEqual(results[1], expected_output_2)
        self.assertDictEqual(results[2], expected_output_3)

    def test_csv_datetime_as_last_column(self):
        """Test parsing a CSV where datetime is the last column."""
        data_generator = read_and_validate_csv(
            "tests/test_events/csv_datetime_last_column.csv"
        )
        results = list(data_generator)

        self.assertEqual(len(results), 4)

        expected_output_1 = {
            "timestamp": 1532689087000000,
            "message": "193408 foobar true",
            "timestamp_desc": "Access Time",
            "datetime": "2018-07-27T10:58:07+00:00",
        }
        expected_output_2 = {
            "timestamp": 1532691305000000,
            "message": "193408 foobar true",
            "timestamp_desc": "Access Time",
            "datetime": "2018-07-27T11:35:05+00:00",
        }
        expected_output_3 = {
            "timestamp": 1532692593000000,
            "message": "193408 foobar true",
            "timestamp_desc": "Access Time",
            "datetime": "2018-07-27T11:56:33+00:00",
        }

        self.assertDictEqual(results[0], expected_output_1)
        self.assertDictEqual(results[1], expected_output_2)
        self.assertDictEqual(results[2], expected_output_3)

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

    def test_convert_timestamp_to_datetime(self):
        """Test the timestamp to datetime conversion helper."""
        # Test seconds
        ts_seconds = 1658689261
        dt_seconds = _convert_timestamp_to_datetime(ts_seconds)
        self.assertEqual(dt_seconds, pd.Timestamp("2022-07-24 19:01:01+00:00"))

        # Test milliseconds
        ts_milliseconds = 1658689261123
        dt_milliseconds = _convert_timestamp_to_datetime(ts_milliseconds)
        self.assertEqual(dt_milliseconds, pd.Timestamp("2022-07-24 19:01:01.123+00:00"))

        # Test microseconds
        ts_microseconds = 1658689261123456
        dt_microseconds = _convert_timestamp_to_datetime(ts_microseconds)
        self.assertEqual(
            dt_microseconds, pd.Timestamp("2022-07-24 19:01:01.123456+00:00")
        )

        # Test nanoseconds
        ts_nanoseconds = 1658689261123456789
        dt_nanoseconds = _convert_timestamp_to_datetime(ts_nanoseconds)
        self.assertEqual(
            dt_nanoseconds, pd.Timestamp("2022-07-24 19:01:01.123456789+00:00")
        )

        # Test NaN
        dt_nan = _convert_timestamp_to_datetime(float("nan"))
        self.assertTrue(pd.isna(dt_nan))
