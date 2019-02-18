from __future__ import unicode_literals

import altair as alt

from timesketch.lib.aggregators import manager
from timesketch.lib.aggregators import interface


class BarChart(interface.BaseChart):

    NAME = 'barchart'

    def __init__(self, data):
        super(BarChart, self).__init__(data)

    def to_vega_lite_spec(self):
        chart = alt.Chart(self.data.values).mark_bar()
        chart.encoding = alt.Encoding.from_dict(self.data.encoding)
        return chart

    def to_vega_lite_html(self):
        chart = alt.Chart(self.data.values).mark_bar()
        chart.encoding = alt.Encoding.from_dict(self.data.encoding)
        return chart.to_html()


class HorizontalBarChart(interface.BaseChart):

    NAME = 'h_barchart'

    def __init__(self):
        super(HorizontalBarChart, self).__init__()

    @staticmethod
    def generate(data):

        encoding = data.encoding.copy()
        encoding['x'] = data.encoding['y']
        encoding['y'] = data.encoding['x']

        bars = alt.Chart(data.values).mark_bar()
        bars.encoding = alt.Encoding.from_dict(encoding)

        text = bars.mark_text(align='left', baseline='middle', dx=3).encode(
            text='{0:s}:{1:s}'.format(
                encoding['x']['field'], encoding['x']['type']))

        chart = (bars + text)
        return chart


manager.ChartManager.register_chart(BarChart)
manager.ChartManager.register_chart(HorizontalBarChart)
