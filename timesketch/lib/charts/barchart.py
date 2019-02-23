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
"""Barcharts."""

from __future__ import unicode_literals

import altair as alt

from timesketch.lib.charts import manager
from timesketch.lib.charts import interface


class BarChart(interface.BaseChart):

    NAME = 'barchart'

    def __init__(self, data):
        super(BarChart, self).__init__(data)

    def generate(self):
        chart = alt.Chart(self.values).mark_bar()
        chart.encoding = alt.Encoding.from_dict(self.encoding)
        return chart


class HorizontalBarChart(interface.BaseChart):

    NAME = 'hbarchart'

    def __init__(self, data):
        super(HorizontalBarChart, self).__init__(data)

    def generate(self):

        encoding = self.encoding.copy()
        encoding['x'] = self.encoding['y']
        encoding['y'] = self.encoding['x']

        bars = alt.Chart(self.values).mark_bar()
        bars.encoding = alt.Encoding.from_dict(encoding)

        text = bars.mark_text(align='left', baseline='middle', dx=3).encode(
            text='{0:s}:{1:s}'.format(
                encoding['x']['field'], encoding['x']['type']))

        chart = (bars + text)
        return chart


manager.ChartManager.register(BarChart)
manager.ChartManager.register(HorizontalBarChart)
