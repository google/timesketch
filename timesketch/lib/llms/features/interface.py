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
"""Interface for LLM features."""

from typing import Any, Optional
from abc import ABC, abstractmethod
from timesketch.models.sketch import Sketch


class LLMFeatureInterface(ABC):
    """Interface for LLM features.

    This abstract class defines the required methods and attributes for implementing
    an LLM-powered feature in Timesketch. Features must override the NAME constant
    and implement the abstract methods.

    Attributes:
        NAME: String identifier for the feature. Must be overridden in subclasses.
        RESPONSE_SCHEMA: Optional JSON schema that defines the expected format of
            the LLM response. When defined, this schema will be passed to the LLM
            provider to enforce structured outputs matching the defined format.
            For example:

            {
                "type": "object",
                "properties": {"summary": {"type": "string"}},
                "required": ["summary"],
            }

            If None, the LLM will return unstructured text.
    """

    NAME: str = "llm_feature_interface"  # Must be overridden in subclasses
    RESPONSE_SCHEMA: Optional[dict[str, Any]] = None

    @abstractmethod
    def generate_prompt(self, sketch: Sketch, **kwargs: Any) -> str:
        """Generates a prompt for the LLM.

        Args:
            sketch_id: The ID of the sketch.
            kwargs: Feature-specific keyword arguments for prompt generation.

        Returns:
            The generated prompt string.
        """
        raise NotImplementedError()

    @abstractmethod
    def process_response(self, llm_response: str, **kwargs: Any) -> dict[str, Any]:
        """Processes the LLM response and formats it for API consumption.

        This method takes the response from the LLM provider and transforms it into
        a structured format to be returned to the frontend through the API. The
        response handling varies depending on whether RESPONSE_SCHEMA is defined:

        - If RESPONSE_SCHEMA is None: Typically receives a string response
        - If RESPONSE_SCHEMA is defined: Typically receives a structured dict

        The returned dictionary defines the data contract with the frontend, which will
        use these fields to render the appropriate UI elements.

        Args:
            llm_response: The response from the LLM provider. This may be a
                        string or a structured dict depending on RESPONSE_SCHEMA.
            **kwargs: Additional data needed for processing, which may include:
                    - sketch_id: The ID of the sketch
                    - sketch: The Sketch object

        Returns:
            A dictionary that will be JSON-serialized and returned through the API.
            This dictionary defines the data contract with the frontend and must include
            all fields that the frontend expects to render. Example for NL2Q:
            - {"name": "AI generated search query","query_string": "...","error":null}
        """
        raise NotImplementedError()
