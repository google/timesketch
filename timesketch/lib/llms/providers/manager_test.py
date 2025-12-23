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
"""Tests for LLM provider manager."""

from timesketch.lib.testlib import BaseTest
from timesketch.lib.llms.providers import manager


class MockAistudioProvider:
    """A mock provider for Google AI Studio (using API key)."""

    NAME = "aistudio"

    def __init__(self, config, **kwargs):
        self.config = config
        self.kwargs = kwargs

    def generate(self) -> str:
        return "Generated response from AI Studio."


class MockVertexAIProvider:
    """A mock provider for Google Cloud Vertex AI."""

    NAME = "vertexai"

    def __init__(self, config, **kwargs):
        if not config.get("project_id"):
            raise ValueError(
                "Vertex AI provider requires a 'project_id' in its configuration."
            )
        self.config = config
        self.kwargs = kwargs

    def generate(self) -> str:
        return "Generated response from Vertex AI."


class TestLLMManager(BaseTest):
    """Tests for the functionality of the LLMManager module."""

    def setUp(self) -> None:
        super().setUp()
        manager.LLMManager.clear_registration()
        manager.LLMManager.register_provider(MockAistudioProvider)
        manager.LLMManager.register_provider(MockVertexAIProvider)
        self.app.config["LLM_PROVIDER_CONFIGS"] = {
            "default": {
                "aistudio": {
                    "api_key": "AIzaSyTestDefaultKey",
                    "model": "gemini-2.0-flash-exp",
                }
            },
        }

    def tearDown(self) -> None:
        manager.LLMManager.clear_registration()
        super().tearDown()

    def test_get_providers(self):
        """Test that get_providers returns the registered providers."""
        providers = manager.LLMManager.get_providers()
        provider_list = list(providers)
        self.assertIsInstance(provider_list, list)
        # Verify that both providers are registered.
        found_aistudio = any(
            provider_name == "aistudio" and provider_class == MockAistudioProvider
            for provider_name, provider_class in provider_list
        )
        found_vertexai = any(
            provider_name == "vertexai" and provider_class == MockVertexAIProvider
            for provider_name, provider_class in provider_list
        )
        self.assertTrue(found_aistudio, "AI Studio provider not found.")
        self.assertTrue(found_vertexai, "Vertex AI provider not found.")

    def test_get_provider(self):
        """Test retrieval of a provider class from the registry."""
        provider_class = manager.LLMManager.get_provider("aistudio")
        self.assertEqual(provider_class, MockAistudioProvider)
        self.assertRaises(KeyError, manager.LLMManager.get_provider, "no_such_provider")

    def test_register_provider(self):
        """Test that re-registering an already registered provider raises ValueError."""
        self.assertRaises(
            ValueError, manager.LLMManager.register_provider, MockAistudioProvider
        )

    def test_create_provider_default(self):
        """Test create_provider using the default configuration."""
        provider_instance = manager.LLMManager.create_provider()
        self.assertIsInstance(provider_instance, MockAistudioProvider)
        self.assertEqual(
            provider_instance.config,
            {
                "api_key": "AIzaSyTestDefaultKey",
                "model": "gemini-2.0-flash-exp",
            },
        )

    def test_create_provider_feature(self):
        """Test create_provider using a feature-specific configuration."""
        self.app.config["LLM_PROVIDER_CONFIGS"] = {
            "nl2q": {
                "vertexai": {
                    "model": "gemini-1.5-flash-001",
                    "project_id": "test_project_id",
                },
            },
        }
        provider_instance = manager.LLMManager.create_provider(feature_name="nl2q")
        self.assertIsInstance(provider_instance, MockVertexAIProvider)
        self.assertEqual(
            provider_instance.config,
            {
                "model": "gemini-1.5-flash-001",
                "project_id": "test_project_id",
            },
        )

    def test_create_provider_invalid_config(self):
        """Test that create_provider raises ValueError when configuration is invalid.

        Here, more than one provider is specified in the configuration.
        """
        self.app.config["LLM_PROVIDER_CONFIGS"] = {
            "default": {
                "aistudio": {"api_key": "value"},
                "vertexai": {"model": "value"},
            }
        }
        with self.assertRaises(ValueError):
            manager.LLMManager.create_provider()

    def test_create_provider_missing_config(self):
        """Test that create_provider raises ValueError when configuration is missing."""
        self.app.config["LLM_PROVIDER_CONFIGS"] = {}
        with self.assertRaises(ValueError):
            manager.LLMManager.create_provider()

    def test_create_provider_empty_feature_fallback(self):
        """Test that create_provider falls back to default when feature config empty."""
        self.app.config["LLM_PROVIDER_CONFIGS"] = {
            "llm_summarize": {},  # Empty feature config
            "default": {
                "aistudio": {
                    "api_key": "AIzaSyTestDefaultKey",
                    "model": "gemini-2.0-flash-exp",
                }
            },
        }
        provider_instance = manager.LLMManager.create_provider(
            feature_name="llm_summarize"
        )
        self.assertIsInstance(provider_instance, MockAistudioProvider)
        self.assertEqual(
            provider_instance.config,
            {
                "api_key": "AIzaSyTestDefaultKey",
                "model": "gemini-2.0-flash-exp",
            },
        )

    def test_create_provider_fallback_on_feature_init_error(self):
        """Test fallback to default if a feature's provider init raises ValueError."""
        expected_init_error_msg = (
            "Vertex AI provider requires a 'project_id' in its configuration."
        )
        feature_provider_name = "vertexai"
        default_provider_name = "aistudio"
        feature_name = "test_llm_feature"
        default_api_key = "DefaultKeyForFallbackTest"

        self.app.config["LLM_PROVIDER_CONFIGS"] = {
            feature_name: {
                feature_provider_name: {
                    "model": "gemini-2.0-flash-001",
                    # 'project_id' is missing
                }
            },
            "default": {
                default_provider_name: {
                    "api_key": default_api_key,
                    "model": "default-model",
                }
            },
        }

        with self.assertLogs("timesketch.llm.manager", level="DEBUG") as log_cm:
            provider_instance = manager.LLMManager.create_provider(
                feature_name=feature_name
            )

        self.assertIsInstance(
            provider_instance,
            MockAistudioProvider,
            "Manager should have fallen back to the default MockAistudioProvider.",
        )
        self.assertEqual(provider_instance.config["api_key"], default_api_key)

        self.assertTrue(
            any(
                f"Failed to initialize provider '{feature_provider_name}'" in msg
                and f"feature '{feature_name}'" in msg
                and expected_init_error_msg in msg
                and "Attempting fallback" in msg
                for msg in log_cm.output
            ),
            "Log message for failed feature init and fallback not found or incorrect.",
        )
