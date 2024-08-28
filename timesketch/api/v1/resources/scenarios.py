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
from flask import current_app
from flask_restful import Resource
from flask_restful import reqparse
from flask_login import current_user
from flask_login import login_required

from timesketch.api.v1 import resources
from timesketch.lib.definitions import HTTP_STATUS_CODE_FORBIDDEN
from timesketch.lib.definitions import HTTP_STATUS_CODE_NOT_FOUND
from timesketch.lib.definitions import HTTP_STATUS_CODE_BAD_REQUEST
from timesketch.lib.dfiq import DFIQ
from timesketch.models import db_session
from timesketch.models.sketch import SearchTemplate, Sketch
from timesketch.models.sketch import Scenario
from timesketch.models.sketch import Facet
from timesketch.models.sketch import InvestigativeQuestion
from timesketch.models.sketch import InvestigativeQuestionApproach
from timesketch.models.sketch import InvestigativeQuestionConclusion


logger = logging.getLogger("timesketch.scenario_api")


def load_dfiq_from_config():
    """Create DFIQ object from config.

    Returns:
        DFIQ object or None if no DFIQ_PATH is configured.
    """
    dfiq_path = current_app.config.get("DFIQ_PATH")
    if not current_app.config.get("DFIQ_ENABLED"):
        logger.info("DFIQ is disabled. Enable in the timesketch.conf!")
        return None
    if not dfiq_path:
        logger.error("No DFIQ_PATH configured")
        return None
    return DFIQ(dfiq_path)


class ScenarioTemplateListResource(resources.ResourceMixin, Resource):
    """List all scenarios available."""

    @login_required
    def get(self):
        """Handles GET request to the resource.

        Returns:
            A list of JSON representations of the scenarios.
        """
        dfiq = load_dfiq_from_config()
        if not dfiq:
            return jsonify({"objects": []})

        scenarios = [scenario.__dict__ for scenario in dfiq.scenarios]
        return jsonify({"objects": scenarios})


