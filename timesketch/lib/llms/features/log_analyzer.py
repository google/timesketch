# Copyright 2025 Google Inc. All rights reserved.
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
"""LogAnalyzer feature for automated log analysis using LLMs."""

# file should be placed in timesketch/lib/llms/features/log_analyzer.py

import logging
import json
from typing import Any, Dict, List
from timesketch.models import db_session
from timesketch.models.sketch import Sketch
from timesketch.lib.llms.features.interface import LLMFeatureInterface
from timesketch.models.sketch import InvestigativeQuestion
from timesketch.models.sketch import InvestigativeQuestionConclusion
from timesketch.models.sketch import View
from timesketch.models.sketch import Event

logger = logging.getLogger("timesketch.llm.log_analyzer_feature")


class LogAnalyzer(LLMFeatureInterface):
    """LogAnalyzer feature for automated log analysis."""

    NAME = "log_analyzer"

    def _get_prompt_template(self) -> str:
        """Returns a hardcoded prompt template for log analysis."""
        return """
        Analyze the security logs from sketch {sketch_id} ({sketch_name}).
        
        Focus on {log_type} logs and identify any potential security incidents or suspicious activity.
        Pay special attention to:
        - Successful/failed authentication attempts
        - Privilege escalation
        - Data exfiltration
        - Command execution
        - Lateral movement
        
        Current query filter: {query_string}
        
        Provide a detailed analysis of the logs, including:
        - Attack stages identified
        - Key findings and investigative questions
        - Specific conclusions with relevant entities (IPs, usernames, etc.)
        """

    def generate_prompt(self, sketch: Sketch, **kwargs: Any) -> str:
        """Generates a prompt for log analysis."""
        form = kwargs.get("form", {})
        log_type = form.get("log_type", "all")
        query_string = form.get("query", "*") or "*"

        # Format the prompt with the provided information
        prompt = self._get_prompt_template().format(
            sketch_id=sketch.id,
            sketch_name=sketch.name,
            log_type=log_type,
            query_string=query_string,
        )

        return prompt

    def process_response(self, llm_response: Any, **kwargs: Any) -> Dict[str, Any]:
        """
        Processes the LLM response and creates Questions & Conclusions from it.

        Transforms data from Arcadia's record_id-based structure to a hierarchical question-centric
        structure where each question has one conclusion and multiple observables.

        Args:
            llm_response: The response from the Arcadia LLM provider.
            **kwargs: Additional arguments including sketch_id.

        Returns:
            Dict containing hierarchically structured analysis results.
        """
        sketch_id = kwargs.get("sketch_id")

        # Handle JSON string response from Arcadia
        if isinstance(llm_response, str):
            try:
                arcadia_response = json.loads(llm_response)
            except json.JSONDecodeError:
                logger.error("Failed to parse Arcadia response as JSON")
                return {
                    "questions": [],
                    "meta": {
                        "error": "Invalid JSON response",
                        "raw_response": llm_response[:200],
                    },
                }
        else:
            arcadia_response = llm_response

        if not isinstance(arcadia_response, list):
            return {"questions": [], "meta": {"error": "Expected list response"}}

        questions_dict = {}

        # parsing the JSON
        for record_data in arcadia_response:
            for annotation in record_data.get("annotations", []):
                question_text = annotation.get("investigative_question")
                if question_text not in questions_dict:
                    questions_dict[question_text] = {}

                for conclusion in annotation.get("conclusions", []):
                    if conclusion not in questions_dict[question_text]:
                        questions_dict[question_text][conclusion] = []
                    questions_dict[question_text][conclusion].append(
                        record_data.get("record_id")
                    )

        # Creating questions, conclusions, saved searches and adding event to conclusion
        for question, conclusions in questions_dict.items():
            new_question = InvestigativeQuestion(name=question, sketch_id=sketch_id, display_name=question)
            new_question.add_attribute("source", "AI_GENERATED")
            for conclusion, record_ids in conclusions.items():
                new_conclusion = InvestigativeQuestionConclusion(
                    conclusion=conclusion,
                    investigativequestion=new_question,
                    automated=True
                )
                new_question.conclusions.append(new_conclusion)
                for record_id in record_ids:
                    new_view = View(
                        name=question,
                        sketch_id=sketch_id,
                        query_string='_id:(' + ' OR '.join(f'"{record_id}"' for record_id in record_ids) + ')'
                    )
                    new_event = Event(sketch_id=sketch_id, document_id=record_id, conclusions=[new_conclusion])
                    new_conclusion.saved_searches.append(new_view)
                db_session.add(new_question)
                db_session.add(new_event)


        response = {}
        db_session.commit()
        
        return response

