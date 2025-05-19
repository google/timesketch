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
"""A LLM provider for the Ollama server."""
from typing import Any, Optional
import json
import requests

from timesketch.lib.llms.providers import interface
from timesketch.lib.llms.providers import manager


class Ollama(interface.LLMProvider):
    """A LLM provider for the Ollama server."""

    NAME = "ollama"

    def __init__(self, config: dict, **kwargs: Any):
        """Initialize the Ollama provider.

        Args:
            config: The configuration for the provider.
            **kwargs: Additional arguments passed to the base class.

        Raises:
            ValueError: If required configuration keys ('server_url', 'model')
                        are missing or empty.
        """
        super().__init__(config, **kwargs)

        server_url = self.config.get("server_url")
        model_name = self.config.get("model")

        if not server_url:
            raise ValueError(
                "Ollama provider requires a 'server_url' in its configuration."
            )
        if not model_name:
            raise ValueError("Ollama provider requires a 'model' in its configuration.")

    def _post(self, request_body: str) -> requests.Response:
        """
        Make a POST request to the Ollama server.

        Args:
            request_body: The body of the request in JSON format.

        Returns:
            The response from the server as a requests.Response object.
        """
        api_resource = "/api/chat"
        url = self.config.get("server_url") + api_resource
        try:
            return requests.post(
                url,
                data=request_body,
                headers={"Content-Type": "application/json"},
                timeout=60,
            )
        except requests.exceptions.Timeout as error:
            raise ValueError(f"Request timed out: {error}") from error
        except requests.exceptions.RequestException as error:
            raise ValueError(f"Error making request: {error}") from error

    def generate(self, prompt: str, response_schema: Optional[dict] = None) -> str:
        """
        Generate text using the Ollama server, optionally with a JSON schema.

        Args:
            prompt: The prompt to use for the generation.
            response_schema: An optional JSON schema to define the expected
                response format.

        Returns:
            The generated text as a string (or parsed data if
            response_schema is provided).

        Raises:
            ValueError: If the request fails or JSON parsing fails.
        """
        request_body = {
            "messages": [{"role": "user", "content": prompt}],
            "model": self.config.get("model"),
            "stream": self.config.get("stream"),
            "options": {
                "temperature": self.config.get("temperature"),
                "num_predict": self.config.get("max_output_tokens"),
                "top_p": self.config.get("top_p"),
                "top_k": self.config.get("top_k"),
            },
        }

        if response_schema:
            request_body["format"] = response_schema

        response = self._post(json.dumps(request_body))

        if response.status_code != 200:
            raise ValueError(f"Error generating text: {response.text}")

        response_data = response.json()
        text_response = response_data.get("message", {}).get("content", "").strip()

        if response_schema:
            try:
                return json.loads(text_response)
            except json.JSONDecodeError as error:
                raise ValueError(
                    f"Error JSON parsing text: {text_response}: {error}"
                ) from error

        return text_response


manager.LLMManager.register_provider(Ollama)
