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
"""Aggregator for Apex-Chart visualizations."""

import collections

import pandas as pd

from timesketch.lib.aggregators import interface
from timesketch.lib.aggregators import manager


class AggregationQuerySpec:
    """AggregationQuerySpec object.

    The AggregationQuerySpec object is used for building Opensearch aggregation
    query specifications.

    https://opensearch.org/docs/latest/aggregations/index/#general-aggregation-structure

    Attributes:
        spec (dict[str, Any]): the aggregation query specification.
    """

    _VALID_QUERY_CLAUSES = frozenset(
        [
            "must",
            "must_not",
            "should",
            "filter",
        ]
    )

    def __init__(self, sketch_id) -> None:
        """Initializes the AggregationQuerySpec object."""
        self.sketch_id = sketch_id
        self.datetime_ranges = {"must": [], "must_not": [], "should": [], "filter": []}
        self.bool_queries = {"must": [], "must_not": [], "should": [], "filter": []}
        self.aggregation_query = {}

    @property
    def spec(self):
        """Returns the aggregation spec as a dictionary."""
        spec = {"query": {"bool": {}}}
        for clause, queries in self.bool_queries.items():
            if not queries:
                continue
            spec["query"]["bool"][clause] = queries

        for clause, queries in self.datetime_ranges.items():
            if not queries:
                continue
            spec["query"]["bool"][clause].append(
                {"bool": {"should": queries, "minimum_should_match": 1}}
            )

        if self.aggregation_query:
            spec["aggs"] = {"aggregation": self.aggregation_query}

        return spec

    def add_datetime_value(self, datetime_value, operator="gte", clause="filter"):
        """Adds a date range clause to the aggregation query specification.

        Args:
            datetime_value (str): the ISO formatted date time string.
            operator (str): one of `gte` or `lte`.
            clause (str): the boolean clause - one of `must`, `must_not`, `should`,
                `filter`.

        Raises:
            ValueError if the datetime_value is not a valid ISO format or clause
                is an unexpected boolean clause value.
        """
        if not datetime_value:
            return

        if operator not in ("gte", "lte"):
            raise ValueError(f"Unknown operator clause - {operator}.")

        if clause not in self._VALID_QUERY_CLAUSES:
            raise ValueError(f"Unknown boolean clause - {clause}.")

        for query_clause in self.bool_queries[clause]:
            if "range" in query_clause and "datetime" in query_clause["range"]:
                query_clause["range"]["datetime"][operator] = datetime_value
                break
        else:
            self.bool_queries[clause].append(
                {"range": {"datetime": {operator: datetime_value}}}
            )

    def add_query_string_filter(self, query_string, clause="filter"):
        """Adds a query string filter to the agregation query specification.

        Args:
            query_string (str): the query string.
            clause (str): the boolean clause to add the query string to.

        Raises:
            ValueError if the clause is not one of the valid query clause values.
        """
        if not query_string:
            return

        if clause not in self._VALID_QUERY_CLAUSES:
            raise ValueError(f"Unknown boolean clause {clause}")

        self.bool_queries[clause].append(
            {"query_string": {"query": query_string, "default_operator": "AND"}}
        )

    def add_match_phrase_filter(self, field, value, clause="must"):
        """Adds a match phrase filter to the aggregation query specification.

        Args:
            field (str): the match phrase field
            value (str): the match phrase value
            clause (str): the boolean clause to add the query string to.

        Raises:
            ValueError if the clause is not one of the valid query clause values.
        """
        if not field or not value:
            return

        if clause not in self._VALID_QUERY_CLAUSES:
            raise ValueError(f"Unknown boolean clause {clause}")

        self.bool_queries[clause].append({"match_phrase": {field: {"query": value}}})

    def add_term_filter(self, field, value, clause="filter", term_type="term"):
        """Adds a term filter to the aggregation query specification.

        Args:
            field (str): the term field.
            value (str): the term value.
            clause (str): the boolean clause to add the term filter to.
            term_type (str): the term filter type.

        Raises:
            ValueError if the clause is not one of the valid query clause values.
        """
        if not field or not value:
            return

        if clause not in self._VALID_QUERY_CLAUSES:
            raise ValueError(f"Unknown boolean clause {clause}")

        self.bool_queries[clause].append({term_type: {field: value}})

    def add_timeline_filter(self, timeline_ids, clause="filter"):
        """Adds a timeline filter to the aggregation query specification.

        Args:
            timeline_ids (list[int]): a list of timeline IDs to filter on.
            clause (str): the boolean clause to add the timeline filter.
        """
        self.add_term_filter(
            "__ts_timeline_id", timeline_ids, clause, term_type="terms"
        )

    def add_start_datetime_filter(self, datetime_value, clause="filter"):
        """Adds a start datetime filter to the aggregation query specification.

        Args:
            datetime_value (str): the start datetime as an ISO formatted string.
            clause (str): the boolean clause to add the datetime filter.
        """
        self.add_datetime_value(datetime_value, operator="gte", clause=clause)

    def add_end_datetime_filter(self, datetime_value, clause="filter"):
        """Adds a end datetime filter to the aggregation query specification.

        Args:
            datetime_value (str): the end datetime as an ISO formatted string.
            clause (str): the boolean clause to add the datetime filter.
        """
        self.add_datetime_value(datetime_value, operator="lte", clause=clause)

    def add_timesketch_label_filter(self, label, clause="must"):
        """Adds a query for Timesketch labels.

        Args:
            label (str): the timesketch label to filter on.
            clause (str): the boolean clause to add the datetime filter.

        Raises:
            ValueError if the clause is not one of the valid query clause values.
        """
        if not label:
            return

        if clause not in self._VALID_QUERY_CLAUSES:
            raise ValueError(f"Unknown boolean clause {clause}")

        nested_query = {
            "nested": {
                "query": {
                    "bool": {
                        "must": [
                            {"term": {"timesketch_label.name.keyword": label}},
                            {"term": {"timesketch_label.sketch_id": self.sketch_id}},
                        ]
                    }
                },
                "path": "timesketch_label",
            }
        }

        self.bool_queries[clause].append(nested_query)

    def add_datetime_range(self, datetime_range, clause="filter"):
        """Adds a datetime range query used in a should (logical OR) query.

        Args:
            datetime_range (str): a comma separated datetime pair.
            clause (str): the boolean clause to apply the datetime range query.

        Raises:
            ValueError if datetime_range is not in a valid form or clause is not
                one of the valid query clause values.
        """
        if not datetime_range:
            return

        if clause not in self._VALID_QUERY_CLAUSES:
            raise ValueError(f"Unknown boolean clause {clause}")

        # Raises ValueError if datetime_range does not unpack to 2 values.
        start, end = datetime_range.split(",")

        self.datetime_ranges[clause].append(
            {"range": {"datetime": {"gte": start, "lte": end}}}
        )


