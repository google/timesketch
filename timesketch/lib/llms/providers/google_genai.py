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
"""Google GenAI LLM provider (supporting both Vertex AI and Gemini API)."""

import json
import logging
from typing import Any, Optional

from timesketch.lib.llms.providers import interface
from timesketch.lib.llms.providers import manager

has_required_deps = True
try:
    from google import genai
    from google.genai import types
except ImportError:
    has_required_deps = False

logger = logging.getLogger("timesketch.llm.providers.google_genai")


class GoogleGenAI(interface.LLMProvider):
    """Google GenAI LLM provider."""

    NAME = "google_genai"

    def __init__(self, config: dict, **kwargs: Any):
        """Initialize the Google GenAI provider.

        Args:
            config: The configuration for the provider.
            **kwargs: Additional arguments passed to the base class.

        Raises:
            ValueError: If required configuration keys are missing.
        """
        super().__init__(config, **kwargs)
        self._api_key = self.config.get("api_key")
        self._project_id = self.config.get("project_id")
        self._location = self.config.get("location")
        self._model_name = self.config.get("model")

        if not self._model_name:
            raise ValueError(
                "Google GenAI provider requires a 'model' in its configuration."
            )

        try:
            if self._project_id:
                # Vertex AI path
                self.client = genai.Client(
                    vertexai=True, project=self._project_id, location=self._location
                )
            elif self._api_key:
                # Gemini API path
                self.client = genai.Client(api_key=self._api_key)
            else:
                raise ValueError(
                    "Google GenAI provider requires either 'api_key' (for Gemini API) "
                    "or 'project_id' (for Vertex AI) in its configuration."
                )
        except Exception as e:
            raise ValueError(f"Failed to initialize Google GenAI client: {e}") from e

    def generate(self, prompt: str, response_schema: Optional[dict] = None) -> Any:
        """
        Generate text using the Google GenAI service.

        Args:
            prompt: The prompt to use for the generation.
            response_schema: An optional JSON schema to define the expected
                response format.

        Returns:
            The generated text as a string (or parsed data if
                response_schema is provided).
        """
        config_params = {
            "temperature": self.config.get("temperature"),
            "top_k": self.config.get("top_k"),
            "top_p": self.config.get("top_p"),
            "max_output_tokens": self.config.get("max_output_tokens"),
        }

        if response_schema:
            config_params["response_mime_type"] = "application/json"
            config_params["response_schema"] = response_schema

        generate_config = types.GenerateContentConfig(**config_params)

        try:
            response = self.client.models.generate_content(
                model=self._model_name,
                contents=prompt,
                config=generate_config,
            )
        except Exception as e:
            logger.error("Error generating content with Google GenAI: %s", e)
            raise ValueError(f"Error generating content: {e}") from e

        if response_schema:
            try:
                if hasattr(response, "parsed") and response.parsed is not None:
                    return response.parsed
                return json.loads(response.text)
            except Exception as error:
                raise ValueError(
                    f"Error JSON parsing text: {response.text}: {error}"
                ) from error

        return response.text


if has_required_deps:
    manager.LLMManager.register_provider(GoogleGenAI)

    # Register aliases for backward compatibility with old configuration names.
    class VertexAI(GoogleGenAI):
        """Alias for VertexAI."""

        NAME = "vertexai"

    class AIStudio(GoogleGenAI):
        """Alias for AI Studio."""

        NAME = "aistudio"

    manager.LLMManager.register_provider(VertexAI)
    manager.LLMManager.register_provider(AIStudio)
