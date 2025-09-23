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
import uuid as uuid_lib
import json
from os.path import isdir
from typing import Optional
from requests.exceptions import RequestException

from flask import jsonify
from flask import request
from flask import abort
from flask import current_app
from flask_restful import Resource
from flask_restful import reqparse
from flask_login import current_user
from flask_login import login_required

try:
    from yeti.api import YetiApi
    from yeti import errors as yeti_errors

    YETI_AVAILABLE = True
except ImportError:
    YETI_AVAILABLE = False

from timesketch.api.v1 import resources
from timesketch.lib.definitions import HTTP_STATUS_CODE_FORBIDDEN
from timesketch.lib.definitions import HTTP_STATUS_CODE_NOT_FOUND
from timesketch.lib.definitions import HTTP_STATUS_CODE_BAD_REQUEST
from timesketch.lib.dfiq import DFIQCatalog
from timesketch.models import db_session
from timesketch.models.sketch import SearchTemplate, Sketch
from timesketch.models.sketch import Scenario
from timesketch.models.sketch import Facet
from timesketch.models.sketch import InvestigativeQuestion
from timesketch.models.sketch import InvestigativeQuestionApproach
from timesketch.models.sketch import InvestigativeQuestionConclusion
from timesketch.lib.analyzers.dfiq_plugins.manager import DFIQAnalyzerManager


logger = logging.getLogger("timesketch.scenario_api")


def _load_dfiq_from_yeti() -> Optional[DFIQCatalog]:
    """Fetches DFIQ templates from a configured Yeti instance.

    Returns:
        A DFIQ object populated with templates from Yeti, or None if not
        configured or if an error occurs.
    """
    if not YETI_AVAILABLE:
        logger.error(
            "Yeti DFIQ is enabled, but the 'yeti-python' library is not installed."
        )
        return None

    yeti_api_root = current_app.config.get("YETI_API_ROOT")
    yeti_api_key = current_app.config.get("YETI_API_KEY")
    yeti_cert_path = current_app.config.get("YETI_TLS_CERTIFICATE")

    if not all([yeti_api_root, yeti_api_key]):
        logger.warning("Yeti DFIQ is enabled, but API root or key is not configured.")
        return None

    try:
        if yeti_cert_path and yeti_api_root.startswith("https://"):
            api = YetiApi(yeti_api_root, tls_cert=yeti_cert_path)
        else:
            api = YetiApi(yeti_api_root)
        api.auth_api_key(yeti_api_key)
        scenarios = api.search_dfiq(name="", dfiq_type="scenario")
        facets = api.search_dfiq(name="", dfiq_type="facet")
        questions = api.search_dfiq(name="", dfiq_type="question")
        all_dfiq_objects = scenarios + facets + questions

        if not all_dfiq_objects:
            logger.info("No DFIQ objects found in Yeti.")
            return None

    except yeti_errors.YetiApiError as e:
        logger.error("Failed to fetch DFIQ objects from Yeti: %s", str(e))
        return None
    except RequestException as e:
        logger.error("A network error occurred while connecting to Yeti: %s", str(e))
        return None

    # Extract YAML strings and load them directly into a DFIQ object in memory.
    yaml_strings = [
        obj["dfiq_yaml"] for obj in all_dfiq_objects if obj.get("dfiq_yaml")
    ]

    if not yaml_strings:
        return None

    return DFIQCatalog.from_yaml_list(yaml_strings)


def load_dfiq_from_config():
    """Create DFIQ object from config, potentially merging filesystem and Yeti sources.

    Returns:
        DFIQ object or None if DFIQ is not enabled or no templates are found.
    """
    if not current_app.config.get("DFIQ_ENABLED"):
        logger.debug("DFIQ is disabled. Enable in the timesketch.conf!")
        return None

    dfiq_path = current_app.config.get("DFIQ_PATH")
    dfiq_from_files = None
    if dfiq_path and isdir(dfiq_path):
        try:
            dfiq_from_files = DFIQCatalog(dfiq_path)
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Error loading DFIQ from path %s: %s", dfiq_path, str(e))
    else:
        logger.info(
            "No DFIQ_PATH configured or path is invalid, skipping file-based loading."
        )

    if not current_app.config.get("YETI_DFIQ_ENABLED"):
        return dfiq_from_files

    dfiq_from_yeti = _load_dfiq_from_yeti()

    if not dfiq_from_files:
        return dfiq_from_yeti
    if not dfiq_from_yeti:
        return dfiq_from_files

    # Create a new, empty DFIQ object to hold the merged results.
    final_dfiq = DFIQCatalog()

    # Merge components from both sources.
    merged_components = dfiq_from_files.components.copy()
    merged_components.update(dfiq_from_yeti.components)

    final_dfiq.components = merged_components

    final_dfiq.id_to_uuid_map = {
        c.id: c.uuid for c in final_dfiq.components.values() if c.id
    }

    # Rebuild the graph from the final, merged set of components.
    if final_dfiq.components:
        final_dfiq.graph = final_dfiq._build_graph()  # pylint: disable=protected-access

    return final_dfiq


