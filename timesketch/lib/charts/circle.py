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
"""Circle chart class.."""

from __future__ import unicode_literals

import altair as alt

from timesketch.lib.charts import manager
from timesketch.lib.charts import interface


class CircleChart(interface.BaseChart):
    """Circlechart object."""

    NAME = "circlechart"

    def generate(self):
        """Generate the chart.

        Returns:
            Instance of altair.Chart
        """
        chart = self._get_chart_with_transform()
        self._add_url_href(self.encoding)

        if self.chart_title:
            chart = chart.mark_circle(filled=True, size=100).properties(
                title=self.chart_title
            )
        else:
            chart = chart.mark_circle(filled=True, size=100)
        field = self.encoding.get("y", {}).get("field", "count")
        color = alt.Color(field=field, type="quantitative")
        chart.encoding = alt.FacetedEncoding.from_dict(self.encoding)
        chart.encoding.color = color
        return chart


manager.ChartManager.register_chart(CircleChart)
