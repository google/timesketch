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
from timesketch.lib.llms.providers import interface
from timesketch.lib.llms.providers import manager

has_required_deps = True
try:
    from sec_gemini import SecGemini
    from sec_gemini.models.enums import MessageType
except ImportError:
    has_required_deps = False

logger = logging.getLogger(__name__)


class SecGeminiLogAnalyzer(interface.LLMProvider):
    """
    SecGemini Log Analyzer LLM provider.

    This provider interfaces with a SecGemini backend to perform log analysis.
    It uploads logs from a sketch and streams back a raw JSON response containing
    the analysis findings.
    """

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

        self.server_url = self.config.get("logs_processor_api_url")
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
        self.session_id = None
        self.table_hash = None

    async def _run_async_stream(self, log_path, prompt):
        """Initializes a SecGemini session and streams the analysis response.

        This is an async helper method that:
        1. Creates a new SecGemini session.
        2. Uploads the local log file to the session.
        3. Streams the analysis results for the given prompt.

        Args:
            log_path (Path): The local filesystem path to the JSONL log file.
            prompt (str): The analysis prompt to send to the agent.

        Yields:
            str: The content chunks of the streamed response from the agent.
        """
        self._session = self.sg_client.create_session(
            model=self.model, enable_logging=self.enable_logging
        )
        self.session_id = self._session.id
        logger.info("Started new SecGemini session: '%s'", self._session.id)
        self._session.upload_and_attach_logs(
            log_path, custom_fields_mapping=self.custom_fields_mapping
        )
        if hasattr(self._session, "logs_table") and hasattr(
            self._session.logs_table, "blake2s"
        ):
            self.table_hash = self._session.logs_table.blake2s
            logger.info(
                "Uploaded logs table hash (blake2s): '%s'",
                self._session.logs_table.blake2s,
            )
        else:
            logger.warning("Uploaded logs did not produce a blake2s table hash!")

        logger.info("Starting the SecGemini analysis...")
        logger.info(
            "NOTE: 'ConnectionClosedOK' errors from the SecGemini client in the "
            "log are expected. The client automatically reconnects during "
            "long-running analysis."
        )
        async for response in self._session.stream(prompt):
            if (
                response.message_type == MessageType.RESULT
                and response.actor == "summarization_agent"
            ):
                yield response.content

    def generate_stream_from_logs(
        self,
        log_events_generator: Iterable[Dict[str, Any]],
        prompt: str = "Analyze the attached logs for any signs of a compromise.",
    ) -> Generator[str, None, None]:
        """Analyzes a stream of log events using the SecGemini log analysis agent.

        This method orchestrates the entire analysis process:
        1.  It receives a generator of Timesketch log events.
        2.  Each event is serialized into a JSON string and written to a
            temporary JSONL (JSON Lines) file on disk.
        3.  It invokes the asynchronous SecGemini client, passing the path to the
            log file.
        4.  It manages an asyncio event loop to handle the async streaming response.
        5.  It yields chunks of the raw JSON response from the LLM as they are
            received.

        Args:
            log_events_generator: An iterable of dictionaries, where each
                                  dictionary is a Timesketch log event.
            prompt: The prompt to send to the SecGemini agent for analysis.

        Yields:
            str: Chunks of the raw JSON string response from the LLM provider.
        """
        with tempfile.NamedTemporaryFile(
            mode="w", delete=True, suffix=".jsonl", encoding="utf-8"
        ) as tmpfile:
            log_path = pathlib.Path(tmpfile.name)
            logger.info("Write events to tmp file: '%s'", log_path)
            for event in log_events_generator:
                try:
                    # Clean the event to only include required fields
                    specific_fields = {"_id": event.get("_id", "")}
                    source = event.get("_source", event)

                    for key in ["data_type", "datetime", "message", "timestamp_desc"]:
                        specific_fields[key] = source.get(key, "")

                    # Explicitly stringify the tag field for now
                    specific_fields["tag"] = json.dumps(source.get("tag", []))

                    tmpfile.write(json.dumps(specific_fields) + "\n")
                    self._events_sent += 1
                except TypeError as e:
                    logger.error(
                        "Failed to serialize event to JSON: '%s'", e, exc_info=True
                    )
            tmpfile.flush()

            if self._events_sent == 0:
                logger.warning("No events were provided to the log analyzer.")
                return

            file_size_bytes = log_path.stat().st_size
            logger.info(
                "Finished writing %d events to tmp file: '%s' (size: %d bytes)",
                self._events_sent,
                log_path,
                file_size_bytes,
            )

            async def main():
                async for chunk in self._run_async_stream(log_path, prompt):
                    yield chunk

            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            gen = main()
            log_trigger = 0
            while True:
                try:
                    chunk = loop.run_until_complete(gen.__anext__())
                    if chunk is not None:
                        log_trigger += 1
                        if log_trigger % 50 == 0:
                            logger.info(
                                "[%s] SecGemini is still processing table with "
                                "hash [%s] ...",
                                self.session_id,
                                self.table_hash,
                            )
                        yield chunk
                except StopAsyncIteration:
                    break

    def generate(self, prompt: str, response_schema: Optional[dict] = None) -> Any:
        """Standard LLM generation method (not used for streaming log analysis).

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
