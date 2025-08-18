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
"""Generates a synthesized summary from investigative conclusions using a
Large Language Model (LLM).

This feature takes an investigative question and all associated conclusions,
formats them into a single prompt, and sends it to an LLM. The LLM then
synthesizes these conclusions into a coherent summary, which is returned as a
final response. This helps analysts quickly understand the overall findings
without reading each conclusion individually.
"""

import logging
from typing import Any

from flask import current_app

from timesketch.models.sketch import Sketch, InvestigativeQuestion
from timesketch.lib.llms.features.interface import LLMFeatureInterface

logger = logging.getLogger("timesketch.llm.synthesize_feature")


class LLMSynthesizeFeature(LLMFeatureInterface):
    """LLM Synthesize feature."""

    NAME = "llm_synthesize"
    PROMPT_CONFIG_KEY = "PROMPT_LLM_SYNTHESIZE"
    RESPONSE_SCHEMA = {
        "type": "object",
        "properties": {"synthesis": {"type": "string"}},
        "required": ["synthesis"],
    }

    def _get_conclusions_text(self, question: InvestigativeQuestion) -> str:
        """Fetches and formats conclusions for a given question.

        Args:
            question_id: The ID of the InvestigativeQuestion.

        Returns:
            A formatted string of all conclusions, or an empty string if none.
        """
        conclusions = question.conclusions
        if not conclusions:
            return "No conclusions found for this question."

        conclusion_texts = []
        for i, conclusion in enumerate(conclusions):
            author = "AI"
            if conclusion.user:
                author = conclusion.user.username
            conclusion_texts.append(
                f"Conclusion {i+1} (by {author}):\n{conclusion.conclusion}"
            )

        return "\n\n---\n\n".join(conclusion_texts)

    def _get_prompt_text(self, question_text: str, conclusions_text: str) -> str:
        """Reads the prompt template and injects the question and conclusions.

        Args:
            question_text: The text of the investigative question.
            conclusions_text: Formatted string of all conclusions.

        Returns:
            The complete prompt text.
        """
        prompt_file_path = current_app.config.get(self.PROMPT_CONFIG_KEY)
        if not prompt_file_path:
            logger.error("%s config not set", self.PROMPT_CONFIG_KEY)
            raise ValueError("LLM synthesis prompt path not configured.")

        try:
            with open(prompt_file_path, "r", encoding="utf-8") as file_handle:
                prompt_template = file_handle.read()
        except FileNotFoundError as exc:
            logger.error("Prompt file not found: %s", prompt_file_path)
            raise FileNotFoundError(
                f"LLM Prompt file not found: {prompt_file_path}"
            ) from exc
        except OSError as e:
            logger.error("Error reading prompt file: %s", e)
            raise OSError("Error reading LLM prompt file.") from e

        if "<QUESTION>" not in prompt_template:
            raise ValueError(
                "LLM synthesis prompt template is missing the "
                "required <QUESTION> placeholder."
            )
        if "<CONCLUSIONS>" not in prompt_template:
            raise ValueError(
                "LLM synthesis prompt template is missing the "
                "required <CONCLUSIONS> placeholder."
            )

        prompt = prompt_template.replace("<QUESTION>", question_text)
        prompt = prompt.replace("<CONCLUSIONS>", conclusions_text)
        return prompt

    def generate_prompt(self, sketch: Sketch, **kwargs: Any) -> str:
        """Generates the prompt for synthesizing an answer.

        Args:
            sketch: The Sketch object.
            **kwargs: Must contain 'form' with a 'question_id' key.

        Returns:
            The generated prompt string.
        """
        form = kwargs.get("form")
        if not form:
            raise ValueError("Missing 'form' data in kwargs")

        question_id = form.get("question_id")
        if not question_id:
            raise ValueError("Missing 'question_id' in form data")

        question = InvestigativeQuestion.get_by_id(question_id)
        if not question:
            raise ValueError(f"No InvestigativeQuestion found with ID: {question_id}")

        if question.sketch_id != sketch.id:
            raise ValueError("Question does not belong to the provided sketch.")

        conclusions_text = self._get_conclusions_text(question)

        return self._get_prompt_text(question.name, conclusions_text)

    def process_response(self, llm_response: Any, **kwargs: Any) -> dict[str, Any]:
        """Processes the LLM response.

        Args:
            llm_response: The response from the LLM model.
            **kwargs: Additional arguments (not used).

        Returns:
            Dictionary containing the synthesized response.
        """
        if not isinstance(llm_response, dict):
            raise ValueError("LLM response is expected to be a dictionary")

        synthesis_text = llm_response.get("synthesis")
        if synthesis_text is None:
            raise ValueError("LLM response missing 'synthesis' key")

        return {"response": synthesis_text}
