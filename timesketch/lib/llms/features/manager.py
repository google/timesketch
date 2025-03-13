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
"""Manager for LLM features."""

import os
import importlib
import inspect
import pkgutil
import logging
from timesketch.lib.llms.features.interface import LLMFeatureInterface

logger = logging.getLogger("timesketch.llm.manager")


class FeatureManager:
    """The manager for LLM features."""

    _feature_registry = {}

    @classmethod
    def load_llm_features(cls):
        """Dynamically load and register all LLM features."""
        features_path = os.path.dirname(os.path.abspath(__file__))
        cls.clear_registration()

        for _, module_name, _ in pkgutil.iter_modules([features_path]):
            if module_name in ["interface", "manager"] or module_name.endswith("_test"):
                continue
            try:
                module = importlib.import_module(
                    f"timesketch.lib.llms.features.{module_name}"
                )
                for _, obj in inspect.getmembers(module):
                    if (
                        inspect.isclass(obj)
                        and issubclass(obj, LLMFeatureInterface)
                        and obj != LLMFeatureInterface
                    ):
                        try:
                            cls.register_feature(obj)
                        except ValueError as e:
                            logger.debug("Failed to register feature: %s", str(e))

            except (ImportError, AttributeError) as e:
                logger.error(
                    "Error loading LLM feature module %s: %s", module_name, str(e)
                )

        logger.debug("Loaded %d LLM features", len(cls._feature_registry))

    @classmethod
    def register_feature(cls, feature_class: type[LLMFeatureInterface]):
        """Register an LLM feature class."""
        feature_name = feature_class.NAME.lower()
        if feature_name in cls._feature_registry:
            raise ValueError(f"LLM Feature {feature_class.NAME} already registered")
        cls._feature_registry[feature_name] = feature_class

    @classmethod
    def get_feature(cls, feature_name: str) -> type[LLMFeatureInterface]:
        """Get a feature class by name."""
        try:
            return cls._feature_registry[feature_name.lower()]
        except KeyError as no_such_feature:
            raise KeyError(
                f"No such LLM feature: {feature_name.lower()}"
            ) from no_such_feature

    @classmethod
    def get_features(cls):
        """Get all registered features.

        Yields:
            A tuple of (feature_name, feature_class)
        """
        yield from cls._feature_registry.items()

    @classmethod
    def get_feature_instance(cls, feature_name: str) -> LLMFeatureInterface:
        """Get an instance of a feature by name."""
        feature_class = cls.get_feature(feature_name)
        return feature_class()

    @classmethod
    def clear_registration(cls):
        """Clear all registered features."""
        cls._feature_registry = {}
