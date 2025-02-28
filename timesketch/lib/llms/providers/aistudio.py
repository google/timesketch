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
"""Google AI Studio LLM provider."""

import json
from typing import Optional
from timesketch.lib.llms.providers import interface
from timesketch.lib.llms.providers import manager


# Check if the required dependencies are installed.
has_required_deps = True
try:
    import google.generativeai as genai
except ImportError:
    has_required_deps = False


class AIStudio(interface.LLMProvider):
    """AI Studio LLM provider."""

    NAME = "aistudio"

    def __init__(self, config: dict):
        """Initialize the AI Studio provider.
        Args:
            config: The configuration for the provider.
        """
        super().__init__(config)
        self._api_key = self.config.get("api_key")
        self._model_name = self.config.get("model", "gemini-1.5-flash")
        self._temperature = self.config.get("temperature", 0.2)
        self._top_p = self.config.get("top_p", 0.95)
        self._top_k = self.config.get("top_k", 10)
        self._max_output_tokens = self.config.get("max_output_tokens", 8192)

        if not self._api_key:
            raise ValueError("API key is required for AI Studio provider")
        genai.configure(api_key=self._api_key)
        self.model = genai.GenerativeModel(model_name=self._model_name)

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

        generation_config = genai.GenerationConfig(
            temperature=self._temperature,
            top_p=self._top_p,
            top_k=self._top_k,
            max_output_tokens=self._max_output_tokens,
        )

        if response_schema:
            generation_config.response_mime_type = "application/json"
            generation_config.response_schema = response_schema

        response = self.model.generate_content(
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