class ScenarioListResource(resources.ResourceMixin, Resource):
    """List scenarios for a sketch."""

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
        sketch = Sketch.get_with_acl(sketch_id)
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

        This resource creates a new scenario for a sketch based on a DFIQ template.

        Returns:
            A JSON representation of the scenario.
        """
        sketch = Sketch.get_with_acl(sketch_id)
        if not sketch:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No sketch found with this ID")
        if not sketch.has_permission(current_user, "write"):
            abort(
                HTTP_STATUS_CODE_FORBIDDEN,
                "User does not have write access controls on sketch",
            )

        dfiq = load_dfiq_from_config()
        if not dfiq:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "DFIQ is not configured on this server")

        form = request.json
        if not form:
            form = request.data

        dfiq_id = form.get("dfiq_id")
        display_name = form.get("display_name")
        uuid = form.get("uuid")

        scenario = None

        if uuid:
            scenario = next(
                (s for s in dfiq.scenarios if s.uuid == uuid),
                None,
            )
        elif dfiq_id:
            scenario = next(
                (s for s in dfiq.scenarios if s.id == dfiq_id),
                None,
            )
        elif display_name:
            scenario = next(
                (s for s in dfiq.scenarios if s.name == display_name),
                None,
            )

        if not scenario:
            abort(
                HTTP_STATUS_CODE_NOT_FOUND,
                f"No scenario found matching the provided data: {form}",
            )

        if not display_name:
            display_name = scenario.name

        scenario_sql = Scenario(
            dfiq_identifier=scenario.id,
            uuid=scenario.uuid,
            name=scenario.name,
            display_name=display_name,
            description=scenario.description,
            spec_json=scenario.to_json(),
            sketch=sketch,
            user=current_user,
        )

        for facet_id in scenario.facets:
            facet = next(
                (facet for facet in dfiq.facets if facet.id == facet_id),
                None,
            )
            facet_sql = Facet(
                dfiq_identifier=facet.id,
                uuid=facet.uuid,
                name=facet.name,
                display_name=facet.name,
                description=facet.description,
                spec_json=facet.to_json(),
                sketch=sketch,
                user=current_user,
            )
            scenario_sql.facets.append(facet_sql)

            for question_id in facet.questions:
                question = next(
                    (
                        question
                        for question in dfiq.questions
                        if question.id == question_id
                    ),
                    None,
                )
                question_sql = InvestigativeQuestion(
                    dfiq_identifier=question.id,
                    uuid=question.uuid,
                    name=question.name,
                    display_name=question.name,
                    description=question.description,
                    spec_json=question.to_json(),
                    sketch=sketch,
                    # scenario=scenario_sql,
                    user=current_user,
                )
                # facet_sql.questions.append(question_sql)

                # TODO: This is a tmp hack to make all questions oprhaned!
                # We need to fix this by loading connected questions as well in
                # the frontend!
                db_session.add(question_sql)

                for approach in question.approaches:
                    approach_sql = InvestigativeQuestionApproach(
                        name=approach.name,
                        display_name=approach.name,
                        description=approach.description,
                        spec_json=approach.to_json(),
                        user=current_user,
                    )

                    for search_template in approach.search_templates:
                        search_template_sql = SearchTemplate.query.filter_by(
                            template_uuid=search_template["value"]
                        ).first()
                        if search_template_sql:
                            approach_sql.search_templates.append(search_template_sql)

                    question_sql.approaches.append(approach_sql)

        db_session.add(scenario_sql)
        db_session.commit()

        return self.to_json(scenario_sql)


class ScenarioResource(resources.ResourceMixin, Resource):
    """Resource for investigative scenarios."""

    @login_required
    def get(self, sketch_id, scenario_id):
        """Handles GET request to the resource.

        Returns:
            A list of JSON representations of the scenarios.
        """
        sketch = Sketch.get_with_acl(sketch_id)
        scenario = Scenario.get_by_id(scenario_id)

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
        Templates are defined in DFIQ.

        Returns:
            A JSON representation of the scenario.
        """
        sketch = Sketch.get_with_acl(sketch_id)
        scenario = Scenario.get_by_id(scenario_id)

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
        sketch = Sketch.get_with_acl(sketch_id)
        scenario = Scenario.get_by_id(scenario_id)

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


class FacetListResource(resources.ResourceMixin, Resource):
    """List facets for a scenario."""

    @login_required
    def get(self, sketch_id, scenario_id):
        """Get all facets for a scenario.

        Returns:
            A list of JSON representations of the facets.
        """
        sketch = Sketch.get_with_acl(sketch_id)
        scenario = Scenario.get_by_id(scenario_id)

        if not sketch:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No sketch found with this ID")
        if not sketch.has_permission(current_user, "write"):
            abort(
                HTTP_STATUS_CODE_FORBIDDEN,
                "User does not have write access controls on sketch",
            )
        if not scenario.sketch.id == sketch.id:
            abort(HTTP_STATUS_CODE_FORBIDDEN, "Scenario is not part of this sketch.")

        facets = Facet.query.filter_by(scenario=scenario).all()
        return self.to_json(facets)


class QuestionOrphanListResource(resources.ResourceMixin, Resource):
    """List all questions that doesn't have an associated scenario or facet."""

    @login_required
    def get(self, sketch_id):
        """Get all questions that doesn't have an associated scenario or facet.

        Returns:
            A list of JSON representations of the questions.
        """
        sketch = Sketch.get_with_acl(sketch_id)

        if not sketch:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No sketch found with this ID")
        if not sketch.has_permission(current_user, "write"):
            abort(
                HTTP_STATUS_CODE_FORBIDDEN,
                "User does not have write access controls on sketch",
            )

        questions = InvestigativeQuestion.query.filter_by(
            sketch=sketch, scenario=None, facet=None
        ).all()
        return self.to_json(questions)


