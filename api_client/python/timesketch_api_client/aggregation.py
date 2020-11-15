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
import getpass
import json
import logging

import altair
import pandas

from . import error
from . import resource


logger = logging.getLogger('timesketch_api.aggregation')


class Aggregation(resource.BaseResource):
    """Aggregation object.

    Attributes:
        aggregator_name: name of the aggregator class used to
            generate the aggregation.
        chart_color: the color of the chart.
        chart_type: the type of chart that will be generated
            from this aggregation object.
        type: the type of aggregation object.
        view: a view ID if the aggregation is tied to a specific view.
    """

    def __init__(self, sketch, api):
        self._sketch = sketch
        self._aggregator_data = {}
        self._labels = []
        self._username = ''
        self._parameters = {}
        self.aggregator_name = ''
        self.chart_color = ''
        self.chart_type = ''
        self.chart_title = ''
        self.view = None
        self.type = None
        resource_uri = 'sketches/{0:d}/aggregation/explore/'.format(sketch.id)
        super().__init__(api, resource_uri)

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
        self.chart_color = parameters.get('chart_color', '')
        self._parameters = parameters

        form_data = {
            'aggregator_name': aggregator_name,
            'aggregator_parameters': parameters,
            'chart_type': chart_type,
            'view_id': view_id,
        }

        response = self.api.session.post(resource_url, json=form_data)
        if not error.check_return_status(response, logger):
            error.error_message(
                response, message='Unable to query results', error=ValueError)

        return error.get_response_json(response, logger)

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

        label_string = data.get('label_string', '')
        if label_string:
            self._labels = json.loads(label_string)
        else:
            self._labels = []

        chart_type = data.get('chart_type')
        param_string = data.get('parameters', '')
        if param_string:
            parameters = json.loads(param_string)
        else:
            parameters = {}

        self._parameters = parameters

        self._username = data.get('user', {}).get('username', 'System')
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
        self._username = getpass.getuser()
        self.type = 'DSL'

        form_data = {
            'aggregation_dsl': aggregate_dsl,
        }

        response = self.api.session.post(resource_url, json=form_data)
        if not error.check_return_status(response, logger):
            error.error_message(
                response, message='Unable to query results', error=ValueError)

        self.resource_data = error.get_response_json(response, logger)

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
        self._username = getpass.getuser()

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
    def parameters(self):
        """Property that returns the parameters of the aggregation."""
        return self._parameters

    @property
    def user(self):
        """Property that returns the username of who ran the aggregation."""
        if not self._username:
            return 'System'
        return self._username

    @property
    def title(self):
        """Property that returns the chart title of an aggregation."""
        if self.chart_title:
            return self.chart_title

        data = self.lazyload_data()
        meta = data.get('meta', {})
        self.chart_title = meta.get('vega_chart_title', '')

        return self.chart_title

    @title.setter
    def title(self, new_title):
        """Set the chart title of an aggregation."""
        self.chart_title = new_title

    @property
    def chart(self):
        """Property that returns an altair Vega-lite chart."""
        return self.generate_chart()

    @property
    def description(self):
        """Property that returns the description string."""
        return self._aggregator_data.get('description', '')

    @description.setter
    def description(self, description):
        """Set the description of an aggregation."""
        self._aggregator_data['description'] = description

    @property
    def id(self):
        """Property that returns the ID of the aggregator, if possible."""
        agg_id = self._aggregator_data.get('id')
        if agg_id:
            return agg_id

        return 0

    @property
    def labels(self):
        """Property that returns a list of the aggregation labels."""
        return self._labels

    @property
    def name(self):
        """Property that returns the name of the aggregation."""
        name = self._aggregator_data.get('name')
        if name:
            return name
        return self.aggregator_name

    @name.setter
    def name(self, name):
        """Set the name of the aggregation."""
        self._aggregator_data['name'] = name

    @property
    def dict(self):
        """Property that returns back a Dict with the results."""
        return self.to_dict()

    @property
    def table(self):
        """Property that returns a pandas DataFrame."""
        return self.to_pandas()

    def add_label(self, label):
        """Add a label to the aggregation.

        Args:
            label (str): string with the label information.
        """
        if label in self._labels:
            return
        self._labels.append(label)
        self.save()

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

    def save(self):
        """Save the aggregation in the database."""
        data = {
            'name': self.name,
            'description': self.description,
            'agg_type': self.aggregator_name,
            'parameters': self._parameters,
            'chart_type': self.chart_type,
        }
        if self.view:
            data['view_id'] = self.view
        if self._labels:
            data['labels'] = json.dumps(self._labels)

        if self.id:
            resource_url = '{0:s}/sketches/{1:d}/aggregation/{2:d}/'.format(
                self.api.api_root, self._sketch.id, self.id)
        else:
            resource_url = '{0:s}/sketches/{1:d}/aggregation/'.format(
                self.api.api_root, self._sketch.id)

        response = self.api.session.post(resource_url, json=data)
        if not error.check_return_status(response, logger):
            return 'Unable to save the aggregation'

        response_json = response.json()
        objects = response_json.get('objects')
        if not objects:
            return 'Unable to determine ID of saved object.'
        agg_data = objects[0]
        self._aggregator_data = agg_data
        return 'Saved aggregation to ID: {0:d}'.format(self.id)


