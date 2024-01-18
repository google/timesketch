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
"""Vertex AI LLM provider."""

from timesketch.lib.llms import interface
from timesketch.lib.llms import manager

# Check if the required dependencies are installed.
has_required_deps = True
try:
    from google.cloud import aiplatform
    from vertexai.preview.generative_models import GenerativeModel
except ImportError:
    has_required_deps = False


class VertexAI(interface.LLMProvider):
    """Vertex AI LLM provider."""

    NAME = "vertexai"

    def generate(self, prompt: str) -> str:
        """
        Generate text using the Vertex AI service.

        Args:
            prompt: The prompt to use for the generation.
            temperature: The temperature to use for the generation.
            stream: Whether to stream the generation or not.

        Returns:
            The generated text as a string.
        """
        aiplatform.init(
            project=self.config.get("project_id"),
        )
        model = GenerativeModel(self.config.get("model"))
        response = model.generate_content(
            prompt,
            generation_config={
                "max_output_tokens": self.config.get("max_output_tokens"),
                "temperature": self.config.get("temperature"),
            },
            stream=self.config.get("stream"),
        )

        return response.text


# Only register the provider if the required dependencies are installed.
if has_required_deps:
    manager.LLMManager.register_provider(VertexAI)
