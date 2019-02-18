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

from __future__ import unicode_literals

from flask import current_app
from elasticsearch import Elasticsearch

from timesketch.lib.aggregators import manager
from timesketch.models.sketch import Sketch as SQLSketch


class AggregationResult(object):

    def __init__(self, encoding, values):
        self.encoding = encoding
        self.values = values

    def _get_chart(self, chart_name):
        chart_class = manager.ChartManager.get_chart(chart_name)
        return chart_class(data=self.to_dict())

    def to_dict(self):
        return dict(encoding=self.encoding, values=self.values)

    def to_vega_lite_spec(self, chart_name):
        chart = self._get_chart(chart_name)
        return chart.to_vega_lite_spec()

    def to_vega_lite_html(self, chart_name):
        chart = self._get_chart(chart_name)
        return chart.to_vega_lite_spec()


class BaseAggregator(object):
    """Base class for an aggregator."""

    NAME = 'name'
    FORM_FIELDS = {}
    SUPPORTED_CHARTS = frozenset()

    def __init__(self, sketch_id=None, index=None):
        """Initialize the aggregator object.

        Args:
            sketch_id: Sketch ID.
            index: List of elasticsearch index names.
        """
        if not sketch_id and not index:
            raise RuntimeError('Need at least sketch_id or index')

        self.sketch = SQLSketch.query.get(sketch_id)
        self.index = index

        if self.sketch and not index:
            active_timelines = self.sketch.active_timelines
            self.index = [t.searchindex.index_name for t in active_timelines]

    def run_es_aggregation(self, aggregation_dict):
        es_client = Elasticsearch(
            host=current_app.config['ELASTIC_HOST'],
            port=current_app.config['ELASTIC_PORT'])
        aggregation = es_client.search(
            index=self.index, body=aggregation_dict, size=0)
        return aggregation

    def run(self, *args, **kwargs):
        """Entry point for the aggregator."""
        raise NotImplementedError


class BaseChart(object):

    NAME = 'name'

    def __init__(self, data):
        self.name = self.NAME
        self.data = data
