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
"""Interface for aggregators."""
import datetime
import logging

from flask import current_app

import opensearchpy
import pandas

from timesketch.lib.charts import manager as chart_manager
from timesketch.lib.datastores.opensearch import OpenSearchDataStore
from timesketch.models.sketch import Sketch as SQLSketch


logger = logging.getLogger("timesketch.aggregator_interface")


class AggregationResult(object):
    """Result object for aggregations.

    Attributes:
        chart_type: Chart type to render, defaults to "table".
        encoding: Dict with Vega-Lite encoding information.
        field: String that contains the field name used for URL generation.
        values: List of dicts with aggregation data.
    """

    def __init__(
        self,
        encoding,
        values,
        chart_type="table",
        sketch_url="",
        field="",
        extra_query_url="",
    ):
        """Initialize the object.

        Args:
            encoding: Dict with Vega-Lite encoding information.
            values: List of dicts with aggregation data.
            chart_type: Chart type to render, defaults to "table".
            sketch_url: Sketch URL for rendering.
            field: String that contains the field name used for URL generation.
            extra_query_url: For Chart URL transformation. If provided an extra
                condition will be added to URL transformations in the query
                field.
        """
        self.chart_type = chart_type
        self.encoding = encoding
        self.field = field
        self.values = values
        self._sketch_url = sketch_url
        self._extra_query_url = extra_query_url

    def to_dict(self, encoding=False):
        """Encode aggregation result as dict.

        Args:
            encoding: Boolean indicating if encoding info should be returned.

        Returns:
            Dict with aggregation result.
        """
        aggregation_data = dict(values=self.values)
        if encoding:
            aggregation_data["encoding"] = self.encoding
        return aggregation_data

    def to_pandas(self):
        """Encode aggregation result as a pandas dataframe.

        Returns:
            Pandas dataframe with aggregation results.
        """
        return pandas.DataFrame(self.values)

    def to_chart(
        self,
        chart_name="",
        chart_title="",
        as_html=False,
        interactive=False,
        as_chart=False,
        color="",
    ):
        """Encode aggregation result as Vega-Lite chart.

        Args:
            chart_name: Name of chart as string, defaults to initialized
                value of the chart type..
            chart_title: The title of the chart.
            as_html: Boolean indicating if chart should be returned in HTML.
            interactive: Boolean indicating if chart should be interactive.
            as_chart: Boolean indicating if chart should be returned as a
                chart object (instance of altair.vegalite.v3.api.LayerChart).
            color: String with the color information for the chart.

        Returns:
            Vega-Lite chart spec in either JSON or HTML format.

        Raises:
            RuntimeError if chart type does not exist.
        """
        if not chart_name:
            chart_name = self.chart_type
        chart_class = chart_manager.ChartManager.get_chart(chart_name)

        if not chart_class:
            raise RuntimeError("No such chart type: {0:s}".format(chart_name))

        chart_data = self.to_dict(encoding=True)
        chart_object = chart_class(
            chart_data,
            title=chart_title,
            sketch_url=self._sketch_url,
            field=self.field,
            extra_query_url=self._extra_query_url,
        )

        if color:
            chart_object.set_color(color)

        chart = chart_object.generate()

        if interactive:
            chart = chart.interactive()

        if as_html:
            return chart.to_html()

        if as_chart:
            return chart
        return chart.to_dict()


