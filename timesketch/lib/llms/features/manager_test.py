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
"""Tests for LLM feature manager."""

from typing import Any
from timesketch.lib.testlib import BaseTest
from timesketch.lib.llms.features import manager
from timesketch.models.sketch import Sketch


class MockSummarizeFeature:
    """A mock LLM summarize feature."""

    NAME = "llm_summarize"

    def generate_prompt(self, _sketch: Sketch, **_kwargs: Any) -> str:
        """Mock implementation of generate_prompt."""
        return "Summarize these events."

    def process_response(self, llm_response: str, **kwargs: Any) -> dict[str, Any]:
        """Mock implementation of process_response."""
        return {"response": f"Summary: {llm_response}"}


class MockNl2qFeature:
    """A mock Natural Language to Query feature."""

    NAME = "nl2q"

    def generate_prompt(self, _sketch: Sketch, **_kwargs: Any) -> str:
        """Mock implementation of generate_prompt."""
        return "Convert this question to a query."

    def process_response(self, llm_response: str, **_kwargs: Any) -> dict[str, Any]:
        """Mock implementation of process_response."""
        return {"response": f"Query: {llm_response}"}


class TestFeatureManager(BaseTest):
    """Tests for the functionality of the FeatureManager module."""

    def setUp(self) -> None:
        super().setUp()
        manager.FeatureManager.clear_registration()
        manager.FeatureManager.register_feature(MockSummarizeFeature)
        manager.FeatureManager.register_feature(MockNl2qFeature)

    def tearDown(self) -> None:
        manager.FeatureManager.clear_registration()
        super().tearDown()

    def test_get_features(self):
        """Test that get_features returns the registered features."""
        features = manager.FeatureManager.get_features()
        feature_list = list(features)
        self.assertIsInstance(feature_list, list)

        found_summarize = any(
            feature_name == "llm_summarize" and feature_class == MockSummarizeFeature
            for feature_name, feature_class in feature_list
        )
        found_nl2q = any(
            feature_name == "nl2q" and feature_class == MockNl2qFeature
            for feature_name, feature_class in feature_list
        )
        self.assertTrue(found_summarize, "LLM Summarize feature not found.")
        self.assertTrue(found_nl2q, "NL2Q feature not found.")

    def test_get_feature(self):
        """Test retrieval of a feature class from the registry."""
        feature_class = manager.FeatureManager.get_feature("llm_summarize")
        self.assertEqual(feature_class, MockSummarizeFeature)

        feature_class = manager.FeatureManager.get_feature("LLM_SUMMARIZE")
        self.assertEqual(feature_class, MockSummarizeFeature)

        self.assertRaises(
            KeyError, manager.FeatureManager.get_feature, "no_such_feature"
        )

    def test_register_feature(self):
        """Test that re-registering an already registered feature raises ValueError."""
        self.assertRaises(
            ValueError, manager.FeatureManager.register_feature, MockSummarizeFeature
        )

    def test_get_feature_instance(self):
        """Test get_feature_instance creates the correct feature instance."""
        feature_instance = manager.FeatureManager.get_feature_instance("llm_summarize")
        self.assertIsInstance(feature_instance, MockSummarizeFeature)

        feature_instance = manager.FeatureManager.get_feature_instance("nl2q")
        self.assertIsInstance(feature_instance, MockNl2qFeature)

        self.assertRaises(
            KeyError, manager.FeatureManager.get_feature_instance, "no_such_feature"
        )

    def test_feature_methods(self):
        """Test that feature methods work correctly."""
        summarize_instance = manager.FeatureManager.get_feature_instance(
            "llm_summarize"
        )
        nl2q_instance = manager.FeatureManager.get_feature_instance("nl2q")

        sketch = None

        self.assertEqual(
            summarize_instance.generate_prompt(sketch), "Summarize these events."
        )
        self.assertEqual(
            nl2q_instance.generate_prompt(sketch), "Convert this question to a query."
        )

        self.assertEqual(
            summarize_instance.process_response("Test events"),
            {"response": "Summary: Test events"},
        )
        self.assertEqual(
            nl2q_instance.process_response("timestamp:*"),
            {"response": "Query: timestamp:*"},
        )

    def test_clear_registration(self):
        """Test clear_registration removes all registered features."""
        self.assertEqual(len(list(manager.FeatureManager.get_features())), 2)

        manager.FeatureManager.clear_registration()

        self.assertEqual(len(list(manager.FeatureManager.get_features())), 0)
        self.assertRaises(KeyError, manager.FeatureManager.get_feature, "llm_summarize")