def check_and_run_dfiq_analysis_steps(
    dfiq_obj: object,
    sketch: Sketch,
    analyzer_manager: Optional[DFIQAnalyzerManager] = None,
):
    """Checks if any DFIQ analyzers need to be executed for the given DFIQ object.

    Args:
        dfiq_obj: The DFIQ object (Scenario, Question, or Approach).
        sketch: The sketch object associated with the DFIQ object.
        analyzer_manager: Optional. An existing instance of DFIQAnalyzerManager.

    Returns:
        List of analyzer_session objects (can be empty) or False.
    """
    # Initialize the analyzer manager only once.
    if not analyzer_manager:
        analyzer_manager = DFIQAnalyzerManager(sketch=sketch)

    analyzer_sessions = []
    if isinstance(dfiq_obj, InvestigativeQuestionApproach):
        session = analyzer_manager.trigger_analyzers_for_approach(approach=dfiq_obj)
        if session:
            analyzer_sessions.extend(session)
    elif isinstance(dfiq_obj, InvestigativeQuestion):
        for approach in dfiq_obj.approaches:
            session = analyzer_manager.trigger_analyzers_for_approach(approach=approach)
            if session:
                analyzer_sessions.extend(session)
    elif isinstance(dfiq_obj, Facet):
        for question in dfiq_obj.questions:
            result = check_and_run_dfiq_analysis_steps(
                question, sketch, analyzer_manager
            )
            if result:
                analyzer_sessions.extend(result)
    elif isinstance(dfiq_obj, Scenario):
        if dfiq_obj.facets:
            for facet in dfiq_obj.facets:
                result = check_and_run_dfiq_analysis_steps(
                    facet, sketch, analyzer_manager
                )
                if result:
                    analyzer_sessions.extend(result)
        if dfiq_obj.questions:
            for question in dfiq_obj.questions:
                result = check_and_run_dfiq_analysis_steps(
                    question, sketch, analyzer_manager
                )
                if result:
                    analyzer_sessions.extend(result)
    else:
        return False  # Invalid DFIQ object type

    return analyzer_sessions if analyzer_sessions else False


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
        It uses UUIDs as the primary identifier for looking up templates.

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

        form = request.json or request.data
        dfiq_id = form.get("dfiq_id")
        display_name = form.get("display_name")
        template_uuid = form.get("uuid")

        scenario_template = None
        # Prioritize UUID for lookup, falling back to ID.
        if template_uuid:
            scenario_template = dfiq.get_by_uuid(template_uuid)
        elif dfiq_id:
            scenario_template = dfiq.get_by_id(dfiq_id)
        elif display_name:
            # Name lookup is less precise and remains a final fallback.
            scenario_template = next(
                (s for s in dfiq.scenarios if s.name == display_name),
                None,
            )

        if not scenario_template:
            abort(
                HTTP_STATUS_CODE_NOT_FOUND,
                f"No scenario template found matching the provided data: {form}",
            )

        objects_to_add = []

        scenario_sql = Scenario(
            dfiq_identifier=scenario_template.id,
            uuid=scenario_template.uuid,
            name=scenario_template.name,
            display_name=display_name or scenario_template.name,
            description=scenario_template.description,
            spec_json=scenario_template.to_json(),
            sketch=sketch,
            user=current_user,
        )
        objects_to_add.append(scenario_sql)

        for facet_uuid in scenario_template.facets:
            facet_template = dfiq.get_by_uuid(facet_uuid)
            if not facet_template:
                logger.warning("Facet with UUID [%s] not found, skipping.", facet_uuid)
                continue

            facet_sql = Facet(
                dfiq_identifier=facet_template.id,
                uuid=facet_template.uuid,
                name=facet_template.name,
                display_name=facet_template.name,
                description=facet_template.description,
                spec_json=facet_template.to_json(),
                sketch=sketch,
                user=current_user,
                scenario=scenario_sql,
            )
            objects_to_add.append(facet_sql)

            for question_uuid in facet_template.questions:
                question_template = dfiq.get_by_uuid(question_uuid)
                if not question_template:
                    continue

                question_sql = self._create_question_sql(
                    sketch, question_template, facet_sql=facet_sql
                )
                objects_to_add.append(question_sql)

        for question_uuid in scenario_template.questions:
            question_template = dfiq.get_by_uuid(question_uuid)
            if not question_template:
                continue

            # Create the question, linking it to the scenario but not a facet.
            question_sql = self._create_question_sql(
                sketch, question_template, scenario_sql=scenario_sql
            )
            objects_to_add.append(question_sql)

        db_session.add_all(objects_to_add)
        db_session.commit()

        # Trigger analyzers after the transaction is complete.
        for obj in objects_to_add:
            if isinstance(obj, InvestigativeQuestion):
                check_and_run_dfiq_analysis_steps(obj, sketch)

        return self.to_json(scenario_sql)

    def _create_question_sql(
        self, sketch, question_template, scenario_sql=None, facet_sql=None
    ):
        """Helper to create an InvestigativeQuestion object and its approaches."""
        question_sql = InvestigativeQuestion(
            dfiq_identifier=question_template.id,
            uuid=question_template.uuid,
            name=question_template.name,
            display_name=question_template.name,
            description=question_template.description,
            spec_json=question_template.to_json(),
            sketch=sketch,
            user=current_user,
            scenario=scenario_sql,
            facet=facet_sql,
        )

        for approach_template in question_template.approaches:
            approach_sql = InvestigativeQuestionApproach(
                name=approach_template.name,
                display_name=approach_template.name,
                description=approach_template.description,
                spec_json=approach_template.to_json(),
                user=current_user,
            )
            for search_template in approach_template.search_templates:
                search_template_sql = SearchTemplate.query.filter_by(
                    template_uuid=search_template["value"]
                ).first()
                if search_template_sql:
                    approach_sql.search_templates.append(search_template_sql)
            question_sql.approaches.append(approach_sql)

        return question_sql


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
        if not scenario:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No scenario found with this ID")

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
        if not sketch.has_permission(current_user, "read"):
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
        if not sketch.has_permission(current_user, "read"):
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
        if not sketch.has_permission(current_user, "write"):
            abort(
                HTTP_STATUS_CODE_FORBIDDEN,
                "User does not have write access controls on sketch",
            )

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

        dfiq_question = None
        if template_id or uuid:
            dfiq = load_dfiq_from_config()
            if not dfiq:
                abort(
                    HTTP_STATUS_CODE_NOT_FOUND, "DFIQ is not configured on this server"
                )

            if uuid:
                dfiq_question = dfiq.get_by_uuid(uuid)
            elif template_id:
                dfiq_question = dfiq.get_by_id(template_id)

            if not dfiq_question:
                abort(HTTP_STATUS_CODE_NOT_FOUND, "DFIQ Question template not found.")

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
            if not new_question.uuid:
                new_question.uuid = str(uuid_lib.uuid4())

        db_session.add(new_question)
        db_session.commit()

        check_and_run_dfiq_analysis_steps(new_question, sketch)

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
        if not sketch:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No sketch found with this ID")

        question = InvestigativeQuestion.get_by_id(question_id)
        if not question:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No question found with this ID")
        if not question.sketch.id == sketch.id:
            abort(HTTP_STATUS_CODE_FORBIDDEN, "Question is not part of this sketch.")

        return self.to_json(question)

    @login_required
    def post(self, sketch_id, question_id):
        """Handles POST request to the resource to update a question.

        Returns:
            A JSON representation of the updated question.
        """
        VALID_STATUSES = {"new", "pending-review", "verified", "rejected"}
        VALID_PRIORITIES = {
            "__ts_priority_low",
            "__ts_priority_medium",
            "__ts_priority_high",
        }

        sketch = Sketch.get_with_acl(sketch_id)
        if not sketch:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No sketch found with this ID")
        if not sketch.has_permission(current_user, "write"):
            abort(
                HTTP_STATUS_CODE_FORBIDDEN,
                "User does not have write access controls on sketch",
            )

        question = InvestigativeQuestion.get_by_id(question_id)
        if not question:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No question found with this ID")
        if not question.sketch.id == sketch.id:
            abort(HTTP_STATUS_CODE_FORBIDDEN, "Question is not part of this sketch.")

        form = request.json
        if not form:
            form = request.data

        # Flag to check if the object was updated, to avoid unnecessary DB writes.
        updated = False

        attributes = form.get("attributes")
        if attributes and isinstance(attributes, list):
            for attr in attributes:
                name = attr.get("name")
                value = attr.get("value")
                ontology = attr.get("ontology")
                description = attr.get("description")
                if name and value:
                    question.add_attribute(
                        name=name,
                        value=value,
                        ontology=ontology,
                        user=current_user,
                        description=description,
                    )
            updated = True

        status = form.get("status")
        if status:
            if status not in VALID_STATUSES:
                abort(
                    HTTP_STATUS_CODE_BAD_REQUEST,
                    f"Invalid question status: '{status}'. Valid statuses are: "
                    f"{', '.join(sorted(list(VALID_STATUSES)))}",
                )
            question.set_status(status)
            updated = True

        name = form.get("name")
        if name:
            question.name = name
            updated = True

        display_name = form.get("display_name")
        if display_name:
            question.display_name = display_name
            updated = True

        description = form.get("description")
        if description:
            question.description = description
            updated = True

        priority = form.get("priority")
        if priority:
            if priority not in VALID_PRIORITIES:
                abort(
                    HTTP_STATUS_CODE_BAD_REQUEST,
                    f"Invalid question priority value: '{priority}'. Valid "
                    "priorities are: "
                    f"{', '.join(sorted(list(VALID_PRIORITIES - {''})))}",
                )

            # Remove existing priority label
            existing_priority_label = None
            for label in question.get_labels:
                if label.startswith("__ts_priority_"):
                    existing_priority_label = label
                    break

            if existing_priority_label:
                question.remove_label(existing_priority_label)

            question.add_label(priority)
            updated = True

        if updated:
            db_session.add(question)
            db_session.commit()

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

        conclusions = InvestigativeQuestionConclusion.query.filter_by(
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
        if not sketch.has_permission(current_user, "write"):
            abort(
                HTTP_STATUS_CODE_FORBIDDEN,
                "User does not have write access controls on sketch",
            )

        question = InvestigativeQuestion.get_by_id(question_id)
        if not question:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No question found with this ID")

        form = request.json
        if not form:
            form = request.data

        conclusion_text = form.get("conclusionText")
        automated = form.get("automated", False)

        if automated:
            conclusion = InvestigativeQuestionConclusion(
                conclusion=conclusion_text,
                user=None,
                investigativequestion=question,
                automated=True,
            )
            db_session.add(conclusion)
            db_session.commit()
        else:
            # Create conclusion for the calling user if it doesn't exist.
            conclusion = InvestigativeQuestionConclusion.get_or_create(
                user=current_user, investigativequestion=question
            )

            if conclusion_text:
                conclusion.conclusion = conclusion_text
                db_session.add(conclusion)
                db_session.commit()

        meta = {"new_conclusion_id": conclusion.id}
        return self.to_json(question, meta=meta)


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
        if not sketch.has_permission(current_user, "write"):
            abort(
                HTTP_STATUS_CODE_FORBIDDEN,
                "User does not have write access controls on sketch",
            )

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

        Deletes a conclusion and removes associated fact labels from events.
        """
        sketch = Sketch.get_with_acl(sketch_id)
        if not sketch:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No sketch found with this ID")
        if not sketch.has_permission(current_user, "write"):
            abort(
                HTTP_STATUS_CODE_FORBIDDEN,
                "User does not have write access controls on sketch",
            )

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

        is_owner = conclusion.user == current_user
        is_automated = conclusion.automated
        if not (is_owner or is_automated):
            abort(
                HTTP_STATUS_CODE_FORBIDDEN,
                "You can only delete your own conclusions or those generated by AI.",
            )

        label_to_remove = f"__ts_fact_{conclusion_id}"
        events_to_update = list(conclusion.events)
        for event in events_to_update:
            existing_labels = event.get_labels

            if label_to_remove in existing_labels:
                self.datastore.set_label(
                    searchindex_id=event.searchindex.index_name,
                    event_id=event.document_id,
                    sketch_id=sketch.id,
                    user_id=current_user.id,
                    label=label_to_remove,
                    toggle=True,
                )

        self.datastore.flush_queued_events()

        db_session.delete(conclusion)
        db_session.commit()

        return self.to_json(question)