class QuestionWithScenarioListResource(resources.ResourceMixin, Resource):
    """List all questions for a scenario that doesn't have an associated facet."""

    @login_required
    def get(self, sketch_id, scenario_id):
        """Get all questions for a scenario that doesn't have an associated facet.

        Returns:
            A list of JSON representations of the questions.
        """
        sketch = Sketch.get_with_acl(sketch_id)
        scenario = Scenario.get_by_id(scenario_id)

        if not sketch:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No sketch found with this ID")
        if not sketch.has_permission(current_user, "write"):
            abort(
                HTTP_STATUS_CODE_FORBIDDEN,
                "User does not have write access controls on sketch",
            )

        if not scenario:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No scenario found with this ID")
        if not scenario.sketch.id == sketch.id:
            abort(HTTP_STATUS_CODE_FORBIDDEN, "Scenario is not part of this sketch.")

        questions = InvestigativeQuestion.query.filter_by(
            sketch=sketch, scenario=scenario, facet=None
        ).all()

        if not questions:
            return jsonify({"objects": [[]]})

        return self.to_json(questions)


class QuestionWithFacetListResource(resources.ResourceMixin, Resource):
    """List all investigative questions for a facet."""

    @login_required
    def get(self, sketch_id, scenario_id, facet_id):
        """Get all questions for a facet.

        Returns:
            A list of JSON representations of the questions.
        """
        sketch = Sketch.get_with_acl(sketch_id)
        scenario = Scenario.get_by_id(scenario_id)
        facet = Facet.get_by_id(facet_id)

        if not sketch:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No sketch found with this ID")
        if not sketch.has_permission(current_user, "write"):
            abort(
                HTTP_STATUS_CODE_FORBIDDEN,
                "User does not have write access controls on sketch",
            )

        if not scenario:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No scenario found with this ID")
        if not scenario.sketch.id == sketch.id:
            abort(HTTP_STATUS_CODE_FORBIDDEN, "Scenario is not part of this sketch.")

        if not facet:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No facet found with this ID")
        if not facet.scenario.id == scenario.id:
            abort(HTTP_STATUS_CODE_FORBIDDEN, "Facet is not part of this scenario.")

        questions = InvestigativeQuestion.query.filter_by(facet=facet).all()
        return self.to_json(questions)


class QuestionTemplateListResource(resources.ResourceMixin, Resource):
    """List all scenarios available."""

    @login_required
    def get(self):
        """Handles GET request to the resource.

        Returns:
            A list of JSON representations of the scenarios.
        """
        dfiq = load_dfiq_from_config()
        if not dfiq:
            return jsonify({"objects": []})

        questions = [json.loads(question.to_json()) for question in dfiq.questions]
        return jsonify({"objects": questions})


class QuestionListResource(resources.ResourceMixin, Resource):
    """Create an investigative question."""

    @login_required
    def post(self, sketch_id):
        """Create an investigative question.

        Returns:
            A JSON representation of the question.
        """
        sketch = Sketch.get_with_acl(sketch_id)
        dfiq_question = None

        if not sketch:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No sketch found with this ID")

        form = request.json
        if not form:
            form = request.data
        question_text = form.get("question_text")
        scenario_id = form.get("scenario_id")
        facet_id = form.get("facet_id")
        template_id = form.get("template_id")
        uuid = form.get("uuid")

        scenario = Scenario.get_by_id(scenario_id) if scenario_id else None
        facet = Facet.get_by_id(facet_id) if facet_id else None

        if template_id or uuid:
            dfiq = load_dfiq_from_config()
            if not dfiq:
                abort(
                    HTTP_STATUS_CODE_NOT_FOUND, "DFIQ is not configured on this server"
                )
            if uuid:
                dfiq_question = [
                    question for question in dfiq.questions if question.uuid == uuid
                ][0]
            else:
                dfiq_question = [
                    question
                    for question in dfiq.questions
                    if question.id == template_id
                ][0]

        if dfiq_question:
            new_question = InvestigativeQuestion(
                dfiq_identifier=dfiq_question.id,
                uuid=dfiq_question.uuid,
                name=dfiq_question.name,
                display_name=dfiq_question.name,
                description=dfiq_question.description,
                spec_json=dfiq_question.to_json(),
                sketch=sketch,
                user=current_user,
            )
            for approach in dfiq_question.approaches:
                approach_sql = InvestigativeQuestionApproach(
                    name=approach.name,
                    display_name=approach.name,
                    description=approach.description,
                    spec_json=approach.to_json(),
                    user=current_user,
                )

                for search_template in approach.search_templates:
                    search_template_sql = SearchTemplate.query.filter_by(
                        template_uuid=search_template["value"]
                    ).first()
                    if search_template_sql:
                        approach_sql.search_templates.append(search_template_sql)

                new_question.approaches.append(approach_sql)

        else:
            if not question_text:
                abort(HTTP_STATUS_CODE_BAD_REQUEST, "Question is missing")

            if scenario:
                if scenario.sketch.id != sketch.id:
                    abort(
                        HTTP_STATUS_CODE_FORBIDDEN,
                        "Scenario is not part of this sketch.",
                    )

            if facet:
                if facet.sketch.id != sketch.id:
                    abort(
                        HTTP_STATUS_CODE_FORBIDDEN, "Facet is not part of this sketch."
                    )

            new_question = InvestigativeQuestion.get_or_create(
                name=question_text,
                display_name=question_text,
                sketch=sketch,
                scenario=scenario,
                facet=facet,
                user=current_user,
            )

        db_session.add(new_question)
        db_session.commit()

        return self.to_json(new_question)


