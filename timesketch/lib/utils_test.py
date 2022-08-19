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

    def test_invalid_CSV_headers_mapping(self):
        """Test for invalid headers mapping"""
        current_headers = ["DT", "message", "TD"]

        invalid_mapping_1 = [
            {"target": "datetime", "source": ["DT"], "default_value": None},
            {"target": "timestamp_desc", "source": ["No."], "default_value": None},
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
            {"target": "timestamp_desc", "source": ["DT"], "default_value": None},
        ]
        # 2 mandatory headers point to the same existing one
        with self.assertRaises(RuntimeError):
            # Call next to work around lazy generators.
            next(check_mapping_errors(current_headers, invalid_mapping_3))

    def test_valid_CSV_headers_mapping(self):
        """Test for valid headers mapping"""
        current_headers = ["DT", "message", "TD"]

        valid_mapping_1 = [
            {"target": "datetime", "source": ["DT"], "default_value": None},
            {"target": "timestamp_desc", "source": ["TD"], "default_value": None},
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
            {"target": "message", "source": ["TD", "file_path"], "default_value": None},
        ]
        self.assertIs(check_mapping_errors(current_headers, valid_mapping_3), None)

        current_headers = ["DT", "last_access", "TD", "file_path", "T_desc"]
        valid_mapping_4 = [
            {"target": "datetime", "source": ["DT"], "default_value": None},
            {"target": "timestamp_desc", "source": ["T_desc"], "default_value": None},
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


def test_valid_JSONL_headers_mapping(self):
    ...


def test_invalid_JSONL_headers_mapping(self):
    ...
