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

import logging
import json

from flask import current_app
from flask import jsonify
from flask import request
from flask import abort
from flask_restful import Resource
from flask_login import current_user
from flask_login import login_required

from timesketch.api.v1 import resources
from timesketch.api.v1.utils import load_yaml_config
from timesketch.lib.definitions import HTTP_STATUS_CODE_FORBIDDEN
from timesketch.lib.definitions import HTTP_STATUS_CODE_NOT_FOUND
from timesketch.models import db_session
from timesketch.models.sketch import Sketch
from timesketch.models.sketch import Scenario
from timesketch.models.sketch import Investigation
from timesketch.models.sketch import InvestigativeQuestion


logger = logging.getLogger('timesketch.scenario_api')


class ScenarioTemplateListResource(resources.ResourceMixin, Resource):
    """Resource for investigative scenarios."""

    @login_required
    def get(self):
        """Handles GET request to the resource.
        
        Returns:
            A list of JSON representations of the scenarios.
        """
        scenarios = load_yaml_config('SCENARIOS_PATH')
        return jsonify(scenarios)


class ScenarioListResource(resources.ResourceMixin, Resource):
    """Resource for investigative scenarios."""

    @login_required
    def get(self, sketch_id):
        """Handles GET request to the resource.
        
        Returns:
            A list of JSON representations of the scenarios.
        """
        sketch = Sketch.query.get_with_acl(sketch_id)
        if not sketch:
            abort(
                HTTP_STATUS_CODE_NOT_FOUND, 'No sketch found with this ID')
        if not sketch.has_permission(current_user, 'write'):
            abort(HTTP_STATUS_CODE_FORBIDDEN,
                  'User does not have write access controls on sketch')

        scenarios = Scenario.query.filter_by(sketch=sketch).all()
        return self.to_json(scenarios)

    @login_required
    def post(self, sketch_id):
        """Handles POST request to the resource.

        This resource creates a new scenario for a sketch based on a template.
        Templates are defined in data/scenarios.yaml.
        
        Returns:
            A JSON representation of the scenario.
        """
        sketch = Sketch.query.get_with_acl(sketch_id)
        if not sketch:
            abort(
                HTTP_STATUS_CODE_NOT_FOUND, 'No sketch found with this ID')
        if not sketch.has_permission(current_user, 'write'):
            abort(HTTP_STATUS_CODE_FORBIDDEN,
                  'User does not have write access controls on sketch')

        form = request.json
        if not form:
            form = request.data

        scenarios = load_yaml_config('SCENARIOS_PATH')
        investigations = load_yaml_config('INVESTIGATIONS_PATH')
        questions = load_yaml_config('QUESTIONS_PATH')

        scenario_name = form.get('scenario_name')
        scenario_dict = scenarios.get(scenario_name)

        if not scenario_dict:
            abort(
                HTTP_STATUS_CODE_NOT_FOUND,
                f'No such scenario: {scenario_name}')

        scenario = Scenario(
            name=scenario_name,
            display_name=scenario_dict.get('display_name', ''),
            description=scenario_dict.get('description', ''),
            spec_json=json.dumps(scenario_dict),
            sketch=sketch,
            user=current_user)

        for investigation_name in scenario_dict.get('investigations', []):
            investigation_dict = investigations.get(investigation_name)
            investigation = Investigation(
                name=investigation_name,
                display_name=investigation_dict.get('display_name', ''),
                description=investigation_dict.get('description', ''),
                spec_json=json.dumps(investigation_dict),
                user=current_user)
            scenario.investigations.append(investigation)

            for question_name in investigation_dict.get('questions', []):
                question_dict = questions.get(question_name)
                question = InvestigativeQuestion(
                    name=investigation_name,
                    display_name=question_dict.get('display_name', ''),
                    description=question_dict.get('description', ''),
                    spec_json=json.dumps(question_dict),
                    user=current_user)
                investigation.questions.append(question)

        db_session.add(scenario) 
        db_session.commit()        

        return self.to_json(scenario)


class ScenarioResource(resources.ResourceMixin, Resource):
    """Resource for investigative scenarios."""

    @login_required
    def get(self, sketch_id, scenario_id):
        """Handles GET request to the resource.
        
        Returns:
            A list of JSON representations of the scenarios.
        """
        sketch = Sketch.query.get_with_acl(sketch_id)
        scenario = Scenario.query.get(scenario_id)

        if not sketch:
            abort(
                HTTP_STATUS_CODE_NOT_FOUND, 'No sketch found with this ID')
        if not sketch.has_permission(current_user, 'write'):
            abort(HTTP_STATUS_CODE_FORBIDDEN,
                  'User does not have write access controls on sketch')

        if not scenario.sketch.id == sketch.id:
            abort(HTTP_STATUS_CODE_FORBIDDEN,
                  'Scenario is not part of this sketch.')

        return self.to_json(scenario)