class ApexAggregationResult:
    """Result object for ApexChart aggregations.

    Attributes:
        chart_options (str): the chart options
        chart_type (str): the chart type to render
        fields (list[str]): the fields to aggregate on.
        labels (): the labels
        values (): the values
    """

    def __init__(
        self, chart_type, fields, sketch_url, labels, values, chart_options, spec
    ):
        self.chart_options = chart_options
        self.chart_type = chart_type
        self.fields = fields
        self.labels = labels
        self.sketch_url = sketch_url
        self.spec = spec
        self.values = values

    def to_dict(self):
        """Encode aggregation as an ApexChart dictionary."""
        return {
            "values": self.values,
            "labels": self.labels,
            "chart_options": self.chart_options,
            "chart_type": self.chart_type,
            "spec": self.spec,
        }

    def to_pandas(self):
        """Encode aggregation result as a pandas dataframe.

        Returns:
            Pandas dataframe with aggregation results.
        """
        return pd.DataFrame(self.values)

    def to_chart(self, *_args):
        """Encode aggregation result as Vega-Lite chart.

        Since ApexChart does not support Vega charts, None is returned.
        """
        return None


class ApexAggregation(interface.BaseAggregator):
    """Base Aggregator for ApexChart visualizations for frontend-ng.

    Attributes:
        chart_type: the Apex chart type.
        chart_options (dict[str, Any]): the Apedx chart options.
        fields (list[str]): the event fields to aggregate.
        metric (str): the aggregation metric.
        sketch_id (int): the sketch ID.
    """

    NAME = "apex_chart"
    DISPLAY_NAME = "Apex Chart Aggregation"
    DESCRIPTION = "Aggregating values for an ApexChart visualization."
    SUPPORTED_CHARTS = frozenset(
        ["bar", "column", "line", "heatmap", "gantt", "number", "table"]
    )

    # No form fields since this is not meant to be used in the legacy UI.
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
        self.chart_type = None
        self.chart_options = {}
        self.fields = []
        self.metric = None
        self.sketch_id = sketch_id

    @property
    def chart_title(self):
        """Returns a title for the chart."""
        if self.fields:
            return f"{self.DISPLAY_NAME} for {' - '.join(self.fields)}"
        return self.DISPLAY_NAME

    def _get_aggregation_dsl(self, aggregator_options):
        """Returns the aggregation specific DSL as a dictionary."""
        raise NotImplementedError

    def _get_vega_encoding(self):
        """Returns the Vega encoding for rendering the aggregation chart as a dict."""
        raise RuntimeError(f"{self.__name__} cannot be used for Vega encodings.")

    def _process_aggregation_response(self, response):
        """Processes the OpenSearch aggregation response extracting values for the
        AggregationResult.

        Args:
            response (dict[str, Any]): the OpenSearch aggregation response.

        Returns:
            the aggregation values.
        """
        raise NotImplementedError

    def _build_aggregation_query_spec(self, aggregator_options):
        """Builds an Aggregation Query specification.

        Args:
            aggregator_options (dict[str, Any]): a mapping of options for
                filtering/searching aggregations.

        Returns:
            an opensearch query DSL as a dict

        Raises:
            ValueError if an unknown chip type is provided in the aggregator_options.
        """
        start_time = aggregator_options.pop("start_time", "")
        end_time = aggregator_options.pop("end_time", "")
        query_string = aggregator_options.pop("query_string", "")
        query_chips = aggregator_options.pop("query_chips", [])
        timeline_ids = aggregator_options.pop("timeline_ids", self.timeline_ids)

        aggregation_query = AggregationQuerySpec(self.sketch_id)
        aggregation_query.add_start_datetime_filter(start_time)
        aggregation_query.add_end_datetime_filter(end_time)
        aggregation_query.add_timeline_filter(timeline_ids)
        aggregation_query.add_query_string_filter(query_string)

        for field in self.fields:
            aggregation_query.add_term_filter(
                field="field", value=field["field"], clause="must", term_type="exists"
            )

        if query_chips:
            for query_chip in query_chips:
                if not query_chip.get("active", True):
                    continue

                chip_type = query_chip.get("type")
                if not chip_type:
                    continue

                chip_field = query_chip.get("field")
                chip_value = query_chip.get("value")
                chip_operator = query_chip.get("operator")
                if chip_type == "label":
                    aggregation_query.add_timesketch_label_filter(chip_value)
                elif chip_type == "datetime_range":
                    aggregation_query.add_datetime_range(chip_value, chip_operator)
                elif chip_type == "term":
                    aggregation_query.add_term_filter(
                        chip_field, chip_value, chip_operator
                    )
                else:
                    raise ValueError("Unknown chip type")

        aggregation_query.aggregation_query = self._get_aggregation_dsl(
            aggregator_options
        )

        return aggregation_query.spec

    def run(
        self, *, fields, aggregator_options, chart_type, chart_options
    ):  # pylint: disable=arguments-differ
        """Runs the aggregator.

        Returns:
            ApexChartResult object.

        Raises:
            ValueError when:
            * fields is empty or an invalid format.
            * chart type is not a supported type.
        """
        if not fields:
            raise ValueError("Fields cannot be empty")

        if isinstance(fields, str):
            self.fields = [fields]
        elif isinstance(fields, list):
            self.fields = fields
        else:
            raise ValueError("Fields is in an invalid format.")

        if chart_type not in self.SUPPORTED_CHARTS:
            raise ValueError(f"Chart type {chart_type} is not supported.")
        self.chart_type = chart_type
        self.chart_options = chart_options

        aggregation_query_spec = self._build_aggregation_query_spec(aggregator_options)
        response = self.opensearch_aggregation(aggregation_query_spec)
        values, labels = self._process_aggregation_response(response)

        return ApexAggregationResult(
            chart_type=chart_type,
            fields=self.fields,
            sketch_url=self._sketch_url,
            labels=labels,
            values=values,
            chart_options=chart_options,
            spec=response,
        )


