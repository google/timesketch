"""Tests for the AnonRouter provider."""

import json
from unittest import mock

from timesketch.lib.llms.providers.contrib import anonrouter
from timesketch.lib.testlib import BaseTest


def _mock_response(status_code=200, payload=None, text=""):
    """Builds a mock requests.Response like object."""
    response = mock.Mock()
    response.status_code = status_code
    response.text = text
    response.json.return_value = payload
    return response


class TestAnonRouter(BaseTest):
    """Tests for the AnonRouter provider."""

    def setUp(self):
        """Set up the tests."""
        super().setUp()
        self.config = {
            "api_key": "test-api-key",
            "model": "meta-llama/llama-3.3-70b",
        }

    def test_init_defaults(self):
        """Test that the default server URL and timeout are used."""
        provider = anonrouter.AnonRouter(self.config)
        self.assertEqual(provider.server_url, anonrouter.DEFAULT_SERVER_URL)
        self.assertEqual(provider.timeout, anonrouter.DEFAULT_TIMEOUT)

    def test_init_missing_config(self):
        """Test initialization with missing configuration."""
        with self.assertRaises(ValueError):
            anonrouter.AnonRouter({"model": "meta-llama/llama-3.3-70b"})
        with self.assertRaises(ValueError):
            anonrouter.AnonRouter({"api_key": "test-api-key"})

    @mock.patch("requests.post")
    def test_generate(self, mock_post):
        """Test text generation."""
        mock_post.return_value = _mock_response(
            payload={"choices": [{"message": {"content": "Generated text"}}]}
        )

        provider = anonrouter.AnonRouter(self.config)
        response = provider.generate("Test prompt")

        self.assertEqual(response, "Generated text")
        args, kwargs = mock_post.call_args
        self.assertEqual(args[0], f"{anonrouter.DEFAULT_SERVER_URL}/chat/completions")
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer test-api-key")
        self.assertEqual(kwargs["json"]["model"], "meta-llama/llama-3.3-70b")
        self.assertEqual(
            kwargs["json"]["messages"], [{"role": "user", "content": "Test prompt"}]
        )
        self.assertNotIn("response_format", kwargs["json"])

    @mock.patch("requests.post")
    def test_generate_with_schema(self, mock_post):
        """Test text generation with JSON schema."""
        mock_post.return_value = _mock_response(
            payload={
                "choices": [{"message": {"content": json.dumps({"key": "value"})}}]
            }
        )

        provider = anonrouter.AnonRouter(self.config)
        schema = {"type": "object", "properties": {"key": {"type": "string"}}}
        response = provider.generate("Test prompt", response_schema=schema)

        self.assertEqual(response, {"key": "value"})
        _, kwargs = mock_post.call_args
        self.assertEqual(
            kwargs["json"]["response_format"],
            {
                "type": "json_schema",
                "json_schema": {"name": "response", "schema": schema},
            },
        )

    @mock.patch("requests.post")
    def test_generate_error_status(self, mock_post):
        """Test that a non-200 response raises an error."""
        mock_post.return_value = _mock_response(
            status_code=401, text='{"error": {"message": "Invalid API key provided."}}'
        )

        provider = anonrouter.AnonRouter(self.config)
        with self.assertRaises(ValueError):
            provider.generate("Test prompt")

    @mock.patch("requests.post")
    def test_generate_unexpected_response(self, mock_post):
        """Test that an unexpected response structure raises an error."""
        mock_post.return_value = _mock_response(payload={"choices": []}, text="{}")

        provider = anonrouter.AnonRouter(self.config)
        with self.assertRaises(ValueError):
            provider.generate("Test prompt")
