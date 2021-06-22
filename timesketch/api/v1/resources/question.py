# Copyright 2021 Google Inc. All rights reserved.
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
"""API for asking Timesketch questions for version 1 of the Timesketch API."""

import os
import logging
import uuid

import yaml

from flask import current_app
from flask import jsonify
from flask import request
from flask import abort
from flask_restful import Resource
from flask_login import login_required

from timesketch.api.v1 import resources
from timesketch.lib.definitions import HTTP_STATUS_CODE_BAD_REQUEST
from timesketch.lib.definitions import HTTP_STATUS_CODE_NOT_FOUND
from timesketch.models.sketch import Sketch


logger = logging.getLogger('timesketch.question_api')


def _get_questions_from_config():
    """Return a dict with the """
    question_path = current_app.config.get('INVESTIGATIVE_QUESTION_PATH', '')
    if not question_path:
        logger.error(
            'The path to the investigative questions isn\'t defined in the '
            'main configuration file.')
        return {}
    if not os.path.isfile(question_path):
        logger.error(
            'Unable to read the investigative question config, file: '
            '[{0:s}] does not exist.'.format(question_path))
        return {}

    with open(question_path, 'r') as fh:
        return yaml.safe_load(fh)


class QuestionListResource(resources.ResourceMixin, Resource):
    """Resource for asking a question within a Sketch."""

    @login_required
    def get(self):
        """Handles GET request to the resource.

        Returns:
            A list of JSON representations of available questions.
        """
        questions = _get_questions_from_config()
        meta = {'count': len(questions.keys())}
        objects = [questions]
        return jsonify({'meta': meta, 'objects': objects})

    # TODO: Implement a POST method that creates a new question, implement
    # once we allow questions to be stored in the database as an opposed to
    # solely be defined in a YAML file.


class QuestionResource(resources.ResourceMixin, Resource):
    """Resource for asking a question within a Sketch."""

    @login_required
    def post(self, sketch_id):
        """Handles POST request to the resource.

        Args:
          sketch_id (int): Identifier for the Sketch the datasource belongs to.

        Returns:
            A list of JSON representations of the data sources.
        """
        sketch = Sketch.query.get_with_acl(sketch_id)
        if not sketch:
            abort(
                HTTP_STATUS_CODE_NOT_FOUND,
                'No sketch found with this ID.')

        if sketch.get_status.status == 'archived':
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                'Unable to ask questions on an archived sketch.')

        form = request.json
        if not form:
            form = request.data

        start_date = form.get('start_date')
        if not start_date:
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                'Need a start date for questions.')

        end_date = form.get('end_date')
        if not end_date:
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                'Need an end date for questions.')

        question_name = form.get('question_name','')
        if not question_name:
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                'Need to provide a question_name to be able to ask a question')
        question_name = question_name.lower()

        questions = _get_questions_from_config()
        question = questions.get(question_name)

        if not question:
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                'Question [{0:s}] is not defined, please check '
                'if it\'s correct.')

        timeline_ids_read = form.get('timeline_ids', [])
        timeline_ids = []
        for timeline in sketch.active_timelines:
            if timeline.id in timeline_ids_read:
                timeline_ids.append(timeline.id)

        parameters = form.get('parameters')
        if parameters and not isinstance(parameters, dict):
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                'If parameters are provided, it needs to be a dict.')

        data_sources = question.get('data_sources', [])
        results = {}
        if data_sources:
            results['data_sources'] = self._run_data_finder_pipeline(
                data_sources=data_sources, sketch=sketch,
                start_date=start_date, end_date=end_date,
                timeline_ids=timeline_ids, parameters=parameters)

            data_available = True
            data_missing = []
            for result in results:
                for rule_name, rule_results in result.items():
                    value, reason = rule_results
                    if not value:
                        data_missing.append(f'[{rule_name}] - {reason}')
                        data_available = False

            if not data_available:
                schema = {
                  'meta': {
                      'data_available': False,
                      'data_missing': data_missing,
                      'question_asked': question_name,
                  },
                  'objects': [results]
                }
                return jsonify(schema)

        # TODO: Use variables.
        # pylint: disable=unused-variable
        analyzers = question.get('analyzers', [])
        # TODO: Run analyzers.

        answer_source = question.get('answer_source', {})
        answer_musts = answer_source.get('must', [])
        results = self._run_data_finder_pipeline(
            data_sources=data_sources, sketch=sketch,
            start_date=start_date, end_date=end_date,
            timeline_ids=timeline_ids, parameters=parameters)

        answer_must_not = answer_source.get('must_not', [])
        # TODO: Run all answer data sources.

        answer_analyzer = question.get('graph_plugins', [])
        # TODO: Run the answer analyzer.

        graph_plugins = question.get('graph_plugins', [])
        searches = question.get('graph_plugins', [])
        schema = {
            'meta': {
                'data_available': True,
                'question_asked': question_name,
                'graph_plugins': graph_plugins,
                'searches': searches,
            },
            'objects': [results],
        }
        return jsonify(schema)

    def _run_data_finder_pipeline(
            self, data_sources, sketch, start_date, end_date, timeline_ids,
            parameters):
        """Run the data finder pipeline and return the results."""
        # Start Celery pipeline for indexing and analysis.
        # Import here to avoid circular imports.
        # pylint: disable=import-outside-toplevel
        from timesketch.lib import tasks
        pipeline = tasks.run_data_finder(
            rule_names=data_sources, sketch_id=sketch.id, start_date=start_date,
            end_date=end_date, timeline_ids=timeline_ids, parameters=parameters)
        task_id = uuid.uuid4().hex
        pipeline.apply_async(task_id=task_id)

        result = pipeline.delay()
        return result.join()
