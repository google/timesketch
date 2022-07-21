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
    
    def test_wrong_headers_mapping(self):
        """Test for Timesketch header mapping validation"""
        mandatory_fields = ["message", "datetime", "timestamp_desc"]
        file_name = "test_tools/test_events/incorrect.csv"
        # incorrect is a file without datetime and timestamp_desc as mandatory headers
        all_wrong_headers_mapping = [
            {"datetime":["DT",""],"timestamp_desc":["No.",""], "message":["Source",""]},
            {"datetime":["DT",""],"timestamp_desc":["NotExisitingColumn",""]},
            {"datetime":["DT",""],"timestamp_desc":["DT",""]},
            {"datetime":["New header","foo"],"timestamp_desc":["New header",""]}
        ]
        for header_mapping in all_wrong_headers_mapping:
            with self.assertRaises(RuntimeError):
                next(read_and_validate_csv(TEST_CSV, ",", mandatory_fields, header_mapping))
    
    def test_right_headers_mapping(self):
        """Test for Timesketch header mapping validation"""
        mandatory_fields = ["message", "datetime", "timestamp_desc"]
        file_name = "test_tools/test_events/incorrect.csv"
        # incorrect is a file without datetime and timestamp_desc as mandatory headers
        all_good_headers_mapping = [
            {"datetime":["DT",""],"timestamp_desc":["No.",""]},
            {"datetime":["No.",""],"timestamp_desc":["DT",""]},
            {"datetime":["New header","foo"],"timestamp_desc":["New header","baz"]}
        ]
        for header_mapping in all_good_headers_mapping:
            res = read_and_validate_csv(TEST_CSV, ",", mandatory_fields, header_mapping)
            self.assertIsNot(res, None)

    def test_wrong_CSV_file(self):
        """Test for wrong CSV file with wrong or missing mandatory headers"""
        file_name = "/tmp/unittest_file.csv"
        dfS = [
                pd.DataFrame({'DT': ['test'],
                   'MSG': ['test'],
                   'TD': ['test']}),
                pd.DataFrame({'datetime': ['test'],
                   'MSG': ['test'],
                   'TD': ['test']}),
                pd.DataFrame({'datetime': ['test'],
                   'message': ['test'],
                   'TD': ['test']}),
                ]
        mandatory_fields = ["message", "datetime", "timestamp_desc"]
        for df in dfS:
            df.to_csv(file_name, index=False)
            with self.assertRaises(RuntimeError):
            # Call next to work around lazy generators.
                next(read_and_validate_csv(file_name, ",", mandatory_fields))

    def test_mapped_CSV_file(self):
        """Test for wrong CSV file with wrong or missing mandatory headers but with correct mapping"""
        file_name = "/tmp/unittest_file.csv"
        dfS = [
                (   pd.DataFrame({'DT': ['test'],
                    'MSG': ['test'],
                    'TD': ['test']})
                   ,
                    {"datetime":["DT",""],"timestamp_desc":["TD",""], "message":["MSG",""]}
                ),
                (   pd.DataFrame({'datetime': ['test'],
                    'MSG': ['test'],
                    'TD': ['test']})
                   ,
                    {"timestamp_desc":["TD",""], "message":["MSG",""]}
                ),
                (   pd.DataFrame({'datetime': ['test'],
                    'message': ['test'],
                    'TD': ['test']})
                   ,
                    {"timestamp_desc":["TD",""]}
                ),
                (
                    pd.DataFrame({'datetime': ['test'],
                    'message': ['test'],
                    'timestamp_desc': ['test']})
                   ,
                    {}
                )
            ]
        mandatory_fields = ["message", "datetime", "timestamp_desc"]
        for x in dfS:
            x[0].to_csv(file_name, index=False)
            headers_mapping = x[1]
            res = read_and_validate_csv(file_name, ",", mandatory_fields, headers_mapping)
            self.assertIsNot(res, None)
