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
from timesketch.lib.analyzers import interface


class AggregationResult(object):

    def __init__(self, encoding):
        self._encoding = encoding
        self._values = []

    def append(self, value):
        self._values.append(value)

    def to_dict(self):
        return dict(encoding=self._encoding, values=self._values)

    @property
    def encoding(self):
        return self._encoding

    @property
    def values(self):
        return dict(values=self._values)


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

        self.sketch = None
        self.index = None

        if sketch_id:
            self.sketch = interface.Sketch(sketch_id=sketch_id)

        if isinstance(index, (list, tuple)):
            self.index = index

        if isinstance(index, (str, unicode)):
            self.index = [index]

        if self.sketch and not index:
            self.index = self.sketch.get_all_indices()

        self.cached_result = None

    def get_form_input(self):
        return self.FORM_FIELDS

    def run_es_query(self, aggregation_dict):
        es_client = Elasticsearch(
            host=current_app.config['ELASTIC_HOST'],
            port=current_app.config['ELASTIC_PORT'])
        result = es_client.search(
            index=self.index, body=aggregation_dict, size=0)
        return result

    def to_chart(self, chart_name):
        chart = manager.ChartManager.get_chart(chart_name)
        chart = chart.generate(data=self.cached_result)
        return chart.to_html()

    def to_dict(self):
        return dict(values=self.cached_result.values)

    def run(self, *args, **kwargs):
        """Entry point for the aggregator."""
        self.cached_result = self.run_wrapper(*args, **kwargs)

    def run_wrapper(self, *args, **kwargs):
        raise NotImplementedError


class BaseChart(object):

    NAME = 'name'

    def __init__(self):
        self.name = self.NAME
