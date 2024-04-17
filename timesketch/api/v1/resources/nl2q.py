# Copyright 2023 Google Inc. All rights reserved.
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
"""NL2Q API for version 1 of the Timesketch API."""

import logging
from timesketch.lib.llms import manager

from flask import jsonify
from flask import request
from flask import abort
from flask_restful import Resource
from flask_login import login_required

from timesketch.lib.definitions import HTTP_STATUS_CODE_BAD_REQUEST
from timesketch.lib.definitions import HTTP_STATUS_CODE_INTERNAL_SERVER_ERROR

logger = logging.getLogger("timesketch.api_nl2q")


class Nl2qResource(Resource):
    """Resource to get NL2Q prediction."""

    def build_prompt(self, question):
      """Builds the prompt.

      Return:
        String containing the whole prompt.
      """

      prompt = """
      Convert this question to a Lucene query for Timesketch:

      {question}
      """
      prompt = prompt.format(question=question)
      return prompt

    @login_required
    def post(self):
        """Handles POST request to the resource.

        Returns:
            String representing the LLM prediction.
        """
        form = request.json
        if not form:
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                "No JSON data provided",
            )

        if "question" not in form:
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                "question parameter is required",
            )

        question = form.get("question")
        prompt = build_prompt(question)
        llm = manager.LLMManager().get_provider("vertexai")()

        try:
            prediction = llm.generate(prompt)
        except Exception as e:  # pylint: disable=broad-except
            logger.error("Error NL2Q prompt: {}".format(e))
            abort(
                HTTP_STATUS_CODE_INTERNAL_SERVER_ERROR,
                e,
            )

        return jsonify(prediction)
