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

import re
import time

from datetime import datetime

from timesketch.lib.aggregators import manager
from timesketch.lib.aggregators import interface


def get_fnc_duration(first, last, fmt_durat="days"):
    """Returns duration between first and last seen.
    Args:
        first (str): this denotes the field term.
        last (str): this denotes the value of term.
        format (str): choose return format days/hours/seconds
    Returns:
        Duration Int
    """
    if first == "NC":
        return -1
    if last == "NC":
        return -1
    try:
        duration = datetime.strptime(time.ctime(last/1000000),
                                     "%a %b %d %H:%M:%S %Y") \
            - datetime.strptime(time.ctime(first/1000000),
                                "%a %b %d %H:%M:%S %Y")
        if fmt_durat == "hours":
            return int(duration.seconds/3600)
        if fmt_durat == "seconds":
            return int(duration.seconds)
        return int(duration.days)
    except ValueError:
        return -1


def get_spec(field, limit=10, order_type="desc", query="", query_dsl=""):
    """Returns aggregation specs for a term of filtered events.

    The aggregation spec will summarize values of an attribute
    whose events fall under a filter.

    Args:
        field (str): this denotes the event attribute that is used
            for aggregation.
        limit (int): How many buckets to return, defaults to 10.
        order_type (str): Order terms asc/desc aggregation.
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
        "aggs": {
            "aggregation": {
                "terms": {
                    "field": field,
                    "size": limit,
                    "order": {"_count": order_type}
                }
            }
        },
    }


class FilteredTermsAggregation(interface.BaseAggregator):
    """Query Filter Term Aggregation."""

    NAME = "query_bucket"
    DISPLAY_NAME = "Filtered Terms Aggregation"
    DESCRIPTION = "Aggregating values of a field after applying a filter"

    SUPPORTED_CHARTS = frozenset(
        ["barchart", "circlechart", "hbarchart", "linechart", "table"]
    )

    SUPPORTED_ORDER = frozenset(
        ["desc", "asc"]
    )

    SUPPORTED_BOOL = frozenset(
        [True, False]
    )

    SUPPORTED_DURE = frozenset(
        [None, "days", "hours", "seconds"]
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
        {
            "type": "ts-dynamic-form-select-input",
            "name": "order_type",
            "label": "Order",
            "options": list(SUPPORTED_ORDER),
            "default_value": "desc",
            "display": True
        },
        {
            "name": "filter_re",
            "type": "ts-dynamic-form-text-input",
            "label": "Filter regex",
            "display": True
        },
        {
            "name": "keep_re_notfound",
            "type": "ts-dynamic-form-select-input",
            "label": "Keep term not match to re filter (if used)",
            "options": list(SUPPORTED_BOOL),
            "default_value": False,
            "display": True
        },
        {
            "name": "get_duration",
            "type": "ts-dynamic-form-select-input",
            "label": "Get first, last and duration of each terms",
            "options": list(SUPPORTED_DURE),
            "default_value": False,
            "display": True
        },
    ]

    @property
    def chart_title(self):
        """Returns a title for the chart."""
        if self.field:
            return 'Top filtered results for "{0:s}"'.format(self.field)
        return "Top results for an unknown field after filtering"

    def get_date_event(self, field, value, order, query=""):
        """Returns event date first or last for a term of filtered events.
        Function get first or last term date
        Args:
            field (str): this denotes the field term.
            value (str): this denotes the value of term.
            query (str): the original query field used on aggregation.
        Raises:
            ValueError: if neither query_string is provided.
        Returns:
            a string value contains date of first ou last event
            (according by order).
        """

        if query:
            query_filter = {
                "bool": {
                    "must": [
                        {
                            "query_string": {
                                "query": query
                            }
                        },
                        {
                            "match_phrase": {
                                field: value
                            }
                        }
                    ]
                }
            }
        else:
            raise ValueError("Neither query nor query DSL provided.")

        spec = {
            "query": query_filter,
            "sort": [
                {
                    "timestamp": {
                        "order": order
                    }
                }
            ],
            "size": 1,
            "_source": ["datetime", "timestamp"]
        }

        response = self.opensearch_aggregation(spec, size=1)
        hits = response.get("hits", {})
        hit = hits.get("hits", {})
        if not hit:
            return "NC"
        source = hit[0].get("_source", {})
        date = source.get("datetime", "NC")
        tsdate = source.get("timestamp", "NC")
        return date, tsdate

    # pylint: disable=arguments-differ,too-many-arguments
    def run(
        self,
        field,
        query_string="",
        query_dsl="",
        order_type="desc",
        supported_charts="table",
        start_time="",
        end_time="",
        limit=10,
        filter_re="",
        keep_re_notfound=False,
        get_duration=None
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
            order_type: terms aggregation orders by desc/asc document _count.
            supported_charts: Chart type to render. Defaults to table.
            start_time: Optional ISO formatted date string that limits the time
                range for the aggregation.
            end_time: Optional ISO formatted date string that limits the time
                range for the aggregation.
            limit (int): How many buckets to return, defaults to 10.
            filter_re (str): pre-filter result term to extract specific values.
            keep_re_notfound (bool): keep term value dont match to filter_re.
            get_duration (bool): get first, last date and duration
                of term value.

        Returns:
            Instance of interface.AggregationResult with aggregation result.

        Raises:
            ValueError: if neither query_string or query_dsl is provided.
        """
        if not (query_string or query_dsl):
            raise ValueError("Both query_string and query_dsl are missing")

        re_compiled = None
        if filter_re:
            try:
                re_compiled = re.compile(filter_re, re.IGNORECASE)
            except re.error as reerror:
                raise ValueError("Regexp filter not valid") from reerror

        self.field = field
        formatted_field_name = self.format_field_by_type(field)

        aggregation_spec = get_spec(
            field=formatted_field_name,
            limit=limit,
            order_type=order_type,
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

        if get_duration:
            encoding["tooltip"] = [
                {"field": "duration", "type": "quantitative"},
                {"field": "first", "type": "nominal"},
                {"field": "last", "type": "nominal"},
                {"field": field, "type": "nominal"},
                {"field": "count", "type": "quantitative"},
            ]

        response = self.opensearch_aggregation(aggregation_spec)
        aggregations = response.get("aggregations", {})
        aggregation = aggregations.get("aggregation", {})

        buckets = aggregation.get("buckets", [])
        values = []
        re_chg = {}
        for bucket in buckets:
            d = {field: bucket.get("key", "N/A"),
                 "count": bucket.get("doc_count", 0)}
            if get_duration:
                d["first"], d["fdate"] = self.get_date_event(
                    field=formatted_field_name,
                    value=d[field],
                    order="asc",
                    query=query_string)
                d["last"], d["ldate"] = self.get_date_event(
                    field=formatted_field_name,
                    value=d[field],
                    order="desc",
                    query=query_string)
                d["duration"] = get_fnc_duration(
                    d["fdate"], d["ldate"], get_duration)
                if not filter_re:
                    del d["fdate"]
                    del d["ldate"]
            if filter_re and isinstance(d[field], str):
                match = re_compiled.search(d[field])
                if match:
                    d[field] = " ".join(match.groups())
                    if d[field] in re_chg:
                        re_chg[d[field]]["count"] = re_chg[d[field]]["count"] \
                                                    + d['count']
                        if get_duration and -1 != d["duration"]:
                            if -1 == re_chg[d[field]]["duration"]:
                                re_chg[d[field]]["duration"] = d["duration"]
                            elif d["duration"] > re_chg[d[field]]["duration"]:
                                re_chg[d[field]]["duration"] = d["duration"]
                        if get_duration and d["first"] != "NC":
                            if re_chg[d[field]]["first"] == "NC":
                                re_chg[d[field]]["first"] = d["first"]
                                re_chg[d[field]]["fdate"] = d["fdate"]
                            elif re_chg[d[field]]["fdate"] > d["fdate"]:
                                re_chg[d[field]]["first"] = d["first"]
                                re_chg[d[field]]["fdate"] = d["fdate"]
                        if get_duration and d["last"] != "NC":
                            if re_chg[d[field]]["last"] == "NC":
                                re_chg[d[field]]["last"] = d["last"]
                                re_chg[d[field]]["ldate"] = d["ldate"]
                            elif d["ldate"] > re_chg[d[field]]["ldate"]:
                                re_chg[d[field]]["last"] = d["last"]
                                re_chg[d[field]]["ldate"] = d["ldate"]
                    else:
                        re_chg[d[field]] = d
                elif keep_re_notfound:
                    if get_duration:
                        del d["fdate"]
                        del d["ldate"]
                    values.append(d)
            else:
                values.append(d)

        if re_chg:
            for k, v in re_chg.items():
                if get_duration:
                    d = {
                        field: k,
                        "count": v["count"],
                        "first": v["first"],
                        "last": v["last"],
                        "duration": v["duration"]
                    }
                    values.append(d)
                else:
                    d = {
                        field: k,
                        "count": v["count"]
                    }
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
