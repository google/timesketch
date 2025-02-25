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
"""A LLM provider for the ollama server."""
import json
import requests
from typing import Optional

from timesketch.lib.llms.providers import interface
from timesketch.lib.llms.providers import manager


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
        api_resource = "/api/chat"
        url = self.config.get("server_url") + api_resource
        return requests.post(url, data=request_body)

    def generate(self, prompt: str, response_schema: Optional[dict] = None) -> str:
        """
        Generate text using the ollama server, optionally with a JSON schema.

        Args:
            prompt: The prompt to use for the generation.
            response_schema: An optional JSON schema to define the expected
                response format.

        Returns:
            The generated text as a string (or parsed data if
                response_schema is provided).
        """
        request_body = {
            "messages": [{"role": "user", "content": prompt}],
            "model": self.config.get("model"),
            "stream": False,  # Force to false, streaming not available with /api/chat endpoint
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

        try:
            text_response = response.json().get("content", "").strip()
            if response_schema:
                return json.loads(text_response)
            
            return text_response

        except json.JSONDecodeError as error:
            raise ValueError(
                f"Error JSON parsing text: {text_response}: {error}"
            ) from error

        except Exception as error:
            raise ValueError(
                f"An unexpected error occurred: {error}"
            ) from error


manager.LLMManager.register_provider(Ollama)
