# Copyright 2015 Google Inc. All rights reserved.
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
"""Tests for aggregations."""

from timesketch.lib.aggregators import heatmap
from timesketch.lib.testlib import BaseTest
from timesketch.lib.testlib import MockDataStore


class TestAggregators(BaseTest):
    """Tests for the functionality of the aggregation module."""

    def test_heatmap(self):
        """Test to get heatmap data."""
        es_client = MockDataStore(u'127.0.0,1', 4711)
        h = heatmap(es_client, 1, u'test', {}, [], [u'all'])
        self.assertIsInstance(h, list)
