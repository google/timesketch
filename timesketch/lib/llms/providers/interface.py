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
from typing import Optional

DEFAULT_TEMPERATURE = 0.1
DEFAULT_TOP_P = 0.1
DEFAULT_TOP_K = 1
DEFAULT_MAX_OUTPUT_TOKENS = 2048
DEFAULT_STREAM = False
DEFAULT_LOCATION = None


class LLMProvider:
    """
    Base class for LLM providers.

    The provider is instantiated with a configuration dictionary that
    was extracted (by the manager) from timesketch.conf.
    Subclasses should override the NAME attribute.
    """

    NAME = "name"

    def __init__(
        self,
        config: dict,
        temperature: float = DEFAULT_TEMPERATURE,
        top_p: float = DEFAULT_TOP_P,
        top_k: int = DEFAULT_TOP_K,
        max_output_tokens: int = DEFAULT_MAX_OUTPUT_TOKENS,
        stream: bool = DEFAULT_STREAM,
        location: Optional[str] = DEFAULT_LOCATION,
    ):
        """Initialize the LLM provider.

        Args:
            config: A dictionary of provider-specific configuration options.
            temperature: Temperature setting for text generation.
            top_p: Top probability (p) value used for generation.
            top_k: Top-k value used for generation.
            max_output_tokens: Maximum number of tokens to generate in the output.
            stream: Whether to enable streaming of the generated content.
            location: An optional location parameter for the provider.

        Attributes:
            config: The configuration for the LLM provider.

        Raises:
            Exception: If the LLM provider is not configured.
        """
        self.config = {
            "temperature": temperature,
            "top_p": top_p,
            "top_k": top_k,
            "max_output_tokens": max_output_tokens,
            "stream": stream,
            "location": location,
        }
        self.config.update(config)

    def prompt_from_template(self, template: str, kwargs: dict) -> str:
        """Format a prompt from a template."""
        formatter = string.Formatter()
        return formatter.format(template, **kwargs)

    def generate(self, prompt: str, response_schema: Optional[dict] = None) -> str:
        """Generate a response from the LLM provider.

        Args:
            prompt: The prompt to generate a response for.
            response_schema: An optional JSON schema to define the expected
                response format.

        Returns:
            The generated response.

        Subclasses must override this method.
        """
        raise NotImplementedError()
