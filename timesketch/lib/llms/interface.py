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
"""Interface for LLM providers."""

import string

from flask import current_app

DEFAULT_TEMPERATURE = 0.1
DEFAULT_TOP_P = 0.1
DEFAULT_TOP_K = 0
DEFAULT_MAX_OUTPUT_TOKENS = 2048
DEFAULT_STREAM = False


class LLMProvider:
    """Base class for LLM providers."""

    NAME = "name"

    def __init__(
        self,
        temperature: float = DEFAULT_TEMPERATURE,
        top_p: float = DEFAULT_TOP_P,
        top_k: int = DEFAULT_TOP_K,
        max_output_tokens: int = DEFAULT_MAX_OUTPUT_TOKENS,
        stream: bool = DEFAULT_STREAM,
    ):
        """Initialize the LLM provider.

        Args:
            temperature: The temperature to use for the response.
            top_p: The top_p to use for the response.
            top_k: The top_k to use for the response.
            max_output_tokens: The maximum number of output tokens to generate.
            stream: Whether to stream the response.

        Attributes:
            config: The configuration for the LLM provider.

        Raises:
            Exception: If the LLM provider is not configured.
        """
        config = {}
        config["temperature"] = temperature
        config["top_p"] = top_p
        config["top_k"] = top_k
        config["max_output_tokens"] = max_output_tokens
        config["stream"] = stream

        # Load the LLM provider config from the Flask app config
        config_from_flask = current_app.config.get("LLM_PROVIDER_CONFIGS").get(
            self.NAME
        )
        if not config_from_flask:
            raise Exception(f"{self.NAME} config not found")

        config.update(config_from_flask)
        self.config = config

    def prompt_from_template(self, template: str, kwargs: dict) -> str:
        """Format a prompt from a template.

        Args:
            template: The template to format.
            kwargs: The keyword arguments to format the template with.

        Returns:
            The formatted prompt.
        """
        formatter = string.Formatter()
        return formatter.format(template, **kwargs)

    def generate(self, prompt: str) -> str:
        """Generate a response from the LLM provider.

        Args:
            prompt: The prompt to generate a response for.
            temperature: The temperature to use for the response.
            stream: Whether to stream the response.

        Returns:
            The generated response.
        """
        raise NotImplementedError()
