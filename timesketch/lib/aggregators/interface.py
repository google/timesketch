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

    def __init__(self, encoding, values):
        self.encoding = encoding
        self.values = values

    def to_dict(self):
        return dict(encoding=self.encoding, values=self.values)

    def to_chart(self, chart_name):
        chart = manager.ChartManager.get_chart(chart_name)
        chart = chart.generate(data=self.to_dict())
        return chart.to_dict()


class BaseAggregator(object):
    """Base class for an aggregator."""

    NAME = 'name'
    FORM_FIELDS = {}
    SUPPORTED_CHARTS = frozenset()

    def __init__(self, sketch_id=None, indices=None):
        """Initialize the aggregator object.

        Args:
            sketch_id: Sketch ID.
            indices: List of elasticsearch index names.
        """
        if not sketch_id and not indices:
            raise RuntimeError('Need at least sketch_id or index')

        self.sketch = None
        self.indices = indices

        if sketch_id:
            self.sketch = interface.Sketch(sketch_id=sketch_id)

        if self.sketch and not indices:
            self.indices = self.sketch.get_all_indices()

    def run_es_aggregation(self, aggregation_dict):
        es_client = Elasticsearch(
            host=current_app.config['ELASTIC_HOST'],
            port=current_app.config['ELASTIC_PORT'])
        aggregation = es_client.search(
            index=self.indices, body=aggregation_dict, size=0)
        return aggregation

    def run(self, *args, **kwargs):
        """Entry point for the aggregator."""
        return self.run_wrapper(*args, **kwargs)

    def run_wrapper(self, *args, **kwargs):
        raise NotImplementedError


class BaseChart(object):

    NAME = 'name'

    def __init__(self):
        self.name = self.NAME
