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
"""Arcadia LLM provider for Timesketch."""
import json
import logging
from typing import Optional, Any, Generator, Iterable, Dict

import requests

from timesketch.lib.llms.providers import interface
from timesketch.lib.llms.providers import manager

logger = logging.getLogger(__name__)


class Arcadia(interface.LLMProvider):
    """Arcadia LLM provider implementation for streaming log analysis."""

    NAME = "arcadia"
    SUPPORTS_STREAMING = True

    def __init__(self, config: dict, **kwargs: Any):
        super().__init__(config, **kwargs)
        self.server_url = self.config.get("server_url")
        if not self.server_url:
            raise ValueError(
                "Arcadia provider requires 'server_url' in its configuration. "
            )

        self.api_endpoint = "/analyze_logs"
        self.timeout_connect = int(self.config.get("timeout_connect", 10))
        self.timeout_read_stream = int(
            self.config.get("timeout_read_stream", 60 * 20)
        )  # 20 minutes

        self._events_sent = 0
        self._findings_received = 0

    def _stream_log_data_as_ndjson_gen(
        self, log_events_generator: Iterable[Dict[str, Any]]
    ) -> Generator[bytes, None, None]:
        """Converts log events to NDJSON format for streaming.

        This method is used internally to prepare data for the SecGemini API.
        It converts each event dictionary to a JSON line and yields it as bytes.

        Args:
            log_events_generator: An iterable of log event dictionaries.

        Yields:
            bytes: JSON-encoded event lines in NDJSON format.
        """
        logger.info("Arcadia: Preparing to stream log data as NDJSON.")

        for event_dict in log_events_generator:
            try:
                line_to_yield = (json.dumps(event_dict) + "\n").encode("utf-8")
                yield line_to_yield
                self._events_sent += 1
            except TypeError as exception:
                logger.error(
                    "Arcadia: Error serializing event to JSON: %s... Error: %s",
                    str(event_dict)[:100],
                    exception,
                )
            except Exception as exception:  # pylint: disable=broad-except
                logger.error(
                    "Arcadia: Unexpected error during event serialization "
                    "for stream: %s",
                    exception,
                    exc_info=False,
                )

        if self._events_sent == 0:
            logger.warning(
                "Arcadia: _stream_log_data_as_ndjson_gen: "
                "log_events_generator was empty or yielded no data."
            )

    def generate_stream_from_logs(
        self,
        log_events_generator: Iterable[Dict[str, Any]],
    ) -> Generator[Dict[str, Any], None, None]:
        """Streams log events to SecGemini and yields findings as they arrive.

        Args:
            log_events_generator: An iterable of log event dictionaries to analyze.

        Yields:
            Dict[str, Any]: Finding dictionaries from SecGemini, or error dictionaries.

        Raises:
            requests.exceptions.RequestException: For non-recoverable connection errors.
            Exception: For unexpected errors during streaming.
        """
        full_url = f"{self.server_url.rstrip('/')}{self.api_endpoint}"
        headers = {
            "Content-Type": "application/x-ndjson",
            "Accept": "application/x-ndjson",
        }

        logger.info("Arcadia: Streaming logs to SecGemini at %s", full_url)

        data_to_send = self._stream_log_data_as_ndjson_gen(log_events_generator)

        try:
            with requests.post(
                full_url,
                headers=headers,
                data=data_to_send,
                stream=True,
                timeout=(self.timeout_connect, self.timeout_read_stream),
            ) as response:
                response.raise_for_status()

                received_findings_count = 0
                for line_bytes in response.iter_lines():
                    if line_bytes:
                        try:
                            finding_dict = json.loads(line_bytes.decode("utf-8"))
                            received_findings_count += 1
                            self._findings_received += 1
                            yield finding_dict
                        except json.JSONDecodeError as exception:
                            logger.error(
                                "Arcadia: Error decoding JSON finding from "
                                "SecGemini: %s... Error: %s",
                                line_bytes.decode("utf-8", "ignore")[:100],
                                exception,
                            )
                            continue
                        except Exception as exception:  # pylint: disable=broad-except
                            logger.error(
                                "Arcadia: Unexpected error processing line from "
                                "SecGemini: %s",
                                exception,
                                exc_info=False,
                            )
                            continue

                logger.info(
                    "Arcadia: Finished streaming findings from SecGemini. "
                    "Total findings received: %s",
                    received_findings_count,
                )

        except requests.exceptions.RequestException as e_req:
            logger.error(
                "Arcadia: Request to SecGemini (%s) FAILED: %s",
                full_url,
                e_req,
                exc_info=True,
            )
            raise
        except Exception as e_outer:  # pylint: disable=broad-except
            logger.error(
                "Arcadia: Unexpected error in generate_stream_from_logs " + "(%s): %s",
                full_url,
                e_outer,
                exc_info=True,
            )
            raise

    def generate(self, prompt: str, response_schema: Optional[dict] = None) -> Any:
        """Standard LLM generation method (not used for streaming log analysis).

        Args:
            prompt: The prompt to send to the LLM.
            response_schema: Optional schema for the response format.

        Returns:
            Any: A mock response indicating this method shouldn't be used.
        """
        logger.warning(
            "Arcadia.generate() was called. This method is not intended for "
            "streaming log analysis with SecGemini. Use generate_stream_from_logs."
        )
        return json.dumps(
            [
                {
                    "log_name": "fs:stat",
                    "record_id": "placeholder_static_id_1",
                    "annotations": [
                        {
                            "attack_stage": "execution",
                            "investigative_question": "Mock question for fs:stat?",
                            "conclusions": ["Static mock conclusion for fs:stat."],
                        }
                    ],
                    "entities": [{"type": "file", "value": "/tmp/static_mock_file"}],
                }
            ]
        )

    def get_statistics(self) -> Dict[str, int]:
        """Returns provider statistics.

        Returns:
            Dict[str, int]: Statistics about events and findings.
        """
        return {
            "events_sent": self._events_sent,
            "findings_received": self._findings_received,
        }


manager.LLMManager.register_provider(Arcadia)