class CalendarDateHistogram(ApexAggregation):
    """Aggregates events using the Date Histogram (with calendar intervals)
    bucket aggregator."""

    NAME = "calendar_date_histogram"
    DESCRIPTION = "Calendar Date Histogram Aggregation for use with ApexCharts"

    DEFAULT_CALENDAR_INTERVAL = "year"

    DEFAULT_METRIC = "value_count"

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
        self.calendar_interval = None

    def _get_aggregation_dsl(self, aggregator_options):
        """Returns the aggregation specific DSL as a dictionary."""
        self.calendar_interval = aggregator_options.get(
            "calendar_interval", self.DEFAULT_CALENDAR_INTERVAL
        )

        self.metric = aggregator_options.get("metric", self.DEFAULT_METRIC)

        dsl = {
            "date_histogram": {"field": "datetime", "interval": self.calendar_interval},
            "aggs": {},
        }

        for field in self.fields:
            if field["type"] == "text":
                field = f"{field['field']}.keyword"
            else:
                field = field["field"]

            dsl["aggs"][self.metric] = {self.metric: {"field": field}}
        return dsl

    def _process_aggregation_response(self, response):
        """Processes the OpenSearch aggregation response extracting values for the
        AggregationResult.

        Args:
            response (dict[str, Any]): the OpenSearch aggregation response.

        Returns:
            the aggregation values.
        """
        try:
            buckets = response["aggregations"]["aggregation"]["buckets"]
        except IndexError as err:
            raise ValueError(
                f"Unexpected response in aggregation query: {err}"
            ) from err

        data = collections.defaultdict(list)
        labels = []
        for bucket in buckets:
            _ = int(bucket.pop("key"))
            labels.append(bucket.pop("key_as_string"))
            for k, v in bucket.items():
                if k == "doc_count":
                    data[k].append(v)
                else:
                    data[k].append(v["value"])

        return data, labels


