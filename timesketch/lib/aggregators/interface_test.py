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
"""Tests for aggregator interface."""

import unittest
from unittest import mock

from timesketch.lib.aggregators import interface
from timesketch.lib.charts import interface as chart_interface


class MockChart(chart_interface.BaseChart):
    """Mock chart class."""

    NAME = "mockchart"

    def generate(self):
        return mock.Mock(
            to_dict=lambda: {"chart": "data"}, to_html=lambda: "<html></html>"
        )


class TestAggregationResult(unittest.TestCase):
    """Tests for AggregationResult."""

    def setUp(self):
        self.values = [{"field": "foo", "count": 10}, {"field": "bar", "count": 20}]
        self.encoding = {
            "x": {"field": "field", "type": "nominal"},
            "y": {"field": "count", "type": "quantitative"},
        }
        self.result = interface.AggregationResult(
            encoding=self.encoding, values=self.values
        )

    @mock.patch("timesketch.lib.charts.manager.ChartManager.get_chart")
    def test_to_chart_valid(self, mock_get_chart):
        """Test to_chart with valid data."""
        mock_get_chart.return_value = MockChart

        # Call to_chart
        result = self.result.to_chart(chart_name="mockchart")

        # Assert chart was generated and returned as dict by default
        self.assertEqual(result, {"chart": "data"})

    @mock.patch("timesketch.lib.aggregators.interface.logger")
    @mock.patch("timesketch.lib.charts.manager.ChartManager.get_chart")
    def test_to_chart_missing_encoding(self, mock_get_chart, mock_logger):
        """Test to_chart with missing encoding (should skip generation)."""
        mock_get_chart.return_value = MockChart

        # Result without encoding
        result_obj = interface.AggregationResult(encoding=None, values=self.values)

        result = result_obj.to_chart(chart_name="mockchart")

        # Should return empty dict
        self.assertEqual(result, {})

        # Verify logger.warning was called
        mock_logger.warning.assert_called_with(
            "No encoding found for chart [%s] with title [%s]. "
            "Skipping chart generation.",
            "mockchart",
            "",
        )

    @mock.patch("timesketch.lib.aggregators.interface.logger")
    @mock.patch("timesketch.lib.charts.manager.ChartManager.get_chart")
    def test_to_chart_missing_values_and_encoding(self, mock_get_chart, mock_logger):
        """Test to_chart with missing values and encoding."""
        mock_get_chart.return_value = MockChart

        # Result with empty values and no encoding
        result_obj = interface.AggregationResult(encoding=None, values=[])

        result = result_obj.to_chart(chart_name="mockchart")

        # Should return empty dict
        self.assertEqual(result, {})

        # Verify logger.warning was called
        mock_logger.warning.assert_called_with(
            "No encoding found for chart [%s] with title [%s]. "
            "Skipping chart generation.",
            "mockchart",
            "",
        )

    @mock.patch("timesketch.lib.aggregators.interface.logger")
    @mock.patch("timesketch.lib.charts.manager.ChartManager.get_chart")
    def test_to_chart_missing_encoding_unable_to_guess(
        self, mock_get_chart, mock_logger
    ):
        """Test to_chart when unable to guess encoding (e.g. 1 column)."""
        mock_get_chart.return_value = MockChart

        values = [{"field": "foo"}]  # Only 1 column
        result_obj = interface.AggregationResult(encoding=None, values=values)

        result = result_obj.to_chart(chart_name="mockchart")
        self.assertEqual(result, {})

        # Verify logger.warning was called
        mock_logger.warning.assert_called()


class TestBaseAggregator(unittest.TestCase):
    """Tests for BaseAggregator."""

    @mock.patch("timesketch.lib.aggregators.interface.OpenSearchDataStore")
    @mock.patch("timesketch.lib.aggregators.interface.SQLSketch")
    def test_init_no_sketch_id(self, _mock_sketch, _mock_ds):
        """Test initialization without sketch_id."""
        agg = interface.BaseAggregator(indices=["index1"])
        self.assertIsNone(agg.sketch)
        self.assertEqual(agg.indices, ["index1"])
        # pylint: disable=protected-access
        self.assertEqual(agg._sketch_url, "")

    @mock.patch("timesketch.lib.aggregators.interface.OpenSearchDataStore")
    @mock.patch("timesketch.lib.aggregators.interface.SQLSketch")
    def test_init_with_sketch_id(self, mock_sketch, _mock_ds):
        """Test initialization with sketch_id."""
        mock_sketch_obj = mock.Mock()
        mock_t1 = mock.Mock()
        mock_t1.searchindex.index_name = "index1"
        mock_t1.id = 1
        mock_sketch_obj.active_timelines = [mock_t1]
        mock_sketch.get_by_id.return_value = mock_sketch_obj

        agg = interface.BaseAggregator(sketch_id=1)
        self.assertEqual(agg.sketch, mock_sketch_obj)
        self.assertEqual(agg.indices, ["index1"])
        # pylint: disable=protected-access
        self.assertEqual(agg._sketch_url, "/sketch/1/explore")
