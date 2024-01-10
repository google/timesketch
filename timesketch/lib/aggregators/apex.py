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

from datetime import datetime
import json

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

    def __init__(self, sketch_id, query=True, aggs=True) -> None:
        """Initializes the AggregationQuerySpec object."""
        self.sketch_id = sketch_id
        self.spec = {}

        if query:
            self.spec["query"] = {
                "bool": {
                    "must": [],
                    "must_not": {
                        "should": [],
                        "minimum_should_match": 1
                    },
                    "filter": []
                }
            }

        if aggs:
            self.spec["aggs"] = {}

    def add_aggregation_dsl(self, name, spec):
        """Updates the query specification with an aggregation DSL.

        If the aggregation with `name` already exists, it will be replaced by the new
        specification.

        Args:
            name (str): the aggregation name.
            spec (dict[str, Any]): the aggregation specification to add.
        """
        self.spec["aggs"][name] = spec

    def add_datetime_range_clause(
        self, datetime_value, operator="gte", clause="filter"
    ):
        """Adds a date range clause to the aggregation query specification.

        Args:
            datetime_value (str): ISO formatted date time string.
            operator (str): one of `gte` or `lte`.
            clause (str): boolean clause - one of `must`, `must_not`, `should`,
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

        try:
            _ = datetime.fromisoformat(datetime_value)
        except ValueError as error:
            raise ValueError(f"{datetime_value} is not ISO formatted.") from error

        existing_clauses = self.spec["query"]["bool"][clause]
        for filter in existing_clauses:
            if "range" in filter and "datetime" in filter["range"]:
                filter["range"]["datetime"][operator] = datetime_value
                break
        else:
            self.spec["query"]["bool"][clause].append(
                {"range": {"datetime": {operator: datetime_value}}}
            )

    def add_query_string_filter(self, query_string, clause="filter"):
        if not query_string:
            return

        if clause not in self._VALID_QUERY_CLAUSES:
            raise ValueError(f"Unknown boolean clause {clause}")

        self.spec["query"]["bool"][clause].append(
            {"query_string": {"query": query_string, "default_operator": "AND"}}
        )

    def add_bool_query_filter(self, field_name, field_value, clause="filter", term_type="term"):
        if not field_name or not field_value:
            return

        if clause not in self._VALID_QUERY_CLAUSES:
            raise ValueError(f"Unknown boolean clause {clause}")

        self.spec["query"]["bool"][clause].append({term_type: {field_name: field_value}})

    def add_timeline_filter(self, timeline_ids, clause="filter"):
        self.add_bool_query_filter("__ts_timeline_id", timeline_ids, clause, term_type="terms")

    def add_start_datetime_filter(self, datetime_value, clause="filter"):
        self.add_datetime_range_clause(datetime_value, operator="gte", clause=clause)

    def add_end_datetime_filter(self, datetime_value, clause="filter"):
        self.add_datetime_range_clause(datetime_value, operator="lte", clause=clause)

    def _add_label_query():

    def add_query_chips_filter(self, query_chips):
        for chip in query_chips:
            if not chip.get("active", True):
                continue

            chip_type = chip.get("type", None)

            if not chip_type:
                continue

            if chip_type == "label":


class ApexAggregationResult:
    """Result object for ApexChart aggregations.

    Attributes:
        chart_type: the chart type to render, defaults to "table"
    """

    def __init__(self, chart_type, fields, sketch_url, values, chart_options):
        self.chart_type = chart_type
        self.fields = fields
        self.sketch_url = sketch_url
        self.values = values
        self.chart_options = chart_options

    def to_dict(self):
        """Encode aggregation as an ApexChart dictionary."""
        return {"values": self.values}

    def to_chart(self):
        return None


class ApexAggregation(interface.BaseAggregator):
    """Base Aggregator for ApexChart visualizations for frontend-ng.

    Attributes:
        chart_type: the chart type
        fields (list[str]): the fields to aggregate
        aggregator_type (str): the OpenSearch aggregation.
        sketch (Sketch): the Sketch.
        indices (list[str]): the OpenSearch index names.
        timeline_ids (list[int]): the timeline IDs.
        start_time (str): the ISO formatted start time bound.
        end_time (str): the ISO formatted end time bound.
        query_string (str): the query filter string.
        query_is_dsl (bool): True if the query string is an OpenSearch DSL.
        query_chips (list[dict[str, str]]): a list of query chips for filtering.
    """

    NAME = "apex_chart"
    DISPLAY_NAME = "Apex Chart Aggregation"
    DESCRIPTION = "Aggregating values for an ApexChart visualization."

    SUPPORTED_CHARTS = frozenset(
        ["bar", "column", "line", "heatmap", "gantt", "number", "table"
    ])

    # No form fields since this is not meant to be used in the legacy UI.
    FORM_FIELDS = frozenset([])

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
        super().__init__(sketch_id=sketch_id, indices=indices, timeline_ids=timeline_ids)
        self.chart_type = None
        self.chart_options = {}
        self.fields = []
        self.aggregator_type = None
        self.start_time = None
        self.end_time = None
        self.query_string = None
        self.query_is_dsl = False
        self.query_chips = []

    @property
    def chart_title(self):
        """Returns a title for the chart."""
        if self.fields:
            return f"{self.DISPLAY_NAME} for {' - '.join(self.fields)}"
        return self.DISPLAY_NAME

    def _get_aggregation_dsl(self):
        """Returns the aggregation specific DSL as a dictionary."""


    def _get_vega_encoding(self):
        """Returns the Vega encoding for rendering the aggregation chart as a dictionary."""
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
        """Builds an Aggregation Query specification."""
        aggregation_query = AggregationQuerySpec()
        aggregation_query.add_start_datetime_filter(self.start_time)
        aggregation_query.add_end_datetime_filter(self.end_time)
        aggregation_query.add_timeline_filter(self.timeline_ids)

        if self.query_string:
            if self.query_is_dsl:
                try:
                    query_dsl = json.loads(self.query_string)
                except:
                    raise ValueError("The query_filter is not valid JSON")
                aggregation_query.spec["query"] = query_dsl
            else:
                aggregation_query.add_query_string_filter(self.query_string)

        for query_chip in self.query_chips:
            print(query_chip)

        aggregation_query.add_aggregation_dsl(
            "aggregation", self._get_aggregation_dsl()
        )
        return aggregation_query.spec

    def run(
        self,
        *,
        fields,
        aggregator_type,
        aggregator_options,
        chart_type,
        chart_options,):
        """Runs the aggregator.

        Returns:
            ApexChartResult

        Raises:
            ValueError when:
            * fields is empty or an invalid format.
            * chart type is not a supported type.
        """
        if not fields:
            raise ValueError("Fields cannot be empty")
        elif isinstance(fields, str):
            self.fields = [fields]
        elif isinstance(fields, list):
            self.fields = fields
        else:
            raise ValueError("Fields is an invalid format.")

        if chart_type not in self.SUPPORTED_CHARTS:
            raise ValueError(f"Chart type is not supported.")
        self.chart_type = chart_type
        self.chart_options = chart_options

        self.start_time = aggregator_options.pop('start_time', '')
        self.end_time = aggregator_options.pop('end_time', '')
        self.query_string = aggregator_options.pop('query_string', '')
        self.query_is_dsl = aggregator_options.pop('query_is_dsl', False)
        self.query_chips = aggregator_options.pop('query_chips', [])
        self.timeline_ids = aggregator_options.pop('timeline_ids', self.timeline_ids)

        from pprint import pprint

        aggregation_query_spec = self._build_aggregation_query_spec(aggregator_options)
        pprint(aggregation_query_spec)

        response = self.opensearch_aggregation(aggregation_query_spec)
        pprint(response)

        values = self._process_aggregation_response(response)

        return ApexAggregationResult(
            chart_type=chart_type,
            fields=self.fields,
            sketch_url=self._sketch_url,
            values=[],
            chart_options=self.chart_options,
        )


manager.AggregatorManager.register_aggregator(ApexAggregation, exclude_from_list=True)
