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

import pandas

from timesketch.lib.charts import manager as chart_manager
from timesketch.models.sketch import Sketch as SQLSketch


class AggregationResult(object):
    """Result object for aggregations.

    Attributes:
        encoding: Dict with Vega-Lite encoding information.
        values: List of dicts with aggregation data.
    """

    def __init__(self, encoding, values):
        """Initialize the object.

        Args:
            encoding: Dict with Vega-Lite encoding information.
            values: List of dicts with aggregation data.
        """
        self.encoding = encoding
        self.values = values

    def to_dict(self, encoding=False):
        """Encode aggregation result as dict.

        Args:
            encoding: Boolean indicating if encoding info should be returned.

        Returns:
            Dict with aggregation result.
        """
        aggregation_data = dict(values=self.values)
        if encoding:
            aggregation_data['encoding'] = self.encoding
        return aggregation_data

    def to_pandas(self):
        """Encode aggregation result as a pandas dataframe.

        Returns:
            Pandas dataframe with aggregation results.
        """
        return pandas.DataFrame(self.values)

    def to_chart(self, chart_name, as_html=False):
        """Encode aggregation result as Vega-Lite chart.

        Args:
            chart_name: Name of chart as string.
            as_html: Boolean indicating if chart should be returned in HTML.
        """
        chart_class = chart_manager.ChartManager.get_chart(chart_name)
        chart = chart_class(data=self.to_dict(encoding=True)).generate()
        if as_html:
            return chart.to_html()
        return chart.to_dict()


class BaseAggregator(object):
    """Base class for an aggregator."""

    NAME = 'name'

    # Used as hints to the frontend UI in order to render input forms.
    FORM_FIELDS = {}

    # List of supported chart types.
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
        self.elastic = Elasticsearch(
            host=current_app.config['ELASTIC_HOST'],
            port=current_app.config['ELASTIC_PORT'])

        if not self.index:
            active_timelines = self.sketch.active_timelines
            self.index = [t.searchindex.index_name for t in active_timelines]

    def elastic_aggregation(self, aggregation_spec):
        """Helper method to execute aggregation in Elasticsearch.

        Args:
            aggregation_spec: Dict with Elasticsearch aggregation spec.

        Returns:
            Elasticsearch aggregation result.
        """
        # pylint: disable=unexpected-keyword-arg
        aggregation = self.elastic.search(
            index=self.index, body=aggregation_spec, size=0)
        return aggregation

    def run(self, *args, **kwargs):
        """Entry point for the aggregator."""
        raise NotImplementedError
