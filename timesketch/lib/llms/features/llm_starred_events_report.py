# Copyright 2026 Google Inc. All rights reserved.
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
"""LLM Starred Events Report feature."""

import json
import logging
import time
from typing import Any, Optional

import pandas as pd
import prometheus_client
from flask import current_app

from timesketch.lib import utils
from timesketch.api.v1 import export
from timesketch.models.sketch import Sketch
from timesketch.lib.stories import utils as story_utils
from timesketch.lib.definitions import METRICS_NAMESPACE
from timesketch.lib.llms.features.interface import LLMFeatureInterface
from timesketch.lib.datastores.opensearch import OpenSearchDataStore

logger = logging.getLogger("timesketch.llm.starred_events_report_feature")

METRICS = {
    "llm_starred_events_report_events_processed_total": prometheus_client.Counter(
        "llm_starred_events_report_events_processed_total",
        "Total number of events processed for LLM starred events reports",
        ["sketch_id"],
        namespace=METRICS_NAMESPACE,
    ),
    "llm_starred_events_report_unique_events_total": prometheus_client.Counter(
        "llm_starred_events_report_unique_events_total",
        "Total number of unique events sent to the LLM for report generation",
        ["sketch_id"],
        namespace=METRICS_NAMESPACE,
    ),
    "llm_starred_events_report_stories_created_total": prometheus_client.Counter(
        "llm_starred_events_report_stories_created_total",
        "Total number of starred events report stories created",
        ["sketch_id"],
        namespace=METRICS_NAMESPACE,
    ),
}


