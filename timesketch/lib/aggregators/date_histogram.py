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
"""Date Histogram aggregations."""
from __future__ import unicode_literals

import copy
from datetime import datetime

from timesketch.lib.aggregators import interface
from timesketch.lib.aggregators import manager


class DateHistogramAggregation(interface.BaseAggregator):
    """Date Histogram Aggregation.

    This aggregator uses "date_histogram" which is a type of OpenSearch
    aggregation that buckets documents (i.e. events in Timesketch) into
    time-based intervals.
    """

    NAME = "date_histogram"
    DISPLAY_NAME = "Date Histogram Aggregation"
    DESCRIPTION = "Aggregates values of a field into a time interval bucket."

    SUPPORTED_CHARTS = frozenset(["heatmap", "date_histogram", "table"])

    SUPPORTED_INTERVALS = frozenset(["year", "month", "day", "day_of_week", "hour"])

    FORM_FIELDS = [
        {
            "type": "ts-dynamic-form-select-input",
            "name": "supported_charts",
            "label": "Chart type to render",
            "options": list(SUPPORTED_CHARTS),
            "display": True,
        },
        {
            "type": "ts-dynamic-form-select-input",
            "name": "supported_intervals",
            "label": "Time interval",
            "options": list(SUPPORTED_INTERVALS),
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
            "type": "ts-dynamic-form-text-input",
            "name": "field_query_string",
            "label": "The filter query to narrow down the result set",
            "placeholder": "Query",
            "default_value": "*",
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
    ]

    _BASE_VEGA_ENCODING = {
        "x": {"field": "", "type": "ordinal"},
        "y": {"field": "", "type": "ordinal"},
        "color": {
            "field": "count",
            "type": "quantitative",
            "scale": {"scheme": "blues"},
        },
        "tooltip": [
            {"field": "", "type": "ordinal"},
            {"field": "count", "type": "quantitative"},
        ],
    }

    _QUERY_TEMPLATE = {
        "query": {"bool": {"must": []}},
        "aggs": {
            "aggregation": {
                "date_histogram": {
                    "field": "datetime",
                    # "interval": "TODO"
                }
            }
        },
    }

    @property
    def chart_title(self):
        """Returns a title for the chart."""
        if self.field:
            return f"Date History Aggregation for {self.field}"
        return "Date History Aggregation"

    def _get_heatmap_encoding(self):
        """Returns the heatmap Vega-Lite spec encoding."""
        encoding = copy.deepcopy(self._BASE_VEGA_ENCODING)

        if self.interval == "month":
            encoding["x"]["field"] = "year"
            encoding["x"]["title"] = "Year"
            encoding["y"]["field"] = "month"
            encoding["y"]["title"] = "month"
            encoding["tooltip"][0]["field"] = "month"
            encoding["tooltip"][0]["title"] = "Month"
        elif self.interval == "day":
            encoding["x"]["timeUnit"] = "utcyearmonth"
            encoding["x"]["title"] = "Year"
            encoding["y"]["timeUnit"] = "date"
            encoding["y"]["title"] = "Day of Month"
            encoding["tooltip"][0]["timeUnit"] = "utcyearmonthdate"
            encoding["tooltip"][0]["title"] = "Date"
        elif self.interval == "hour":
            encoding["x"]["timeUnit"] = "utcyearmonthdate"
            encoding["x"]["title"] = "Date"
            encoding["y"]["timeUnit"] = "hours"
            encoding["y"]["title"] = "Hour"
            encoding["tooltip"][0]["timeUnit"] = "utcyearmonthdatehours"
            encoding["tooltip"][0]["title"] = "Hour"

        return encoding

    def _get_date_histogram_encoding(self):
        """Returns the hisogram Vega-Lite spec encoding."""
        encoding = copy.deepcopy(self._BASE_VEGA_ENCODING)
        # TODO: update encoding
        return encoding

    def _get_table_encoding(self):
        """Returns the table Vega-Lite spec encoding."""
        encoding = copy.deepcopy(self._BASE_VEGA_ENCODING)
        # TODO: update encoding
        return encoding

    def _get_vega_encoding(self, supported_charts):
        """Returns the Vega-Lite spec encoding."""
        if supported_charts == "heatmap":
            return self._get_heatmap_encoding()
        if supported_charts == "histogram":
            return self._get_date_histogram_encoding()
        if supported_charts == "table":
            return self._get_table_encoding()
        return None

    def _get_histogram_aggregation_spec(self, start_time, end_time):
        """Returns the aggregation specification."""
        formatted_field_name = self.format_field_by_type(self.field)
        if self.field_query_string == "*":
            formatted_field_query_string = self.field_query_string
        else:
            formatted_field_query_string = f'"{self.field_query_string}"'
        query = f"{formatted_field_name}:{formatted_field_query_string}"
        aggregation_spec = copy.deepcopy(self._QUERY_TEMPLATE)
        aggregation_spec["query"]["bool"]["must"].append(
            {"query_string": {"query": query}}
        )
        aggregation_spec["aggs"]["aggregation"]["date_histogram"][
            "interval"
        ] = self.interval
        aggregation_spec["aggs"]["aggregation"]["date_histogram"]["missing"] = 0
        aggregation_spec["aggs"]["aggregation"]["date_histogram"]["min_doc_count"] = 0
        aggregation_spec["aggs"]["aggregation"]["date_histogram"]["extended_bounds"] = {
            "min": start_time,
            "max": end_time,
        }

        aggregation_spec["aggs"]["datetime_cardinality"] = {
            "cardinality": {"field": "datetime"}
        }

        aggregation_spec["aggs"]["datetime_min"] = {"min": {"field": "datetime"}}
        aggregation_spec["aggs"]["datetime_max"] = {"max": {"field": "datetime"}}
        aggregation_spec["aggs"]["value_cardinality"] = {
            "cardinality": {"field": formatted_field_name}
        }
        aggregation_spec["aggs"]["value_count"] = {
            "value_count": {"field": formatted_field_name}
        }
        aggregation_spec = self._add_query_to_aggregation_spec(
            aggregation_spec, start_time, end_time
        )

        return aggregation_spec

    # pylint: disable=arguments-differ
    def run(
        self,
        field,
        field_query_string="*",
        supported_intervals="day",
        supported_charts="heatmap",
        start_time="",
        end_time="",
    ):
        """Runs the date_histogram aggregator.

        Args:
            field: What field to aggregate on.
            field_query_string: The field value(s) to aggregate on.
            supported_charts: The chart type to render.  Defaults to table.
            start_time: Optional ISO formatted date string that limits the time range
                for the aggregation.
            end_time: Optional ISO formatted date string that limits the time range
                for the aggregation.

        Returns:
            interface.AggregationResult: the aggreation result.
        """
        if not field or not field_query_string:
            raise ValueError("Missing field and/or field_query_string.")

        self.field = field
        # pylint: disable=attribute-defined-outside-init
        self.field_query_string = field_query_string
        self.interval = supported_intervals
        # pylint: enable=attribute-defined-outside-init

        encoding = self._get_vega_encoding(supported_charts)

        histogram_aggregation_spec = self._get_histogram_aggregation_spec(
            start_time, end_time
        )

        response = self.opensearch_aggregation(histogram_aggregation_spec)
        aggregations = response.get("aggregations", {})
        aggregation = aggregations.get("aggregation", {})
        buckets = aggregation.get("buckets", [])

        values = []
        for bucket in buckets:
            dt = datetime.utcfromtimestamp(bucket["key"] / 1000)

            value = {
                "timestamp": bucket["key"],
                "datetime": bucket["key_as_string"],
                "count": bucket["doc_count"],
                "year": dt.year,
            }

            if self.interval in ("month", "day", "day_of_week", "hour"):
                value["month"] = dt.month

                if self.interval in ("day", "day_of_week", "hour"):
                    value["day"] = dt.day
                    value["dow"] = dt.weekday()

                    if self.interval == ("hour"):
                        value["hour"] = dt.hour
            values.append(value)

        return interface.AggregationResult(
            encoding=encoding,
            values=[values],
            chart_type=supported_charts,
            sketch_url=self._sketch_url,
            field=field,
        )


manager.AggregatorManager.register_aggregator(DateHistogramAggregation)
