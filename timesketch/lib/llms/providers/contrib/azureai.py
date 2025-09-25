"""Azure Ai Foundry LLM provider."""

import json
from typing import Optional, Any
import requests
from timesketch.lib.llms.providers import interface, manager


class AzureAI(interface.LLMProvider):
    """AzureAI class for interacting with the Azure OpenAI API via Timesketch."""

    NAME = "azureai"

    def __init__(self, config: dict, **kwargs: Any):
        super().__init__(config, **kwargs)
        self.endpoint = self.config.get("endpoint")
        self.api_key = self.config.get("api_key")
        self.model = self.config.get("model")
        self.api_version = self.config.get("api_version", "2024-02-15-preview")
        if not self.endpoint or not self.api_key or not self.model:
            raise ValueError(
                "endpoint, api_key, and model are required for AzureAI provider"
            )

    def generate(self, prompt: str, response_schema: Optional[dict] = None) -> dict:

        url = (
            f"{self.endpoint}/openai/deployments/{self.model}/chat/completions?"
            f"api-version={self.api_version}"
        )
        headers = {"Content-Type": "application/json", "api-key": self.api_key}
        data = {
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": self.config.get("max_output_tokens", 1024),
            "temperature": self.config.get("temperature", 0.2),
            "top_p": self.config.get("top_p", 0.95),
        }
        response = requests.post(url, headers=headers, json=data, timeout=60)
        response.raise_for_status()
        response_data = response.json()["choices"][0]["message"]["content"]

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
