# Copyright 2021 Google Inc. All rights reserved.
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
"""End to end tests of Timesketch aggregation functionality."""

from timesketch_api_client import aggregation

from . import interface
from . import manager


class AggregationTest(interface.BaseEndToEndTest):
    """End to end tests for aggregation functionality."""

    NAME = "aggregation_test"

    def setup(self):
        """Import test timeline."""
        self.import_timeline("evtx.plaso")
        self.import_timeline("evtx_part.csv")

    def test_entire_set(self):
        """Test aggregating over the entire data set in the sketch."""
        agg_obj = aggregation.Aggregation(self.sketch)
        parameters = {
            "supported_charts": "table",
            "field": "computer_name",
            "limit": 5,
        }
        agg_obj.from_aggregator_run("field_bucket", parameters)
        df = agg_obj.table

        self.assertions.assertEqual(df.shape, (1, 3))

        computer_names = list(df.computer_name.values)
        self.assertions.assertEqual(len(computer_names), 1)
        self.assertions.assertEqual(
            computer_names[0], "WKS-WIN764BITB.shieldbase.local"
        )
        count = list(df["count"].values)[0]
        self.assertions.assertEqual(count, 3215)

    def test_partial_set(self):
        """Test partial aggregation sets."""
        timelines = {t.name: t.id for t in self.sketch.list_timelines()}
        evtx_part_id = timelines.get("evtx_part", "evtx_part")
        self.assertions.assertEqual(len(timelines.values()), 2)

        partial_agg = aggregation.Aggregation(self.sketch)
        partial_parameters = {
            "supported_charts": "table",
            "field": "computer_name",
            "index": [evtx_part_id],
            "limit": 5,
        }
        partial_agg.from_aggregator_run("field_bucket", partial_parameters)

        df = partial_agg.table
        self.assertions.assertEqual(df.shape, (1, 3))

        computer_names = list(df.computer_name.values)
        self.assertions.assertEqual(len(computer_names), 1)
        self.assertions.assertEqual(
            computer_names[0], "WKS-WIN764BITB.shieldbase.local"
        )
        count = list(df["count"].values)[0]
        self.assertions.assertEqual(count, 13)

        agg_obj = aggregation.Aggregation(self.sketch)
        parameters = {
            "supported_charts": "table",
            "field": "computer_name",
            "index": ["evtx"],
            "limit": 5,
        }
        agg_obj.from_aggregator_run("field_bucket", parameters)
        df = agg_obj.table

        self.assertions.assertEqual(df.shape, (1, 3))

        computer_names = list(df.computer_name.values)
        self.assertions.assertEqual(len(computer_names), 1)
        self.assertions.assertEqual(
            computer_names[0], "WKS-WIN764BITB.shieldbase.local"
        )
        count = list(df["count"].values)[0]
        self.assertions.assertEqual(count, 3202)


manager.EndToEndTestManager.register_test(AggregationTest)