class LLMStarredEventsReportFeature(LLMFeatureInterface):
    """LLM Starred Events Report feature."""

    NAME = "llm_starred_events_report"
    PROMPT_CONFIG_KEY = "PROMPT_LLM_STARRED_EVENTS_REPORT"
    RESPONSE_SCHEMA = {
        "type": "object",
        "properties": {
            "summary": {
                "type": "string",
                "description": "Detailed report summary of the events",
            }
        },
        "required": ["summary"],
    }

    def _get_prompt_text(self, events_dict: list[dict[str, Any]]) -> str:
        """Reads the prompt template from file and injects events.
        Args:
            events_dict: List of event dictionaries to inject into prompt.
        Returns:
            Complete prompt text with injected events.
        Raises:
            ValueError: If the prompt path is not configured or placeholder is missing.
            FileNotFoundError: If the prompt file cannot be found.
            IOError: If there's an error reading the prompt file.
            OSError: If there's an error reading the prompt file.
        """
        prompt_file_path = current_app.config.get(self.PROMPT_CONFIG_KEY)
        if not prompt_file_path:
            logger.error("%s config not set", self.PROMPT_CONFIG_KEY)
            raise ValueError("LLM starred events report prompt path not configured.")
        try:
            with open(prompt_file_path, "r", encoding="utf-8") as file_handle:
                prompt_template = file_handle.read()
        except FileNotFoundError as exc:
            logger.error(
                "Starred events report prompt file not found: %s", prompt_file_path
            )
            raise FileNotFoundError(
                f"LLM Prompt file not found: {prompt_file_path}"
            ) from exc
        except IOError as e:
            logger.error("Error reading prompt file: %s", e)
            raise IOError("Error reading LLM prompt file.") from e
        if "<EVENTS_JSON>" not in prompt_template:
            logger.error("Prompt template is missing the <EVENTS_JSON> placeholder")
            raise ValueError(
                "LLM starred events report prompt template is missing the "
                "required <EVENTS_JSON> placeholder."
            )
        prompt_text = prompt_template.replace("<EVENTS_JSON>", json.dumps(events_dict))
        return prompt_text

    def _run_timesketch_query(
        self,
        sketch: Sketch,
        query_string: str = "*",
        query_filter: Optional[dict] = None,
        id_list: Optional[list] = None,
        timeline_ids: Optional[list] = None,
    ) -> pd.DataFrame:
        """Runs a timesketch query and returns results as a DataFrame.
        Args:
            sketch: The Sketch object to query.
            query_string: Search query string.
            query_filter: Dictionary with filter parameters.
            id_list: List of event IDs to retrieve.
            timeline_ids: List of timeline IDs to query.
        Returns:
            pd.DataFrame: DataFrame containing query results.
        Raises:
            ValueError: If no valid indices are found.
        """
        datastore = OpenSearchDataStore(
            host=current_app.config.get("OPENSEARCH_HOSTS")[0]["host"],
            port=current_app.config.get("OPENSEARCH_HOSTS")[0]["port"],
        )
        if not query_filter:
            query_filter = {}
        if id_list:
            id_query = " OR ".join([f'_id:"{event_id}"' for event_id in id_list])
            query_string = id_query
        all_timeline_ids = [t.id for t in sketch.timelines]
        indices = query_filter.get("indices", all_timeline_ids)
        if "_all" in indices:
            indices = all_timeline_ids
        indices, timeline_ids = utils.get_validated_indices(indices, sketch)
        if not indices:
            raise ValueError(
                "No valid search indices were found to perform the search on."
            )
        result = datastore.search(
            sketch_id=sketch.id,
            query_string=query_string,
            query_filter=query_filter,
            query_dsl="",
            indices=indices,
            timeline_ids=timeline_ids,
        )
        return export.query_results_to_dataframe(result, sketch)

    def generate_prompt(self, sketch: Sketch, form: dict = None, **kwargs: Any) -> str:
        """Generates the starred events report prompt based on events from a query.
        Args:
            sketch: The Sketch object containing events to analyze.
            form: Form data containing query and filter information.
            **kwargs: Additional arguments including:
                - timeline_ids: List of timeline IDs to query.
        Returns:
            str: Generated prompt text with events to analyze.
        Raises:
            ValueError: If required parameters are missing or if no events are found.
        """
        timeline_ids = kwargs.get("timeline_ids")
        if not form:
            raise ValueError("Missing 'form' data")
        query_filter = form.get("filter", {})
        query_string = form.get("query", "*") or "*"
        events_df = self._run_timesketch_query(
            sketch,
            query_string,
            query_filter,
            timeline_ids=timeline_ids,
        )
        if events_df is None or events_df.empty:
            return "No events to analyze for starred events report."
        events_df["datetime_str"] = events_df["datetime"].astype(str)
        events_df["combined_key"] = events_df["datetime_str"] + events_df["message"]
        unique_df = events_df.drop_duplicates(subset="combined_key", keep="first")
        events_dict = (
            unique_df[["datetime_str", "message"]]
            .rename(columns={"datetime_str": "datetime"})
            .to_dict(orient="records")
        )
        total_events_count = len(events_df)
        unique_events_count = len(unique_df)
        METRICS["llm_starred_events_report_events_processed_total"].labels(
            sketch_id=str(sketch.id)
        ).inc(total_events_count)
        METRICS["llm_starred_events_report_unique_events_total"].labels(
            sketch_id=str(sketch.id)
        ).inc(unique_events_count)
        if not events_dict:
            return "No events to analyze for starred events report."
        return self._get_prompt_text(events_dict)

    def process_response(
        self, llm_response: Any, sketch: Sketch = None, form: dict = None, **kwargs: Any
    ) -> dict[str, Any]:
        """Processes the LLM response and creates a Story in the sketch.
        Args:
            llm_response: The response from the LLM model, expected to be a dictionary.
            sketch: The Sketch object.
            form: Form data containing query and filter information.
            **kwargs: Additional arguments including:
                - sketch_id: ID of the sketch being processed.
                - timeline_ids: List of timeline IDs to query.
        Returns:
            Dictionary containing the processed response:
                - summary: The report text
                - summary_event_count: Total number of events analyzed
                - summary_unique_event_count: Number of unique events analyzed
                - story_id: ID of the created story
        Raises:
            ValueError: If required parameters are missing or if the LLM response
                      is not in the expected format.
        """
        timeline_ids = kwargs.get("timeline_ids")
        if not sketch:
            raise ValueError("Missing 'sketch'")
        if not form:
            raise ValueError("Missing 'form' data")
        if not isinstance(llm_response, dict):
            raise ValueError("LLM response is expected to be a dictionary")
        summary_text = llm_response.get("summary")
        if summary_text is None:
            raise ValueError("LLM response missing 'summary' key")
        query_filter = form.get("filter", {})
        query_string = form.get("query", "*") or "*"
        events_df = self._run_timesketch_query(
            sketch,
            query_string,
            query_filter,
            timeline_ids=timeline_ids,
        )
        total_events_count = len(events_df)
        events_df["combined_key"] = (
            events_df["datetime"].astype(str) + events_df["message"]
        )
        unique_events_count = len(
            events_df.drop_duplicates(subset="combined_key", keep="first")
        )
        try:
            story_title = f"Starred Events Report - {time.strftime('%Y-%m-%d %H:%M')}"
            story_id = story_utils.create_story(
                sketch=sketch, content=summary_text, title=story_title
            )
            METRICS["llm_starred_events_report_stories_created_total"].labels(
                sketch_id=str(sketch.id)
            ).inc()
        except Exception as e:
            logger.error("Error creating story for starred events report: %s", e)
            raise ValueError(
                f"Error creating story to save starred events report: {e}"
            ) from e
        return {
            "summary": summary_text,
            "summary_event_count": total_events_count,
            "summary_unique_event_count": unique_events_count,
            "story_id": story_id,
        }
