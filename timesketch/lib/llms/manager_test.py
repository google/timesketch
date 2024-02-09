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
from timesketch.lib.llms import manager


class MockProvider:
    """A mock LLM provider."""

    NAME = "mock"

    def generate_text(self) -> str:
        """Generate text."""
        return "This is a mock LLM provider."


class TestLLMManager(BaseTest):
    """Tests for the functionality of the manager module."""

    manager.LLMManager.clear_registration()
    manager.LLMManager.register_provider(MockProvider)

    def test_get_providers(self):
        """Test to get provider class objects."""
        providers = manager.LLMManager.get_providers()
        provider_list = list(providers)
        first_provider_tuple = provider_list[0]
        provider_name, provider_class = first_provider_tuple
        self.assertIsInstance(provider_list, list)
        self.assertIsInstance(first_provider_tuple, tuple)
        self.assertEqual(provider_class, MockProvider)
        self.assertEqual(provider_name, "mock")

    def test_get_provider(self):
        """Test to get provider class from registry."""
        provider_class = manager.LLMManager.get_provider("mock")
        self.assertEqual(provider_class, MockProvider)
        self.assertRaises(KeyError, manager.LLMManager.get_provider, "no_such_provider")

    def test_register_provider(self):
        """Test so we raise KeyError when provider is already registered."""
        self.assertRaises(
            ValueError, manager.LLMManager.register_provider, MockProvider
        )
