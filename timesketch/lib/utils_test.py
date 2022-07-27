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

TEST_CSV = "test_tools/test_events/sigma_events.csv"
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
        """Test for wrong header mapping dictionary"""
        file_name = "/tmp/unit_test_file.csv"
        df = pd.DataFrame({
            'DT': ['test'],
            'message': ['test'],
            'TD': ['test']
        })
        df.to_csv(file_name, index=False)
        mandatory_fields = ["message", "datetime", "timestamp_desc"]

        wrong_header_1 = {
            "datetime": ["DT", ""],
            "timestamp_desc": ["No.", ""],
            "message": ["Source", ""]
        }
        # column message already exists

        with self.assertRaises(RuntimeError):
            next(read_and_validate_csv(
                file_name,
                ",",
                mandatory_fields,
                wrong_header_1
            ))

        wrong_header_2 = {
            "datetime": ["DT", ""],
            "timestamp_desc": ["No Existing Column", ""]
        }
        # Mandatory header points to non existing column

        with self.assertRaises(RuntimeError):
            next(read_and_validate_csv(
                file_name,
                ",",
                mandatory_fields,
                wrong_header_2
            ))

        wrong_header_3 = {
            "datetime": ["DT", ""],
            "timestamp_desc": ["DT", ""],
        }
        # 2 mandatory headers point to the same existing one

        with self.assertRaises(RuntimeError):
            next(read_and_validate_csv(
                file_name,
                ",",
                mandatory_fields,
                wrong_header_3
            ))

    def test_right_headers_mapping(self):
        """Test for correct header mapping dictionary"""
        file_name = "/tmp/unit_test_file.csv"
        df = pd.DataFrame({
            'DT': ['test'],
            'message': ['test'],
            'TD': ['test']
        })
        df.to_csv(file_name, index=False)
        mandatory_fields = ["message", "datetime", "timestamp_desc"]

        right_header_1 = {
            "datetime": ["DT", ""],
            "timestamp_desc": ["No.", ""],
        }
        res = read_and_validate_csv(
            TEST_CSV, ",", mandatory_fields, right_header_1)
        self.assertIsNot(res, None)

        right_header_2 = {
            "datetime": ["DT", ""],
            "timestamp_desc": ["New header", "foo"],
        }
        res = read_and_validate_csv(
            TEST_CSV, ",", mandatory_fields, right_header_2)
        self.assertIsNot(res, None)

    def test_wrong_CSV_file(self):
        """Test for CSV with missing mandatory headers without mapping"""
        file_name = "/tmp/unit_test_file.csv"
        mandatory_fields = ["message", "datetime", "timestamp_desc"]

        df = pd.DataFrame({
            'DT': ['test'],
            'MSG': ['test'],
            'TD': ['test']
        })

        df.to_csv(file_name, index=False)

        with self.assertRaises(RuntimeError):
            # Call next to work around lazy generators.
            next(read_and_validate_csv(file_name, ",", mandatory_fields))

        df = pd.DataFrame({
            'datetime': ['test'],
            'MSG': ['test'],
            'TD': ['test']
        })

        df.to_csv(file_name, index=False)
        with self.assertRaises(RuntimeError):
            # Call next to work around lazy generators.
            next(read_and_validate_csv(file_name, ",", mandatory_fields))

    def test_mapped_CSV_file(self):
        """Test for CSV with missing mandatory headers but correct mapping"""
        file_name = "/tmp/unit_test_file.csv"
        mandatory_fields = ["message", "datetime", "timestamp_desc"]

        df = pd.DataFrame({
            'DT': ['test'],
            'MSG': ['test'],
            'TD': ['test']
        })
        df.to_csv(file_name, index=False)
        headers_mapping = {
            "datetime": ["DT", ""],
            "timestamp_desc": ["TD", ""],
            "message": ["MSG", ""]
        }
        res = read_and_validate_csv(
            file_name, ",", mandatory_fields, headers_mapping)
        self.assertIsNot(res, None)

        df = pd.DataFrame({
            'datetime': ['test'],
            'MSG': ['test'],
            'TD': ['test']
        })
        df.to_csv(file_name, index=False)
        headers_mapping = {
            "timestamp_desc": ["TD", ""],
            "message": ["MSG", ""]
        }
        res = read_and_validate_csv(
            file_name, ",", mandatory_fields, headers_mapping)
        self.assertIsNot(res, None)

        df = pd.DataFrame({
            'datetime': ['test'],
            'message': ['test'],
            'timestamp_desc': ['test']
        })
        df.to_csv(file_name, index=False)
        headers_mapping = {}
        res = read_and_validate_csv(
            file_name, ",", mandatory_fields, headers_mapping)
        self.assertIsNot(res, None)
