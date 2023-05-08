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
"""Summary aggregations.

This aggregator is primarily used for the event data analytics and not useful
for the UI.  Therefore,  by default this aggregator is "hidden" from views.
"""
from __future__ import unicode_literals

from timesketch.lib.aggregators import manager
from timesketch.lib.aggregators import interface


class SummaryAggregation(interface.BaseAggregator):
    """Summary Aggregations."""

    NAME = "field_summary"
    DISPLAY_NAME = "Field summary aggregations"
    DESCRIPTION = "Summary/descriptive statistics for a user supplied field."

    FORM_FIELDS = [
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
            "label": "ISO formatted start time of the aggregated data",
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
            "name": "most_common_limit",
            "label": "Number of most common values",
            "placeholder": "Enter maximum number of most common values to return",
            "default_value": "10",
            "display": True,
        },
        {
            "type": "ts-dynamic-form-text-input",
            "name": "rare_value_document_limit",
            "label": "Maximum document counts for rare values",
            "placeholder": "Enter upper bound of document count",
            "default_value": "5",
            "display": True,
        },
    ]

    @property
    def chart_title(self):
        """Returns a title for the chart."""
        if self.field:
            return 'Summary aggregations for "{0:s}"'.format(self.field)
        return "Summary aggregations for an unknown field."

    # pylint: disable=arguments-differ
    def run(
        self,
        field,
        field_query_string="*",
        start_time="",
        end_time="",
        most_common_limit=10,
        rare_value_document_limit=5,
    ):
        """Runs the SummaryAggregation aggregator.

        Args:
            field: What field to aggregate on.
            field_query_string: The field value(s) to aggregate on.
            supported_charts: The chart type to render.  Defaults to table.
            start_time: Optional ISO formatted date string that limits the time range
                for the aggregation.
            end_time: Optional ISO formatted date string that limits the time range
                for the aggregation.
            most_common_limit: Optional number of results to return for top terms.
            rare_value_document_limit: Optional document count upper bound for rare
                values.

        Returns:
            interface.AggregationResult: the aggreation result.
        """
        self.field = field
        # pylint: disable=attribute-defined-outside-init
        self.field_query_string = field_query_string
        # pylint: enable=attribute-defined-outside-init
        formatted_field_name = self.format_field_by_type(field)

        if field_query_string == "*":
            formatted_field_query_string = field_query_string
        else:
            formatted_field_query_string = f'"{field_query_string}"'

        query_string = f"{formatted_field_name}:{formatted_field_query_string}"
        aggregation_spec = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "query_string": {"query": query_string},
                        }
                    ]
                }
            },
            "aggs": {
                "datetime_percentiles": {"percentiles": {"field": "datetime"}},
                "datetime_min": {"min": {"field": "datetime"}},
                "datetime_max": {"max": {"field": "datetime"}},
                "value_cardinality": {"cardinality": {"field": formatted_field_name}},
                "value_count": {"value_count": {"field": formatted_field_name}},
                "all_values": {
                    "global": {},
                    "aggs": {
                        "datetime_min": {"min": {"field": "datetime"}},
                        "datetime_max": {"max": {"field": "datetime"}},
                        "field_cardinality": {
                            "cardinality": {"field": formatted_field_name}
                        },
                        "field_count": {"value_count": {"field": formatted_field_name}},
                        "top_terms": {
                            "terms": {
                                "field": formatted_field_name,
                                "size": most_common_limit,
                            }
                        },
                        "rare_terms": {
                            "rare_terms": {
                                "field": formatted_field_name,
                                "max_doc_count": rare_value_document_limit,
                            }
                        },
                    },
                },
            },
        }

        # TODO: break down aggregation into timelines
        self._add_query_to_aggregation_spec(aggregation_spec, start_time, end_time)
        response = self.opensearch_aggregation(aggregation_spec)
        aggregations = response.get("aggregations", {})
        return interface.AggregationResult(
            encoding=None,
            values=[aggregations],
            chart_type=None,
            sketch_url=self._sketch_url,
            field=field,
        )


