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
"""API for asking Timesketch scenarios for version 1 of the Timesketch API."""

import logging
import json

from flask import jsonify
from flask import request
from flask import abort
from flask_restful import Resource
from flask_restful import reqparse
from flask_login import current_user
from flask_login import login_required

from timesketch.api.v1 import resources
from timesketch.api.v1.utils import load_yaml_config
from timesketch.lib.definitions import HTTP_STATUS_CODE_FORBIDDEN
from timesketch.lib.definitions import HTTP_STATUS_CODE_NOT_FOUND
from timesketch.models import db_session
from timesketch.models.sketch import SearchTemplate, Sketch
from timesketch.models.sketch import Scenario
from timesketch.models.sketch import Facet
from timesketch.models.sketch import InvestigativeQuestion
from timesketch.models.sketch import InvestigativeQuestionConclusion


logger = logging.getLogger("timesketch.scenario_api")


class ScenarioTemplateListResource(resources.ResourceMixin, Resource):
    """Resource for investigative scenarios."""

    @login_required
    def get(self):
        """Handles GET request to the resource.

        Returns:
            A list of JSON representations of the scenarios.
        """
        scenarios = load_yaml_config("SCENARIOS_PATH")
        return jsonify({"objects": scenarios})


class ScenarioListResource(resources.ResourceMixin, Resource):
    """Resource for investigative scenarios."""

    def __init__(self):
        super().__init__()
        self.parser = reqparse.RequestParser()
        self.parser.add_argument(
            "status", type=str, required=False, default="", location="args"
        )

    @login_required
    def get(self, sketch_id):
        """Handles GET request to the resource.

        Returns:
            A list of JSON representations of the scenarios.
        """
        args = self.parser.parse_args()
        filter_on_status = args.get("status")
        sketch = Sketch.query.get_with_acl(sketch_id)
        if not sketch:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No sketch found with this ID")
        if not sketch.has_permission(current_user, "write"):
            abort(
                HTTP_STATUS_CODE_FORBIDDEN,
                "User does not have write access controls on sketch",
            )

        base_query = Scenario.query.filter_by(sketch=sketch)
        if filter_on_status:
            base_query = base_query.filter(Scenario.status.any(status=filter_on_status))

        scenarios = base_query.order_by(Scenario.created_at.asc()).all()
        return self.to_json(scenarios)

    @login_required
    def post(self, sketch_id):
        """Handles POST request to the resource.

        This resource creates a new scenario for a sketch based on a template.
        Templates are defined in SCENARIOS_PATH.

        Returns:
            A JSON representation of the scenario.
        """
        sketch = Sketch.query.get_with_acl(sketch_id)
        if not sketch:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No sketch found with this ID")
        if not sketch.has_permission(current_user, "write"):
            abort(
                HTTP_STATUS_CODE_FORBIDDEN,
                "User does not have write access controls on sketch",
            )

        form = request.json
        if not form:
            form = request.data

        scenarios = load_yaml_config("SCENARIOS_PATH")
        facets = load_yaml_config("FACETS_PATH")
        questions = load_yaml_config("QUESTIONS_PATH")

        scenario_name = form.get("scenario_name")
        scenario_dict = next(
            scenario
            for scenario in scenarios
            if scenario["short_name"] == scenario_name
        )
        scenario_display_name = form.get(
            "display_name", scenario_dict.get("display_name", "")
        )

        if not scenario_dict:
            abort(HTTP_STATUS_CODE_NOT_FOUND, f"No such scenario: {scenario_name}")

        scenario = Scenario(
            name=scenario_name,
            display_name=scenario_display_name,
            description=scenario_dict.get("description", ""),
            spec_json=json.dumps(scenario_dict),
            sketch=sketch,
            user=current_user,
        )

        for facet_name in scenario_dict.get("facets", []):
            facet_dict = facets.get(facet_name)
            facet = Facet(
                name=facet_name,
                display_name=facet_dict.get("display_name", ""),
                description=facet_dict.get("description", ""),
                spec_json=json.dumps(facet_dict),
                user=current_user,
            )
            scenario.facets.append(facet)

            for question_name in facet_dict.get("questions", []):
                question_dict = questions.get(question_name)
                question = InvestigativeQuestion(
                    name=question_name,
                    display_name=question_dict.get("display_name", ""),
                    description=question_dict.get("description", ""),
                    spec_json=json.dumps(question_dict),
                    user=current_user,
                )
                search_templates = question_dict.get("search_templates", [])
                for template_uuid in search_templates:
                    search_template = SearchTemplate.query.filter_by(
                        template_uuid=template_uuid
                    ).first()
                    if search_template:
                        question.search_templates.append(search_template)
                facet.questions.append(question)

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
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No sketch found with this ID")
        if not sketch.has_permission(current_user, "write"):
            abort(
                HTTP_STATUS_CODE_FORBIDDEN,
                "User does not have write access controls on sketch",
            )

        if not scenario.sketch.id == sketch.id:
            abort(HTTP_STATUS_CODE_FORBIDDEN, "Scenario is not part of this sketch.")

        return self.to_json(scenario)

    @login_required
    def post(self, sketch_id, scenario_id):
        """Handles POST request to the resource.

        This resource creates a new scenario for a sketch based on a template.
        Templates are defined in SCENARIOS_PATH.

        Returns:
            A JSON representation of the scenario.
        """
        sketch = Sketch.query.get_with_acl(sketch_id)
        scenario = Scenario.query.get(scenario_id)

        if not sketch:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No sketch found with this ID")
        if not sketch.has_permission(current_user, "write"):
            abort(
                HTTP_STATUS_CODE_FORBIDDEN,
                "User does not have write access controls on sketch",
            )

        if not scenario.sketch.id == sketch.id:
            abort(HTTP_STATUS_CODE_FORBIDDEN, "Scenario is not part of this sketch.")

        form = request.json
        if not form:
            form = request.data

        scenario.display_name = form.get("scenario_name")
        db_session.add(scenario)
        db_session.commit()

        return self.to_json(scenario)


