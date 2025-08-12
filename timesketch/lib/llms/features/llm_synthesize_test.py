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
"""Tests for the llm_synthesize feature."""

from unittest import mock

from flask import current_app

from timesketch.lib.testlib import BaseTest
from timesketch.lib.llms.features.llm_synthesize import LLMSynthesizeFeature
from timesketch.models.sketch import (
    InvestigativeQuestion,
    InvestigativeQuestionConclusion,
)
from timesketch.models.user import User


# pylint: disable=protected-access
class TestLLMSynthesizeFeature(BaseTest):
    """Tests for the LLMSynthesizeFeature."""

    def setUp(self):
        """Set up the tests."""
        super().setUp()
        self.llm_feature = LLMSynthesizeFeature()
        current_app.config["PROMPT_LLM_SYNTHESIZE"] = "./data/llm_synthesize/prompt.txt"

    @mock.patch(
        "timesketch.lib.llms.features.llm_synthesize.InvestigativeQuestion.get_by_id"
    )
    def test_get_conclusions_text(self, mock_get_question):
        """Tests _get_conclusions_text method."""
        mock_question = mock.MagicMock(spec=InvestigativeQuestion)
        mock_user1 = mock.MagicMock(spec=User)
        mock_user1.username = "analyst1"
        mock_user2 = mock.MagicMock(spec=User)
        mock_user2.username = "analyst2"

        mock_conclusion1 = mock.MagicMock(spec=InvestigativeQuestionConclusion)
        mock_conclusion1.conclusion = "First conclusion text."
        mock_conclusion1.user = mock_user1

        mock_conclusion2 = mock.MagicMock(spec=InvestigativeQuestionConclusion)
        mock_conclusion2.conclusion = "Second conclusion text."
        mock_conclusion2.user = mock_user2

        mock_conclusion3 = mock.MagicMock(spec=InvestigativeQuestionConclusion)
        mock_conclusion3.conclusion = "AI conclusion."
        mock_conclusion3.user = None

        mock_question.conclusions = [
            mock_conclusion1,
            mock_conclusion2,
            mock_conclusion3,
        ]
        mock_get_question.return_value = mock_question

        conclusions_text = self.llm_feature._get_conclusions_text(mock_question)

        expected_text = (
            "Conclusion 1 (by analyst1):\nFirst conclusion text.\n\n"
            "---\n\n"
            "Conclusion 2 (by analyst2):\nSecond conclusion text.\n\n"
            "---\n\n"
            "Conclusion 3 (by AI):\nAI conclusion."
        )
        self.assertEqual(conclusions_text, expected_text)

    @mock.patch(
        "timesketch.lib.llms.features.llm_synthesize.InvestigativeQuestion.get_by_id"
    )
    def test_get_conclusions_text_no_conclusions(self, mock_get_question):
        """Tests _get_conclusions_text with no conclusions."""
        mock_question = mock.MagicMock(spec=InvestigativeQuestion)
        mock_question.conclusions = []
        mock_get_question.return_value = mock_question

        conclusions_text = self.llm_feature._get_conclusions_text(mock_question)
        self.assertEqual(conclusions_text, "No conclusions found for this question.")

    @mock.patch(
        "builtins.open",
        mock.mock_open(read_data="Question: <QUESTION>\nConclusions:\n<CONCLUSIONS>"),
    )
    def test_get_prompt_text(self):
        """Tests _get_prompt_text method."""
        prompt = self.llm_feature._get_prompt_text(
            "What happened?", "Lots of things happened."
        )
        self.assertEqual(
            prompt, "Question: What happened?\nConclusions:\nLots of things happened."
        )

    @mock.patch(
        "timesketch.lib.llms.features.llm_synthesize."
        "LLMSynthesizeFeature._get_conclusions_text"
    )
    @mock.patch(
        "timesketch.lib.llms.features.llm_synthesize."
        "LLMSynthesizeFeature._get_prompt_text"
    )
    @mock.patch(
        "timesketch.lib.llms.features.llm_synthesize.InvestigativeQuestion.get_by_id"
    )
    def test_generate_prompt(
        self, mock_get_question, mock_get_prompt_text, mock_get_conclusions_text
    ):
        """Tests the main generate_prompt method."""
        mock_question = mock.MagicMock(spec=InvestigativeQuestion)
        mock_question.id = 1
        mock_question.sketch_id = 1
        mock_question.name = "The Question"
        mock_get_question.return_value = mock_question

        mock_sketch = mock.MagicMock()
        mock_sketch.id = 1

        mock_get_conclusions_text.return_value = "Test conclusions"
        mock_get_prompt_text.return_value = "Final prompt"

        prompt = self.llm_feature.generate_prompt(
            sketch=mock_sketch, form={"question_id": 1}
        )

        self.assertEqual(prompt, "Final prompt")
        mock_get_conclusions_text.assert_called_once_with(mock_question)
        mock_get_prompt_text.assert_called_once_with("The Question", "Test conclusions")

    def test_process_response(self):
        """Tests the process_response method."""
        llm_response = {"synthesis": "This is the synthesized answer."}
        result = self.llm_feature.process_response(llm_response)
        self.assertEqual(result, {"response": "This is the synthesized answer."})

    def test_process_response_invalid_format(self):
        """Tests process_response with invalid LLM response."""
        with self.assertRaises(ValueError):
            self.llm_feature.process_response("just a string")

        with self.assertRaises(ValueError):
            self.llm_feature.process_response({"wrong_key": "some value"})
