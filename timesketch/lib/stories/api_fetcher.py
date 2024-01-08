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
"""This file contains the interface for a story exporter."""

from __future__ import unicode_literals

import json

from flask import current_app
import altair as alt
import pandas as pd

from timesketch.lib.stories import interface

from timesketch.lib.aggregators import manager as aggregator_manager
from timesketch.lib.datastores.opensearch import OpenSearchDataStore
from timesketch.models.sketch import Aggregation
from timesketch.models.sketch import AggregationGroup
from timesketch.models.sketch import Sketch
from timesketch.models.sketch import View


class ApiDataFetcher(interface.DataFetcher):
    """Data Fetcher for an API story exporter."""

    def __init__(self):
        """Initialize the data fetcher."""
        super().__init__()
        self._datastore = OpenSearchDataStore(
            host=current_app.config["OPENSEARCH_HOST"],
            port=current_app.config["OPENSEARCH_PORT"],
        )

    def get_aggregation(self, agg_dict):
        """Returns an aggregation object from an aggregation dict.

        Args:
            agg_dict (dict): a dictionary containing information
                about the stored aggregation.

        Returns:
            A dict with metadata information as well as the aggregation
            object (instance of AggregationResult) from a saved aggregation
            or an empty dict if not found.
        """
        aggregation_id = agg_dict.get("id")
        if not aggregation_id:
            return {}

        aggregation = Aggregation.get_by_id(aggregation_id)
        if not aggregation:
            return {}

        try:
            agg_class = aggregator_manager.AggregatorManager.get_aggregator(
                aggregation.agg_type
            )
        except KeyError:
            return {}

        if not agg_class:
            return pd.DataFrame()

        parameter_string = aggregation.parameters
        parameters = json.loads(parameter_string)
        parameter_index = parameters.pop("index", None)
        indices, timeline_ids = self.get_indices_and_timelines(parameter_index)
        aggregator = agg_class(
            sketch_id=self._sketch_id, indices=indices, timeline_ids=timeline_ids
        )

        _ = parameters.pop("supported_charts", None)
        chart_color = parameters.pop("chart_color", "N/A")
        chart_title = parameters.pop("chart_title", "N/A")

        data = {
            "aggregation": aggregator.run(**parameters),
            "name": aggregation.name,
            "description": aggregation.description,
            "agg_type": aggregation.agg_type,
            "parameters": parameters,
            "chart_type": aggregation.chart_type,
            "chart_title": chart_title,
            "chart_color": chart_color,
            "user": aggregation.user,
        }
        return data

    def get_aggregation_group(self, agg_dict):
        """Returns an aggregation object from an aggregation dict.

        Args:
            agg_dict (dict): a dictionary containing information
                about the stored aggregation.

        Returns:
            A dict that contains metadata about the aggregation group
            as well as a chart object (instance of altair.Chart)
            with the combined chart object from the group.
        """
        group_id = agg_dict.get("id")
        if not group_id:
            return None

        group = AggregationGroup.get_by_id(group_id)
        if not group:
            return None

        orientation = group.orientation

        result_chart = None
        for aggregator in group.aggregations:
            if aggregator.parameters:
                aggregator_parameters = json.loads(aggregator.parameters)
            else:
                aggregator_parameters = {}

            agg_class = aggregator_manager.AggregatorManager.get_aggregator(
                aggregator.agg_type
            )
            if not agg_class:
                continue

            parameter_index = aggregator_parameters.pop("index", None)
            indices, timeline_ids = self.get_indices_and_timelines(parameter_index)
            aggregator_obj = agg_class(
                sketch_id=self._sketch_id, indices=indices, timeline_ids=timeline_ids
            )
            chart_type = aggregator_parameters.pop("supported_charts", None)
            color = aggregator_parameters.pop("chart_color", "")
            chart_title = aggregator_parameters.pop("chart_title", None)
            result_obj = aggregator_obj.run(**aggregator_parameters)

            title = chart_title or aggregator_obj.chart_title

            chart = result_obj.to_chart(
                chart_name=chart_type,
                chart_title=title,
                as_chart=True,
                interactive=True,
                color=color,
            )

            if result_chart is None:
                result_chart = chart
            elif orientation == "horizontal":
                result_chart = alt.hconcat(chart, result_chart)
            elif orientation == "vertical":
                result_chart = alt.vconcat(chart, result_chart)
            else:
                result_chart = alt.layer(chart, result_chart)

        data = {
            "name": group.name,
            "description": group.description,
            "chart": result_chart,
            "parameters": group.parameters,
            "orientation": group.orientation,
            "user": group.user,
        }
        return data

    def get_indices_and_timelines(self, index_list):
        """Returns a tuple with two lists from indices and timeline IDs.

        Args:
            index_list (list): A list of timeline IDs (int) and
                indices (str).

        Returns:
            A tuple with two items, a list of indices and a list of
            timeline IDs.
        """
        indices = []
        timeline_ids = []

        if isinstance(index_list, str):
            index_list = index_list.split(",")

        for index in index_list:
            if isinstance(index, str):
                indices.append(index)
            if isinstance(index, int):
                timeline_ids.append(index)

        return indices, timeline_ids

    def get_view(self, view_dict):
        """Returns a data frame from a view dict.

        Args:
            view_dict (dict): a dictionary containing information
                about the stored view.

        Returns:
            A pandas DataFrame with the results from a view aggregation.
        """
        view_id = view_dict.get("id")
        if not view_id:
            return pd.DataFrame()

        view = View.get_by_id(view_id)
        if not view:
            return pd.DataFrame()

        if not view.query_string and not view.query_dsl:
            return pd.DataFrame()

        query_filter = view.query_filter
        if query_filter and isinstance(query_filter, str):
            query_filter = json.loads(query_filter)
        elif not query_filter:
            query_filter = {"indices": "_all", "size": 100}

        if view.query_dsl:
            query_dsl = json.loads(view.query_dsl)
        else:
            query_dsl = None

        sketch = Sketch.get_with_acl(self._sketch_id)
        sketch_indices = [t.searchindex.index_name for t in sketch.active_timelines]

        results = self._datastore.search_stream(
            sketch_id=self._sketch_id,
            query_string=view.query_string,
            query_filter=query_filter,
            query_dsl=query_dsl,
            indices=sketch_indices,
        )
        result_list = [x.get("_source") for x in results]
        return pd.DataFrame(result_list)