class AutoDateHistogram(ApexAggregation):
    """Aggregates events using the Auto Date Histogram bucket aggregator."""

    NAME = "auto_date_histogram"
    DESCRIPTION = "Auto Date Histogram Aggregation for an ApexChart visualization"
    DEFAULT_METRIC = "value_count"

    def _get_aggregation_dsl(self, aggregator_options):
        """Returns the aggregation specific DSL as a dictionary."""
        max_items = aggregator_options.get("max_items", 10)
        metric = aggregator_options.get("metric", self.DEFAULT_METRIC)

        dsl = {
            "auto_date_histogram": {"field": "datetime", "buckets": max_items},
            "aggs": {},
        }

        for field in self.fields:
            if field["type"] == "text":
                field = f"{field['field']}.keyword"
            else:
                field = field["field"]

            dsl["aggs"][metric] = {metric: {"field": field}}
        return dsl

    def _process_aggregation_response(self, response):
        """Processes the OpenSearch aggregation response extracting values for the
        AggregationResult.

        Args:
            response (dict[str, Any]): the OpenSearch aggregation response.

        Returns:
            the aggregation values.
        """
        try:
            buckets = response["aggregations"]["aggregation"]["buckets"]
        except IndexError as err:
            raise ValueError(
                f"Unexpected response in aggregation query: {err}"
            ) from err
        data = collections.defaultdict(list)
        labels = []
        for bucket in buckets:
            _ = bucket.pop("key")
            labels.append(bucket.pop("key_as_string"))
            for k, v in bucket.items():
                if k == "doc_count":
                    data[k].append(v)
                else:
                    data[k].append(v["value"])

        return data, labels


