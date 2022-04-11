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

from __future__ import unicode_literals

import altair as alt
import pandas as pd


class BaseChart(object):
    """Base class for a chart."""

    # Name that the chart will be registered as.
    NAME = "name"

    def __init__(
        self,
        data,
        title="",
        sketch_url="",
        field="",
        extra_query_url="",
        aggregation_id=None,
    ):
        """Initialize the chart object.

        Args:
            data: Dictionary with list of values and dict of encoding info.
            title: String used for the chart title.
            sketch_url: Sketch URL for rendering href links.
            field: The field used to generate search terms for URL.
            extra_query_url: For Chart URL transformation. If provided an extra
                condition will be added to URL transformations in the query
                field.
            aggregation_id: Integer with the aggregation ID.

        Raises:
            RuntimeError if values or encoding is missing from data.
        """
        _values = data.get("values")
        _encoding = data.get("encoding")

        if _values is None or not _encoding:
            raise RuntimeError("Values and/or Encoding missing from data")

        self.name = self.NAME
        if isinstance(_values, pd.DataFrame):
            self.values = _values
        else:
            self.values = pd.DataFrame(_values)

        self.encoding = _encoding
        self.chart_title = title

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
        chart = alt.Chart(self.values)
        if not self._sketch_url:
            return chart

        if not self._field:
            return chart

        datum = getattr(alt.datum, self._field)
        if self._aggregation_id:
            agg_string = "a={0:d}&".format(self._aggregation_id)
        else:
            agg_string = ""
        url = '{0:s}?{1:s}q={2:s}:"'.format(self._sketch_url, agg_string, self._field)
        return chart.transform_calculate(url=url + datum + '" ' + self._extra_query_url)

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
