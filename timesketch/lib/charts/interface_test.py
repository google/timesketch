# Copyright 2026 Google Inc. All rights reserved.
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
"""Tests for chart interface."""

import unittest
from unittest import mock
import pandas as pd

from timesketch.lib.charts import interface


class TestBaseChart(unittest.TestCase):
    """Tests for BaseChart."""

    def test_get_chart_with_transform_converts_to_dict(self):
        """Test that _get_chart_with_transform converts DataFrame to dict."""
        data = {
            "values": pd.DataFrame([{"a": 1, "b": 2}]),
            "encoding": {"x": "a", "y": "b"},
        }
        chart = interface.BaseChart(data)

        # We want to verify that alt.Chart is called with a list of dicts,
        # not a DataFrame.
        with mock.patch("timesketch.lib.charts.interface.alt.Chart") as mock_chart:
            # pylint: disable=protected-access
            chart._get_chart_with_transform()

            # Get the argument passed to alt.Chart
            args, _ = mock_chart.call_args
            passed_data = args[0]

            # Assert it is a list (result of to_dict)
            self.assertIsInstance(passed_data, list)
            self.assertEqual(passed_data, [{"a": 1, "b": 2}])

    def test_get_chart_with_transform_invalid_data(self):
        """Test that _get_chart_with_transform handles invalid data gracefully."""
        # Setup mock data where values is not a DataFrame or list
        # Since init forces DataFrame, we have to mock self.values
        # on the instance.

        data = {"values": pd.DataFrame(), "encoding": {"x": "a", "y": "b"}}
        chart = interface.BaseChart(data)

        # Override values with invalid type
        chart.values = "invalid_string"

        with mock.patch("timesketch.lib.charts.interface.logger") as mock_logger:
            with mock.patch("timesketch.lib.charts.interface.alt.Chart") as mock_chart:
                # pylint: disable=protected-access
                chart._get_chart_with_transform()

                # Check error logged
                mock_logger.error.assert_called()

                # Check alt.Chart called with empty list
                args, _ = mock_chart.call_args
                self.assertEqual(args[0], [])
