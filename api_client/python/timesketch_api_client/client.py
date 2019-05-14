# Copyright 2017 Google Inc. All rights reserved.
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
"""Timesketch API client."""
from __future__ import unicode_literals

import json
import uuid

# pylint: disable=wrong-import-order
import bs4
import requests

# pylint: disable=redefined-builtin
from requests.exceptions import ConnectionError
from timesketch.lib.charts import manager as chart_manager
import altair
import pandas
import numpy
from .definitions import HTTP_STATUS_CODE_20X


class TimesketchApi(object):
    """Timesketch API object

    Attributes:
        api_root: The full URL to the server API endpoint.
        session: Authenticated HTTP session.
    """

    def __init__(self,
                 host_uri,
                 username,
                 password,
                 verify=True,
                 auth_mode='timesketch'):
        """Initializes the TimesketchApi object.

        Args:
            host_uri: URI to the Timesketch server (https://<server>/).
            username: User username.
            password: User password.
            verify: Verify server SSL certificate.
            auth_mode: The authentication mode to use. Defaults to 'timesketch'
                Supported values are 'timesketch' (Timesketch login form) and
                'http-basic' (HTTP Basic authentication).
        """
        self._host_uri = host_uri
        self.api_root = '{0:s}/api/v1'.format(host_uri)
        try:
            self.session = self._create_session(
                username, password, verify=verify, auth_mode=auth_mode)
        except ConnectionError:
            raise ConnectionError('Timesketch server unreachable')

    def _authenticate_session(self, session, username, password):
        """Post username/password to authenticate the HTTP seesion.

        Args:
            session: Instance of requests.Session.
            username: User username.
            password: User password.
        """
        # Do a POST to the login handler to set up the session cookies
        data = {'username': username, 'password': password}
        session.post('{0:s}/login/'.format(self._host_uri), data=data)

    def _set_csrf_token(self, session):
        """Retrieve CSRF token from the server and append to HTTP headers.

        Args:
            session: Instance of requests.Session.
        """
        # Scrape the CSRF token from the response
        response = session.get(self._host_uri)
        soup = bs4.BeautifulSoup(response.text, features='html.parser')
        csrf_token = soup.find(id='csrf_token').get('value')

        session.headers.update({
            'x-csrftoken': csrf_token,
            'referer': self._host_uri
        })

    def _create_session(self, username, password, verify, auth_mode):
        """Create authenticated HTTP session for server communication.

        Args:
            username: User to authenticate as.
            password: User password.
            verify: Verify server SSL certificate.
            auth_mode: The authentication mode to use. Supported values are
                'timesketch' (Timesketch login form) and 'http-basic'
                (HTTP Basic authentication).

        Returns:
            Instance of requests.Session.
        """
        session = requests.Session()
        session.verify = verify  # Depending if SSL cert is verifiable
        # If using HTTP Basic auth, add the user/pass to the session
        if auth_mode == 'http-basic':
            session.auth = (username, password)

        # Get and set CSRF token and authenticate the session if appropriate.
        self._set_csrf_token(session)
        if auth_mode == 'timesketch':
            self._authenticate_session(session, username, password)

        return session

    def fetch_resource_data(self, resource_uri):
        """Make a HTTP GET request.

        Args:
            resource_uri: The URI to the resource to be fetched.

        Returns:
            Dictionary with the response data.
        """
        # TODO: Catch HTTP errors and add descriptive message string.
        resource_url = '{0:s}/{1:s}'.format(self.api_root, resource_uri)
        response = self.session.get(resource_url)
        return response.json()

    def create_sketch(self, name, description=None):
        """Create a new sketch.

        Args:
            name: Name of the sketch.
            description: Description of the sketch.

        Returns:
            Instance of a Sketch object.
        """
        if not description:
            description = name

        resource_url = '{0:s}/sketches/'.format(self.api_root)
        form_data = {'name': name, 'description': description}
        response = self.session.post(resource_url, json=form_data)
        response_dict = response.json()
        sketch_id = response_dict['objects'][0]['id']
        return self.get_sketch(sketch_id)

    def get_sketch(self, sketch_id):
        """Get a sketch.

        Args:
            sketch_id: Primary key ID of the sketch.

        Returns:
            Instance of a Sketch object.
        """
        return Sketch(sketch_id, api=self)

    def list_sketches(self):
        """Get list of all open sketches that the user has access to.

        Returns:
            List of Sketch objects instances.
        """
        sketches = []
        response = self.fetch_resource_data('sketches/')
        for sketch in response['objects'][0]:
            sketch_id = sketch['id']
            sketch_name = sketch['name']
            sketch_obj = Sketch(
                sketch_id=sketch_id, api=self, sketch_name=sketch_name)
            sketches.append(sketch_obj)
        return sketches

    def get_searchindex(self, searchindex_id):
        """Get a searchindex.

        Args:
            searchindex_id: Primary key ID of the searchindex.

        Returns:
            Instance of a SearchIndex object.
        """
        return SearchIndex(searchindex_id, api=self)

    def get_or_create_searchindex(self,
                                  searchindex_name,
                                  es_index_name=None,
                                  public=False):
        """Create a new searchindex.

        Args:
            searchindex_name: Name of the searchindex in Timesketch.
            es_index_name: Name of the index in Elasticsearch.
            public: Boolean indicating if the searchindex should be public.

        Returns:
            Instance of a SearchIndex object and a boolean indicating if the
            object was created.
        """
        if not es_index_name:
            es_index_name = uuid.uuid4().hex

        resource_url = '{0:s}/searchindices/'.format(self.api_root)
        form_data = {
            'searchindex_name': searchindex_name,
            'es_index_name': es_index_name,
            'public': public
        }
        response = self.session.post(resource_url, json=form_data)

        if response.status_code not in HTTP_STATUS_CODE_20X:
            raise RuntimeError('Error creating searchindex')

        response_dict = response.json()
        metadata_dict = response_dict['meta']
        created = metadata_dict.get('created', False)
        searchindex_id = response_dict['objects'][0]['id']
        return self.get_searchindex(searchindex_id), created

    def list_searchindices(self):
        """Get list of all searchindices that the user has access to.

        Returns:
            List of SearchIndex object instances.
        """
        indices = []
        response = self.fetch_resource_data('searchindices/')
        for index in response['objects'][0]:
            index_id = index['id']
            index_name = index['name']
            index_obj = SearchIndex(
                searchindex_id=index_id, api=self, searchindex_name=index_name)
            indices.append(index_obj)
        return indices


