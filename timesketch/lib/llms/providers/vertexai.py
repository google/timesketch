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
"""Vertex AI LLM provider."""

import json
from typing import Any, Optional

from timesketch.lib.llms.providers import interface
from timesketch.lib.llms.providers import manager

# Check if the required dependencies are installed.
has_required_deps = True
try:
    from google.cloud import aiplatform
    from vertexai.preview.generative_models import GenerativeModel
    from vertexai.preview.generative_models import GenerationConfig
except ImportError:
    has_required_deps = False


class VertexAI(interface.LLMProvider):
    """Vertex AI LLM provider."""

    NAME = "vertexai"

    def __init__(self, config: dict, **kwargs: Any):
        """Initialize the Vertex AI provider.

        Args:
            config: The configuration for the provider.
            **kwargs: Additional arguments passed to the base class.

        Raises:
            ValueError: If required configuration keys are missing.
        """
        super().__init__(config, **kwargs)
        project_id = self.config.get("project_id")
        model_name = self.config.get("model")

        if not project_id:
            raise ValueError(
                "Vertex AI provider requires a 'project_id' in its configuration."
            )
        if not model_name:
            raise ValueError(
                "Vertex AI provider requires a 'model' in its configuration."
            )

    def generate(self, prompt: str, response_schema: Optional[dict] = None) -> str:
        """
        Generate text using the Vertex AI service.

        Args:
            prompt: The prompt to use for the generation.
            response_schema: An optional JSON schema to define the expected
                response format.

        Returns:
            The generated text as a string (or parsed data if
                response_schema is provided).
        """
        aiplatform.init(
            project=self.config.get("project_id"),
            location=self.config.get("location"),
        )
        model = GenerativeModel(self.config.get("model"))

        if response_schema:
            generation_config = GenerationConfig(
                temperature=self.config.get("temperature"),
                top_k=self.config.get("top_k"),
                top_p=self.config.get("top_p"),
                response_mime_type="application/json",
                response_schema=response_schema,
            )
        else:
            generation_config = GenerationConfig(
                temperature=self.config.get("temperature"),
                top_k=self.config.get("top_k"),
                top_p=self.config.get("top_p"),
            )

        response = model.generate_content(
            prompt,
            generation_config=generation_config,
            stream=self.config.get("stream"),
        )

        if response_schema:
            try:
                return json.loads(response.text)
            except Exception as error:
                raise ValueError(
                    f"Error JSON parsing text: {response.text}: {error}"
                ) from error

        return response.text


# Only register the provider if the required dependencies are installed.
if has_required_deps:
    manager.LLMManager.register_provider(VertexAI)
