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
"""A LLM provider for the ollama server."""
import json
import requests

from timesketch.lib.llms import interface
from timesketch.lib.llms import manager


class Ollama(interface.LLMProvider):
    """A LLM provider for the ollama server."""

    NAME = "ollama"

    def _post(self, request_body: str) -> requests.Response:
        """
        Make a POST request to the ollama server.

        Args:
            request_body: The body of the request in JSON format.

        Returns:
            The response from the server as a dictionary.
        """
        api_resource = "/api/generate/"
        url = self.config.get("server_url") + api_resource
        return requests.post(url, data=request_body)

    def generate(self, prompt: str) -> str:
        """
        Generate text using the ollama server.

        Args:
            prompt: The prompt to use for the generation.
            temperature: The temperature to use for the generation.
            stream: Whether to stream the generation or not.

        Raises:
            ValueError: If the generation fails.

        Returns:
            The generated text as a string.
        """
        request_body = {
            "prompt": prompt,
            "model": self.config.get("model"),
            "stream": self.config.get("stream"),
            "options": {
                "temperature": self.config.get("temperature"),
                "num_predict": self.config.get("max_output_tokens"),
            },
        }
        response = self._post(json.dumps(request_body))
        if response.status_code != 200:
            raise ValueError(f"Error generating text: {response.text}")

        return response.json().get("response", "").strip()


manager.LLMManager.register_provider(Ollama)
