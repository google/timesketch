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
"""Analysis resources for version 1 of the Timesketch API."""

from flask import jsonify
from flask import request
from flask import abort
from flask_restful import Resource
from flask_login import login_required
from flask_login import current_user

from timesketch.api.v1 import resources
from timesketch.lib.analyzers import manager as analyzer_manager
from timesketch.lib.definitions import HTTP_STATUS_CODE_BAD_REQUEST
from timesketch.lib.definitions import HTTP_STATUS_CODE_FORBIDDEN
from timesketch.lib.definitions import HTTP_STATUS_CODE_NOT_FOUND
from timesketch.models.sketch import Analysis
from timesketch.models.sketch import AnalysisSession
from timesketch.models.sketch import Sketch
from timesketch.models.sketch import Timeline


class AnalysisResource(resources.ResourceMixin, Resource):
    """Resource to get analyzer session."""

    @login_required
    def get(self, sketch_id, timeline_id):
        """Handles GET request to the resource.

        Returns:
            An analysis in JSON (instance of flask.wrappers.Response)
        """
        sketch = Sketch.query.get_with_acl(sketch_id)
        if not sketch:
            abort(
                HTTP_STATUS_CODE_NOT_FOUND, 'No sketch found with this ID.')

        if not sketch:
            abort(
                HTTP_STATUS_CODE_NOT_FOUND, 'No sketch found with this ID.')

        if not sketch.has_permission(current_user, 'read'):
            abort(
                HTTP_STATUS_CODE_FORBIDDEN,
                'User does not have read access to sketch')

        timeline = Timeline.query.get(timeline_id)
        if not timeline:
            abort(
                HTTP_STATUS_CODE_NOT_FOUND, 'No timeline found with this ID.')

        analysis_history = Analysis.query.filter_by(timeline=timeline).all()

        return self.to_json(analysis_history)


class AnalyzerSessionResource(resources.ResourceMixin, Resource):
    """Resource to get analyzer session."""

    @login_required
    def get(self, sketch_id, session_id):
        """Handles GET request to the resource.

        Returns:
            A analyzer session in JSON (instance of flask.wrappers.Response)
        """
        sketch = Sketch.query.get_with_acl(sketch_id)

        if not sketch:
            abort(
                HTTP_STATUS_CODE_NOT_FOUND, 'No sketch found with this ID.')

        if not sketch.has_permission(current_user, 'read'):
            abort(
                HTTP_STATUS_CODE_FORBIDDEN,
                'User does not have read access to sketch')

        analysis_session = AnalysisSession.query.get(session_id)

        return self.to_json(analysis_session)


class AnalyzerRunResource(resources.ResourceMixin, Resource):
    """Resource to list or run analyzers for sketch."""

    @login_required
    def get(self, sketch_id):
        """Handles GET request to the resource.

        Returns:
            A list of all available analyzer names.
        """
        sketch = Sketch.query.get_with_acl(sketch_id)
        if not sketch:
            abort(
                HTTP_STATUS_CODE_NOT_FOUND, 'No sketch found with this ID.')
        if not sketch.has_permission(current_user, 'read'):
            abort(
                HTTP_STATUS_CODE_FORBIDDEN,
                'User does not have read access to sketch')
        analyzers = [
            x for x, y in analyzer_manager.AnalysisManager.get_analyzers()]

        return analyzers

    @login_required
    def post(self, sketch_id):
        """Handles POST request to the resource.

        Returns:
            A string with the response from running the analyzer.
        """
        sketch = Sketch.query.get_with_acl(sketch_id)
        if not sketch:
            abort(
                HTTP_STATUS_CODE_NOT_FOUND, 'No sketch found with this ID.')
        if not sketch.has_permission(current_user, 'read'):
            return abort(
                HTTP_STATUS_CODE_FORBIDDEN,
                'User does not have read permission on the sketch.')

        form = request.json
        if not form:
            form = request.data

        if not form:
            return abort(
                HTTP_STATUS_CODE_FORBIDDEN,
                'Unable to run an analyzer without any data submitted.')

        timeline_id = form.get('timeline_id')
        if not timeline_id:
            return abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                'Need to provide a timeline ID')

        timeline = Timeline.query.get(timeline_id)
        if timeline not in sketch.timelines:
            return abort(
                HTTP_STATUS_CODE_FORBIDDEN,
                'Timeline is not part of this sketch')

        search_index = timeline.searchindex

        if not search_index:
            return abort(
                HTTP_STATUS_CODE_BAD_REQUEST, (
                    'No timeline was found, make sure you\'ve got the correct '
                    'timeline ID or timeline name.'))

        analyzer_names = form.get('analyzer_names')
        if analyzer_names:
            if not isinstance(analyzer_names, (tuple, list)):
                return abort(
                    HTTP_STATUS_CODE_BAD_REQUEST,
                    'Analyzer names needs to be a list of analyzers.')

        analyzer_kwargs = form.get('analyzer_kwargs')
        if analyzer_kwargs:
            if not isinstance(analyzer_kwargs, dict):
                return abort(
                    HTTP_STATUS_CODE_BAD_REQUEST,
                    'Kwargs needs to be a dictionary of parameters.')

        # Import here to avoid circular imports.
        # pylint: disable=import-outside-toplevel
        from timesketch.lib import tasks
        try:
            analyzer_group, session_id = tasks.build_sketch_analysis_pipeline(
                sketch_id=sketch_id, searchindex_id=search_index.id,
                user_id=current_user.id, analyzer_names=analyzer_names,
                analyzer_kwargs=analyzer_kwargs)
        except KeyError as e:
            return abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                'Unable to build analyzer pipeline, analyzer does not exist. '
                'Error message: {0!s}'.format(e))

        if analyzer_group:
            pipeline = (tasks.run_sketch_init.s(
                [search_index.index_name]) | analyzer_group)
            pipeline.apply_async()

        schema = {
            'objects': [{
                'analysis_session': session_id
            }]
        }
        return jsonify(schema)
