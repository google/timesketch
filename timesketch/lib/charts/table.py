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
"""Table chart."""
import altair as alt

from timesketch.lib.charts import manager
from timesketch.lib.charts import interface


class TableChart(interface.BaseChart):
    """Table chart object."""

    NAME = "table"

    def generate(self):
        """Generate the chart.

        Returns:
            Instance of altair.Chart
        """
        # Only the data attribute is used for table rendering but we need the
        # mark to construct the chart.
        chart = alt.Chart().mark_bar()
        chart.data = self.values
        return chart


manager.ChartManager.register_chart(TableChart)
