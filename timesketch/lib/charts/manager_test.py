# Copyright 2019 Google Inc. All rights reserved.
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
"""Tests for chart manager."""

from __future__ import unicode_literals

from timesketch.lib.testlib import BaseTest
from timesketch.lib.charts import manager


class MockChart(object):
    """Mock chart class."""

    NAME = "MockChart"


class TestChartManager(BaseTest):
    """Tests for the functionality of the manager module."""

    manager.ChartManager.clear_registration()
    manager.ChartManager.register_chart(MockChart)

    def test_get_charts(self):
        """Test to get chart class objects."""
        charts = manager.ChartManager.get_charts()
        chart_list = list(charts)
        first_chart_tuple = chart_list[0]
        chart_name, chart_class = first_chart_tuple
        self.assertIsInstance(chart_list, list)
        self.assertIsInstance(first_chart_tuple, tuple)
        self.assertEqual(chart_class, MockChart)
        self.assertEqual(chart_name, "mockchart")

    def test_get_chart(self):
        """Test to get chart class from registry."""
        chart_class = manager.ChartManager.get_chart("mockchart")
        self.assertEqual(chart_class, MockChart)
        self.assertRaises(KeyError, manager.ChartManager.get_chart, "no_such_chart")

    def test_register_chart(self):
        """Test so we raise KeyError when chart is already registered."""
        self.assertRaises(KeyError, manager.ChartManager.register_chart, MockChart)
