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
"""SecGemini Log Analyzer LLM provider for Timesketch."""
import json
import logging
import os
import asyncio
import pathlib
import tempfile
from typing import Any, Dict, Generator, Iterable, Optional

has_required_deps = True
try:
    from sec_gemini import SecGemini
except ImportError:
    has_required_deps = False

from timesketch.lib.llms.providers import interface
from timesketch.lib.llms.providers import manager

logger = logging.getLogger(__name__)


class SecGeminiLogAnalyzer(interface.LLMProvider):
    """SecGemini Log Analyzer LLM provider."""

    NAME = "secgemini_log_analyzer_agent"
    SUPPORTS_STREAMING = True

    def __init__(self, config: dict, **kwargs: Any):
        """Initialize the LLM provider.

        Args:
            config: A dictionary of provider-specific configuration options.
            kwargs: Additional arguments for the provider.

        Raises:
            ValueError: If the provider is not configured correctly.
        """
        super().__init__(config, **kwargs)

        self.api_key = self.config.get("api_key")
        if not self.api_key:
            raise ValueError("SecGemini provider requires an 'api_key' in its config.")

        self.server_url = self.config.get("server_url")
        if self.server_url:
            os.environ["SEC_GEMINI_LOGS_PROCESSOR_API_URL"] = self.server_url

        try:
            self.sg_client = SecGemini(api_key=self.api_key)
        except Exception as e:
            raise ValueError(f"Failed to initialize SecGemini client: {e}") from e

        self.model = self.config.get("model", "sec-gemini-experimental")
        self.custom_fields_mapping = {
            "id": "_id",
            "enrichment": "tag",
            "timestamp": "datetime",
        }
        self.enable_logging = self.config.get("enable_logging", True)
        self._events_sent = 0
        self._session = None

    async def _run_async_stream(self, log_path, prompt):
        """Runs the async streaming logic for SecGemini.

        Args:
            log_path: Path to the log file to analyze.
            prompt: The prompt to use for the analysis.

        Yields:
            str: The content of the response from the LLM.
        """
        self._session = self.sg_client.create_session(
            model=self.model, enable_logging=self.enable_logging
        )
        self._session.upload_and_attach_logs(
            log_path, custom_fields_mapping=self.custom_fields_mapping
        )

        async for response in self._session.stream(prompt):
            yield response.content

    def generate_stream_from_logs(
        self,
        log_events_generator: Iterable[Dict[str, Any]],
        prompt: str = "Analyze the attached logs for any signs of a compromise.",
    ) -> Generator[str, None, None]:
        """Streams log events to SecGemini and yields the raw LLM response.

        Args:
            log_events_generator: An iterable of log event dictionaries to analyze.
            prompt: The prompt to use for the analysis.

        Yields:
            str: The raw text response from the LLM.
        """
        with tempfile.NamedTemporaryFile(
            mode="w", delete=True, suffix=".jsonl", encoding="utf-8"
        ) as tmpfile:
            log_path = pathlib.Path(tmpfile.name)
            for event in log_events_generator:
                try:
                    tmpfile.write(json.dumps(event) + "\n")
                    self._events_sent += 1
                except TypeError as e:
                    logger.error(
                        "Failed to serialize event to JSON: %s", e, exc_info=True
                    )
            tmpfile.flush()

            if self._events_sent == 0:
                logger.warning("No events were provided to the log analyzer.")
                return

            async def run_stream():
                async for chunk in self._run_async_stream(log_path, prompt):
                    yield chunk

            async def main():
                async for chunk in run_stream():
                    yield chunk

            # This is a bit of a hack to run an async generator from a sync method.
            # It's not ideal, but it works for this use case.
            # We create a new event loop and run the async generator in it.
            # This is necessary because the SecGemini library is async.
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            gen = main()
            while True:
                try:
                    yield loop.run_until_complete(gen.__anext__())
                except StopAsyncIteration:
                    break

    def generate(self, prompt: str, response_schema: Optional[dict] = None) -> Any:
        """Standard LLM generation method.

        Args:
            prompt: The prompt to send to the LLM.
            response_schema: Optional schema for the response format.

        Raises:
            NotImplementedError: This method is not supported by this provider.
        """
        raise NotImplementedError(
            "The 'generate' method is not supported by the "
            "SecGeminiLogAnalyzer provider. Use 'generate_stream_from_logs' "
            "for streaming analysis."
        )

    def get_statistics(self) -> Dict[str, Any]:
        """Returns provider statistics.

        Returns:
            Dict[str, Any]: Statistics about events, findings and token usage.
        """
        stats = {
            "events_sent": self._events_sent,
        }
        if self._session:
            stats["usage"] = self._session.usage.model_dump()
        return stats


manager.LLMManager.register_provider(SecGeminiLogAnalyzer)
