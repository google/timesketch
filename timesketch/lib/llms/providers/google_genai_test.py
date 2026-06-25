# Copyright 2026 Google Inc. All rights reserved.
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
"""Tests for the Google GenAI provider."""

from unittest import mock
from timesketch.lib.testlib import BaseTest
from timesketch.lib.llms.providers.google_genai import GoogleGenAI


# pylint: disable=protected-access
class TestGoogleGenAI(BaseTest):
    """Tests for the Google GenAI provider."""

    def setUp(self):
        """Set up the tests."""
        super().setUp()
        self.config_vertex = {
            "model": "gemini-2.0-flash",
            "project_id": "test-project",
            "location": "us-central1",
        }
        self.config_gemini = {
            "model": "gemini-2.0-flash",
            "api_key": "test-api-key",
        }

    @mock.patch("google.genai.Client")
    def test_init_vertex(self, mock_client):
        """Test initialization with Vertex AI configuration."""
        provider = GoogleGenAI(self.config_vertex)
        self.assertEqual(provider._project_id, "test-project")
        self.assertEqual(provider._location, "us-central1")
        mock_client.assert_called_once_with(
            vertexai=True, project="test-project", location="us-central1"
        )

    @mock.patch("google.genai.Client")
    def test_init_gemini(self, mock_client):
        """Test initialization with Gemini API configuration."""
        provider = GoogleGenAI(self.config_gemini)
        self.assertEqual(provider._api_key, "test-api-key")
        mock_client.assert_called_once_with(api_key="test-api-key")

    def test_init_missing_config(self):
        """Test initialization with missing configuration."""
        with self.assertRaises(ValueError):
            GoogleGenAI({"model": "test-model"})
        with self.assertRaises(ValueError):
            GoogleGenAI({"api_key": "test-key"})

    @mock.patch("google.genai.Client")
    def test_generate(self, mock_client):
        """Test text generation."""
        mock_response = mock.MagicMock()
        mock_response.text = "Generated text"
        mock_client.return_value.models.generate_content.return_value = mock_response

        provider = GoogleGenAI(self.config_gemini)
        response = provider.generate("Test prompt")

        self.assertEqual(response, "Generated text")
        mock_client.return_value.models.generate_content.assert_called_once()

    @mock.patch("google.genai.Client")
    def test_generate_with_schema(self, mock_client):
        """Test text generation with JSON schema."""
        mock_response = mock.MagicMock()
        mock_response.parsed = {"key": "value"}
        mock_client.return_value.models.generate_content.return_value = mock_response

        provider = GoogleGenAI(self.config_gemini)
        schema = {"type": "object", "properties": {"key": {"type": "string"}}}
        response = provider.generate("Test prompt", response_schema=schema)

        self.assertEqual(response, {"key": "value"})
        # Verify that generate_content was called with the correct config
        _, kwargs = mock_client.return_value.models.generate_content.call_args
        self.assertEqual(kwargs["config"].response_schema, schema)
        self.assertEqual(kwargs["config"].response_mime_type, "application/json")

    @mock.patch("google.genai.Client")
    def test_generate_error_concise(self, mock_client):
        """Test that API errors are returned in a concise format."""

        class MockAPIError(Exception):
            def __init__(self, code, status, message):
                self.code = code
                self.status = status
                self.message = message
                super().__init__(f"{code} {status}")

        mock_error = MockAPIError(429, "RESOURCE_EXHAUSTED", "Quota exceeded")
        mock_client.return_value.models.generate_content.side_effect = mock_error

        provider = GoogleGenAI(self.config_gemini)

        with mock.patch("google.genai.errors.APIError", MockAPIError):
            with self.assertRaises(ValueError) as cm:
                provider.generate("Test prompt")

            self.assertEqual(
                str(cm.exception),
                "Error generating content: 429 RESOURCE_EXHAUSTED: Quota exceeded",
            )
