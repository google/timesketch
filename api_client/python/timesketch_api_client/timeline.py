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
import logging

from . import analyzer
from . import error
from . import index
from . import resource


logger = logging.getLogger('timesketch_api.timeline')


class Timeline(resource.BaseResource):
    """Timeline object.

    Attributes:
        id: Primary key of the timeline.
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
        self._color = ''
        self._name = name
        self._description = ''
        self._searchindex = searchindex
        self._sketch_id = sketch_id
        resource_uri = 'sketches/{0:d}/timelines/{1:d}/'.format(
            sketch_id, self.id)
        super().__init__(api, resource_uri)

    @property
    def labels(self):
        """Property that returns the timeline labels."""
        data = self.lazyload_data(refresh_cache=True)
        objects = data.get('objects', [])
        if not objects:
            return []

        timeline_data = objects[0]
        label_string = timeline_data.get('label_string', '')
        if label_string:
            return json.loads(label_string)

        return []

    @property
    def color(self):
        """Property that returns timeline color.

        Returns:
            Color name as string.
        """
        if not self._color:
            timeline = self.lazyload_data()
            self._color = timeline['objects'][0]['color']
        return self._color

    @property
    def description(self):
        """Property that returns timeline description.

        Returns:
            Description as string.
        """
        if not self._description:
            timeline = self.lazyload_data()
            self._description = timeline['objects'][0]['description']
        return self._description

    @description.setter
    def description(self, description):
        """Change the timeline description."""
        self._description = description
        self._commit()

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

    @name.setter
    def name(self, name):
        """Change the name of the timeline."""
        self._name = name
        self._commit()

    @property
    def index(self):
        """Property that returns index object.

        Returns:
            Index (instance of SearchIndex) object.
        """
        timeline = self.lazyload_data()
        objects = timeline.get('objects')
        if not objects:
            return None

        index_dict = objects[0].get('searchindex', {})

        return index.SearchIndex(
            index_dict.get('id'),
            api=self.api,
            searchindex_name=index_dict.get('index_name'))

    @property
    def index_name(self):
        """Property that returns index name.

        Returns:
            Elasticsearch index name as string.
        """
        if not self._searchindex:
            timeline = self.lazyload_data()
            index_name = timeline['objects'][0]['searchindex']['index_name']
            self._searchindex = index_name
        return self._searchindex

    def is_archived(self):
        """Return a boolean indicating whether the timeline is archived."""
        resource_url = (
            f'{self.api.api_root}/sketches/{self._sketch_id}/archive/')
        response = self.api.session.get(resource_url)
        data = error.get_response_json(response, logger)
        meta = data.get('meta', {})
        sketch_is_archived = meta.get('is_archived', False)

        timeline_dict = meta.get('timelines')
        if not timeline_dict:
            return sketch_is_archived
        return timeline_dict.get(self.index_name)

    def run_analyzer(
            self, analyzer_name, analyzer_kwargs=None, ignore_previous=False):
        """Run an analyzer on a timeline.

        Args:
            analyzer_name: a name of an analyzer class to run against the
                timeline.
            analyzer_kwargs: optional dict with parameters for the analyzer.
                This is optional and just for those analyzers that can accept
                further parameters.
            ignore_previous (bool): an optional bool, if set to True then
                analyzer is run irrelevant on whether it has been previously
                been run.

        Raises:
            error.UnableToRunAnalyzer: if not able to run the analyzer.

        Returns:
            If the analyzer runs successfully return back an AnalyzerResult
            object.
        """
        if self.is_archived():
            raise error.UnableToRunAnalyzer(
                'Unable to run an analyzer on an archived timeline.')

        if analyzer_kwargs:
            if not isinstance(analyzer_kwargs, dict):
                raise error.UnableToRunAnalyzer(
                    'Unable to run analyzer, analyzer kwargs needs to be a '
                    'dict')

            if analyzer_name not in analyzer_kwargs:
                analyzer_kwargs = {analyzer_name: analyzer_kwargs}
            elif not isinstance(analyzer_kwargs[analyzer_name], dict):
                raise error.UnableToRunAnalyzer(
                    'Unable to run analyzer, analyzer kwargs needs to be a '
                    'dict where the value for the analyzer is also a dict.')

        return self.run_analyzers(
            analyzer_names=[analyzer_name], analyzer_kwargs=analyzer_kwargs,
            ignore_previous=ignore_previous)


    def run_analyzers(
            self, analyzer_names, analyzer_kwargs=None, ignore_previous=False):
        """Run an analyzer on a timeline.

        Args:
            analyzer_names: a list of analyzer class names to run against the
                timeline.
            analyzer_kwargs: optional dict with parameters for the analyzer.
                This is optional and just for those analyzers that can accept
                further parameters. It is expected that this is a dict with
                the key value being the analyzer name, and the value being
                another key/value dict with the parameters for that analyzer.
            ignore_previous (bool): an optional bool, if set to True then
                analyzer is run irrelevant on whether it has been previously
                been run.

        Raises:
            error.UnableToRunAnalyzer: if not able to run the analyzer.

        Returns:
            If the analyzer runs successfully return back an AnalyzerResult
            object.
        """
        if self.is_archived():
            raise error.UnableToRunAnalyzer(
                'Unable to run an analyzer on an archived timeline.')

        resource_url = '{0:s}/sketches/{1:d}/analyzer/'.format(
            self.api.api_root, self._sketch_id)

        if not ignore_previous:
            all_names = {x.lower() for x in analyzer_names}
            done_names = set()

            response = self.api.fetch_resource_data(
                f'sketches/{self._sketch_id}/timelines/{self.id}/analysis/')
            analyzer_data = response.get('objects', [[]])

            if analyzer_data:
                for result in analyzer_data[0]:
                    result_analyzer = result.get('analyzer_name', 'N/A')
                    done_names.add(result_analyzer.lower())

            analyzer_names = list(all_names.difference(done_names))
            for name in all_names.intersection(done_names):
                logger.error(
                    f'Analyzer {0:s} has already been run on the timeline, '
                    'use "ignore_previous=True" to overwrite'.format(
                        name))

            if not analyzer_names:
                return None

        data = {
            'timeline_id': self.id,
            'analyzer_names': analyzer_names,
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
            timeline_id=self.id, session_id=session_id,
            sketch_id=self._sketch_id, api=self.api)
        return session

    @property
    def status(self):
        """Property that returns the timeline status.

        Returns:
            String with the timeline status.
        """
        data = self.lazyload_data(refresh_cache=True)
        timeline_object = data.get('objects', [{}])[0]
        status_list = timeline_object.get('status')

        if not status_list:
            return 'Unknown'

        status = status_list[0]
        return status.get('status')

    def _commit(self):
        """Commit changes to the timeline."""
        resource_url = '{0:s}/{1:s}'.format(
            self.api.api_root, self.resource_uri)

        data = {
            'name': self.name,
            'description': self.description,
            'color': self.color,
        }
        response = self.api.session.post(resource_url, json=data)

        status = error.check_return_status(response, logger)
        if not status:
            logger.error('Unable to commit changes to the timeline.')

        return status

    def add_timeline_label(self, label):
        """Add a label to the timelinne.

        Args:
            label (str): A string with the label to add to the timeline.

        Returns:
            bool: A boolean to indicate whether the label was successfully
                  added to the timeline.
        """
        if label in self.labels:
            logger.error(
                'Label [{0:s}] already applied to timeline.'.format(label))
            return False

        resource_url = '{0:s}/{1:s}'.format(
            self.api.api_root, self.resource_uri)

        data = {
            'name': self.name,
            'description': self.description,
            'color': self.color,
            'labels': json.dumps([label]),
            'label_action': 'add',
        }
        response = self.api.session.post(resource_url, json=data)

        status = error.check_return_status(response, logger)
        if not status:
            logger.error('Unable to add the label to the timeline.')

        return status

    def remove_timeline_label(self, label):
        """Remove a label from the timeline.

        Args:
            label (str): A string with the label to remove from the timeline.

        Returns:
            bool: A boolean to indicate whether the label was successfully
                  removed from the timeline.
        """
        if label not in self.labels:
            logger.error(
                'Unable to remove label [{0:s}], not a label '
                'attached to this timeline.'.format(label))
            return False

        resource_url = '{0:s}/{1:s}'.format(
            self.api.api_root, self.resource_uri)

        data = {
            'name': self.name,
            'description': self.description,
            'color': self.color,
            'labels': json.dumps([label]),
            'label_action': 'remove',
        }
        response = self.api.session.post(resource_url, json=data)

        status = error.check_return_status(response, logger)
        if not status:
            logger.error('Unable to remove the label from the sketch.')

        return status

    def delete(self):
        """Deletes the timeline."""
        resource_url = '{0:s}/{1:s}'.format(
            self.api.api_root, self.resource_uri)
        response = self.api.session.delete(resource_url)
        return error.check_return_status(response, logger)
