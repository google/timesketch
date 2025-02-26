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
    """Interface for LLM features."""

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
        """Processes the raw LLM response.

        Args:
            llm_response:  The raw string response from the LLM provider.
            kwargs: Feature-specific arguments.

        Returns:
            A dictionary containing the processed response data, suitable for
            returning from the API.  Must include a "response" key with the
            main result, and can optionally include other metadata.
        """
        raise NotImplementedError()