class TopTerms(ApexAggregation):
    """Aggregates events using the (Top) Terms bucket aggregator."""

    NAME = "top_terms"
    DESCRIPTION = "Top Terms Aggregation for an ApexChart visualization"
    DEFAULT_MAX_ITEMS = 10

    SUPPORTED_CHARTS = frozenset(
        ["bar", "column", "donut", "line", "heatmap", "gantt", "number", "table"]
    )

    def _get_aggregation_dsl(self, aggregator_options):
        """Returns the aggregation specific DSL as a dictionary."""
        max_items = aggregator_options.get("max_items", self.DEFAULT_MAX_ITEMS)
        field = self.fields[0]
        if field["type"] == "text":
            field = f"{field['field']}.keyword"
        else:
            field = field["field"]
        dsl = {"terms": {"field": field, "size": max_items}}
        return dsl

    def _process_aggregation_response(self, response):
        """Processes the OpenSearch aggregation response extracting values for the
        AggregationResult.

        Args:
            response (dict[str, Any]): the OpenSearch aggregation response.

        Returns:
            the aggregation values.
        """
        try:
            buckets = response["aggregations"]["aggregation"]["buckets"]
        except IndexError as err:
            raise ValueError(
                f"Unexpected response in aggregation query: {err}"
            ) from err
        data = {"value_count": []}
        labels = []
        for bucket in buckets:
            data["value_count"].append(bucket["doc_count"])
            labels.append(bucket["key"])
        return data, labels


class RareTerms(ApexAggregation):
    """Aggregates events using the Rare Terms bucket aggregator."""

    NAME = "rare_terms"
    DESCRIPTION = "Rare Terms Aggregation for an ApexChart visualization"

    DEFAULT_MAX_DOC_COUNT = 3

    def _get_aggregation_dsl(self, aggregator_options):
        """Returns the aggregation specific DSL as a dictionary."""
        max_items = aggregator_options.get("max_items", self.DEFAULT_MAX_DOC_COUNT)
        field = self.fields[0]
        if field["type"] == "text":
            field = f"{field['field']}.keyword"
        else:
            field = field["field"]
        dsl = {"rare_terms": {"field": field, "max_doc_count": max_items}}
        return dsl

    def _process_aggregation_response(self, response):
        """Processes the OpenSearch aggregation response extracting values for the
        AggregationResult.

        Args:
            response (dict[str, Any]): the OpenSearch aggregation response.

        Returns:
            the aggregation values.
        """
        try:
            buckets = response["aggregations"]["aggregation"]["buckets"]
        except IndexError as err:
            raise ValueError(
                f"Unexpected response in aggregation query: {err}"
            ) from err

        data = {"value_count": []}
        labels = []
        for bucket in buckets:
            data["value_count"].append(bucket["doc_count"])
            labels.append(bucket["key"])
        return data, labels


class SingleMetric(ApexAggregation):
    """Aggregates events using a single metric aggregator."""

    NAME = "single_metric"
    DESCRIPTION = "Single Metric Aggregation for an ApexChart visualization"
    SUPPORTED_METRICS = frozenset(
        ["avg", "cardinality", "min", "max", "sum", "value_count"]
    )

    DEFAULT_METRIC = "value_count"

    def _get_aggregation_dsl(self, aggregator_options):
        """Returns the aggregation specific DSL as a dictionary."""
        self.metric = aggregator_options.get("metric", self.DEFAULT_METRIC)
        field = self.fields[0]
        if field["type"] == "text":
            field = f"{field['field']}.keyword"
        else:
            field = field["field"]
        dsl = {
            self.metric: {
                "field": field,
            }
        }
        return dsl

    def _process_aggregation_response(self, response):
        """Processes the OpenSearch aggregation response extracting values for the
        AggregationResult.

        Args:
            response (dict[str, Any]): the OpenSearch aggregation response.

        Returns:
            the aggregation values.
        """
        try:
            result = response["aggregations"]["aggregation"]["value"]
        except IndexError as err:
            raise ValueError("Unexpected response in aggregation query: {err}") from err

        return {self.fields[0]["field"]: [result]}, [self.metric]


manager.AggregatorManager.register_aggregator(AutoDateHistogram, exclude_from_list=True)
manager.AggregatorManager.register_aggregator(
    CalendarDateHistogram, exclude_from_list=True
)
manager.AggregatorManager.register_aggregator(RareTerms, exclude_from_list=True)
manager.AggregatorManager.register_aggregator(SingleMetric, exclude_from_list=True)
manager.AggregatorManager.register_aggregator(TopTerms, exclude_from_list=True)