class ScenarioStatusResource(resources.ResourceMixin, Resource):
    """Resource for investigative scenarios."""

    @login_required
    def post(self, sketch_id, scenario_id):
        """Handles POST request to the resource.

        This resource adds/changes the status for a scenario.

        Returns:
            A JSON representation of the updated scenario.
        """
        sketch = Sketch.query.get_with_acl(sketch_id)
        scenario = Scenario.query.get(scenario_id)

        if not sketch:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No sketch found with this ID")
        if not sketch.has_permission(current_user, "write"):
            abort(
                HTTP_STATUS_CODE_FORBIDDEN,
                "User does not have write access controls on sketch",
            )

        if not scenario.sketch.id == sketch.id:
            abort(HTTP_STATUS_CODE_FORBIDDEN, "Scenario is not part of this sketch.")

        form = request.json
        if not form:
            form = request.data

        status = form.get("status")

        if status:
            scenario.set_status(status)
            db_session.add(scenario)
            db_session.commit()

        return self.to_json(scenario)


class QuestionConclusionListResource(resources.ResourceMixin, Resource):
    """Resource for investigative question conclusion."""

    @login_required
    def get(self, sketch_id, question_id):
        """Handles GET request to the resource.

        Returns:
            A list of JSON representations of the conclusions.
        """
        sketch = Sketch.query.get_with_acl(sketch_id)
        if not sketch:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No sketch found with this ID")

        question = InvestigativeQuestion.query.get(question_id)
        if not question:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No question found with this ID")

        conclusions = InvestigativeQuestionConclusion.filter_by(
            investigativequestion=question
        ).all()

        return self.to_json(conclusions)

    @login_required
    def post(self, sketch_id, question_id):
        """Handles POST request to the resource.

        Adds or edits a conclusion.

        Returns:
            A JSON representation of the conclusion.
        """
        sketch = Sketch.query.get_with_acl(sketch_id)
        if not sketch:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No sketch found with this ID")

        question = InvestigativeQuestion.query.get(question_id)
        if not question:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No question found with this ID")

        # Create conclusion for the calling user if it doesn't exist.
        conclusion = InvestigativeQuestionConclusion.get_or_create(
            user=current_user, investigativequestion=question
        )

        form = request.json
        if not form:
            form = request.data

        conclusion_text = form.get("conclusionText")
        if conclusion_text:
            conclusion.conclusion = conclusion_text
            db_session.add(conclusion)
            db_session.commit()

        return self.to_json(conclusion)


class QuestionConclusionResource(resources.ResourceMixin, Resource):
    """Resource for investigative question conclusion."""

    def put(self, sketch_id, question_id, conclusion_id):
        """Handles PUT request to the resource.

        Edit a conclusion.

        Returns:
            A JSON representation of the conclusion.
        """
        sketch = Sketch.query.get_with_acl(sketch_id)
        if not sketch:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No sketch found with this ID")

        question = InvestigativeQuestion.query.get(question_id)
        if not question:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No question found with this ID")

        conclusion = InvestigativeQuestionConclusion.query.get(conclusion_id)
        if not conclusion:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No conclusion found with this ID")

        if conclusion.user != current_user:
            abort(HTTP_STATUS_CODE_FORBIDDEN, "You can only edit your own conclusion.")

        form = request.json
        if not form:
            form = request.data

        conclusion_text = form.get("conclusionText")
        if conclusion_text:
            conclusion.conclusion = conclusion_text
            db_session.add(conclusion)
            db_session.commit()

        return self.to_json(conclusion)

    @login_required
    def delete(self, sketch_id, question_id, conclusion_id):
        """Handles DELETE request to the resource.

        Deletes a conclusion.
        """
        sketch = Sketch.query.get_with_acl(sketch_id)
        if not sketch:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No sketch found with this ID")

        question = InvestigativeQuestion.query.get(question_id)
        if not question:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No question found with this ID")

        conclusion = InvestigativeQuestionConclusion.query.get(conclusion_id)
        if not conclusion:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No conclusion found with this ID")

        if conclusion.investigativequestion != question:
            abort(
                HTTP_STATUS_CODE_FORBIDDEN, "Conclusion is not part of this question."
            )

        if conclusion.user != current_user:
            abort(
                HTTP_STATUS_CODE_FORBIDDEN, "You can only delete your own concluions."
            )

        db_session.delete(conclusion)
        db_session.commit()
