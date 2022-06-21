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
"""Vega Spec aggregation.

This file provides a manual vega spec aggregator. This is useful for
analyzers that generate specific vega specs (or altair charts) that
are not yet supported by other aggregators and/or charts. This can
also be used by those manually generating charts in notebooks.

This aggregator is not useful for UI and therefore is "hidden" from
views.
"""
from __future__ import unicode_literals

import altair as alt
import pandas as pd

from timesketch.lib.aggregators import manager
from timesketch.lib.aggregators import interface


class VegaResult:
    """Result object for manual vega specification aggregations.

    Attributes:
        chart_type: Chart type to render, defaults to "table".
    """

    def __init__(self, spec):
        """Initialize the object.

        Args:
            spec: dict with the vega specification.
        """

        self.chart_type = "manual_vega"
        self._spec = spec

    # pylint: disable=unused-argument
    def to_dict(self, encoding=False):
        """Encode aggregation result as dict.

        Args:
            encoding: Boolean indicating if encoding info should be returned.

        Returns:
            Dict with aggregation result.
        """
        datasets = self._spec.get("datasets", {})
        values = []

        for dataset in datasets.values():
            values.extend(list(dataset))

        return {"values": values}

    def to_pandas(self):
        """Encode aggregation result as a pandas dataframe.

        Returns:
            Pandas dataframe with aggregation results.
        """
        return pd.DataFrame()

    # pylint: disable=unused-argument
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

        # Create an empty chart and then fill it with the spec.
        chart = alt.Chart(pd.DataFrame())
        chart = chart.from_dict(self._spec)

        if interactive:
            chart = chart.interactive()

        if as_html:
            return chart.to_html()

        if as_chart:
            return chart

        return self._spec


class ManualVegaSpecAggregation(interface.BaseAggregator):
    """Manual Vega Spec Aggregation."""

    NAME = "manual_vega"
    DISPLAY_NAME = "Manual Vega-Spec Aggregation"
    DESCRIPTION = "Aggregating values of a user supplied vega-spec"

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
        return "Results From A Manual Vega Spec"

    # pylint: disable=arguments-differ
    def run(self, data, title="", **kwargs):
        """Run the aggregation.

        Args:
            data: dict with the vega specification for the chart.
            title: string with the aggregation title.

        Returns:
            Instance of interface.AggregationResult with aggregation result.

        Raises:
            ValueError: data is not supplied.
        """
        if not data:
            raise ValueError("Data is missing")

        if not isinstance(data, dict):
            raise ValueError("Supplied data needs to be a dict.")

        self.title = title
        return VegaResult(data)


manager.AggregatorManager.register_aggregator(
    ManualVegaSpecAggregation, exclude_from_list=True
)
