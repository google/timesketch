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
"""Bucket aggregations."""

from timesketch.lib.aggregators import manager
from timesketch.lib.aggregators import interface


class TermsAggregation(interface.BaseAggregator):
    """Terms Bucket Aggregation."""

    NAME = "field_bucket"
    DISPLAY_NAME = "Terms Aggregation"
    DESCRIPTION = "Aggregating values of a particular field"

    SUPPORTED_CHARTS = frozenset(
        ["barchart", "circlechart", "hbarchart", "linechart", "table"]
    )

    FORM_FIELDS = [
        {
            "type": "ts-dynamic-form-select-input",
            "name": "supported_charts",
            "label": "Chart type to render",
            "options": list(SUPPORTED_CHARTS),
            "display": True,
        },
        {
            "type": "ts-dynamic-form-text-input",
            "name": "field",
            "label": "What field to aggregate on",
            "placeholder": "Enter a field to aggregate",
            "default_value": "",
            "display": True,
        },
        {
            "type": "ts-dynamic-form-datetime-input",
            "name": "start_time",
            "label": (
                "ISO formatted timestamp for the start time " "of the aggregated data"
            ),
            "placeholder": "Enter a start date for the aggregation",
            "default_value": "",
            "display": True,
        },
        {
            "type": "ts-dynamic-form-datetime-input",
            "name": "end_time",
            "label": "ISO formatted end time for the aggregation",
            "placeholder": "Enter an end date for the aggregation",
            "default_value": "",
            "display": True,
        },
        {
            "type": "ts-dynamic-form-text-input",
            "name": "limit",
            "label": "Number of results to return",
            "placeholder": "Enter number of results to return",
            "default_value": "10",
            "display": True,
        },
    ]

    @property
    def chart_title(self):
        """Returns a title for the chart."""
        if self.field:
            return f'Top results for "{self.field:s}"'
        return "Top results for an unknown field"

    # pylint: disable=arguments-differ
    def run(
        self,
        field,
        limit=10,
        supported_charts="table",
        start_time="",
        end_time="",
        order_field="count",
    ):
        """Run the aggregation.

        Args:
            field: What field to aggregate on.
            limit: How many buckets to return.
            supported_charts: Chart type to render. Defaults to table.
            start_time: Optional ISO formatted date string that limits the time
                range for the aggregation.
            end_time: Optional ISO formatted date string that limits the time
                range for the aggregation.
            order_field: The name of the field that is used for the order
                of items in the aggregation, defaults to "count".

        Returns:
            Instance of interface.AggregationResult with aggregation result.
        """
        self.field = field
        formatted_field_name = self.format_field_by_type(field)

        # Encoding information for Vega-Lite.
        encoding = {
            "x": {
                "field": field,
                "type": "nominal",
                "sort": {"op": "sum", "field": order_field, "order": "descending"},
            },
            "y": {"field": "count", "type": "quantitative"},
            "tooltip": [
                {"field": field, "type": "nominal"},
                {"field": order_field, "type": "quantitative"},
            ],
        }

        aggregation_spec = {
            "aggs": {
                "aggregation": {"terms": {"field": formatted_field_name, "size": limit}}
            }
        }

        aggregation_spec = self._add_query_to_aggregation_spec(
            aggregation_spec, start_time, end_time
        )

        response = self.opensearch_aggregation(aggregation_spec)
        aggregations = response.get("aggregations", {})
        aggregation = aggregations.get("aggregation", {})

        buckets = aggregation.get("buckets", [])
        values = []
        for bucket in buckets:
            d = {field: bucket["key"], "count": bucket["doc_count"]}
            values.append(d)

        return interface.AggregationResult(
            encoding=encoding,
            values=values,
            chart_type=supported_charts,
            sketch_url=self._sketch_url,
            field=field,
        )


manager.AggregatorManager.register_aggregator(TermsAggregation)