class BaseResource(object):
    """Base resource object."""

    def __init__(self, api, resource_uri):
        """Initialize object.

        Args:
            api: An instance of TimesketchApi object.
        """
        self.api = api
        self.resource_uri = resource_uri
        self.resource_data = None

    def lazyload_data(self, refresh_cache=False):
        """Load resource data once and cache the result.

        Args:
            refresh_cache: Boolean indicating if to update cache.

        Returns:
            Dictionary with resource data.
        """
        if not self.resource_data or refresh_cache:
            self.resource_data = self.api.fetch_resource_data(self.resource_uri)
        return self.resource_data

    @property
    def data(self):
        """Property to fetch resource data.

        Returns:
            Dictionary with resource data.
        """
        return self.lazyload_data()


class Sketch(BaseResource):
    """Timesketch sketch object.

    A sketch in Timesketch is a collection of one or more timelines. It has
    access control and its own namespace for things like labels and comments.

    Attributes:
        id: The ID of the sketch.
        api: An instance of TimesketchApi object.
    """

    DEFAULT_SIZE_LIMIT = 10000

    def __init__(self, sketch_id, api, sketch_name=None):
        """Initializes the Sketch object.

        Args:
            sketch_id: Primary key ID of the sketch.
            api: An instance of TimesketchApi object.
            sketch_name: Name of the sketch (optional).
        """
        self.id = sketch_id
        self.api = api
        self._sketch_name = sketch_name
        self._resource_uri = 'sketches/{0:d}'.format(self.id)
        super(Sketch, self).__init__(api=api, resource_uri=self._resource_uri)

    @property
    def name(self):
        """Property that returns sketch name.

        Returns:
            Sketch name as string.
        """
        if not self._sketch_name:
            sketch = self.lazyload_data()
            self._sketch_name = sketch['objects'][0]['name']
        return self._sketch_name

    @property
    def description(self):
        """Property that returns sketch description.

        Returns:
            Sketch description as string.
        """
        sketch = self.lazyload_data()
        return sketch['objects'][0]['description']

    @property
    def status(self):
        """Property that returns sketch status.

        Returns:
            Sketch status as string.
        """
        sketch = self.lazyload_data()
        return sketch['objects'][0]['status'][0]['status']

    def _build_pandas_dataframe(self, search_response):
        """Return a Pandas DataFrame from a query result dict.

        Args:
            search_response: dictionary with query results.

        Returns:
            pandas DataFrame with the results.
        """
        return_list = []
        timelines = {}
        for timeline in self.list_timelines():
            timelines[timeline.index] = timeline.name

        for result in search_response.get('objects', []):
            source = result.get('_source', {})
            source['_id'] = result.get('_id')
            source['_type'] = result.get('_type')
            source['_index'] = result.get('_index')
            source['_source'] = timelines.get(result.get('_index'))

            return_list.append(source)

        data_frame = pandas.DataFrame(return_list)
        if 'datetime' in data_frame:
            data_frame['datetime'] = pandas.to_datetime(data_frame.datetime)
        elif 'timestamp' in data_frame:
            data_frame['datetime'] = pandas.to_datetime(
                data_frame.timestamp / 1e6, utc=True, unit='s')

        return data_frame

    def _get_aggregation_buckets(self, entry, name=''):
        """Yields all buckets from a aggregation result object.

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

    def list_aggregations(self):
        """List all saved aggregations for this sketch.

        Returns:
            List of aggregations (instances of Aggregation objects)
        """
        sketch = self.lazyload_data()
        aggregations = []
        for aggregation in sketch['meta']['aggregations']:
            aggregation_obj = Aggregation(
                aggregation_id=aggregation['id'],
                aggregation_name=aggregation['name'],
                sketch=self,
                sketch_id=self.id,
                api=self.api)
            aggregations.append(aggregation_obj)
        return aggregations

    def list_views(self):
        """List all saved views for this sketch.

        Returns:
            List of views (instances of View objects)
        """
        sketch = self.lazyload_data()
        views = []
        for view in sketch['meta']['views']:
            view_obj = View(
                view_id=view['id'],
                view_name=view['name'],
                sketch_id=self.id,
                api=self.api)
            views.append(view_obj)
        return views

    def list_timelines(self):
        """List all timelines for this sketch.

        Returns:
            List of timelines (instances of Timeline objects)
        """
        sketch = self.lazyload_data()
        timelines = []
        for timeline in sketch['objects'][0]['timelines']:
            timeline_obj = Timeline(
                timeline_id=timeline['id'],
                sketch_id=self.id,
                api=self.api,
                name=timeline['name'],
                searchindex=timeline['searchindex']['index_name'])
            timelines.append(timeline_obj)
        return timelines

    def upload(self, timeline_name, file_path):
        """Upload a CSV, JSONL, or Plaso file to the server for indexing.

        Args:
            timeline_name: Name of the resulting timeline.
            file_path: Path to the file to be uploaded.

        Returns:
            Timeline object instance.
        """
        resource_url = '{0:s}/upload/'.format(self.api.api_root)
        files = {'file': open(file_path, 'rb')}
        data = {'name': timeline_name, 'sketch_id': self.id}
        response = self.api.session.post(resource_url, files=files, data=data)
        response_dict = response.json()
        timeline = response_dict['objects'][0]
        timeline_obj = Timeline(
            timeline_id=timeline['id'],
            sketch_id=self.id,
            api=self.api,
            name=timeline['name'],
            searchindex=timeline['searchindex']['index_name'])
        return timeline_obj

    def add_timeline(self, searchindex):
        """Add timeline to sketch.

        Args:
            searchindex: SearchIndex object instance.

        Returns:
            Timeline object instance.
        """
        resource_url = '{0:s}/sketches/{1:d}/timelines/'.format(
            self.api.api_root, self.id)
        form_data = {'timeline': searchindex.id}
        response = self.api.session.post(resource_url, json=form_data)

        if response.status_code not in HTTP_STATUS_CODE_20X:
            raise RuntimeError('Failed adding timeline')

        response_dict = response.json()
        timeline = response_dict['objects'][0]
        timeline_obj = Timeline(
            timeline_id=timeline['id'],
            sketch_id=self.id,
            api=self.api,
            name=timeline['name'],
            searchindex=timeline['searchindex']['index_name'])
        return timeline_obj

    def explore(self,
                query_string=None,
                query_dsl=None,
                query_filter=None,
                view=None,
                return_fields=None,
                as_pandas=False,
                max_entries=None):
        """Explore the sketch.

        Args:
            query_string: Elasticsearch query string.
            query_dsl: Elasticsearch query DSL as JSON string.
            query_filter: Filter for the query as JSON string.
            view: View object instance (optional).
            return_fields: List of fields that should be included in the
                response.
            as_pandas: Optional bool that determines if the results should
                be returned back as a dictionary or a Pandas DataFrame.
            max_entries: Optional integer denoting a best effort to limit
                the output size to the number of events. Events are read in,
                10k at a time so there may be more events in the answer back
                than this number denotes, this is a best effort.

        Returns:
            Dictionary with query results or a pandas DataFrame if as_pandas
            is set to True.

        Raises:
            ValueError: if unable to query for the results.
        """
        default_filter = {
            'time_start': None,
            'time_end': None,
            'size': self.DEFAULT_SIZE_LIMIT,
            'terminate_after': self.DEFAULT_SIZE_LIMIT,
            'indices': '_all',
            'order': 'asc'
        }

        if as_pandas:
            default_filter['size'] = 10000
            default_filter['terminate_after'] = 10000

        if not (query_string or query_filter or query_dsl or view):
            raise RuntimeError('You need to supply a query or view')

        if not query_filter:
            query_filter = default_filter

        if view:
            if view.query_string:
                query_string = view.query_string
            query_filter = json.loads(view.query_filter)

            query_filter['size'] = self.DEFAULT_SIZE_LIMIT
            query_filter['terminate_after'] = self.DEFAULT_SIZE_LIMIT

            if view.query_dsl:
                query_dsl = json.loads(view.query_dsl)

        resource_url = '{0:s}/sketches/{1:d}/explore/'.format(
            self.api.api_root, self.id)

        form_data = {
            'query': query_string,
            'filter': query_filter,
            'dsl': query_dsl,
            'fields': return_fields,
            'enable_scroll': True,
        }

        response = self.api.session.post(resource_url, json=form_data)
        if response.status_code != 200:
            raise ValueError(
                'Unable to query results, with error: [{0:d}] {1:s}'.format(
                    response.status_code, response.reason))

        response_json = response.json()

        scroll_id = response_json.get('meta', {}).get('scroll_id', '')
        form_data['scroll_id'] = scroll_id

        count = len(response_json.get('objects', []))
        total_count = count
        while count > 0:
            if max_entries and total_count >= max_entries:
                break
            more_response = self.api.session.post(resource_url, json=form_data)
            if more_response.status_code != 200:
                raise ValueError((
                    'Unable to query results, with error: '
                    '[{0:d}] {1:s}').format(
                        response.status_code, response.reason))
            more_response_json = more_response.json()
            count = len(more_response_json.get('objects', []))
            total_count += count
            response_json['objects'].extend(
                more_response_json.get('objects', []))
            added_time = more_response_json['meta']['es_time']
            response_json['meta']['es_time'] += added_time

        if as_pandas:
            return self._build_pandas_dataframe(response_json)

        return response_json


    def aggregate(self, aggregate_dsl, as_pandas=False):
        """Run an aggregation request on the sketch.

        Args:
            aggregate_dsl: Elasticsearch aggregation query DSL string.
            as_pandas: Optional bool that determines if the results should
                be returned back as a dictionary or a Pandas DataFrame.

        Returns:
            Dictionary with query results or a pandas DataFrame if as_pandas
            is set to True.

        Raises:
            ValueError: if unable to query for the results.
        """
        if not aggregate_dsl:
            raise RuntimeError(
                'You need to supply an aggregation query DSL string.')

        resource_url = '{0:s}/sketches/{1:d}/aggregation/explore/'.format(
            self.api.api_root, self.id)

        form_data = {
            'aggregation_dsl': aggregate_dsl,
        }

        response = self.api.session.post(resource_url, json=form_data)
        if response.status_code != 200:
            raise ValueError(
                'Unable to query results, with error: [{0:d}] {1:s}'.format(
                    response.status_code, response.reason))

        response_json = response.json()

        if as_pandas:
            panda_list = []
            for entry in response_json.get('objects', []):
                for bucket in self._get_aggregation_buckets(entry):
                    panda_list.append(bucket)
            return pandas.DataFrame(panda_list)

        return response_json

    def run_aggregator(
            self, aggregator_name, aggregator_parameters, as_pandas=False):
        """Run an aggregator class.

        Args:
            aggregator_name: Name of the aggregator to run.
            aggregator_parameters: A dict with key/value pairs of parameters
                the aggregator needs to run.
            as_pandas: Optional bool that determines if the results should
                be returned back as a dictionary or a Pandas DataFrame.

        Returns:
            Dictionary with query results or a pandas DataFrame if as_pandas
            is set to True.
        """
        resource_url = '{0:s}/sketches/{1:d}/aggregation/explore/'.format(
            self.api.api_root, self.id)

        form_data = {
            'aggregator_name': aggregator_name,
            'aggregator_parameters': aggregator_parameters,
        }

        response = self.api.session.post(resource_url, json=form_data)
        if response.status_code != 200:
            raise ValueError(
                'Unable to query results, with error: [{0:d}] {1:s}'.format(
                    response.status_code, response.reason))

        response_json = response.json()

        if as_pandas:
            panda_list = []
            for entry in response_json.get('objects', []):
                for bucket in self._get_aggregation_buckets(entry):
                    panda_list.append(bucket)
            return pandas.DataFrame(panda_list)

        return response_json

    def label_events(self, events, label_name):
        """Labels one or more events with label_name.

        Args:
            events: Array of JSON objects representing events.
            label_name: String to label the event with.

        Returns:
            Dictionary with query results.
        """
        form_data = {
            'annotation': label_name,
            'annotation_type': 'label',
            'events': events
        }
        resource_url = '{0:s}/sketches/{1:d}/event/annotate/'.format(
            self.api.api_root, self.id)
        response = self.api.session.post(resource_url, json=form_data)
        return response.json()

    def search_by_label(self, label_name):
        """Searches for all events containing a given label.

        Args:
            label_name: A string representing the label to search for.

        Returns:
            A dictionary with query results.
        """
        query = {
            "nested": {
                "path": "timesketch_label",
                "query": {
                    "bool": {
                        "must": [
                            {
                                "term": {
                                    "timesketch_label.name": label_name
                                }
                            },
                            {
                                "term": {
                                    "timesketch_label.sketch_id": self.id
                                }
                            }
                        ]
                    }
                }
            }
        }
        return self.explore(query_dsl=json.dumps({'query': query}))

    def add_event(self, message, timestamp, timestamp_desc):
        """Adds an event to the sketch specific timeline.

        Args:
            message: Array of JSON objects representing events.
            timestamp: Micro seconds since 1970-01-01 00:00:00.
            timestamp_desc : Description of the timestamp.

        Returns:
            Dictionary with query results.
        """
        form_data = {
            'timestamp': timestamp,
            'timestamp_desc': timestamp_desc,
            'message': message
        }

        resource_url = '{0:s}/sketches/{1:d}/event/create/'.format(
            self.api.api_root, self.id)
        response = self.api.session.post(resource_url, json=form_data)
        return response.json()


class SearchIndex(BaseResource):
    """Timesketch searchindex object.

    Attributes:
        id: The ID of the search index.
        api: An instance of TimesketchApi object.
    """

    def __init__(self, searchindex_id, api, searchindex_name=None):
        """Initializes the SearchIndex object.

        Args:
            searchindex_id: Primary key ID of the searchindex.
            searchindex_name: Name of the searchindex (optional).
        """
        self.id = searchindex_id
        self._searchindex_name = searchindex_name
        self._resource_uri = 'searchindices/{0:d}'.format(self.id)
        super(SearchIndex, self).__init__(
            api=api, resource_uri=self._resource_uri)

    @property
    def name(self):
        """Property that returns searchindex name.

        Returns:
            Searchindex name as string.
        """
        if not self._searchindex_name:
            searchindex = self.lazyload_data()
            self._searchindex_name = searchindex['objects'][0]['name']
        return self._searchindex_name

    @property
    def index_name(self):
        """Property that returns Elasticsearch index name.

        Returns:
            Elasticsearch index name as string.
        """
        searchindex = self.lazyload_data()
        return searchindex['objects'][0]['index_name']


class Aggregation(BaseResource):
    """Saved aggregation object.

    Attributes:
        id: Primary key of the aggregation.
        name: Name of the aggregation.
    """

    def __init__(
            self, aggregation_id, aggregation_name, sketch, sketch_id, api):
        self.id = aggregation_id
        self.name = aggregation_name
        self._sketch = sketch
        resource_uri = 'sketches/{0:d}/aggregation/{1:d}/'.format(
            sketch_id, aggregation_id)
        super(Aggregation, self).__init__(api, resource_uri)

    def _aggregation(self):
        """Return the aggregation object."""
        data = self.lazyload_data()
        return data.get('objects', [])[0]

    @property
    def agg_type(self):
        """Property that returns the agg_type string."""
        aggregation = self._aggregation()
        return aggregation.get('agg_type', '')

    @property
    def chart(self):
        """Property that returns an altair Vega-lite chart."""
        return self.generate_chart()

    @property
    def chart_type(self):
        """Property that returns the chart_type string."""
        aggregation = self._aggregation()
        return aggregation.get('chart_type', '')

    @property
    def description(self):
        """Property that returns the description string."""
        aggregation = self._aggregation()
        return aggregation.get('description', '')

    @property
    def view(self):
        """Property that returns the view_id integer."""
        aggregation = self._aggregation()
        return aggregation.get('view_id', 0)

    @property
    def parameters(self):
        """Property that returns the parameter dict."""
        aggregation = self._aggregation()
        param_string = aggregation.get('parameters', '')
        if not param_string:
            return {}
        return json.loads(param_string)

    @property
    def table(self):
        """Property that returns a pandas DataFrame."""
        return self.run(as_pandas=True)

    def generate_chart(self):
        """Returns an altair Vega-lite chart."""
        chart_class = chart_manager.ChartManager.get_chart(self.chart_type)

        if not chart_class:
            return altair.Chart(pandas.DataFrame()).mark_point()

        data = self.run(as_pandas=True)
        x_value = ''
        y_value = ''
        for name, obj_type in data.dtypes.items():
            if name == self.name:
                continue
            if numpy.issubdtype(obj_type, numpy.integer):
                y_value = name
            else:
                x_value = name

        encoding = {
            'x': {'field': x_value, 'type': 'ordinal'},
            'y': {'field': y_value, 'type': 'quantitative'},
        }
        chart_obj = chart_class({
            'values': data,
            'encoding': encoding,
        })

        return chart_obj.generate()

    def run(self, as_pandas=False):
        """Returns the results from an aggregator run."""
        return self._sketch.run_aggregator(
            self.name, self.parameters, as_pandas=as_pandas)


class View(BaseResource):
    """Saved view object.

    Attributes:
        id: Primary key of the view.
        name: Name of the view.
    """

    def __init__(self, view_id, view_name, sketch_id, api):
        """Initializes the View object.

        Args:
            view_id: Primary key ID for the view.
            view_name: The name of the view.
            sketch_id: ID of a sketch.
            api: Instance of a TimesketchApi object.
        """
        self.id = view_id
        self.name = view_name
        resource_uri = 'sketches/{0:d}/views/{1:d}/'.format(sketch_id, self.id)
        super(View, self).__init__(api, resource_uri)

    @property
    def query_string(self):
        """Property that returns the views query string.

        Returns:
            Elasticsearch query as string.
        """
        view = self.lazyload_data()
        return view['objects'][0]['query_string']

    @property
    def query_filter(self):
        """Property that returns the views filter.

        Returns:
            Elasticsearch filter as JSON string.
        """
        view = self.lazyload_data()
        return view['objects'][0]['query_filter']

    @property
    def query_dsl(self):
        """Property that returns the views query DSL.

        Returns:
            Elasticsearch DSL as JSON string.
        """
        view = self.lazyload_data()
        return view['objects'][0]['query_dsl']


class Timeline(BaseResource):
    """Timeline object.

    Attributes:
        id: Primary key of the view.
    """

    def __init__(self, timeline_id, sketch_id, api, name=None,
                 searchindex=None):
        """Initializes the Timeline object.

        Args:
            timeline_id: The primary key ID of the timeline.
            sketch_id: ID of a sketch.
            api: Instance of a TimesketchApi object.
            name: Name of the timeline (optional)
            searchindex: The Elasticsearch index name (optional)
        """
        self.id = timeline_id
        self._name = name
        self._searchindex = searchindex
        resource_uri = 'sketches/{0:d}/timelines/{1:d}/'.format(
            sketch_id, self.id)
        super(Timeline, self).__init__(api, resource_uri)

    @property
    def name(self):
        """Property that returns timeline name.

        Returns:
            Timeline name as string.
        """
        if not self._name:
            timeline = self.lazyload_data()
            self._name = timeline['objects'][0]['name']
        return self._name

    @property
    def index(self):
        """Property that returns index name.

        Returns:
            Elasticsearch index name as string.
        """
        if not self._searchindex:
            timeline = self.lazyload_data()
            index_name = timeline['objects'][0]['searchindex']['index_name']
            self._searchindex = index_name
        return self._searchindex
