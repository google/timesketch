# Copyright 2024 Google Inc. All rights reserved.
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
"""Natural language to query (NL2Q) API for version 1 of the Timesketch API."""

import logging

from flask import jsonify
from flask import request
from flask import abort
from flask import current_app
from flask_restful import Resource
from flask_login import login_required
from flask_login import current_user

import pandas as pd

from timesketch.api.v1 import utils
from timesketch.lib.llms import manager
from timesketch.lib.definitions import HTTP_STATUS_CODE_BAD_REQUEST
from timesketch.lib.definitions import HTTP_STATUS_CODE_INTERNAL_SERVER_ERROR
from timesketch.lib.definitions import HTTP_STATUS_CODE_NOT_FOUND
from timesketch.lib.definitions import HTTP_STATUS_CODE_FORBIDDEN
from timesketch.models.sketch import Sketch


logger = logging.getLogger("timesketch.api_nl2q")


class Nl2qResource(Resource):
    """Resource to get NL2Q prediction."""

    def build_prompt(self, question, sketch_id):
        """Builds the prompt.

        Args:
          sketch_id: Sketch ID.

        Return:
          String containing the whole prompt.
        """
        prompt = ""
        examples = ""
        prompt_file = current_app.config.get("PROMPT_NL2Q", "")
        examples_file = current_app.config.get("EXAMPLES_NL2Q", "")
        try:
            with open(prompt_file, "r") as file:
                prompt = file.read()
        except (OSError, IOError):
            abort(HTTP_STATUS_CODE_INTERNAL_SERVER_ERROR, "No prompt file found")
        try:
            with open(examples_file, "r") as file:
                examples = file.read()
        except (OSError, IOError):
            abort(HTTP_STATUS_CODE_INTERNAL_SERVER_ERROR, "No examples file found")
        prompt = prompt.format(
            examples=examples,
            question=question,
            data_types=self.data_types_descriptions(self.sketch_data_types(sketch_id)),
        )
        return prompt

    def sketch_data_types(self, sketch_id):
        """Get the data types for the current sketch.

        Args:
          sketch_id: Sketch ID.

        Returns:
          List of data types in a sketch.
        """
        output = []
        sketch = Sketch.get_with_acl(sketch_id)
        if not sketch:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No sketch found with this ID.")

        if not sketch.has_permission(current_user, "read"):
            abort(
                HTTP_STATUS_CODE_FORBIDDEN, "User does not have read access to sketch"
            )

        data_type_aggregation = utils.run_aggregator(
            sketch_id, "field_bucket", {"field": "data_type", "limit": "1000"}
        )

        if not data_type_aggregation or not data_type_aggregation[0]:
            abort(
                HTTP_STATUS_CODE_INTERNAL_SERVER_ERROR,
                "Internal problem with the aggregations.",
            )
        data_types = data_type_aggregation[0].values
        if not data_types:
            abort(
                HTTP_STATUS_CODE_INTERNAL_SERVER_ERROR,
                "No data types in the sketch.",
            )
        for data_type in data_types:
            output.append(data_type.get("data_type"))
        return ",".join(output)

    def data_types_descriptions(self, data_types):
        """Creates a formatted string of data types and attribute descriptions.

        Args:
          data_types: List of data types in the sketch.

        Returns:
          Formatted string of data types and attribute descriptions.
        """
        df_data_types = utils.load_csv_file("DATA_TYPES_PATH")
        if df_data_types.empty:
            abort(
                HTTP_STATUS_CODE_INTERNAL_SERVER_ERROR,
                "No data types description file or the file is empty.",
            )
        df_short_data_types = pd.DataFrame(
            df_data_types.groupby("data_type").apply(self.concatenate_values),
            columns=["fields"],
        )
        df_short_data_types["data_type"] = df_short_data_types.index
        df_short_data_types["data_type"] = df_short_data_types["data_type"].apply(
            lambda x: x.strip()
        )
        df_short_data_types.reset_index(drop=True, inplace=True)
        output = []
        for dtype in data_types.split(","):
            extract = df_short_data_types[
                df_short_data_types["data_type"] == dtype.strip()
            ]
            if extract.empty:
                print(f"'{dtype.strip()}' not found in [{data_types}]")
                continue
            output.append(extract.iloc[0]["fields"])
        return "\n".join(output)

    def generate_fields(self, group):
        """Generated the fields for a data type.

        Args:
          group: Data type fields.

        Returns:
          String of the generated fields.
        """
        return ", ".join(
            f'"{f}"'
            for f, t, d in zip(group["field"], group["type"], group["description"])
        )

    def concatenate_values(self, group):
        """Concatenates the fields for a data type.

        Args:
          group: Data type fields.

        Returns:
          String of the concatenated fields.
        """
        return f'* "{group["data_type"].iloc[0]}" -> {self.generate_fields(group)}'

    @login_required
    def post(self, sketch_id):
        """Handles POST request to the resource.

        Args:
          sketch_id: Sketch ID.

        Returns:
            JSON representing the LLM prediction.
        """
        llm_provider = current_app.config.get("LLM_PROVIDER", "")
        if not llm_provider:
            logger.error("No LLM provider was defined in the main configuration file")
            abort(
                HTTP_STATUS_CODE_INTERNAL_SERVER_ERROR,
                "No LLM provider was defined in the main configuration file",
            )
        form = request.json
        if not form:
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                "No JSON data provided",
            )

        if "question" not in form:
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                "The 'question' parameter is required!",
            )

        question = form.get("question")
        prompt = self.build_prompt(question, sketch_id)
        result_schema = {
            "name": "AI generated search query",
            "query_string": None,
            "error": None,
        }
        try:
            llm = manager.LLMManager().get_provider(llm_provider)()
        except Exception as e:  # pylint: disable=broad-except
            logger.error("Error LLM Provider: {}".format(e))
            result_schema["error"] = (
                "Error loading LLM Provider. Please try again later!"
            )
            return jsonify(result_schema)

        try:
            prediction = llm.generate(prompt)
        except Exception as e:  # pylint: disable=broad-except
            logger.error("Error NL2Q prompt: {}".format(e))
            result_schema["error"] = (
                "An error occurred generating the query via the defined LLM. "
                "Please try again later!"
            )
            return jsonify(result_schema)
        # The model sometimes output tripple backticks that needs to be removed.
        result_schema["query_string"] = prediction.strip("```")

        return jsonify(result_schema)
