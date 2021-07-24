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
import time
import uuid

import yaml

from flask import current_app
from flask import jsonify
from flask import request
from flask import abort
from flask_restful import Resource
from flask_login import current_user
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
        print('foo')
        questions = _get_questions_from_config()
        meta = {'count': len(questions.keys())}
        objects = [questions]
        return jsonify({'meta': meta, 'objects': objects})

    # TODO: Implement a POST method that creates a new question, implement
    # once we allow questions to be stored in the database as an opposed to
    # solely be defined in a YAML file.


class QuestionResource(resources.ResourceMixin, Resource):
    """Resource for asking a question within a Sketch."""

    # Number of seconds to wait between checking whether analyzers have
    # finished running.
    ANALYZER_WAIT_PERIOD = 5

    # Maximum number of seconds to wait until all analyzers complete.
    MAXIMUM_WAIT_SECONDS = 600

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
        indices_struct = {}
        for timeline in sketch.active_timelines:
            if timeline.id in timeline_ids_read:
                timeline_ids.append(timeline.id)
                indices_struct.setdefault(
                    f'{timeline.searchindex.id}|'
                    f'{timeline.searchindex.index_name}', set())
                indices_struct[timeline.searchindex.id].add(timeline.id)

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

        analyzers = question.get('analyzers', [])
        max_wait_seconds = form.get(
            'maximum_wait_seconds', self.MAXIMUM_WAIT_SECONDS)
        errors = None
        if analyzers:
            _, errors = self._run_analyzers(
                indices_struct=indices_struct, analyzers=analyzers,
                sketch_id=sketch.id, max_wait_seconds=max_wait_seconds,
                get_answer=False)

        answer_source = question.get('answer_source', {})
        answer_musts = answer_source.get('must', [])

        results = self._run_data_finder_pipeline(
            data_sources=answer_musts, sketch=sketch,
            start_date=start_date, end_date=end_date,
            timeline_ids=timeline_ids, parameters=parameters)
        print(results)

        answer_must_not = answer_source.get('must_not', [])
        results = self._run_data_finder_pipeline(
            data_sources=answer_must_not, sketch=sketch,
            start_date=start_date, end_date=end_date,
            timeline_ids=timeline_ids, parameters=parameters)
        print(results)

        answer_analyzer = question.get('answer_analyzer', '')
        answer = None  # TODO: Fix this, results should be all encompassing.
        if answer_analyzer:
            answer, errors = self._run_analyzers(
                indices_struct=indices_struct,
                analyzers=[answer_analyzer], sketch_id=sketch_id,
                max_wait_seconds=max_wait_seconds, get_answer=True)

        graph_plugins = question.get('graph_plugins', [])
        searches = question.get('searches', [])
        schema = {
            'meta': {
                'data_available': True,
                'question_asked': question_name,
                'graph_plugins': graph_plugins,
                'searches': searches,
                'errors': errors,
            },
            'objects': [results, answer],
        }
        return jsonify(schema)

    def _run_analyzers(
            self, indices_struct, analyzers, sketch_id, max_wait_seconds,
            get_answer=False):
        """Run analyzers and finish writing this docstring."""
        # Import here to avoid circular imports.
        # pylint: disable=import-outside-toplevel
        from timesketch.lib import tasks

        sessions = []
        pipelines = []
        for index_string, timeline_ids in indices_struct.items():
            index_id_str, _, index_name = index_string.partition('|')
            index_id = int(index_id_str)

            for timeline_id in timeline_ids:
                try:
                    group, session = tasks.build_sketch_analysis_pipeline(
                        sketch_id=sketch_id, searchindex_id=index_id,
                        user_id=current_user.id, analyzer_names=analyzers,
                        timeline_id=timeline_id)
                except KeyError:
                    logger.warning(
                        'Unable to build analyzer pipeline, analyzer does not '
                        'exists.', exc_info=True)
                    continue

                if group:
                    pipeline = (tasks.run_sketch_init.s(
                        [index_name]) | group)
                    pipeline.apply_async()
                    sessions.append(session)
                    if get_answer:
                        pipelines.append(pipeline)

        errors = []

        # Wait until analyzers are complete.
        # Since many of the questions rely on analyzers to run before
        # attempting to answer them, we need to make sure the analyzers
        # have successfully completed before moving on to the next step.
        if sessions:
            completed = False
            total_wait = 0
            while not completed:
                completed = True
                for session in sessions:
                    for analyzer in session.analyses:
                        if analyzer.get_status.status not in ('DONE', 'ERROR'):
                            completed = False

                # Sleep for few seconds to allow analyzer to complete
                # it's run.
                time.sleep(self.ANALYZER_WAIT_PERIOD)
                total_wait += self.ANALYZER_WAIT_PERIOD

                if total_wait >= max_wait_seconds:
                    logger.error(
                        'Unable to wait for analyzers to complete, answers '
                        'may be un-reliable.')
                    errors.append(
                        'Unable to wait for analyzers to complete, took '
                        'too long')
                    break

        if get_answer:
            results = []
            for pipeline in pipelines:
                result = pipeline.delay()
                results.append(result.join())
            return results, errors

        return None, errors

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
