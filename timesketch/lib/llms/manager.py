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


class LLMManager:
    """The manager for LLM providers."""

    _class_registry = {}

    @classmethod
    def get_providers(cls):
        """Get all registered providers.

        Yields:
            A tuple of (provider_name, provider_class)
        """
        for provider_name, provider_class in cls._class_registry.items():
            yield provider_name, provider_class

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
    def register_provider(cls, provider_class: type) -> None:
        """Register a provider.

        Args:
            provider_class: The provider class to register.

        Raises:
            ValueError: If the provider is already registered.
        """
        provider_name = provider_class.NAME.lower()
        if provider_name in cls._class_registry:
            raise ValueError(f"Provider {provider_class.NAME} already registered")
        cls._class_registry[provider_name] = provider_class

    @classmethod
    def clear_registration(cls):
        """Clear all registered providers."""
        cls._class_registry = {}