class DateSummaryAggregator(interface.BaseAggregator):
    """Date-based Summary Aggregations."""

    NAME = "datefield_summary"
    DISPLAY_NAME = "Date field summary aggregations"
    DESCRIPTION = "Date field statistics for a user supplied field."

    FORM_FIELDS = [
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
            "label": "ISO formatted start time of the aggregated data",
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

    @property
    def chart_title(self):
        """Returns a title for the chart."""
        if self.field:
            return 'Date field summary aggregations for "{0:s}"'.format(self.field)
        return "Date field summary aggregations for an unknown field."

    # pylint: disable=arguments-differ
    def run(
        self,
        field,
        field_query_string="*",
        start_time="",
        end_time="",
        date_interval="year",
    ):
        """Runs the SummaryAggregation aggregator.

        Args:
            field: What field to aggregate on.
            field_query_string: The field value(s) to aggregate on.
            supported_charts: The chart type to render.  Defaults to table.
            start_time: Optional ISO formatted date string that limits the time range
                for the aggregation.
            end_time: Optional ISO formatted date string that limits the time range
                for the aggregation.
            date_interval: Optional interval for the date histogram
                aggregation.

        Returns:
            interface.AggregationResult: the aggreation result.
        """
        self.field = field
        # pylint: disable=attribute-defined-outside-init
        self.field_query_string = field_query_string
        # pylint: enable=attribute-defined-outside-init
        formatted_field_name = self.format_field_by_type(field)

        if field_query_string == "*":
            formatted_field_query_string = field_query_string
        else:
            formatted_field_query_string = f'"{field_query_string}"'

        if field_query_string == "*":
            formatted_field_query_string = field_query_string
        else:
            formatted_field_query_string = f'"{field_query_string}"'

        query_string = f"{formatted_field_name}:{formatted_field_query_string}"
        aggregation_spec = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "query_string": {"query": query_string},
                        }
                    ]
                }
            },
            "aggs": {},
        }

        if date_interval == "Year":
            aggregation_spec["aggs"]["year_histogram"] = {
                "histogram": {
                    "script": "doc['datetime'].value.getYear()",
                    "interval": 1,
                    "min_doc_count": 0,
                }
            }
        elif date_interval == "Month":
            aggregation_spec["aggs"]["month_histogram"] = {
                "histogram": {
                    "script": "doc['datetime'].value.getMonthOfYear()",
                    "interval": 1,
                    "extended_bounds": {"min": 1, "max": 12},
                    "min_doc_count": 0,
                }
            }
        elif date_interval == "Day":
            aggregation_spec["aggs"]["day_histogram"] = {
                "histogram": {
                    "script": "doc['datetime'].value.getDayOfWeek()",
                    "interval": 1,
                    "extended_bounds": {"min": 0, "max": 6},
                    "min_doc_count": 0,
                }
            }
        elif date_interval == "Hour":
            aggregation_spec["aggs"]["hour_histogram"] = {
                "histogram": {
                    "script": "doc['datetime'].value.getHourOfDay()",
                    "interval": 1,
                    "extended_bounds": {"min": 0, "max": 23},
                    "min_doc_count": 0,
                }
            }
        elif date_interval == "Hour-Day":
            aggregation_spec["aggs"]["hour_of_week_histogram"] = {
                "histogram": {
                    "script": (
                        "doc['datetime'].value.getDayOfWeek()*24 + "
                        "doc['datetime'].value.getHourOfDay()"
                    ),
                    "interval": 1,
                    "extended_bounds": {"min": 0, "max": 167},
                    "min_doc_count": 0,
                }
            }

        self._add_query_to_aggregation_spec(aggregation_spec, start_time, end_time)
        response = self.opensearch_aggregation(aggregation_spec)
        aggregations = response.get("aggregations", {})
        return interface.AggregationResult(
            encoding=None,
            values=[aggregations],
            chart_type=None,
            sketch_url=self._sketch_url,
            field=field,
        )


manager.AggregatorManager.register_aggregator(
    SummaryAggregation, exclude_from_list=True
)


manager.AggregatorManager.register_aggregator(
    DateSummaryAggregator, exclude_from_list=True
)
