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
"""DFIQ plugin to trigger the LLM Log Analyzer feature."""

import logging
import time

from timesketch.lib.analyzers import interface
from timesketch.lib.analyzers import manager as analyzer_manager
from timesketch.lib.llms.features import manager as feature_manager
from timesketch.lib.llms.providers import manager as llm_provider_manager


logger = logging.getLogger("timesketch.analyzers.dfiq.llm_log_analyzer")


class LLMLogAnalyzer(interface.BaseAnalyzer):
    """DFIQ analyzer for the LLM Log Analyzer feature."""

    NAME = "llm_log_analyzer"
    DISPLAY_NAME = "LLM Log Analyzer"
    DESCRIPTION = (
        "IMPORTANT: This LLM analyzer needs to be configured on the backend "
        "before it can be used!"
    )
    IS_DFIQ_ANALYZER = False

    # The LLM Log analyzer will be triggered once per sketch, not per timeline.
    # The `timeline_id` will be None, and the analyzer should operate on all
    # timelines within the sketch.

    def run(self):
        """Entry point for the analyzer."""
        logger.info(
            "Analyzer for LLM Log Analyzer feature started for sketch [%d].",
            self.sketch.id,
        )

        # 1. Get the feature instance
        try:
            feature_instance = feature_manager.FeatureManager.get_feature_instance(
                "log_analyzer"
            )
        except KeyError:
            error_msg = "LLM Log Analyzer feature not found. Is it registered?"
            logger.error(error_msg)
            self.output.result_status = "ERROR"
            self.output.result_summary = error_msg
            return str(self.output)

        # 2. Get the LLM provider instance
        try:
            llm_provider = llm_provider_manager.LLMManager.create_provider(
                feature_name=feature_instance.NAME
            )
        except Exception as e:  # pylint: disable=broad-except
            error_msg = (
                f"Failed to initialize LLM provider: '{e!s}'. Please make sure "
                "to configure a specific 'log_analyzer_agent' provider for this"
                " feature!"
            )
            logger.error(error_msg, exc_info=True)
            self.output.result_status = "ERROR"
            self.output.result_summary = error_msg
            return str(self.output)

        # 3. Call the feature's execute method.
        try:
            logger.info(
                "Triggering Log Analyzer LLM feature for sketch [%d]", self.sketch.id
            )
            start_time = time.time()
            result = feature_instance.execute(
                sketch=self.sketch.sql_sketch,
                form={
                    "return_fields": [
                        "data_type",
                        "datetime",
                        "message",
                        "timestamp",
                        "timestamp_desc",
                        "tag",
                        "_id",
                        "_index",
                    ]
                },
                llm_provider=llm_provider,
            )
            duration_seconds = time.time() - start_time
            if duration_seconds > 60:
                minutes, seconds = divmod(duration_seconds, 60)
                duration_formatted = f"{int(minutes)} minutes and {seconds:.2f} seconds"
            else:
                duration_formatted = f"{duration_seconds:.2f} seconds"

            # 4. Summarize the result.
            total_findings = result.get("total_findings_processed", 0)
            errors_encountered = result.get("errors_encountered", 0)
            events_exported = result.get("events_exported", 0)

            if result.get("status") == "error":
                self.output.result_status = "ERROR"
                self.output.result_priority = "HIGH"
                error_message = result.get(
                    "message", "Unknown error from Log Analyzer feature."
                )
                summary = f"Log Analyzer failed: {error_message}"
            else:
                self.output.result_status = "SUCCESS"
                self.output.result_priority = "NOTE"
                summary = (
                    f"Log Analyzer finished. Exported {events_exported} events, "
                    f"processed {total_findings} findings with {errors_encountered} "
                    f"errors."
                )

            # Add provider-specific details if available
            if llm_provider.NAME == "secgemini_log_analyzer_agent":
                session_id = getattr(llm_provider, "session_id", "N/A")
                table_hash = getattr(llm_provider, "table_hash", "N/A")
                summary += (
                    f"\n\n## SecGemini Session Details:\n"
                    f" * Execution time: {duration_formatted}:\n"
                    f" * Session ID: '{session_id}'\n"
                    f" * Table Hash (blake2s): '{table_hash}'"
                )

            # Create a story with the full AI response if available.
            full_response_text = result.get("full_response_text")
            if full_response_text:
                if self.output.result_status == "ERROR":
                    story_title = f"[err] Full AI Log Analysis Report - [{session_id}]"
                else:
                    story_title = f"Full AI Log Analysis Report - [{session_id}]"

                story = self.sketch.add_story(story_title)
                story.add_text(f"## Session Details\n\n{summary}")
                story.add_text(
                    "This story contains the complete, raw output from the "
                    "AI Log Analyzer agent."
                )

                story.add_text(f"```\n{full_response_text}\n```")

            self.output.result_summary = summary

            logger.info(summary)

        except Exception as e:  # pylint: disable=broad-except
            error_msg = (
                "An unexpected error occurred during Log Analyzer execution: " f"{e!s}"
            )
            logger.error(error_msg, exc_info=True)
            self.output.result_status = "ERROR"
            self.output.result_summary = error_msg

        return str(self.output)


analyzer_manager.AnalysisManager.register_analyzer(LLMLogAnalyzer)