class QuestionResource(resources.ResourceMixin, Resource):
    """Resource for an investigative question."""

    @login_required
    def get(self, sketch_id, question_id):
        """Get a investigative question.

        Returns:
            A list of JSON representations of the question.
        """
        sketch = Sketch.get_with_acl(sketch_id)
        question = InvestigativeQuestion.get_by_id(question_id)

        if not sketch:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No sketch found with this ID")
        if not sketch.has_permission(current_user, "write"):
            abort(
                HTTP_STATUS_CODE_FORBIDDEN,
                "User does not have write access controls on sketch",
            )

        if not question:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No question found with this ID")
        if not question.sketch.id == sketch.id:
            abort(HTTP_STATUS_CODE_FORBIDDEN, "Question is not part of this sketch.")

        return self.to_json(question)


class QuestionConclusionListResource(resources.ResourceMixin, Resource):
    """Resource for investigative question conclusion."""

    @login_required
    def get(self, sketch_id, question_id):
        """Handles GET request to the resource.

        Returns:
            A list of JSON representations of the conclusions.
        """
        sketch = Sketch.get_with_acl(sketch_id)
        if not sketch:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No sketch found with this ID")

        question = InvestigativeQuestion.get_by_id(question_id)
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
        sketch = Sketch.get_with_acl(sketch_id)
        if not sketch:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No sketch found with this ID")

        question = InvestigativeQuestion.get_by_id(question_id)
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

        return self.to_json(question)


class QuestionConclusionResource(resources.ResourceMixin, Resource):
    """Resource for investigative question conclusion."""

    def put(self, sketch_id, question_id, conclusion_id):
        """Handles PUT request to the resource.

        Edit a conclusion.

        Returns:
            A JSON representation of the conclusion.
        """
        sketch = Sketch.get_with_acl(sketch_id)
        if not sketch:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No sketch found with this ID")

        question = InvestigativeQuestion.get_by_id(question_id)
        if not question:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No question found with this ID")

        conclusion = InvestigativeQuestionConclusion.get_by_id(conclusion_id)
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

        return self.to_json(question)

    @login_required
    def delete(self, sketch_id, question_id, conclusion_id):
        """Handles DELETE request to the resource.

        Deletes a conclusion.
        """
        sketch = Sketch.get_with_acl(sketch_id)
        if not sketch:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No sketch found with this ID")

        question = InvestigativeQuestion.get_by_id(question_id)
        if not question:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No question found with this ID")

        conclusion = InvestigativeQuestionConclusion.get_by_id(conclusion_id)
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

        return self.to_json(question)
