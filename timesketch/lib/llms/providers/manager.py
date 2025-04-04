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
"""This file contains a class for managing Large Language Model (LLM) providers."""

import logging

from flask import current_app
from timesketch.lib.llms.providers.interface import LLMProvider

logger = logging.getLogger("timesketch.llm.manager")


class LLMManager:
    """The manager for LLM providers."""

    _class_registry = {}

    @classmethod
    def register_provider(cls, provider_class: type) -> None:
        """Register a provider class."""
        provider_name = provider_class.NAME.lower()
        if provider_name in cls._class_registry:
            raise ValueError(f"Provider {provider_class.NAME} already registered")
        cls._class_registry[provider_name] = provider_class

    @classmethod
    def get_providers(cls):
        """Get all registered providers.

        Yields:
            A tuple of (provider_name, provider_class)
        """
        yield from cls._class_registry.items()

    @classmethod
    def get_provider(cls, provider_name: str) -> type:
        """Get a provider by name.

        Args:
            provider_name: The name of the provider.

        Returns:
            The provider class.
        """
        try:
            provider_class = cls._class_registry[provider_name.lower()]
        except KeyError as no_such_provider:
            raise KeyError(
                f"No such provider: {provider_name.lower()}"
            ) from no_such_provider
        return provider_class

    @classmethod
    def create_provider(cls, feature_name: str = None, **kwargs) -> LLMProvider:
        """
        Create an instance of the provider for the given feature.

        If a valid configuration exists for the feature in
        current_app.config["LLM_PROVIDER_CONFIGS"], use it; otherwise,
        fall back to the configuration under the "default" key.

        The configuration is expected to be a dict with exactly one key:
        the provider name.
        """
        llm_configs = current_app.config.get("LLM_PROVIDER_CONFIGS", {})

        if feature_name and feature_name in llm_configs:
            config_mapping = llm_configs[feature_name]
            if config_mapping and len(config_mapping) == 1:
                provider_name = next(iter(config_mapping))
                provider_config = config_mapping[provider_name]
                provider_class = cls.get_provider(provider_name)
                # Check that provider specifies required fields
                try:
                    return provider_class(config=provider_config, **kwargs)
                except ValueError as e:
                    logger.debug(
                        "Failed to initialize provider '%s' for feature '%s' "
                        "due to configuration error: %s. "
                        "Attempting fallback to default provider.",
                        provider_name,
                        feature_name,
                        e,
                        exc_info=False,
                    )

        # Fallback to default config
        config_mapping = llm_configs.get("default")
        if not config_mapping or len(config_mapping) != 1:
            raise ValueError("Default configuration must specify exactly one provider.")
        provider_name = next(iter(config_mapping))
        provider_config = config_mapping[provider_name]

        provider_class = cls.get_provider(provider_name)
        return provider_class(config=provider_config, **kwargs)

    @classmethod
    def clear_registration(cls):
        """Clear all registered providers."""
        cls._class_registry = {}
