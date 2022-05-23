# Copyright 2020 Google Inc. All rights reserved.
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
"""Feed aggregation.

This file provides a manual feed aggregator. This is useful for analyzers
that have already done the aggregation inside the analyzer, as part of the
analysis work they do. Instead of adding attributes to all events or
redo the aggregation each time the analyzer can simply store the aggregation
results as part of the parameters to the manual aggregator. That way the
aggregation can be used to generate charts and tables in stories and stored
insights. This analyzer is not useful for UI and therefore is "hidden" from
views.
"""

from __future__ import unicode_literals

from timesketch.lib.aggregators import manager
from timesketch.lib.aggregators import interface


class ManualFeedAggregation(interface.BaseAggregator):
    """Manual Feed Aggregation."""

    NAME = "manual_feed"
    DISPLAY_NAME = "Manual Feed Aggregation"
    DESCRIPTION = "Aggregating values of a user supplied data"

    SUPPORTED_CHARTS = frozenset(["barchart", "circlechart", "hbarchart", "table"])

    # No Form fields since this is not meant to be used in the UI.
    FORM_FIELDS = []

    def __init__(self, sketch_id=None, indices=None, timeline_ids=None):
        """Initialize the aggregator object.

        Args:
            sketch_id: Sketch ID.
            indices: Optional list of OpenSearch index names. If not provided
                the default behavior is to include all the indices in a sketch.
            timeline_ids: Optional list of timeline IDs, if not provided the
                default behavior is to query all the data in the provided
                search indices.
        """
        super().__init__(
            sketch_id=sketch_id, indices=indices, timeline_ids=timeline_ids
        )
        self.title = ""

    @property
    def chart_title(self):
        """Returns a title for the chart."""
        if self.title:
            return self.title
        return "Results From A Manually Fed Table"

    # pylint: disable=arguments-differ
    def run(
        self, data, title="", supported_charts="table", field=None, order_field="count"
    ):
        """Run the aggregation.

        Args:
            data: list of dict objects, each entry in the list is a
                dictionary, representing a single entry in the aggregation.
            title: string with the aggregation title.
            supported_charts: Chart type to render. Defaults to table.
            field: What field to aggregate on.
            order_field: The name of the field that is used for the order
                of items in the aggregation, defaults to "count".

        Returns:
            Instance of interface.AggregationResult with aggregation result.

        Raises:
            ValueError: data is not supplied.
        """
        if not data:
            raise ValueError("Data is missing")

        self.title = title

        if not field:
            keys = set()
            for row in data:
                list(map(keys.add, row.keys()))
            keys.discard("count")
            keys.discard("bucket_name")
            if keys:
                field = list(keys)[0]
            else:
                field = "count"

        # Encoding information for Vega-Lite.
        encoding = {
            "x": {
                "field": field,
                "type": "nominal",
                "sort": {"op": "sum", "field": order_field, "order": "descending"},
            },
            "y": {"field": "count", "type": "quantitative"},
        }

        return interface.AggregationResult(
            encoding=encoding, values=data, chart_type=supported_charts
        )


manager.AggregatorManager.register_aggregator(
    ManualFeedAggregation, exclude_from_list=True
)