class AggregationGroup(resource.BaseResource):
    """Aggregation Group object.

    Attributes:
        id: the ID of the group.
    """

    def __init__(self, sketch, api):
        """Initialize the aggregation group."""
        resource_uri = 'sketches/{0:d}/aggregation/group/'.format(
            sketch.id)
        super().__init__(api, resource_uri)

        self.id = None
        self._name = 'N/A'
        self._description = 'N/A'
        self._orientation = ''
        self._parameters = {}
        self._sketch = sketch
        self._aggregations = []

    def __str__(self):
        """Return a string representation of the group."""
        return '[{0:d}] {1:s} - {2:s}'.format(
            self.id, self._name, self._description)

    @property
    def chart(self):
        """Property that returns an altair Vega-lite chart."""
        if not self._aggregations:
            return altair.Chart()
        return self.generate_chart()

    @property
    def description(self):
        """Returns the description of the aggregation group."""
        return self._description

    @description.setter
    def description(self, description):
        """Sets the description of the aggregation group."""
        self._description = description
        self.save()

    @property
    def name(self):
        """Returns the name of the aggregation group."""
        return self._name

    @name.setter
    def name(self, name):
        """Sets the name of the aggregation group."""
        self._name = name
        self.save()

    @property
    def orientation(self):
        """Returns the chart orientation."""
        return self._orientation

    @orientation.setter
    def orientation(self, orientation):
        """Sets the chart orientation."""
        self._orientation = orientation
        self.save()

    @property
    def parameters(self):
        """Returns a dict with the group parameters."""
        return self._parameters

    @parameters.setter
    def parameters(self, parameters):
        """Sets the group parameters."""
        self._parameters = parameters
        self.save()

    @property
    def table(self):
        """Property that returns a pandas DataFrame."""
        return self.to_pandas()

    def delete(self):
        """Deletes the group from the store."""
        if not self.id:
            return False

        response = self.api.session.delete(
            '{0:s}/{1:s}'.format(self.api.api_root, self.resource_uri))

        return error.check_return_status(response, logger)

    def from_dict(self, group_dict):
        """Feed group data from a dictionary.

        Args:
            group_dict (dict): a dictionary with the aggregation group
                information.

        Raises:
            TypeError: if the dictionary does not contain the correct
                information.
        """
        group_id = group_dict.get('id')
        if not group_id:
            raise TypeError('Group ID is missing.')
        self.id = group_id
        self.resource_uri = 'sketches/{0:d}/aggregation/group/{1:d}/'.format(
            self._sketch.id, group_id)

        self._name = group_dict.get('name', '')
        self._description = group_dict.get('description', '')

        self._orientation = group_dict.get('orientation')
        if not self._orientation:
            raise TypeError('How a group is connected needs to be defined.')

        parameter_string = group_dict.get('parameters', '')
        if parameter_string:
            self._parameters = json.loads(parameter_string)

        aggs = group_dict.get('agg_ids')
        if not aggs:
            raise TypeError('Group contains no aggregations')

        aggs = json.loads(aggs)
        if not isinstance(aggs, (list, tuple)):
            raise TypeError('Aggregations need to be a list.')

        self._aggregations = []
        for agg_id in aggs:
            agg_obj = Aggregation(self._sketch, self.api)
            agg_obj.from_store(agg_id)
            self._aggregations.append(agg_obj)

    def from_store(self, group_id):
        """Feed group data from a group ID.

        Args:
            group_id (int): the group ID to fetch from the store.

        Raises:
            TypeError: if the group ID does not exist.
        """
        self.id = group_id
        resource_uri = 'sketches/{0:d}/aggregation/group/'.format(
            self._sketch.id)
        resource_data = self.api.fetch_resource_data(resource_uri)
        for group_dict in resource_data.get('objects', []):
            group_dict_id = group_dict.get('id')
            if not group_dict_id:
                continue
            if group_dict_id == group_id:
                self.from_dict(group_dict)
                return
        raise TypeError('Group ID not found.')

    def generate_chart(self):
        """Returns an altair Vega-lite chart."""
        if not self._aggregations:
            return altair.Chart()

        data = self.lazyload_data()

        meta = data.get('meta', {})
        vega_spec = meta.get('vega_spec')

        if not vega_spec:
            return altair.Chart(pandas.DataFrame()).mark_point()

        vega_spec_string = json.dumps(vega_spec)
        return altair.Chart.from_json(vega_spec_string)

    def get_charts(self):
        """Returns a list of altair Chart objects from each aggregation."""
        return [x.chart for x in self._aggregations]

    def get_tables(self):
        """Returns a list of pandas DataFrame from each aggregation."""
        return [x.table for x in self._aggregations]

    def save(self):
        """Save the aggregation group in the database."""
        if not self._aggregations:
            return False

        data = {
            'name': self._name,
            'description': self._description,
            'parameters': json.dumps(self._parameters),
            'aggregations': json.dumps([x.id for x in self._aggregations]),
            'orientation': self._orientation,
        }

        if self.id:
            res_url = '{0:s}/sketches/{1:d}/aggregation/group/{2:d}/'.format(
                self.api.api_root, self._sketch.id, self.id)
        else:
            res_url = '{0:s}/sketches/{1:d}/aggregation/group/'.format(
                self.api.api_root, self._sketch.id)

        response = self.api.session.post(res_url, json=data)
        _ = self.lazyload_data(refresh_cache=True)
        return error.check_return_status(response, logger)

    def to_pandas(self):
        """Returns a pandas DataFrame.

        Aggregation groups are meant for charts, not data frames. However
        there are situations where you may want to be able to produce
        a DataFrame, and in that case all DataFrame objects from each
        aggregation are concatenated to return a single one.

        Returns:
            A single DataFrame that consists of a DataFrame from each
            aggregation in the group concatenated.
        """
        if not self._aggregations:
            return pandas.DataFrame()

        data_frames = []
        for agg_obj in self._aggregations:
            data_frames.append(agg_obj.to_pandas())

        return pandas.concat(data_frames)
