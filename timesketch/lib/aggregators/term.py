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
"""Term aggregations."""

from __future__ import unicode_literals

from timesketch.lib.aggregators import manager
from timesketch.lib.aggregators import interface


def get_spec(field, limit=10, query="", query_dsl=""):
    """Returns aggregation specs for a term of filtered events.

    The aggregation spec will summarize values of an attribute
    whose events fall under a filter.

    Args:
        field (str): this denotes the event attribute that is used
            for aggregation.
        limit (int): How many buckets to return, defaults to 10.
        query (str): the query field to run on all documents prior to
            aggregating the results.
        query_dsl (str): the query DSL field to run on all documents prior
            to aggregating the results (optional). Either a query string
            or a query DSL has to be present.

    Raises:
        ValueError: if neither query_string or query_dsl is provided.

    Returns:
        a dict value that can be used as an aggregation spec.
    """
    if query:
        query_filter = {"bool": {"must": [{"query_string": {"query": query}}]}}
    elif query_dsl:
        query_filter = query_dsl
    else:
        raise ValueError("Neither query nor query DSL provided.")

    return {
        "query": query_filter,
        "aggs": {"aggregation": {"terms": {"field": field, "size": limit}}},
    }


class FilteredTermsAggregation(interface.BaseAggregator):
    """Query Filter Term Aggregation."""

    NAME = "query_bucket"
    DISPLAY_NAME = "Filtered Terms Aggregation"
    DESCRIPTION = "Aggregating values of a field after applying a filter"

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
            "name": "query_string",
            "type": "ts-dynamic-form-text-input",
            "label": "The filter query to narrow down the result set",
            "placeholder": "Query",
            "default_value": "",
            "display": True,
        },
        {
            "name": "query_dsl",
            "type": "ts-dynamic-form-text-input",
            "label": "The filter query DSL to narrow down the result",
            "placeholder": "Query DSL",
            "default_value": "",
            "display": False,
        },
        {
            "name": "field",
            "type": "ts-dynamic-form-text-input",
            "label": "What field to aggregate.",
            "display": True,
        },
        {
            "type": "ts-dynamic-form-datetime-input",
            "name": "start_time",
            "label": (
                "ISO formatted timestamp for the start time of the aggregated data"
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
            return 'Top filtered results for "{0:s}"'.format(self.field)
        return "Top results for an unknown field after filtering"

    # pylint: disable=arguments-differ
    def run(
        self,
        field,
        query_string="",
        query_dsl="",
        supported_charts="table",
        start_time="",
        end_time="",
        limit=10,
    ):
        """Run the aggregation.

        Args:
            field (str): this denotes the event attribute that is used
                for aggregation.
            query_string (str): the query field to run on all documents prior to
                aggregating the results.
            query_dsl (str): the query DSL field to run on all documents prior
                to aggregating the results. Either a query string or a query
                DSL has to be present.
            supported_charts: Chart type to render. Defaults to table.
            start_time: Optional ISO formatted date string that limits the time
                range for the aggregation.
            end_time: Optional ISO formatted date string that limits the time
                range for the aggregation.
            limit (int): How many buckets to return, defaults to 10.

        Returns:
            Instance of interface.AggregationResult with aggregation result.

        Raises:
            ValueError: if neither query_string or query_dsl is provided.
        """
        if not (query_string or query_dsl):
            raise ValueError("Both query_string and query_dsl are missing")

        self.field = field
        formatted_field_name = self.format_field_by_type(field)

        aggregation_spec = get_spec(
            field=formatted_field_name,
            limit=limit,
            query=query_string,
            query_dsl=query_dsl,
        )

        aggregation_spec = self._add_query_to_aggregation_spec(
            aggregation_spec, start_time=start_time, end_time=end_time
        )

        # Encoding information for Vega-Lite.
        encoding = {
            "x": {
                "field": field,
                "type": "nominal",
                "sort": {"op": "sum", "field": "count", "order": "descending"},
            },
            "y": {"field": "count", "type": "quantitative"},
            "tooltip": [
                {"field": field, "type": "nominal"},
                {"field": "count", "type": "quantitative"},
            ],
        }

        response = self.opensearch_aggregation(aggregation_spec)
        aggregations = response.get("aggregations", {})
        aggregation = aggregations.get("aggregation", {})

        buckets = aggregation.get("buckets", [])
        values = []
        for bucket in buckets:
            d = {field: bucket.get("key", "N/A"), "count": bucket.get("doc_count", 0)}
            values.append(d)

        if query_string:
            extra_query_url = "AND {0:s}".format(query_string)
        else:
            extra_query_url = ""

        return interface.AggregationResult(
            encoding=encoding,
            values=values,
            chart_type=supported_charts,
            sketch_url=self._sketch_url,
            field=field,
            extra_query_url=extra_query_url,
        )


manager.AggregatorManager.register_aggregator(FilteredTermsAggregation)
