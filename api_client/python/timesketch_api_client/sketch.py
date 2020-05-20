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

import os
import json
import logging

import pandas

from . import aggregation
from . import definitions
from . import error
from . import resource
from . import story
from . import timeline
from . import view as view_lib


logging.basicConfig(level=os.environ.get('LOGLEVEL', 'INFO'))
logger = logging.getLogger('sketch_api')


class Sketch(resource.BaseResource):
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

    def _build_pandas_dataframe(self, search_response, return_fields=None):
        """Return a Pandas DataFrame from a query result dict.

        Args:
            search_response: dictionary with query results.
            return_fields: List of fields that should be included in the
                response. Optional and defaults to None.

        Returns:
            pandas DataFrame with the results.
        """
        return_list = []
        timelines = {}
        for timeline_obj in self.list_timelines():
            timelines[timeline_obj.index] = timeline_obj.name

        return_field_list = []
        if return_fields:
            if return_fields.startswith('\''):
                return_fields = return_fields[1:]
            if return_fields.endswith('\''):
                return_fields = return_fields[:-1]
            return_field_list = return_fields.split(',')

        for result in search_response.get('objects', []):
            source = result.get('_source', {})
            if not return_fields or '_id' in return_field_list:
                source['_id'] = result.get('_id')
            if not return_fields or '_type' in return_field_list:
                source['_type'] = result.get('_type')
            if not return_fields or '_index' in return_field_list:
                source['_index'] = result.get('_index')
            if not return_fields or '_source' in return_field_list:
                source['_source'] = timelines.get(result.get('_index'))

            return_list.append(source)

        data_frame = pandas.DataFrame(return_list)
        if 'datetime' in data_frame:
            try:
                data_frame['datetime'] = pandas.to_datetime(data_frame.datetime)
            except pandas.errors.OutOfBoundsDatetime:
                pass
        elif 'timestamp' in data_frame:
            try:
                data_frame['datetime'] = pandas.to_datetime(
                    data_frame.timestamp / 1e6, utc=True, unit='s')
            except pandas.errors.OutOfBoundsDatetime:
                pass

        return data_frame

    def create_story(self, title):
        """Create a story object.

        Args:
            title: the title of the story.

        Returns:
            A story object (instance of Story) for the newly
            created story.
        """
        resource_url = '{0:s}/sketches/{1:d}/stories/'.format(
            self.api.api_root, self.id)
        data = {
            'title': title,
            'content': ''
        }

        response = self.api.session.post(resource_url, json=data)
        response_json = response.json()
        story_dict = response_json.get('objects', [{}])[0]
        return story.Story(
            story_id=story_dict.get('id', 0),
            sketch=self,
            api=self.api)

    def add_to_acl(self, user_list=None, group_list=None, make_public=False):
        """Add users or groups to the sketch ACL.

        Args:
            user_list: optional list of users to add to the ACL
                of the sketch. Each user is a string.
            group_list: optional list of groups to add to the ACL
                of the sketch. Each user is a string.
            make_public: Optional boolean indicating the sketch should be
                marked as public.

        Returns:
            A boolean indicating whether the ACL change was successful.
        """
        if not user_list and not group_list:
            return True

        resource_url = '{0:s}/sketches/{1:d}/collaborators/'.format(
            self.api.api_root, self.id)

        data = {}
        if group_list:
            group_list_corrected = [str(x).strip() for x in group_list]
            data['groups'] = group_list_corrected

        if user_list:
            user_list_corrected = [str(x).strip() for x in user_list]
            data['users'] = user_list_corrected

        if make_public:
            data['public'] = 'true'

        if not data:
            return True

        response = self.api.session.post(resource_url, json=data)

        return response.status_code in definitions.HTTP_STATUS_CODE_20X

    def list_aggregation_groups(self):
        """List all saved aggregation groups for this sketch.

        Returns:
            List of aggregation groups (instances of AggregationGroup objects)
        """
        groups = []
        resource_url = '{0:s}/sketches/{1:d}/aggregation/group/'.format(
            self.api.api_root, self.id)
        response = self.api.session.get(resource_url)
        data = response.json()
        for group_dict in data.get('objects', []):
            if not group_dict.get('id'):
                continue
            group = aggregation.AggregationGroup(
                sketch=self, api=self.api)
            group.from_dict(group_dict)
            groups.append(group)
        return groups

    def list_aggregations(self, include_labels=None, exclude_labels=None):
        """List all saved aggregations for this sketch.

        Args:
            include_labels (list): list of strings with labels. If defined
                then only return aggregations that have the label in the list.
            exclude_labels (list): list of strings with labels. If defined
                then only return aggregations that don't have a label in the
                list. include_labels will be processed first in case both are
                defined.

        Returns:
            List of aggregations (instances of Aggregation objects)
        """
        aggregations = []
        data = self.lazyload_data(refresh_cache=True)

        objects = data.get('objects')
        if not objects:
            return aggregations

        if not isinstance(objects, (list, tuple)):
            return aggregations

        first_object = objects[0]
        if not isinstance(first_object, dict):
            return aggregations

        aggregation_groups = first_object.get('aggregationgroups')
        if aggregation_groups:
            aggregation_groups = aggregation_groups[0]
            groups = [
                x.get('id', 0) for x in aggregation_groups.get(
                    'aggregations', [])]
        else:
            groups = tuple()

        for aggregation_dict in first_object.get('aggregations', []):
            agg_id = aggregation_dict.get('id')
            if agg_id in groups:
                continue
            label_string = aggregation_dict.get('label_string', '')
            if label_string:
                labels = json.loads(label_string)
            else:
                labels = []

            if include_labels:
                if not any(x in include_labels for x in labels):
                    continue

            if exclude_labels:
                if any(x in exclude_labels for x in labels):
                    continue

            aggregation_obj = aggregation.Aggregation(
                sketch=self, api=self.api)
            aggregation_obj.from_store(aggregation_id=agg_id)
            aggregations.append(aggregation_obj)
        return aggregations

    def get_analyzer_status(self):
        """Returns a list of started analyzers and their status.

        Returns:
            A list of dict objects that contains status information
            of each analyzer run. The dict contains information about
            what timeline it ran against, the results and current
            status of the analyzer run.
        """
        stats_list = []
        for timeline_obj in self.list_timelines():
            resource_uri = (
                '{0:s}/sketches/{1:d}/timelines/{2:d}/analysis').format(
                    self.api.api_root, self.id, timeline_obj.id)
            response = self.api.session.get(resource_uri)
            response_json = response.json()
            objects = response_json.get('objects')
            if not objects:
                continue
            for result in objects[0]:
                stat = {
                    'index': timeline_obj.index,
                    'timeline_id': timeline_obj.id,
                    'analyzer': result.get('analyzer_name', 'N/A'),
                    'results': result.get('result', 'N/A'),
                    'status': 'N/A',
                }
                status = result.get('status', [])
                if len(status) == 1:
                    stat['status'] = status[0].get('status', 'N/A')
                stats_list.append(stat)
        return stats_list

    def get_aggregation(self, aggregation_id):
        """Return a stored aggregation.

        Args:
            aggregation_id: id of the stored aggregation.

        Returns:
            An aggregation object, if stored (instance of Aggregation),
            otherwise None object.
        """
        for aggregation_obj in self.list_aggregations():
            if aggregation_obj.id == aggregation_id:
                return aggregation_obj
        return None

    def get_aggregation_group(self, group_id):
        """Return a stored aggregation group.

        Args:
            goup_id: id of the stored aggregation group.

        Returns:
            An aggregation group object (instance of AggregationGroup)
            if stored, otherwise None object.
        """
        for group_obj in self.list_aggregation_groups():
            if group_obj.id == group_id:
                return group_obj
        return None

    def get_story(self, story_id=None, story_title=None):
        """Returns a story object that is stored in the sketch.

        Args:
            story_id: an integer indicating the ID of the story to
                be fetched. Defaults to None.
            story_title: a string with the title of the story. Optional
                and defaults to None.

        Returns:
            A story object (instance of Story) if one is found. Returns
            a None if neiter story_id or story_title is defined or if
            the view does not exist. If a story title is defined and
            not a story id, the first story that is found with the same
            title will be returned.
        """
        if story_id is None and story_title is None:
            return None

        for story_obj in self.list_stories():
            if story_id and story_id == story_obj.id:
                return story_obj
            if story_title and story_title.lower() == story_obj.title.lower():
                return story_obj
        return None

    def get_view(self, view_id=None, view_name=None):
        """Returns a view object that is stored in the sketch.

        Args:
            view_id: an integer indicating the ID of the view to
                be fetched. Defaults to None.
            view_name: a string with the name of the view. Optional
                and defaults to None.

        Returns:
            A view object (instance of View) if one is found. Returns
            a None if neiter view_id or view_name is defined or if
            the view does not exist.
        """
        if view_id is None and view_name is None:
            return None

        for view in self.list_views():
            if view_id and view_id == view.id:
                return view
            if view_name and view_name.lower() == view.name.lower():
                return view
        return None

    def list_stories(self):
        """Get a list of all stories that are attached to the sketch.

        Returns:
            List of stories (instances of Story objects)
        """
        story_list = []
        resource_url = '{0:s}/sketches/{1:d}/stories/'.format(
            self.api.api_root, self.id)
        response = self.api.session.get(resource_url)
        response_json = response.json()
        story_objects = response_json.get('objects')
        if not story_objects:
            return story_list

        if not len(story_objects) == 1:
            return story_list
        stories = story_objects[0]
        for story_dict in stories:
            story_list.append(story.Story(
                story_id=story_dict.get('id', -1),
                sketch=self,
                api=self.api))
        return story_list

    def list_views(self):
        """List all saved views for this sketch.

        Returns:
            List of views (instances of View objects)
        """
        sketch = self.lazyload_data()
        views = []
        for view in sketch['meta']['views']:
            view_obj = view_lib.View(
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
        for timeline_dict in sketch['objects'][0]['timelines']:
            timeline_obj = timeline.Timeline(
                timeline_id=timeline_dict['id'],
                sketch_id=self.id,
                api=self.api,
                name=timeline_dict['name'],
                searchindex=timeline_dict['searchindex']['index_name'])
            timelines.append(timeline_obj)
        return timelines

    def upload(self, timeline_name, file_path, index=None):
        """Upload a CSV, JSONL, mans, or Plaso file to the server for indexing.

        Args:
            timeline_name: Name of the resulting timeline.
            file_path: Path to the file to be uploaded.
            index: Index name for the ES database

        Returns:
            Timeline object instance.
        """
        # TODO: Deprecate this function.
        logger.warning(
            'This function is about to be deprecated, please use the '
            'timesketch_import_client instead')

        resource_url = '{0:s}/upload/'.format(self.api.api_root)
        files = {'file': open(file_path, 'rb')}
        data = {'name': timeline_name, 'sketch_id': self.id,
                'index_name': index}
        response = self.api.session.post(resource_url, files=files, data=data)
        response_dict = response.json()
        timeline_dict = response_dict['objects'][0]
        timeline_obj = timeline.Timeline(
            timeline_id=timeline_dict['id'],
            sketch_id=self.id,
            api=self.api,
            name=timeline_dict['name'],
            searchindex=timeline_dict['searchindex']['index_name'])
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

        if response.status_code not in definitions.HTTP_STATUS_CODE_20X:
            error.error_message(
                response, message='Failed adding timeline',
                error=RuntimeError)

        response_dict = response.json()
        timeline_dict = response_dict['objects'][0]
        timeline_obj = timeline.Timeline(
            timeline_id=timeline_dict['id'],
            sketch_id=self.id,
            api=self.api,
            name=timeline_dict['name'],
            searchindex=timeline_dict['searchindex']['index_name'])
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
            query_filter: Filter for the query as a dict.
            view: View object instance (optional).
            return_fields: List of fields that should be included in the
                response. Optional and defaults to None.
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
            RuntimeError: if the query is missing needed values.
        """
        if not (query_string or query_filter or query_dsl or view):
            raise RuntimeError('You need to supply a query or view')

        if not query_filter:
            query_filter = {
                'time_start': None,
                'time_end': None,
                'size': self.DEFAULT_SIZE_LIMIT,
                'terminate_after': self.DEFAULT_SIZE_LIMIT,
                'indices': '_all',
                'order': 'asc'
            }

        if not isinstance(query_filter, dict):
            raise ValueError(
                'Unable to query with a query filter that isn\'t a dict.')

        if view:
            if view.query_string:
                query_string = view.query_string
            query_filter = view.query_filter
            query_dsl = view.query_dsl

        if as_pandas:
            query_filter.setdefault('size', self.DEFAULT_SIZE_LIMIT)
            query_filter.setdefault('terminate_after', self.DEFAULT_SIZE_LIMIT)

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
            error.error_message(
                response, message='Unable to query results',
                error=ValueError)

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
                error.error_message(
                    response, message='Unable to query results',
                    error=ValueError)
            more_response_json = more_response.json()
            count = len(more_response_json.get('objects', []))
            total_count += count
            response_json['objects'].extend(
                more_response_json.get('objects', []))
            more_meta = more_response_json.get('meta', {})
            added_time = more_meta.get('es_time', 0)
            response_json['meta']['es_time'] += added_time

        total_elastic_count = response_json.get(
            'meta', {}).get('es_total_count', 0)
        if total_elastic_count != total_count:
            logger.info(
                '{0:d} results were returned, but {1:d} records matched the '
                'search query'.format(total_count, total_elastic_count))

        if as_pandas:
            return self._build_pandas_dataframe(response_json, return_fields)

        return response_json

    def list_available_analyzers(self):
        """Returns a list of available analyzers."""
        resource_url = '{0:s}/sketches/{1:d}/analyzer/'.format(
            self.api.api_root, self.id)

        response = self.api.session.get(resource_url)

        if response.status_code == 200:
            return response.json()

        return '[{0:d}] {1!s} {2!s}'.format(
            response.status_code, response.reason, response.text)

    def run_analyzer(
            self, analyzer_name, analyzer_kwargs=None, timeline_id=None,
            timeline_name=None):
        """Run an analyzer on a timeline.

        Args:
            analyzer_name: the name of the analyzer class to run against the
                timeline.
            analyzer_kwargs: optional dict with parameters for the analyzer.
                This is optional and just for those analyzers that can accept
                further parameters.
            timeline_id: the ID of the timeline. This is optional and only
                required if timeline_name is not set.
            timeline_name: the name of the timeline in the timesketch UI. This
                is optional and only required if timeline_id is not set. If
                there are more than a single timeline with the same name a
                timeline_id is required.

        Returns:
            A string with the results of the API call to run the analyzer.
        """
        if not timeline_id and not timeline_name:
            return (
                'Unable to run analyzer, need to define either '
                'timeline ID or name')

        resource_url = '{0:s}/sketches/{1:d}/analyzer/'.format(
            self.api.api_root, self.id)

        # The analyzer_kwargs is expected to be a dict with the key
        # being the analyzer name, and the value being the key/value dict
        # with parameters for the analyzer.
        if analyzer_kwargs:
            if not isinstance(analyzer_kwargs, dict):
                return (
                    'Unable to run analyzer, analyzer kwargs needs to be a '
                    'dict')
            if analyzer_name not in analyzer_kwargs:
                analyzer_kwargs = {analyzer_name: analyzer_kwargs}

        if timeline_name:
            sketch = self.lazyload_data(refresh_cache=True)
            timelines = []
            for timeline_dict in sketch['objects'][0]['timelines']:
                name = timeline_dict.get('name', '')
                if timeline_name.lower() == name.lower():
                    timelines.append(timeline_dict.get('id'))

            if not timelines:
                return 'No timelines with the name: {0:s} were found'.format(
                    timeline_name)

            if len(timelines) != 1:
                return (
                    'There are {0:d} timelines defined in the sketch with '
                    'this name, please use a unique name or a '
                    'timeline ID').format(len(timelines))

            timeline_id = timelines[0]

        data = {
            'timeline_id': timeline_id,
            'analyzer_names': [analyzer_name],
            'analyzer_kwargs': analyzer_kwargs,
        }

        response = self.api.session.post(resource_url, json=data)

        if response.status_code == 200:
            return response.json()

        return '[{0:d}] {1!s} {2!s}'.format(
            response.status_code, response.reason, response.text)

    def remove_acl(self, user_list=None, group_list=None, remove_public=False):
        """Remove users or groups to the sketch ACL.

        Args:
            user_list: optional list of users to remove from the ACL
                of the sketch. Each user is a string.
            group_list: optional list of groups to remove from the ACL
                of the sketch. Each user is a string.
            remove_public: Optional boolean indicating the sketch should be
                no longer marked as public.

        Returns:
            A boolean indicating whether the ACL change was successful.
        """
        if not user_list and not group_list:
            return True

        resource_url = '{0:s}/sketches/{1:d}/collaborators/'.format(
            self.api.api_root, self.id)

        data = {}
        if group_list:
            group_list_corrected = [str(x).strip() for x in group_list]
            data['remove_groups'] = group_list_corrected

        if user_list:
            user_list_corrected = [str(x).strip() for x in user_list]
            data['remove_users'] = user_list_corrected

        if remove_public:
            data['public'] = 'false'

        if not data:
            return True

        response = self.api.session.post(resource_url, json=data)

        return response.status_code in definitions.HTTP_STATUS_CODE_20X

    def aggregate(self, aggregate_dsl):
        """Run an aggregation request on the sketch.

        Args:
            aggregate_dsl: Elasticsearch aggregation query DSL string.

        Returns:
            An aggregation object (instance of Aggregation).

        Raises:
            ValueError: if unable to query for the results.
        """
        if not aggregate_dsl:
            raise RuntimeError(
                'You need to supply an aggregation query DSL string.')

        aggregation_obj = aggregation.Aggregation(sketch=self, api=self.api)
        aggregation_obj.from_explore(aggregate_dsl)

        return aggregation_obj

    def list_available_aggregators(self):
        """Return a list of all available aggregators in the sketch."""
        data = self.lazyload_data()
        meta = data.get('meta', {})
        entries = []
        for name, options in iter(meta.get('aggregators', {}).items()):
            for field in options.get('form_fields', []):
                entry = {
                    'aggregator_name': name,
                    'parameter': field.get('name'),
                    'notes': field.get('label')
                }
                if field.get('type') == 'ts-dynamic-form-select-input':
                    entry['value'] = '|'.join(field.get('options', []))
                    entry['type'] = 'selection'
                else:
                    _, _, entry['type'] = field.get('type').partition(
                        'ts-dynamic-form-')
                entries.append(entry)
        return pandas.DataFrame(entries)

    def run_aggregator(
            self, aggregator_name, aggregator_parameters):
        """Run an aggregator class.

        Args:
            aggregator_name: Name of the aggregator to run.
            aggregator_parameters: A dict with key/value pairs of parameters
                the aggregator needs to run.

        Returns:
            An aggregation object (instance of Aggregator).
        """
        aggregation_obj = aggregation.Aggregation(
            sketch=self,
            api=self.api)
        aggregation_obj.from_aggregator_run(
            aggregator_name=aggregator_name,
            aggregator_parameters=aggregator_parameters
        )

        return aggregation_obj

    def store_aggregation(
            self, name, description, aggregator_name, aggregator_parameters,
            chart_type=''):
        """Store an aggregation in the sketch.

        Args:
            name: a name that will be associated with the aggregation.
            description: description of the aggregation, visible in the UI.
            aggregator_name: name of the aggregator class.
            aggregator_parameters: parameters of the aggregator.
            chart_type: string representing the chart type.

        Raises:
            RuntimeError: if the client is unable to store the aggregation.

        Returns:
          A stored aggregation object or None if not stored.
        """
        # TODO: Deprecate this function.
        logger.warning(
            'This function is about to be deprecated, please use the '
            '`.save()` function of an aggregation object instead')

        aggregator_obj = self.run_aggregator(
            aggregator_name, aggregator_parameters)
        aggregator_obj.name = name
        aggregator_obj.description = description
        if chart_type:
            aggregator_obj.chart_type = chart_type
        if aggregator_obj.save():
            _ = self.lazyload_data(refresh_cache=True)
            return aggregator_obj

        return None

    def comment_event(self, event_id, index, comment_text):
        """
        Adds a comment to a single event.

        Args:
            event_id: id of the event
            index: The Elasticsearch index name
            comment_text: text to add as a comment
        Returns:
             a json data of the query.
        """
        form_data = {
            'annotation': comment_text,
            'annotation_type': 'comment',
            'events': {
                '_id': event_id,
                '_index': index,
                '_type': 'generic_event'}
        }
        resource_url = '{0:s}/sketches/{1:d}/event/annotate/'.format(
            self.api.api_root, self.id)
        response = self.api.session.post(resource_url, json=form_data)
        return response.json()

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

    def search_by_label(self, label_name, as_pandas=False):
        """Searches for all events containing a given label.

        Args:
            label_name: A string representing the label to search for.
            as_pandas: Optional bool that determines if the results should
                be returned back as a dictionary or a Pandas DataFrame.

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
        return self.explore(
            query_dsl=json.dumps({'query': query}), as_pandas=as_pandas)

    def add_event(self, message, timestamp, timestamp_desc):
        """Adds an event to the sketch specific timeline.

        Args:
            message: A string that will be used as the message string.
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
