# Copyright 2023 Google Inc. All rights reserved.
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
"""Tests for the Timesketch API aggregation object."""
import unittest
import mock

import altair as alt

from . import aggregation
from . import client
from . import test_lib


class AggregationTest(unittest.TestCase):
    """Test Graph object."""

    @mock.patch("requests.Session", test_lib.mock_session)
    def setUp(self):
        """Setup test case."""
        self.api_client = client.TimesketchApi("http://127.0.0.1", "test", "test")
        self.sketch = self.api_client.get_sketch(1)

    # pylint: disable=protected-access
    def test_init(self):
        """Tests the Aggregation init method."""
        aggregation_obj = aggregation.Aggregation(self.sketch)

        # Aggregation attributes
        self.assertEqual(aggregation_obj._created_at, "")
        self.assertEqual(aggregation_obj._group_id, None)
        self.assertEqual(aggregation_obj._parameters, {})
        self.assertEqual(aggregation_obj._updated_at, "")
        self.assertEqual(aggregation_obj._aggregator_name, "")
        self.assertEqual(aggregation_obj.chart_color, "")
        self.assertEqual(aggregation_obj.chart_title, "")
        self.assertEqual(aggregation_obj.search_id, None)
        self.assertEqual(aggregation_obj.type, None)

        # SketchResource attributes
        self.assertEqual(aggregation_obj._labels, [])
        self.assertEqual(aggregation_obj._resource_id, 0)
        self.assertEqual(aggregation_obj._sketch, self.sketch)
        self.assertEqual(aggregation_obj._username, "")

        # BaseResource attributes
        self.assertEqual(aggregation_obj.api, self.api_client)
        self.assertEqual(
            aggregation_obj.resource_uri, "sketches/1/aggregation/explore/"
        )
        self.assertEqual(aggregation_obj.resource_data, None)

    def test_created_at(self):
        """Tests the created_at property."""
        aggregation_obj = aggregation.Aggregation(self.sketch)
        self.assertEqual(aggregation_obj.created_at, "")

        aggregation_obj.from_saved(1)
        self.assertEqual(aggregation_obj.created_at, "2023-01-08T08:45:23.113454")

    def test_parameters(self):
        """Tests the parameters property."""
        aggregation_obj = aggregation.Aggregation(self.sketch)
        self.assertEqual(aggregation_obj.parameters, {})

        aggregation_obj.from_saved(1)
        self.assertEqual(
            aggregation_obj.parameters,
            {
                "supported_charts": "barchart",
                "field": "ip",
                "start_time": "",
                "end_time": "",
                "limit": "10",
                "index": [1, 2],
            },
        )

    def test_is_part_of_group(self):
        """Tests the is_part_of_group property."""
        aggregation_obj = aggregation.Aggregation(self.sketch)
        self.assertEqual(aggregation_obj.is_part_of_group, False)

        aggregation_obj.from_saved(1)
        self.assertEqual(aggregation_obj.is_part_of_group, False)

    def test_title(self):
        """Tests the title property."""
        aggregation_obj = aggregation.Aggregation(self.sketch)
        self.assertEqual(aggregation_obj.title, "")

        aggregation_obj.from_saved(1)
        self.assertEqual(aggregation_obj.title, "Top results for an unknown field")

    def test_title_setter(self):
        """Tests the title setter."""
        aggregation_obj = aggregation.Aggregation(self.sketch)
        aggregation_obj.title = "new title"
        self.assertEqual(aggregation_obj.title, "new title")

    def test_chart(self):
        """Tests the chart property."""
        aggregation_obj = aggregation.Aggregation(self.sketch)
        with self.assertRaises(TypeError) as err:
            _ = aggregation_obj.chart
        self.assertEqual(
            str(err.exception), "Unable to generate chart, missing a chart type."
        )

        aggregation_obj.from_saved(1)
        chart = aggregation_obj.chart
        self.assertIsInstance(chart, alt.Chart)

    def test_description(self):
        """Tests the description property."""
        aggregation_obj = aggregation.Aggregation(self.sketch)
        self.assertEqual(aggregation_obj.description, "")

        aggregation_obj.from_saved(1)
        self.assertEqual(
            aggregation_obj.description, "Aggregating values of a particular field"
        )

    def test_description_setter(self):
        """Tests the description property setter."""

    def test_name(self):
        """Tests the name property."""
        aggregation_obj = aggregation.Aggregation(self.sketch)
        self.assertEqual(aggregation_obj.name, "")

        aggregation_obj.from_saved(1)
        self.assertEqual(aggregation_obj.name, "ip barchart")

    def test_aggregator_name(self):
        """Tests the aggregator_name property."""
        aggregation_obj = aggregation.Aggregation(self.sketch)
        self.assertEqual(aggregation_obj.name, "")

        aggregation_obj.from_saved(1)
        self.assertEqual(aggregation_obj.name, "ip barchart")

    def test_add_label(self):
        """Test the add_label function."""

    def test_from_saved(self):
        """Tests the from_saved method."""
        aggregation_obj = aggregation.Aggregation(self.sketch)
        aggregation_obj.from_saved(2)
        self.assertEqual(aggregation_obj._aggregator_name, "field_bucket")
        self.assertEqual(aggregation_obj.chart_color, "")
        self.assertEqual(aggregation_obj.chart_type, "table")
        self.assertEqual(aggregation_obj.chart_title, "")
        self.assertEqual(aggregation_obj.search_id, None)
        self.assertEqual(aggregation_obj.type, "stored")

        self.assertEqual(aggregation_obj.created_at, "2023-01-08T08:46:24.871292")
        self.assertEqual(
            aggregation_obj.parameters,
            {
                "supported_charts": "table",
                "field": "domain",
                "start_time": "",
                "end_time": "",
                "limit": "10",
                "index": [1, 2],
            },
        )
        self.assertEqual(aggregation_obj.is_part_of_group, False)
        self.assertEqual(aggregation_obj.title, "Top results for an unknown field")
        self.assertEqual(
            aggregation_obj.description, "Aggregating values of a particular field"
        )
        self.assertEqual(aggregation_obj.name, "domain table")
