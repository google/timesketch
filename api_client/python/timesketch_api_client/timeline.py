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

from . import error
from . import resource


logger = logging.getLogger('timesketch_api.timeline')


class Timeline(resource.BaseResource):
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
        self._labels = []
        self._name = name
        self._searchindex = searchindex
        resource_uri = 'sketches/{0:d}/timelines/{1:d}/'.format(
            sketch_id, self.id)
        super(Timeline, self).__init__(api, resource_uri)

    @property
    def labels(self):
        """Property that returns the timeline labels."""
        if self._labels:
            return self._labels

        data = self.lazyload_data()
        objects = data.get('objects', [])
        if not objects:
            return self._labels

        timeline_data = objects[0]
        label_string = timeline_data.get('label_string', '')
        if label_string:
            self._labels = json.loads(label_string)
        else:
            self._labels = []

        return self._labels

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

    @property
    def status(self):
        """Property that returns the timeline status.

        Returns:
            String with the timeline status.
        """
        data = self.data
        timeline_object = data.get('objects', [{}])[0]
        status_list = timeline_object.get('status')

        if not status_list:
            return 'Unknown'

        status = status_list[0]
        return status.get('status')

    def delete(self):
        """Deletes the timeline."""
        resource_url = '{0:s}/{1:s}'.format(
            self.api.api_root, self.resource_uri)
        response = self.api.session.delete(resource_url)
        return error.check_return_status(response, logger)
