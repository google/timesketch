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
"""Tests for aggregator manager."""

from __future__ import unicode_literals

from timesketch.lib.testlib import BaseTest
from timesketch.lib.aggregators import manager


class MockAggregator(object):
    """Mock aggregator class."""

    NAME = "MockAggregator"
    DESCRIPTION = "MockDescription"
    DISPLAY_NAME = "MockDisplayName"
    FORM_FIELDS = {}
    SUPPORTED_CHARTS = frozenset()


class MockAggregator2(object):
    """Mock aggregator class."""

    NAME = "MockAggregatorAgain"
    DESCRIPTION = "MockDescriptionForMocker"
    DISPLAY_NAME = "MockDisplayName"
    FORM_FIELDS = {}
    SUPPORTED_CHARTS = frozenset()


class TestAggregatorManager(BaseTest):
    """Tests for the functionality of the manager module."""

    manager.AggregatorManager.clear_registration()
    manager.AggregatorManager.register_aggregator(MockAggregator)

    def test_get_aggregators(self):
        """Test to get aggregator class objects."""
        aggregators = manager.AggregatorManager.get_aggregators()
        aggregator_list = list(aggregators)
        first_aggregator_tuple = aggregator_list[0]
        aggregator_name, aggregator_class = first_aggregator_tuple
        self.assertIsInstance(aggregator_list, list)
        self.assertIsInstance(first_aggregator_tuple, tuple)
        self.assertEqual(aggregator_class, MockAggregator)
        self.assertEqual(aggregator_name, "mockaggregator")

        # Register the second, but so that it does not appear in list.
        manager.AggregatorManager.register_aggregator(
            MockAggregator2, exclude_from_list=True
        )

        aggregators = manager.AggregatorManager.get_aggregators()
        aggregator_list = list(aggregators)
        self.assertEqual(len(aggregator_list), 1)

    def test_get_aggregator(self):
        """Test to get aggregator class from registry."""
        aggregator_class = manager.AggregatorManager.get_aggregator("mockaggregator")
        self.assertEqual(aggregator_class, MockAggregator)
        self.assertRaises(
            KeyError, manager.AggregatorManager.get_aggregator, "no_such_aggregator"
        )

    def test_register_aggregator(self):
        """Test so we raise KeyError when aggregator is already registered."""
        self.assertRaises(
            KeyError, manager.AggregatorManager.register_aggregator, MockAggregator
        )
