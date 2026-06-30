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
from datetime import datetime
from typing import Any, Dict, Generator, Iterable, Optional

from flask import current_app

from timesketch.lib.llms.providers import interface
from timesketch.lib.llms.providers import manager

has_required_deps = True
try:
    from sec_gemini import SecGemini
except ImportError:
    has_required_deps = False

logger = logging.getLogger(__name__)


CONCLUSION_LOG_RECORDS_HEADER = "**What the selected log records are:**\n\n"
CONCLUSION_RELEVANCE_HEADER = (
    "**How the selected log records are related to the finding:**\n\n"
)


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

        self.host = self.config.get("host")
        self.meta_config = self.config.get("meta", {})

        try:
            if self.host:
                self.sg_client = SecGemini(api_key=self.api_key, host=self.host)
            else:
                self.sg_client = SecGemini(api_key=self.api_key)
        except Exception as e:
            raise ValueError(f"Failed to initialize SecGemini client: {e}") from e

        self._events_sent = 0
        self._session = None
        self.session_id = None

    async def _run_async_stream(self, log_path, prompt):
        """Initializes a SecGemini session and streams the analysis response.

        This is an async helper method that:
        1. Creates a new SecGemini session.
        2. Uploads the local log file to the session.
        3. Streams the analysis results for the given prompt.
        4. If debugging is enabled, streams the raw sec-gemini response to a log.

        Args:
            log_path (Path): The local filesystem path to the JSONL log file.
            prompt (str): The analysis prompt to send to the agent.

        Yields:
            str: The content chunks of the streamed response from the agent.
        """
        # Start the client connection first
        await self.sg_client.start()

        try:
            # Create session via the sessions manager
            self._session = await self.sg_client.sessions.create()
            self.session_id = self._session.id
            logger.info("Started new SecGemini session: '%s'", self.session_id)

            # Upload logs file using the new files.upload API
            await self._session.files.upload(str(log_path), content_type="text/plain")
            logger.info("Uploaded logs file: '%s'", log_path)

            logger.info("Starting the SecGemini analysis...")
            logger.info(
                "NOTE: 'ConnectionClosedOK' errors from the SecGemini client in the "
                "log are expected. The client automatically reconnects during "
                "long-running analysis."
            )

            debug_log_file = None
            if current_app.config.get("DEBUG"):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                log_filename = f"secgemini_response_{timestamp}_{self.session_id}.log"
                log_file_path = os.path.join(tempfile.gettempdir(), log_filename)
                flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
                try:
                    debug_log_file = os.fdopen(
                        os.open(log_file_path, flags, 0o600), "w", encoding="utf-8"
                    )
                    logger.info(
                        "SecGemini raw response is being streamed to: %s", log_file_path
                    )
                except (IOError, FileExistsError) as e:
                    logger.error(
                        "Failed to create SecGemini debug log at %s: %s",
                        log_file_path,
                        e,
                        exc_info=True,
                    )
                    debug_log_file = None

            try:
                # Trigger the prompt first
                logger.info("Sending prompt to SecGemini: '%s'", prompt[:100])
                meta = {"config.mode": "dfir"}
                if self.meta_config:
                    for key, val in self.meta_config.items():
                        if isinstance(val, bool):
                            meta[key] = "true" if val else "false"
                        else:
                            meta[key] = str(val)

                await self._session.prompt(prompt, meta=meta)
                logger.info("Prompt sent successfully!")

                # Stream messages using messages.stream()
                async for response in self._session.messages.stream():
                    if debug_log_file:
                        try:
                            debug_log_file.write(str(response) + "\n")
                            debug_log_file.flush()
                        except IOError as e:
                            logger.error(
                                "Failed to write to SecGemini debug log: %s",
                                e,
                                exc_info=True,
                            )

                    # Extract response dictionary values
                    msg_type = response.get("message_type")
                    content = response.get("content", "")

                    if msg_type == "MESSAGE_TYPE_RESPONSE":
                        start_marker = "\n## Investigation Findings\n\n"
                        if start_marker in content:
                            json_str = content.split(start_marker)[1].strip()
                            try:
                                findings_list = json.loads(json_str)
                                if isinstance(findings_list, list):
                                    translated_findings = []
                                    for f in findings_list:
                                        log_records = [
                                            {"record_id": rid}
                                            for rid in f.get("record_ids", [])
                                            if rid
                                        ]
                                        desc = f.get("description", "")
                                        relevance = f.get("relevance", "")
                                        combined_conclusion = (
                                            f"{CONCLUSION_LOG_RECORDS_HEADER}"
                                            f"{desc}\n\n<br>\n\n"
                                            f"{CONCLUSION_RELEVANCE_HEADER}"
                                            f"{relevance}"
                                        )
                                        annotations = [
                                            {
                                                "investigative_question": f.get(
                                                    "finding", ""
                                                ),
                                                "conclusions": [combined_conclusion],
                                                "priority": f.get("severity", "notice"),
                                            }
                                        ]
                                        translated_findings.append(
                                            {
                                                "log_records": log_records,
                                                "annotations": annotations,
                                            }
                                        )
                                    json_str = json.dumps(
                                        {"findings": translated_findings}
                                    )
                            except Exception as e:  # pylint: disable=broad-except
                                logger.error(
                                    "Failed to translate SecGemini findings JSON: %s",
                                    e,
                                    exc_info=True,
                                )
                                json_str = json.dumps({"findings": []})
                            yield json_str
                            # force termination to avoid back2back runs
                            break
            finally:
                if debug_log_file:
                    debug_log_file.close()
                    logger.info(
                        "Finished writing SecGemini debug log: %s", log_file_path
                    )
        finally:
            # Ensure client is properly closed
            await self.sg_client.close()

    def generate_stream_from_logs(
        self,
        log_events_generator: Iterable[Dict[str, Any]],
        prompt: str = None,
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
        if not prompt:
            prompt = current_app.config.get(
                "LLM_LOG_ANALYZER_DEFAULT_PROMPT",
                "Perform a forensics investigation on the provided logs.",
            )

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

                    # Sec-Gemini cannot handle +0000 timezone offsets, convert to +00:00
                    for key in ["data_type", "datetime", "message", "timestamp_desc"]:
                        value = source.get(key, "")
                        if (
                            key == "datetime"
                            and isinstance(value, str)
                            and value.endswith("+0000")
                        ):
                            value = value.replace("+0000", "+00:00")
                        specific_fields[key] = value

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
                                "[%s] SecGemini is still processing...",
                                self.session_id,
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
