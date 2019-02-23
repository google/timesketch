from __future__ import unicode_literals

import altair as alt

from timesketch.lib.aggregators import manager
from timesketch.lib.aggregators import interface


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


manager.ChartManager.register_chart(BarChart)
manager.ChartManager.register_chart(HorizontalBarChart)
