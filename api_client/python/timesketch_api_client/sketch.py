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

from . import analyzer
from . import aggregation
from . import definitions
from . import error
from . import resource
from . import story
from . import timeline
from . import view as view_lib


logging.basicConfig(level=os.environ.get('LOGLEVEL', 'INFO'))
logger = logging.getLogger('timesketch_api.sketch')


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
        self._archived = None
        self._sketch_name = sketch_name
        self._resource_uri = 'sketches/{0:d}'.format(self.id)
        super(Sketch, self).__init__(api=api, resource_uri=self._resource_uri)

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

    @property
    def acl(self):
        """Property that returns back a ACL dict."""
        data = self.lazyload_data()
        objects = data.get('objects')
        if not objects:
            return {}
        data_object = objects[0]
        permission_string = data_object.get('all_permissions')
        if not permission_string:
            return {}
        return json.loads(permission_string)

    @property
    def attributes(self):
        """Property that returns the sketch attributes."""
        data = self.lazyload_data(refresh_cache=True)
        meta = data.get('meta', {})
        return_dict = {}
        for items in meta.get('attributes', []):
            name, values, ontology = items
            return_dict[name] = (values, ontology)

        return return_dict

    @property
    def attributes_table(self):
        """Property that returns the sketch attributes as a data frame."""
        data = self.lazyload_data(refresh_cache=True)
        meta = data.get('meta', {})
        attributes = meta.get('attributes', [])

        data_frame = pandas.DataFrame(attributes)
        data_frame.columns = ['attribute', 'values', 'ontology']

        return data_frame

    @property
    def description(self):
        """Property that returns sketch description.

        Returns:
            Sketch description as string.
        """
        sketch = self.lazyload_data()
        return sketch['objects'][0]['description']

    @description.setter
    def description(self, description_value):
        """Change the sketch description to a new value."""
        if not isinstance(description_value, str):
            logger.error('Unable to change the name to a non string value')
            return

        resource_url = '{0:s}/sketches/{1:d}/'.format(
            self.api.api_root, self.id)

        data = {
            'description': description_value,
        }
        response = self.api.session.post(resource_url, json=data)
        _ = error.check_return_status(response, logger)

        # Force the new description to be re-loaded.
        _ = self.lazyload_data(refresh_cache=True)

    @property
    def labels(self):
        """Property that returns the sketch labels."""
        data = self.lazyload_data(refresh_cache=True)
        objects = data.get('objects', [])
        if not objects:
            return []

        sketch_data = objects[0]
        label_string = sketch_data.get('label_string', '')
        if label_string:
            return json.loads(label_string)

        return []

    @property
    def my_acl(self):
        """Property that returns back the ACL for the current user."""
        data = self.lazyload_data()
        objects = data.get('objects')
        if not objects:
            return []
        data_object = objects[0]
        permission_string = data_object.get('my_permissions')
        if not permission_string:
            return []
        return json.loads(permission_string)

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

    @name.setter
    def name(self, name_value):
        """Change the name of the sketch to a new value."""
        if not isinstance(name_value, str):
            logger.error('Unable to change the name to a non string value')
            return

        resource_url = '{0:s}/sketches/{1:d}/'.format(
            self.api.api_root, self.id)

        data = {
            'name': name_value,
        }
        response = self.api.session.post(resource_url, json=data)
        _ = error.check_return_status(response, logger)

        # Force the new name to be re-loaded.
        self._sketch_name = ''
        _ = self.lazyload_data(refresh_cache=True)

    @property
    def status(self):
        """Property that returns sketch status.

        Returns:
            Sketch status as string.
        """
        sketch = self.lazyload_data()
        return sketch['objects'][0]['status'][0]['status']

    def add_attribute_list(self, name, values, ontology='text'):
        """Add an attribute to the sketch.

        Args:
            name (str): The name of the attribute.
            values (list): A list of string values of the attribute.
            ontology (str): The ontology (matches with
                /etc/ontology.yaml), which defines how the attribute
                is interpreted.

        Raises:
            ValueError: If any of the parameters are of the wrong type.

        Returns:
            Boolean value whether the attribute was successfully
            added or not.
        """
        if not isinstance(name, str):
            raise ValueError('Name needs to be a string.')

        if not isinstance(values, (list, tuple)):
            if any([not isinstance(x, str) for x in values]):
                raise ValueError('All values need to be a string.')

        if not isinstance(ontology, str):
            raise ValueError('Ontology needs to be a string.')

        resource_url = '{0:s}/sketches/{1:d}/attribute/'.format(
            self.api.api_root, self.id)

        data = {
            'name': name,
            'values': values,
            'ontology': ontology,
            'action': 'post',
        }
        response = self.api.session.post(resource_url, json=data)

        status = error.check_return_status(response, logger)
        if not status:
            logger.error('Unable to add the attribute to the sketch.')

        return status

    def add_attribute(self, name, value, ontology='text'):
        """Add an attribute to the sketch.

        Args:
            name (str): The name of the attribute.
            value (str): Value of the attribute, stored as a string.
            ontology (str): The ontology (matches with
                /etc/timesketch/ontology.yaml), which defines
                how the attribute is interpreted.

        Raises:
            ValueError: If any of the parameters are of the wrong type.

        Returns:
            Boolean value whether the attribute was successfully
            added or not.
        """
        if not isinstance(name, str):
            raise ValueError('Name needs to be a string.')

        return self.add_attribute_list(
            name=name, values=[value], ontology=ontology)

    def add_sketch_label(self, label):
        """Add a label to the sketch.

        Args:
            label (str): A string with the label to add to the sketch.

        Returns:
            bool: A boolean to indicate whether the label was successfully
                  added to the sketch.
        """
        if label in self.labels:
            logger.error(
                'Label [{0:s}] already applied to sketch.'.format(label))
            return False

        resource_url = '{0:s}/sketches/{1:d}/'.format(
            self.api.api_root, self.id)

        data = {
            'labels': [label],
            'label_action': 'add',
        }
        response = self.api.session.post(resource_url, json=data)

        status = error.check_return_status(response, logger)
        if not status:
            logger.error('Unable to add the label to the sketch.')

        return status

    def remove_attribute(self, name):
        """Remove an attribute from the sketch.

        Args:
            name (str): The name of the attribute.

        Raises:
            ValueError: If any of the parameters are of the wrong type.

        Returns:
            Boolean value whether the attribute was successfully
            removed or not.
        """
        if not isinstance(name, str):
            raise ValueError('Name needs to be a string.')

        resource_url = '{0:s}/sketches/{1:d}/attribute/'.format(
            self.api.api_root, self.id)

        data = {
            'name': name,
            'ontology': 'text',
            'action': 'delete',
        }
        response = self.api.session.post(resource_url, json=data)

        status = error.check_return_status(response, logger)
        if not status:
            logger.error('Unable to remove the attriubute from the sketch.')

        return status

    def remove_sketch_label(self, label):
        """Remove a label from the sketch.

        Args:
            label (str): A string with the label to remove from the sketch.

        Returns:
            bool: A boolean to indicate whether the label was successfully
                  removed from the sketch.
        """
        if label not in self.labels:
            logger.error(
                'Unable to remove label [{0:s}], not a label '
                'attached to this sketch.'.format(label))
            return False

        resource_url = '{0:s}/sketches/{1:d}/'.format(
            self.api.api_root, self.id)

        data = {
            'labels': [label],
            'label_action': 'remove',
        }
        response = self.api.session.post(resource_url, json=data)

        status = error.check_return_status(response, logger)
        if not status:
            logger.error('Unable to remove the label from the sketch.')

        return status

    def create_view(
            self, name, query_string='', query_dsl='', query_filter=None):
        """Create a view object.

        Args:
            name (str): the name of the view.
            query_string (str): Elasticsearch query string. This is optional
                yet either a query string or a query DSL is required.
            query_dsl (str): Elasticsearch query DSL as JSON string. This is
                optional yet either a query string or a query DSL is required.
            query_filter (dict): Filter for the query as a dict.

        Raises:
            ValueError: if neither query_string nor query_dsl is provided or
                if query_filter is not a dict.
            RuntimeError: if a view wasn't created for some reason.
        """
        if not (query_string or query_dsl):
            raise ValueError('You need to supply a query string or a dsl')

        if self.is_archived():
            raise RuntimeError('Unable create a view on an archived sketch.')

        resource_url = '{0:s}/sketches/{1:d}/views/'.format(
            self.api.api_root, self.id)

        if not query_filter:
            query_filter = {
                'time_start': None,
                'time_end': None,
                'size': 100,
                'terminate_after': 100,
                'indices': '_all',
                'order': 'asc'
            }

        if not isinstance(query_filter, dict):
            raise ValueError(
                'Unable to query with a query filter that isn\'t a dict.')

        data = {
            'name': name,
            'query': query_string,
            'filter': query_filter,
            'dsl': query_dsl,
        }
        response = self.api.session.post(resource_url, json=data)

        status = error.check_return_status(response, logger)
        if not status:
            error.error_message(
                response, 'Unable to create view', error=RuntimeError)

        response_json = error.get_response_json(response, logger)
        view_dict = response_json.get('objects', [{}])[0]
        return view_lib.View(
            view_id=view_dict.get('id'),
            view_name=name,
            sketch_id=self.id,
            api=self.api)

    def create_story(self, title):
        """Create a story object.

        Args:
            title: the title of the story.

        Raises:
            RuntimeError: if a story wasn't created for some reason.

        Returns:
            A story object (instance of Story) for the newly
            created story.
        """
        if self.is_archived():
            raise RuntimeError(
                'Unable to create a story in an archived sketch.')

        resource_url = '{0:s}/sketches/{1:d}/stories/'.format(
            self.api.api_root, self.id)
        data = {
            'title': title,
            'content': ''
        }

        response = self.api.session.post(resource_url, json=data)

        status = error.check_return_status(response, logger)
        if not status:
            error.error_message(
                response, 'Unable to create a story', error=RuntimeError)

        response_json = error.get_response_json(response, logger)
        story_dict = response_json.get('objects', [{}])[0]
        return story.Story(
            story_id=story_dict.get('id', 0),
            sketch=self,
            api=self.api)

    def delete(self):
        """Deletes the sketch."""
        if self.is_archived():
            raise RuntimeError(
                'Unable to delete an archived sketch, first '
                'unarchive then delete.')

        resource_url = '{0:s}/sketches/{1:d}/'.format(
            self.api.api_root, self.id)
        response = self.api.session.delete(resource_url)
        return error.check_return_status(response, logger)

    def add_to_acl(
            self, user_list=None, group_list=None,
            make_public=False, permissions=None):
        """Add users or groups to the sketch ACL.

        Args:
            user_list: optional list of users to add to the ACL
                of the sketch. Each user is a string.
            group_list: optional list of groups to add to the ACL
                of the sketch. Each user is a string.
            make_public: Optional boolean indicating the sketch should be
                marked as public.
            permissions: optional list of permissions (read, write, delete).
                If not the default set of permissions are applied (read, write)

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

        if permissions:
            allowed_permissions = set(['read', 'write', 'delete'])
            use_permissions = list(
                allowed_permissions.intersection(set(permissions)))
            if set(use_permissions) != set(permissions):
                logger.warning('Some permissions are invalid: {0:s}'.format(
                    ', '.join(list(
                        set(permissions).difference(set(use_permissions))))))

            if not use_permissions:
                logger.error('No permissions left to add.')
                return False

            data['permissions'] = json.dumps(use_permissions)

        if not data:
            return True

        response = self.api.session.post(resource_url, json=data)
        # Refresh the sketch data to reflect ACL changes.
        _ = self.lazyload_data(refresh_cache=True)
        return error.check_return_status(response, logger)

    def list_aggregation_groups(self):
        """List all saved aggregation groups for this sketch.

        Returns:
            List of aggregation groups (instances of AggregationGroup objects)
        """
        if self.is_archived():
            raise RuntimeError(
                'Unable to list aggregation groups on an archived sketch.')
        groups = []
        resource_url = '{0:s}/sketches/{1:d}/aggregation/group/'.format(
            self.api.api_root, self.id)
        response = self.api.session.get(resource_url)
        data = error.get_response_json(response, logger)
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
        if self.is_archived():
            raise RuntimeError(
                'Unable to list aggregations on an archived sketch.')
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

    def get_analyzer_status(self, as_sessions=False):
        """Returns a list of started analyzers and their status.

        Args:
            as_sessions (bool): optional, if set to True then a list of
                AnalyzerResult objects will be returned. Defaults to
                returning a list of dicts.
        Returns:
            If "as_sessions" is set then a list of AnalyzerResult gets
            returned, otherwise a list of dict objects that contains
            status information of each analyzer run. The dict contains
            information about what timeline it ran against, the
            results and current status of the analyzer run.
        """
        if self.is_archived():
            raise RuntimeError(
                'Unable to list analyzer status on an archived sketch.')
        stats_list = []
        sessions = []
        for timeline_obj in self.list_timelines():
            resource_uri = (
                '{0:s}/sketches/{1:d}/timelines/{2:d}/analysis').format(
                    self.api.api_root, self.id, timeline_obj.id)
            response = self.api.session.get(resource_uri)
            response_json = error.get_response_json(response, logger)
            objects = response_json.get('objects')
            if not objects:
                continue
            for result in objects[0]:
                session_id = result.get('analysissession_id')
                stat = {
                    'index': timeline_obj.index,
                    'timeline_id': timeline_obj.id,
                    'session_id': session_id,
                    'analyzer': result.get('analyzer_name', 'N/A'),
                    'results': result.get('result', 'N/A'),
                    'status': 'N/A',
                }
                if as_sessions and session_id:
                    sessions.append(analyzer.AnalyzerResult(
                        timeline_id=timeline_obj.id, session_id=session_id,
                        sketch_id=self.id, api=self.api))
                status = result.get('status', [])
                if len(status) == 1:
                    stat['status'] = status[0].get('status', 'N/A')
                stats_list.append(stat)

        if as_sessions:
            return sessions

        return stats_list

    def get_aggregation(self, aggregation_id):
        """Return a stored aggregation.

        Args:
            aggregation_id: id of the stored aggregation.

        Returns:
            An aggregation object, if stored (instance of Aggregation),
            otherwise None object.
        """
        if self.is_archived():
            raise RuntimeError(
                'Unable to get aggregations on an archived sketch.')
        for aggregation_obj in self.list_aggregations():
            if aggregation_obj.id == aggregation_id:
                return aggregation_obj
        return None

    def get_aggregation_group(self, group_id):
        """Return a stored aggregation group.

        Args:
            group_id: id of the stored aggregation group.

        Returns:
            An aggregation group object (instance of AggregationGroup)
            if stored, otherwise None object.
        """
        if self.is_archived():
            raise RuntimeError(
                'Unable to get aggregation groups on an archived sketch.')

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
        if self.is_archived():
            raise RuntimeError(
                'Unable to get stories on an archived sketch.')

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
        if self.is_archived():
            raise RuntimeError(
                'Unable to get views on an archived sketch.')

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
        if self.is_archived():
            raise RuntimeError(
                'Unable to list stories on an archived sketch.')

        story_list = []
        resource_url = '{0:s}/sketches/{1:d}/stories/'.format(
            self.api.api_root, self.id)
        response = self.api.session.get(resource_url)
        response_json = error.get_response_json(response, logger)
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
        if self.is_archived():
            raise RuntimeError(
                'Unable to list views on an archived sketch.')

        sketch = self.lazyload_data()
        views = []
        for view in sketch['meta'].get('views', []):
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
        if self.is_archived():
            raise RuntimeError(
                'Unable to list timelines on an archived sketch.')

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
        """Upload a CSV, JSONL or Plaso file to the server for indexing.

        Args:
            timeline_name: Name of the resulting timeline.
            file_path: Path to the file to be uploaded.
            index: Index name for the ES database

        Returns:
            Timeline object instance.
        """
        if self.is_archived():
            raise RuntimeError(
                'Unable to upload files to an archived sketch.')

        # TODO: Deprecate this function.
        logger.warning(
            'This function is about to be deprecated, please use the '
            'timesketch_import_client instead')

        resource_url = '{0:s}/upload/'.format(self.api.api_root)
        files = {'file': open(file_path, 'rb')}
        data = {'name': timeline_name, 'sketch_id': self.id,
                'index_name': index}
        response = self.api.session.post(resource_url, files=files, data=data)
        response_dict = error.get_response_json(response, logger)
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
        if self.is_archived():
            raise RuntimeError(
                'Unable to add a timeline to an archived sketch.')

        resource_url = '{0:s}/sketches/{1:d}/timelines/'.format(
            self.api.api_root, self.id)
        form_data = {'timeline': searchindex.id}
        response = self.api.session.post(resource_url, json=form_data)

        if response.status_code not in definitions.HTTP_STATUS_CODE_20X:
            error.error_message(
                response, message='Failed adding timeline',
                error=RuntimeError)

        response_dict = error.get_response_json(response, logger)
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
                max_entries=None,
                file_name=''):
        """Explore the sketch.

        Args:
            query_string (str): Elasticsearch query string.
            query_dsl (str): Elasticsearch query DSL as JSON string.
            query_filter (dict): Filter for the query as a dict.
            view: View object instance (optional).
            return_fields (str): A comma separated string with a list of fields
                that should be included in the response. Optional and defaults
                to None.
            as_pandas (bool): Optional bool that determines if the results
                should be returned back as a dictionary or a Pandas DataFrame.
            max_entries (int): Optional integer denoting a best effort to limit
                the output size to the number of events. Events are read in,
                10k at a time so there may be more events in the answer back
                than this number denotes, this is a best effort.
            file_name (str): Optional filename, if provided the results of
                the query will be exported to a ZIP file instead of being
                returned back as a dict or a pandas DataFrame. The ZIP file
                will contain a METADATA file and a CSV with the results from
                the query.

        Returns:
            Dictionary with query results or a pandas DataFrame if as_pandas
            is set to True. If file_name is provided then no value will be
            returned.

        Raises:
            ValueError: if unable to query for the results.
            RuntimeError: if the query is missing needed values, or if the
                sketch is archived.
        """
        if not (query_string or query_filter or query_dsl or view):
            raise RuntimeError('You need to supply a query or view')

        if self.is_archived():
            raise RuntimeError('Unable to query an archived sketch.')

        if query_filter:
            stop_size = query_filter.get('size', 0)
            terminate_after = query_filter.get('terminate_after', 0)
            if terminate_after and (terminate_after < stop_size):
                stop_size = terminate_after

            scrolling = not bool(stop_size and (
                stop_size < self.DEFAULT_SIZE_LIMIT))
        else:
            scrolling = True
            stop_size = 0
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
            'enable_scroll': scrolling,
            'file_name': file_name,
        }

        response = self.api.session.post(resource_url, json=form_data)
        if not error.check_return_status(response, logger):
            error.error_message(
                response, message='Unable to query results',
                error=ValueError)

        if file_name:
            with open(file_name, 'wb') as fw:
                fw.write(response.content)
            return True

        response_json = error.get_response_json(response, logger)

        scroll_id = response_json.get('meta', {}).get('scroll_id', '')
        form_data['scroll_id'] = scroll_id

        count = len(response_json.get('objects', []))
        total_count = count
        while count > 0:
            if max_entries and total_count >= max_entries:
                break
            if stop_size and total_count >= stop_size:
                break

            if not scroll_id:
                logger.debug('No scroll ID, will stop.')
                break

            more_response = self.api.session.post(resource_url, json=form_data)
            if not error.check_return_status(more_response, logger):
                error.error_message(
                    response, message='Unable to query results',
                    error=ValueError)
            more_response_json = error.get_response_json(more_response, logger)
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

        return error.get_response_json(response, logger)

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

        Raises:
            error.UnableToRunAnalyzer: if not able to run the analyzer.

        Returns:
            If the analyzer runs successfully return back an AnalyzerResult
            object.
        """
        if self.is_archived():
            raise error.UnableToRunAnalyzer(
                'Unable to run an analyzer on an archived sketch.')

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
                raise error.UnableToRunAnalyzer(
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
                raise error.UnableToRunAnalyzer(
                    'No timelines with the name: {0:s} were found'.format(
                        timeline_name))

            if len(timelines) != 1:
                raise error.UnableToRunAnalyzer(
                    'There are {0:d} timelines defined in the sketch with '
                    'this name, please use a unique name or a '
                    'timeline ID'.format(len(timelines)))

            timeline_id = timelines[0]

        data = {
            'timeline_id': timeline_id,
            'analyzer_names': [analyzer_name],
            'analyzer_kwargs': analyzer_kwargs,
        }

        response = self.api.session.post(resource_url, json=data)

        if not error.check_return_status(response, logger):
            raise error.UnableToRunAnalyzer('[{0:d}] {1!s} {2!s}'.format(
                response.status_code, response.reason, response.text))

        data = error.get_response_json(response, logger)
        objects = data.get('objects', [])
        if not objects:
            raise error.UnableToRunAnalyzer(
                'No session data returned back, analyzer may have run but '
                'unable to verify, please verify manually.')

        session_id = objects[0].get('analysis_session')
        if not session_id:
            raise error.UnableToRunAnalyzer(
                'Analyzer may have run, but there is no session ID to '
                'verify that it has. Please verify manually.')

        session = analyzer.AnalyzerResult(
            timeline_id=timeline_id, session_id=session_id,
            sketch_id=self.id, api=self.api)
        return session

    def remove_acl(
            self, user_list=None, group_list=None, remove_public=False,
            permissions=None):
        """Remove users or groups to the sketch ACL.

        Args:
            user_list: optional list of users to remove from the ACL
                of the sketch. Each user is a string.
            group_list: optional list of groups to remove from the ACL
                of the sketch. Each user is a string.
            remove_public: Optional boolean indicating the sketch should be
                no longer marked as public.
            permissions: optional list of permissions (read, write, delete).
                If not the default set of permissions are applied (read, write)

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

        if permissions:
            allowed_permissions = set(['read', 'write', 'delete'])
            permissions = list(
                allowed_permissions.intersection(set(permissions)))
            data['permissions'] = json.dumps(permissions)

        if not data:
            return True

        response = self.api.session.post(resource_url, json=data)
        # Refresh the sketch data to reflect ACL changes.
        _ = self.lazyload_data(refresh_cache=True)
        return error.check_return_status(response, logger)

    def aggregate(self, aggregate_dsl):
        """Run an aggregation request on the sketch.

        Args:
            aggregate_dsl: Elasticsearch aggregation query DSL string.

        Returns:
            An aggregation object (instance of Aggregation).

        Raises:
            ValueError: if unable to query for the results.
        """
        if self.is_archived():
            raise ValueError(
                'Unable to run an aggregation on an archived sketch.')

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
        if self.is_archived():
            raise RuntimeError(
                'Unable to run an aggregator on an archived sketch.')

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
        if self.is_archived():
            raise RuntimeError(
                'Unable to store an aggregator on an archived sketch.')

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
        if self.is_archived():
            raise RuntimeError(
                'Unable to comment on an event in an archived sketch.')

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
        return error.get_response_json(response, logger)

    def label_events(self, events, label_name):
        """Labels one or more events with label_name.

        Args:
            events: Array of JSON objects representing events.
            label_name: String to label the event with.

        Returns:
            Dictionary with query results.
        """
        if self.is_archived():
            raise RuntimeError(
                'Unable to label events in an archived sketch.')

        form_data = {
            'annotation': label_name,
            'annotation_type': 'label',
            'events': events
        }
        resource_url = '{0:s}/sketches/{1:d}/event/annotate/'.format(
            self.api.api_root, self.id)
        response = self.api.session.post(resource_url, json=form_data)
        return error.get_response_json(response, logger)

    def tag_events(self, events, tags, verbose=False):
        """Tags one or more events with a list of tags.

        Args:
            events: Array of JSON objects representing events.
            tags: List of tags (str) to add to the events.
            verbose: Bool that determines whether extra information
                is added to the meta dict that gets returned.

        Raises:
            ValueError: if tags is not a list of strings.
            RuntimeError: if the sketch is archived.

        Returns:
            A dict with the results from the tagging operation.
        """
        if self.is_archived():
            raise RuntimeError(
                'Unable to tag events in an archived sketch.')

        if not isinstance(tags, list):
            raise ValueError('Tags need to be a list.')

        if not all([isinstance(x, str) for x in tags]):
            raise ValueError('Tags need to be a list of strings.')

        form_data = {
            'tag_string': json.dumps(tags),
            'events': events,
            'verbose': verbose,
        }
        resource_url = '{0:s}/sketches/{1:d}/event/tagging/'.format(
            self.api.api_root, self.id)
        response = self.api.session.post(resource_url, json=form_data)
        status = error.check_return_status(response, logger)
        if not status:
            return {
                'number_of_events': len(events),
                'number_of_events_with_tag': 0,
                'success': status
            }

        response_json = error.get_response_json(response, logger)
        meta = response_json.get('meta', {})
        meta['total_number_of_events_sent_by_client'] = len(events)
        return meta

    def search_by_label(
            self, label_name, return_fields=None, max_entries=None,
            as_pandas=False):
        """Searches for all events containing a given label.

        Args:
            label_name: A string representing the label to search for.
            return_fields (str): A comma separated string with a list of fields
                that should be included in the response. Optional and defaults
                to None.
            max_entries (int): Optional integer denoting a best effort to limit
                the output size to the number of events. Events are read in,
                10k at a time so there may be more events in the answer back
                than this number denotes, this is a best effort.
            as_pandas: Optional bool that determines if the results should
                be returned back as a dictionary or a Pandas DataFrame.

        Returns:
            A dictionary with query results.
        """
        if self.is_archived():
            raise RuntimeError(
                'Unable to search for labels in an archived sketch.')

        query = {
            'nested': {
                'path': 'timesketch_label',
                'query': {
                    'bool': {
                        'must': [
                            {
                                'term': {
                                    'timesketch_label.name': label_name
                                }
                            },
                            {
                                'term': {
                                    'timesketch_label.sketch_id': self.id
                                }
                            }
                        ]
                    }
                }
            }
        }
        return self.explore(
            query_dsl=json.dumps({'query': query}), return_fields=return_fields,
            max_entries=max_entries, as_pandas=as_pandas)

    def add_event(
            self, message, date, timestamp_desc, attributes=None,
            tags=None):
        """Adds an event to the sketch specific timeline.

        Args:
            message: A string that will be used as the message string.
            date: A string with the timestamp of the message. This should be
                in a human readable format, eg: "2020-09-03T22:52:21".
            timestamp_desc : Description of the timestamp.
            attributes: A dict of extra attributes to add to the event.
            tags: A list of strings to include as tags.

        Raises:
            ValueError: If tags is not a list of strings or attributes
                is not a dict.

        Returns:
            Dictionary with query results.
        """
        if self.is_archived():
            raise RuntimeError(
                'Unable to add an event to an archived sketch.')

        if tags is None:
            tags = []

        if not isinstance(tags, list):
            raise ValueError('Tags needs to be a list.')

        if any([not isinstance(tag, str) for tag in tags]):
            raise ValueError('Tags needs to be a list of strings.')

        if attributes is None:
            attributes = {}

        if not isinstance(attributes, dict):
            raise ValueError('Attributes needs to be a dict.')

        form_data = {
            'date_string': date,
            'timestamp_desc': timestamp_desc,
            'message': message,
            'tag': tags
        }
        if any([x in attributes for x in form_data]):
            raise ValueError('Attributes cannot overwrite values already set.')

        form_data['attributes'] = attributes

        resource_url = '{0:s}/sketches/{1:d}/event/create/'.format(
            self.api.api_root, self.id)
        response = self.api.session.post(resource_url, json=form_data)
        return error.get_response_json(response, logger)

    def is_archived(self):
        """Return a boolean indicating whether the sketch has been archived."""
        if self._archived is not None:
            return self._archived

        resource_url = '{0:s}/sketches/{1:d}/archive/'.format(
            self.api.api_root, self.id)
        response = self.api.session.get(resource_url)
        data = error.get_response_json(response, logger)
        meta = data.get('meta', {})
        self._archived = meta.get('is_archived', False)
        return self._archived

    def archive(self):
        """Archive a sketch and return a boolean whether it was succesful."""
        if self.is_archived():
            logger.error('Sketch already archived.')
            return False

        resource_url = '{0:s}/sketches/{1:d}/archive/'.format(
            self.api.api_root, self.id)
        data = {
            'action': 'archive'
        }
        response = self.api.session.post(resource_url, json=data)
        return_status = error.check_return_status(response, logger)
        self._archived = return_status

        return return_status

    def unarchive(self):
        """Unarchives a sketch and return boolean whether it was succesful."""
        if not self.is_archived():
            logger.error('Sketch wasn\'t archived.')
            return False

        resource_url = '{0:s}/sketches/{1:d}/archive/'.format(
            self.api.api_root, self.id)
        data = {
            'action': 'unarchive'
        }
        response = self.api.session.post(resource_url, json=data)
        return_status = error.check_return_status(response, logger)

        # return_status = True means unarchive is successful or that
        # the archive status is False.
        self._archived = not return_status
        return return_status

    def export(self, file_path):
        """Exports the content of the story to a ZIP file.

        Args:
            file_path (str): a file path where the ZIP file will be saved.

        Raises:
            RuntimeError: if sketch cannot be exported.
        """
        directory = os.path.dirname(file_path)
        if not os.path.isdir(directory):
            raise RuntimeError(
                'The directory needs to exist, please create: '
                '{0:s} first'.format(directory))

        if not file_path.lower().endswith('.zip'):
            logger.warning('File does not end with a .zip, adding it.')
            file_path = '{0:s}.zip'.format(file_path)

        if os.path.isfile(file_path):
            raise RuntimeError('File [{0:s}] already exists.'.format(file_path))

        form_data = {
            'action': 'export'
        }
        resource_url = '{0:s}/sketches/{1:d}/archive/'.format(
            self.api.api_root, self.id)

        response = self.api.session.post(resource_url, json=form_data)
        status = error.check_return_status(response, logger)
        if not status:
            error.error_message(
                response, message='Failed exporting the sketch',
                error=RuntimeError)

        with open(file_path, 'wb') as fw:
            fw.write(response.content)