class BaseAggregator(object):
    """Base class for an aggregator."""

    # Name that the aggregator will be registered as.
    NAME = "name"

    # Describe what the aggregator does, this will be visible in the UI
    # among other places.
    DESCRIPTION = ""

    # Used as hints to the frontend UI in order to render input forms.
    FORM_FIELDS = []

    # List of supported chart types.
    SUPPORTED_CHARTS = frozenset()

    def __init__(self, sketch_id=None, indices=None, timeline_ids=None):
        """Initialize the aggregator object.

        Args:
            field: String that contains the field name used for URL generation.
            sketch_id: Sketch ID.
            indices: Optional list of OpenSearch index names. If not provided
                the default behavior is to include all the indices in a sketch.
            timeline_ids: Optional list of timeline IDs, if not provided the
                default behavior is to query all the data in the provided
                search indices.
        """
        if not sketch_id and not indices:
            raise RuntimeError("Need at least sketch_id or index")

        self.opensearch = OpenSearchDataStore(
            host=current_app.config.get("OPENSEARCH_HOST"),
            port=current_app.config.get("OPENSEARCH_PORT"),
        )

        self._sketch_url = "/sketch/{0:d}/explore".format(sketch_id)
        self.field = ""
        self.indices = indices
        self.sketch = SQLSketch.get_by_id(sketch_id)
        self.timeline_ids = None

        active_timelines = self.sketch.active_timelines
        if not self.indices:
            self.indices = [t.searchindex.index_name for t in active_timelines]

        if timeline_ids:
            valid_ids = [t.id for t in active_timelines]
            self.timeline_ids = [t for t in timeline_ids if t in valid_ids]

    @property
    def chart_title(self):
        """Returns a title for the chart."""
        raise NotImplementedError

    @property
    def describe(self):
        """Returns dict with name as well as a description of aggregator."""
        return {
            "name": self.NAME,
            "description": self.DESCRIPTION,
        }

    def _add_query_to_aggregation_spec(
        self, aggregation_spec, start_time="", end_time=""
    ):
        """Returns an aggregation spec, adjusted for constraints.

        This function will take an aggregation spec, alongside information
        about start and end time and timeline constraints. It will adjust the
        aggregation spec so that these constraints will be taken into
        consideration when running the aggregation.

        Args:
            aggregation_spec: A dict with the query_dsl for the aggregation.
            start_time: Optional ISO formatted date string that limits the time
                range for the aggregation.
            end_time: Optional ISO formatted date string that limits the time
                range for the aggregation.

        Raises:
            ValueError: If the date strings are badly formatted.

        Returns:
            Dict: The aggregation spec, adjusted to query for additional
                constraints.
        """
        query_filters = []

        if self.timeline_ids:
            query_filters.append(
                {
                    "terms": {
                        "__ts_timeline_id": self.timeline_ids,
                    }
                }
            )

        if start_time:
            try:
                _ = datetime.datetime.fromisoformat(start_time)
            except ValueError:
                raise ValueError(
                    "Start time is not ISO formatted [{0:s}".format(start_time)
                ) from ValueError

        if end_time:
            try:
                _ = datetime.datetime.fromisoformat(end_time)
            except ValueError:
                raise ValueError(
                    "End time is not ISO formatted [{0:s}".format(end_time)
                ) from ValueError

        if start_time and end_time:
            query_filters.append(
                {
                    "range": {
                        "datetime": {
                            "gte": start_time,
                            "lte": end_time,
                        }
                    }
                }
            )
        elif start_time:
            query_filters.append(
                {
                    "range": {
                        "datetime": {
                            "gte": start_time,
                        }
                    }
                }
            )

        elif end_time:
            query_filters.append(
                {
                    "range": {
                        "datetime": {
                            "lte": end_time,
                        }
                    }
                }
            )

        if query_filters:
            if "query" in aggregation_spec:
                original_query = aggregation_spec["query"]
                query_filters.append(original_query)

            if len(query_filters) > 1:
                aggregation_spec["query"] = {
                    "bool": {
                        "must": query_filters,
                        "must_not": [],
                        "should": [],
                    }
                }
            else:
                aggregation_spec["query"] = query_filters[0]

        return aggregation_spec

    def format_field_by_type(self, field_name):
        """Format field name based on mapping type.

        For text fields we need to use .keyword because text fields are not
        available to aggregations per default.

        For all other types using the field name as is works.

        Args:
            field_name (str): Name of the field.

        Returns:
            Field name as string formatted after mapping type.
        """
        # Default field format is just the name unchanged.
        field_format = field_name
        field_type = None

        indices = self.indices
        if isinstance(indices, (list, tuple)):
            indices = ",".join(indices)

        # Get the mapping for the field.
        try:
            mapping = self.opensearch.client.indices.get_field_mapping(
                index=indices, fields=field_name
            )
        except opensearchpy.NotFoundError:
            mapping = {}

        # The returned structure is nested so we need to unpack it.
        # Example:
        # {'<INDEX NAME>': {
        #     'mappings': {
        #         'inode': {
        #             'full_name': 'inode',
        #             'mapping': {
        #                 'inode': {
        #                     'type': 'long'
        #                 }
        #             }
        #         }
        #     }
        # }}
        for value in mapping.values():
            mappings = value.get("mappings", {})
            mapping = mappings.get(field_name, {}).get("mapping", {})
            field_type = mapping.get(field_name, {}).get("type", None)
            if field_type:
                break

        if field_type == "text":
            field_format = f"{field_name}.keyword"

        return field_format

    def opensearch_aggregation(self, aggregation_spec):
        """Helper method to execute aggregation in OpenSearch.

        Args:
            aggregation_spec: Dict with OpenSearch aggregation spec.

        Returns:
            OpenSearch aggregation result.
        """
        # pylint: disable=unexpected-keyword-arg, no-value-for-parameter

        try:
            aggregation = self.opensearch.client.search(
                index=self.indices, body=aggregation_spec, size=0
            )
        except opensearchpy.NotFoundError:
            logger.error("Unable to find indices: {0:s}".format(",".join(self.indices)))
            raise
        return aggregation

    def run(self, *args, **kwargs):
        """Entry point for the aggregator."""
        raise NotImplementedError
