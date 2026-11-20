"""AnonRouter LLM provider."""

import json
from typing import Any, Optional, Union

import requests

from timesketch.lib.llms.providers import interface
from timesketch.lib.llms.providers import manager

# Default configuration values
DEFAULT_SERVER_URL = "https://api.anonrouter.ai/v1"
DEFAULT_TIMEOUT = 60


class AnonRouter(interface.LLMProvider):
    """AnonRouter provider for Timesketch.

    AnonRouter exposes an OpenAI compatible Chat Completions API that routes
    requests to models hosted by multiple providers. Models are addressed by
    their 'creator/model' identifier, for example 'meta-llama/llama-3.3-70b'.
    Run 'GET /v1/models' with your API key to list the models enabled for your
    account.

    This provider uses API key authentication (AnonRouter compatibility mode)
    and non-streaming responses, which is what the Timesketch LLM features
    need. The single-use ticket flow is not implemented.

    Configuration keys:
        api_key: An AnonRouter inference key (required).
        model: The model identifier to send requests to (required).
        server_url: The API base URL. Defaults to DEFAULT_SERVER_URL.
        timeout: Request timeout in seconds. Defaults to DEFAULT_TIMEOUT.
    """

    NAME = "anonrouter"

    def __init__(self, config: dict, **kwargs: Any):
        """Initializes the AnonRouter provider.

        Args:
            config: A dictionary of provider-specific configuration options.
            **kwargs: Additional arguments passed to the base class.

        Raises:
            ValueError: If required configuration keys ('api_key', 'model')
                are missing or empty.
        """
        super().__init__(config, **kwargs)
        self.api_key = self.config.get("api_key")
        self.model = self.config.get("model")
        self.server_url = (self.config.get("server_url") or DEFAULT_SERVER_URL).rstrip(
            "/"
        )
        self.timeout = self.config.get("timeout", DEFAULT_TIMEOUT)

        if not self.api_key:
            raise ValueError(
                "AnonRouter provider requires an 'api_key' in its configuration."
            )
        if not self.model:
            raise ValueError(
                "AnonRouter provider requires a 'model' in its configuration."
            )

    def _post(self, request_body: dict) -> requests.Response:
        """Makes a POST request to the AnonRouter chat completions endpoint.

        Args:
            request_body: The body of the request.

        Returns:
            The response from the server as a requests.Response object.

        Raises:
            ValueError: If the request fails.
        """
        url = f"{self.server_url}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        try:
            return requests.post(
                url, headers=headers, json=request_body, timeout=self.timeout
            )
        except requests.exceptions.Timeout as error:
            raise ValueError(f"Request timed out: {error}") from error
        except requests.exceptions.RequestException as error:
            raise ValueError(f"Error making request: {error}") from error

    def generate(
        self, prompt: str, response_schema: Optional[dict] = None
    ) -> Union[dict, str]:
        """Generates text using AnonRouter, optionally with a JSON schema.

        Args:
            prompt: The prompt to use for the generation.
            response_schema: An optional JSON schema to define the expected
                response format.

        Returns:
            The generated text as a string (or parsed data if
            response_schema is provided).

        Raises:
            ValueError: If the request fails or JSON parsing fails.
        """
        request_body = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self.config.get("temperature"),
            "top_p": self.config.get("top_p"),
            "max_tokens": self.config.get("max_output_tokens"),
        }

        if response_schema:
            request_body["response_format"] = {
                "type": "json_schema",
                "json_schema": {"name": "response", "schema": response_schema},
            }

        response = self._post(request_body)

        if response.status_code != 200:
            raise ValueError(f"Error generating text: {response.text}")

        try:
            text_response = response.json()["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError, json.JSONDecodeError) as error:
            raise ValueError(
                f"Unexpected response structure from AnonRouter: {response.text}"
            ) from error

        text_response = (text_response or "").strip()

        if response_schema:
            try:
                return json.loads(text_response)
            except json.JSONDecodeError as error:
                raise ValueError(
                    f"Error JSON parsing text: {text_response}: {error}"
                ) from error

        return text_response


manager.LLMManager.register_provider(AnonRouter)
