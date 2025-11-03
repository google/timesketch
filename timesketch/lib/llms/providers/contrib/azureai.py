"""Azure AI Foundry LLM provider."""

import json
from typing import Optional, Any, Union
import requests
from timesketch.lib.llms.providers import interface, manager

# Default configuration values
DEFAULT_API_VERSION = "2024-02-15-preview"
DEFAULT_TIMEOUT = 60


class AzureAI(interface.LLMProvider):
    """AzureAI provider for Timesketch.

    This provider uses the Azure OpenAI API to generate text.
    It requires the endpoint, api_key, and model to be configured.
    """

    NAME = "azureai"

    def __init__(self, config: dict, **kwargs: Any):
        """Initializes the AzureAI provider.

        Args:
            config (dict): A dictionary of provider-specific configuration options.
            **kwargs (Any): Additional arguments passed to the base class.

        Raises:
            ValueError: If required configuration keys (endpoint, api_key, model)
                are missing.
        """
        super().__init__(config, **kwargs)
        self.endpoint = self.config.get("endpoint")
        self.api_key = self.config.get("api_key")
        self.model = self.config.get("model")
        self.api_version = self.config.get("api_version", DEFAULT_API_VERSION)
        self.timeout = self.config.get("timeout", DEFAULT_TIMEOUT)
        if not self.endpoint or not self.api_key or not self.model:
            raise ValueError(
                "endpoint, api_key, and model are required for AzureAI provider"
            )

    def generate(
        self, prompt: str, response_schema: Optional[dict] = None
    ) -> Union[dict, str]:

        url = (
            f"{self.endpoint}/openai/deployments/{self.model}/chat/completions?"
            f"api-version={self.api_version}"
        )
        headers = {"Content-Type": "application/json", "api-key": self.api_key}
        data = {
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": self.config.get(
                "max_output_tokens", interface.DEFAULT_MAX_OUTPUT_TOKENS
            ),
            "temperature": self.config.get(
                "temperature", interface.DEFAULT_TEMPERATURE
            ),
            "top_p": self.config.get("top_p", interface.DEFAULT_TOP_P),
        }
        try:
            response = requests.post(
                url, headers=headers, json=data, timeout=self.timeout
            )
            response.raise_for_status()
            response_data = response.json()["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as e:
            raise ValueError(
                f"Unexpected response structure from Azure API: {response.json()}"
            ) from e

        if isinstance(response_schema, dict):
            try:
                props = response_schema.get("properties")
                if props and isinstance(props, dict):
                    key = next(iter(props.keys()), "")
                    formatted_data = json.dumps({key: response_data})
                    return json.loads(formatted_data)
            except json.JSONDecodeError as error:
                raise ValueError(
                    f"Error JSON parsing text: {formatted_data}: {error}"
                ) from error

        return response_data


manager.LLMManager.register_provider(AzureAI)
