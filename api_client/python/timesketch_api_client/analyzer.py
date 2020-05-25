# Copyright 2020 Google Inc. All rights reserved.
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
"""Timesketch API analyzer result object."""
from __future__ import unicode_literals

import json
import logging

from . import definitions
from . import resource

logger = logging.getLogger('analyzer_results')


class AnalyzerResult(resource.BaseResource):
    """Class to store and retrieve session information for an analyzer."""

    def __init__(self, timeline_id, session_id, sketch_id, api):
        """Initialize the class."""
        self._session_id = session_id
        self._sketch_id = sketch_id
        self._timeline_id = timeline_id
        resource_uri = (
            '{0:s}/sketches/{1:d}/timelines/{2:d}/analysis/').format(
                api.api_root, sketch_id, timeline_id)
        super(AnalyzerResult, self).__init__(api, resource_uri)

    def _fetch_data(self):
        """Returns..."""
        response = self.api.session.get(self.resource_uri)
        if not response.status_code in definitions.HTTP_STATUS_CODE_20X:
            return {}

        data = response.json()

        objects = data.get('objects')
        if not objects:
            return {}

        for result in objects[0]:
            result_id = result.get('id')
            if result_id != self._session_id:
                continue
            status_list = result.get('status', [])
            if len(status_list) != 1:
                return {}
            status = status_list[0]

            timeline = result.get('timeline', {})

            return {
                'id': status.get('id', -1),
                'rid': result_id,
                'analyzer': result.get('analyzer_name', 'N/A'),
                'results': result.get('result'),
                'description': result.get('description', 'N/A'),
                'timeline': timeline.get('name', 'N/A'),
                'user': result.get('user', {}).get('username', 'System'),
                'parameters': json.loads(result.get('parameters', '{}')),
                'status': status.get('status', 'Unknown'),
            }

        return {}

    @property
    def id(self):
        """Returns the session ID."""
        return self._session_id

    @property
    def results(self):
        """Returns the results from the analyzer session."""
        data = self._fetch_data()
        return data.get('results', 'No results yet.')

    @property
    def status(self):
        """Returns the current status of the analyzer run."""
        data = self._fetch_data()
        return data.get('status', 'Unknown')
