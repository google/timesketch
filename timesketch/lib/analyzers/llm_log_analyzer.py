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

from timesketch.lib.analyzers import interface
from timesketch.lib.analyzers import manager as analyzer_manager
from timesketch.lib.llms.features import manager as feature_manager
from timesketch.lib.llms.providers import manager as llm_provider_manager


logger = logging.getLogger("timesketch.analyzers.dfiq.llm_log_analyzer")


class LLMLogAnalyzer(interface.BaseAnalyzer):
    """DFIQ analyzer for the LLM Log Analyzer feature."""

    NAME = "llm_log_analyzer"
    DISPLAY_NAME = "LLM Log Analyzer"
    DESCRIPTION = "Triggers the LLM Log Analyzer feature for the entire sketch."
    IS_DFIQ_ANALYZER = False

    # The LLM Log analyzer will be triggered once per sketch, not per timeline.
    # The `timeline_id` will be None, and the analyzer should operate on all
    # timelines within the sketch.

    def run(self):
        """Entry point for the analyzer."""
        logger.info(
            "DFIQ analyzer for Log Analyzer feature started for sketch %d.",
            self.sketch.id,
        )

        # 1. Get the feature instance
        try:
            feature_instance = feature_manager.FeatureManager.get_feature_instance(
                "log_analyzer"
            )
        except KeyError:
            error_msg = "Log Analyzer LLM feature not found. Is it registered?"
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
            error_msg = f"Failed to initialize LLM provider: {e!s}"
            logger.error(error_msg, exc_info=True)
            self.output.result_status = "ERROR"
            self.output.result_summary = error_msg
            return str(self.output)

        # 3. Call the feature's execute method.
        try:
            logger.info(
                "Triggering Log Analyzer LLM feature for sketch %d", self.sketch.id
            )
            # The 'form' can be an empty dict as the feature uses defaults or
            # extracts what it needs from the sketch.
            result = feature_instance.execute(
                sketch=self.sketch.sql_sketch,
                form={},
                llm_provider=llm_provider,
            )

            # 4. Summarize the result.
            total_findings = result.get("total_findings_processed", 0)
            errors_encountered = result.get("errors_encountered", 0)
            events_exported = result.get("events_exported", 0)

            summary = (
                f"Log Analyzer finished. Exported {events_exported} events, "
                f"processed {total_findings} findings with {errors_encountered} errors."
            )

            self.output.result_status = "SUCCESS"
            self.output.result_priority = "NOTE"
            self.output.result_summary = summary

            # Optionally, add more details to markdown.
            self.output.result_markdown = f"### LLM Log Analyzer Results\n\n{summary}"

            if errors_encountered > 0:
                self.output.result_priority = "MEDIUM"
                error_details = result.get("error_details", [])
                self.output.result_markdown += "\n\n**Error samples:**\n"
                for err in error_details:
                    self.output.result_markdown += f"- `{err}`\n"

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
