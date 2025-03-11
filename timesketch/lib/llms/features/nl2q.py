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
"""Natural language to query (NL2Q) version 1."""
import logging
from typing import Any
import pandas as pd
from flask import current_app
from timesketch.api.v1 import utils
from timesketch.models.sketch import Sketch
from timesketch.lib.llms.features.interface import LLMFeatureInterface

logger = logging.getLogger("timesketch.llm.nl2q_feature")


class Nl2qFeature(LLMFeatureInterface):
    """NL2Q feature."""

    NAME = "nl2q"

    def _sketch_data_types(self, sketch: Sketch) -> str:
        """Get the data types for the current sketch.

        Args:
            sketch: The Sketch object to extract data types from.

        Returns:
            str: Comma-separated list of data types found in the sketch.
        """
        output = []
        data_type_aggregation = utils.run_aggregator(
            sketch.id, "field_bucket", {"field": "data_type", "limit": "1000"}
        )
        if not data_type_aggregation or not data_type_aggregation[0]:
            logger.error("Internal problem with the aggregations.")
            return ""
        data_types = data_type_aggregation[0].values
        if not data_types:
            logger.warning("No data types in the sketch.")
            return ""
        for data_type in data_types:
            output.append(data_type.get("data_type"))
        return ",".join(output)

    def _data_types_descriptions(self, data_types: str) -> str:
        """Creates a formatted string of data types and attribute descriptions.

        Args:
            data_types: Comma-separated list of data types.

        Returns:
            str: Multi-line string with data types and their field descriptions.
        """
        df_data_types = utils.load_csv_file("DATA_TYPES_PATH")
        if df_data_types.empty:
            logger.error("No data types description file or the file is empty.")
            return ""
        df_short_data_types = pd.DataFrame(
            df_data_types.groupby("data_type").apply(self._concatenate_values),
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
                logger.warning("'%s' not found in data types", dtype.strip())
                continue
            output.append(extract.iloc[0]["fields"])
        return "\n".join(output)

    def _generate_fields(self, group) -> str:
        """Generated the fields for a data type.

        Args:
            group: DataFrame group containing field, type, and description columns.

        Returns:
            str: Comma-separated list of fields formatted as strings.
        """
        return ", ".join(
            f'"{f}"'
            for f, t, d in zip(group["field"], group["type"], group["description"])
        )

    def _concatenate_values(self, group) -> str:
        """Concatenates the fields for a data type.

        Args:
            group: DataFrame group with data_type and field information.

        Returns:
            str: Formatted string with data type and its fields.
        """
        return f'* "{group["data_type"].iloc[0]}" -> {self._generate_fields(group)}'

    def _build_prompt(self, question: str, sketch: Sketch) -> str:
        """Builds the prompt for NL2Q.

        Args:
            question: Natural language question from the user.
            sketch: The Sketch object to extract data types from.

        Returns:
            str: Complete prompt with question, examples, and data types.

        Raises:
            OSError: If prompt or examples file cannot be opened.
            IOError: If prompt or examples file cannot be read.
        """
        prompt_file = current_app.config.get("PROMPT_NL2Q", "")
        examples_file = current_app.config.get("EXAMPLES_NL2Q", "")
        try:
            with open(prompt_file, "r", encoding="utf-8") as file:
                prompt = file.read()
        except OSError:
            logger.error("No prompt file found")
            raise
        try:
            with open(examples_file, "r", encoding="utf-8") as file:
                examples = file.read()
        except OSError:
            logger.error("No examples file found")
            raise  # Re-raise the exception
        prompt = prompt.format(
            examples=examples,
            question=question,
            data_types=self._data_types_descriptions(self._sketch_data_types(sketch)),
        )
        return prompt

    def generate_prompt(self, sketch: Sketch, **kwargs: Any) -> str:
        """Generates the NL2Q prompt.

        Args:
            sketch: The Sketch object.
            kwargs: Must contain 'form' with a 'question' key.

        Returns:
            str: The generated prompt.

        Raises:
            ValueError: If the required question is missing from the form data.
        """
        form = kwargs.get("form")
        if not form or "question" not in form:
            raise ValueError("Missing 'question' in form data")
        question = form["question"]
        return self._build_prompt(question, sketch)

    def process_response(self, llm_response: str, **kwargs: Any) -> dict[str, Any]:
        """Processes the LLM response, extracting the query.

        Args:
            llm_response: String response from the LLM.
            kwargs: Additional arguments (not used).

        Returns:
            dict[str, Any]: Dictionary containing the search query with keys:
                - name: Name of the generated query
                - query_string: The actual query string
                - error: Error message (None if successful)

        Raises:
            ValueError: If the LLM response is not a string.
        """
        if not isinstance(llm_response, str):
            raise ValueError(f"Unexpected response type from LLM: {type(llm_response)}")
        result_schema = {
            "name": "AI generated search query",
            "query_string": llm_response.strip("`\n\r\t "),
            "error": None,
        }
        return result_schema
