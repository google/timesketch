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
"""Google AI Studio LLM provider."""

import json
from typing import Optional
from timesketch.lib.llms import interface
from timesketch.lib.llms import manager


# Check if the required dependencies are installed.
has_required_deps = True
try:
    import google.generativeai as genai
except ImportError:
    has_required_deps = False


class AIStudio(interface.LLMProvider):
    """AI Studio LLM provider."""

    NAME = "aistudio"

    def generate(self, prompt: str, response_schema: Optional[dict] = None) -> str:
        """
        Generate text using the Google AI Studio service.

        Args:
            prompt: The prompt to use for the generation.
            response_schema: An optional JSON schema to define the expected
                response format.

        Returns:
            The generated text as a string (or parsed data if
                response_schema is provided).
        """

        genai.configure(api_key=self.config.get("api_key"))
        model = genai.GenerativeModel(model_name=self.config.get("model"))

        generation_config = genai.GenerationConfig(
            temperature=self.config.get("temperature"),
            top_p=self.config.get("top_p"),
            top_k=self.config.get("top_k"),
            max_output_tokens=self.config.get("max_output_tokens"),
        )

        if response_schema:
            generation_config.response_mime_type = "application/json"
            generation_config.response_schema = response_schema

        response = model.generate_content(
            contents=prompt,
            generation_config=generation_config,
        )

        if response_schema:
            try:
                return json.loads(response.text)
            except Exception as error:
                raise ValueError(
                    f"Error JSON parsing text: {response.text}: {error}"
                ) from error
        return response.text


if has_required_deps:
    manager.LLMManager.register_provider(AIStudio)
    