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
"""Timesketch API client library."""
from __future__ import unicode_literals

import json

import altair
import pandas

from . import error
from . import resource


class Aggregation(resource.BaseResource):
    """Aggregation object.

    Attributes:
        aggregator_name: name of the aggregator class used to
            generate the aggregation.
        chart_type: the type of chart that will be generated
            from this aggregation object.
        type: the type of aggregation object.
        view: a view ID if the aggregation is tied to a specific view.
    """

    def __init__(
            self, sketch, api):
        self._sketch = sketch
        self._aggregator_data = {}
        self._parameters = {}
        self.aggregator_name = ''
        self.chart_type = ''
        self.view = None
        self.type = None
        resource_uri = 'sketches/{0:d}/aggregation/explore/'.format(sketch.id)
        super(Aggregation, self).__init__(api, resource_uri)

    def _get_aggregation_buckets(self, entry, name=''):
        """Yields all buckets from an aggregation result object.

        Args:
            entry: result dict from an aggregation request.
            name: name of aggregation results that contains
                all aggregation buckets.

        Yields:
            A dict with each aggregation bucket as well as
            the bucket_name.
        """
        if 'buckets' in entry:
            for bucket in entry.get('buckets', []):
                bucket['bucket_name'] = name
                yield bucket
        else:
            for key, value in iter(entry.items()):
                if not isinstance(value, dict):
                    continue
                for bucket in self._get_aggregation_buckets(
                        value, name=key):
                    yield bucket

    def _run_aggregator(
            self, aggregator_name, parameters, view_id=None, chart_type=None):
        """Run an aggregator class.

        Args:
            aggregator_name: the name of the aggregator class.
            parameters: a dict with the parameters for the aggregation class.
            view_id: an optional integer value with a primary key to a view.
            chart_type: string with the chart type.

        Returns:
            A dict with the aggregation results.
        """
        resource_url = '{0:s}/sketches/{1:d}/aggregation/explore/'.format(
            self.api.api_root, self._sketch.id)

        if chart_type is None and parameters.get('supported_charts'):
            chart_type = parameters.get('supported_charts')
            if isinstance(chart_type, (list, tuple)):
                chart_type = chart_type[0]

        if chart_type:
            self.chart_type = chart_type

        if view_id:
            self.view = view_id

        self.aggregator_name = aggregator_name

        form_data = {
            'aggregator_name': aggregator_name,
            'aggregator_parameters': parameters,
            'chart_type': chart_type,
            'view_id': view_id,
        }

        response = self.api.session.post(resource_url, json=form_data)
        if response.status_code != 200:
            error.error_message(
                response, message='Unable to query results', error=ValueError)

        return response.json()

    def from_store(self, aggregation_id):
        """Initialize the aggregation object from a stored aggregation.

        Args:
            aggregation_id: integer value for the stored
                aggregation (primary key).
        """
        resource_uri = 'sketches/{0:d}/aggregation/{1:d}/'.format(
            self._sketch.id, aggregation_id)
        resource_data = self.api.fetch_resource_data(resource_uri)
        data = resource_data.get('objects', [None])[0]
        if not data:
            return

        self._aggregator_data = data
        self.aggregator_name = data.get('agg_type')
        self.type = 'stored'

        chart_type = data.get('chart_type')
        param_string = data.get('parameters', '')
        if param_string:
            parameters = json.loads(param_string)
        else:
            parameters = {}

        self._parameters = parameters
        self.resource_data = self._run_aggregator(
            aggregator_name=self.aggregator_name, parameters=parameters,
            chart_type=chart_type)

    def from_explore(self, aggregate_dsl):
        """Initialize the aggregation object by running an aggregation DSL.

        Args:
            aggregate_dsl: Elasticsearch aggregation query DSL string.
        """
        resource_url = '{0:s}/sketches/{1:d}/aggregation/explore/'.format(
            self.api.api_root, self._sketch.id)

        self.aggregator_name = 'DSL'
        self.type = 'DSL'

        form_data = {
            'aggregation_dsl': aggregate_dsl,
        }

        response = self.api.session.post(resource_url, json=form_data)
        if response.status_code != 200:
            error.error_message(
                response, message='Unable to query results', error=ValueError)

        self.resource_data = response.json()

    def from_aggregator_run(
            self, aggregator_name, aggregator_parameters,
            view_id=None, chart_type=None):
        """Initialize the aggregation object by running an aggregator class.

        Args:
            aggregator_name: name of the aggregator class to run.
            aggregator_parameters: a dict with the parameters of the aggregator
                class.
            view_id: an optional integer value with a primary key to a view.
            chart_type: optional string with the chart type.
        """
        self.type = 'aggregator_run'
        self._parameters = aggregator_parameters
        self.resource_data = self._run_aggregator(
            aggregator_name, aggregator_parameters, view_id, chart_type)

    def lazyload_data(self, refresh_cache=False):
        """Load resource data once and cache the result.

        Args:
            refresh_cache: Boolean indicating if to update cache.

        Returns:
            Dictionary with resource data.
        """
        if self.resource_data and not refresh_cache:
            return self.resource_data

        # TODO: Implement a method to refresh cache.
        return self.resource_data

    @property
    def chart(self):
        """Property that returns an altair Vega-lite chart."""
        return self.generate_chart()

    @property
    def description(self):
        """Property that returns the description string."""
        return self._aggregator_data.get('description', '')

    @property
    def id(self):
        """Property that returns the ID of the aggregator, if possible."""
        agg_id = self._aggregator_data.get('id')
        if agg_id:
            return agg_id

        return -1

    @property
    def name(self):
        """Property that returns the name of the aggregation."""
        name = self._aggregator_data.get('name')
        if name:
            return name
        return self.aggregator_name

    @property
    def dict(self):
        """Property that returns back a Dict with the results."""
        return self.to_dict()

    @property
    def table(self):
        """Property that returns a pandas DataFrame."""
        return self.to_pandas()

    def to_dict(self):
        """Returns a dict."""
        entries = {}
        entry_index = 1
        data = self.lazyload_data()
        for entry in data.get('objects', []):
            for bucket in self._get_aggregation_buckets(entry):
                entries['entry_{0:d}'.format(entry_index)] = bucket
                entry_index += 1
        return entries

    def to_pandas(self):
        """Returns a pandas DataFrame."""
        panda_list = []
        data = self.lazyload_data()
        for entry in data.get('objects', []):
            for bucket in self._get_aggregation_buckets(entry):
                panda_list.append(bucket)
        return pandas.DataFrame(panda_list)

    def generate_chart(self):
        """Returns an altair Vega-lite chart."""
        if not self.chart_type:
            raise TypeError('Unable to generate chart, missing a chart type.')

        if not self._parameters.get('supported_charts'):
            self._parameters['supported_charts'] = self.chart_type

        data = self.lazyload_data()
        meta = data.get('meta', {})
        vega_spec = meta.get('vega_spec')

        if not vega_spec:
            return altair.Chart(pandas.DataFrame()).mark_point()

        vega_spec_string = json.dumps(vega_spec)
        return altair.Chart.from_json(vega_spec_string)
