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
"""Interface for charts."""

import logging
from typing import Any, Dict, List, Optional, Union

import altair as alt
import pandas as pd

logger = logging.getLogger(__name__)


class BaseChart:
    """Base class for a chart."""

    # Name that the chart will be registered as.
    NAME = "name"

    def __init__(
        self,
        data: Dict[str, Union[pd.DataFrame, List[Dict[str, Any]]]],
        title: str = "",
        sketch_url: str = "",
        field: str = "",
        extra_query_url: str = "",
        aggregation_id: Optional[int] = None,
    ):
        """Initialize the chart object.

        Args:
            data: A dictionary containing:
                - 'values': A pandas DataFrame or a list of dictionaries
                    representing the chart data.
                - 'encoding': A dictionary with Vega-Lite encoding information.
            title: String used for the chart title.
            sketch_url: Sketch URL for rendering href links.
            field: The field used to generate search terms for URL.
            extra_query_url: For Chart URL transformation. If provided an extra
                condition will be added to URL transformations in the query
                field.
            aggregation_id: Integer with the aggregation ID.

        Raises:
            RuntimeError: If 'values' is None or 'encoding' is empty in the data
                dictionary.
                The error message now includes types and emptiness status for
                debugging.

        Logs:
            A warning if the chart is initialized with an empty pandas DataFrame,
            indicating that no data will be rendered.
        """
        _values = data.get("values")
        _encoding = data.get("encoding")

        if _values is None or not _encoding:
            error_message = (
                f"Values and/or Encoding missing from data. "
                f"Values type: {type(_values).__name__}, "
                f"empty: {not bool(_values)}. "
                f"Encoding type: {type(_encoding).__name__}, "
                f"empty: {not bool(_encoding)}."
            )
            raise RuntimeError(error_message)

        self.name = self.NAME
        self.chart_title = title
        if isinstance(_values, pd.DataFrame):
            self.values = _values
        else:
            self.values = pd.DataFrame(_values)

        if self.values.empty:
            logger.warning(
                "Chart '%s' ('%s') was created with an empty DataFrame.",
                self.name,
                self.chart_title,
            )

        self.encoding = _encoding

        self._aggregation_id = aggregation_id
        self._extra_query_url = extra_query_url
        self._field = field
        self._sketch_url = sketch_url

    def _get_chart_with_transform(self):
        """Returns a chart object potentially with a URL transform added to it.

        Returns:
            A LayerChart object, either with added transform or not, depending
            on whether sketch URL and field are set.
        """
        data = self.values
        # We need to convert the dataframe to a dict to avoid issues with
        # newer versions of pandas and older versions of altair.
        # See https://github.com/altair-viz/altair/issues/2763
        if isinstance(data, pd.DataFrame):
            data = data.to_dict(orient="records")

        if not isinstance(data, list):
            logger.error(
                "Chart data is not in a supported format. "
                "Expected pandas DataFrame or list, got %s",
                type(data),
            )
            data = []

        chart = alt.Chart(data)

        if not self._sketch_url or not self._field:
            return chart

        datum = getattr(alt.datum, self._field)
        if self._aggregation_id:
            agg_string = f"a={self._aggregation_id:d}&"
        else:
            agg_string = ""

        # Construct Vega-Lite expression
        # usage: url + datum.field + '" ' + extra
        url = f'{self._sketch_url:s}?{agg_string:s}q={self._field:s}:"'
        return chart.transform_calculate(
            url=url + datum + '" ' + self._extra_query_url
        )  # pylint: disable=line-too-long

    def _add_url_href(self, encoding):
        """Adds a HREF reference to encoding dict if needed.

        Args:
            encoding: a dict with encoding information.
        """
        if not self._sketch_url:
            return
        if not self._field:
            return
        encoding["href"] = {"field": "url", "type": "nominal"}

    def generate(self):
        """Entry point for the chart."""
        raise NotImplementedError

    def set_color(self, color):
        """Sets a color value for the chart.

        Args:
            color: a string with the color name to be added.
        """
        self.values["color"] = color
        self.encoding["color"] = {"type": "nominal", "field": "color", "scale": None}
