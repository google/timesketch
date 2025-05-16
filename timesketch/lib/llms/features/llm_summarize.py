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
"""LLM Summarization feature."""
import json
import logging
from typing import Any, Optional
import pandas as pd
import prometheus_client
from flask import current_app
from opensearchpy import OpenSearch
from timesketch.lib import utils
from timesketch.api.v1 import export
from timesketch.models.sketch import Sketch
from timesketch.lib.definitions import METRICS_NAMESPACE
from timesketch.lib.llms.features.interface import LLMFeatureInterface

logger = logging.getLogger("timesketch.llm.summarize_feature")

METRICS = {
    "llm_summary_events_processed_total": prometheus_client.Counter(
        "llm_summary_events_processed_total",
        "Total number of events processed for LLM summarization",
        ["sketch_id"],
        namespace=METRICS_NAMESPACE,
    ),
    "llm_summary_unique_events_total": prometheus_client.Counter(
        "llm_summary_unique_events_total",
        "Total number of unique events sent to the LLM",
        ["sketch_id"],
        namespace=METRICS_NAMESPACE,
    ),
}


class LLMSummarizeFeature(LLMFeatureInterface):
    """LLM Summarization feature."""

    NAME = "llm_summarize"
    PROMPT_CONFIG_KEY = "PROMPT_LLM_SUMMARIZATION"
    RESPONSE_SCHEMA = {
        "type": "object",
        "properties": {"summary": {"type": "string"}},
        "required": ["summary"],
    }

    def __init__(self):
        """Initialize the feature with default values for metrics."""
        super().__init__()
        self._total_events_count = 0
        self._unique_events_count = 0

    def _get_prompt_text(self, events_dict: list[dict[str, Any]]) -> str:
        """Reads the prompt template from file and injects events.
        Args:
            events_dict: List of event dictionaries to inject into prompt.
        Returns:
            str: Complete prompt text with injected events.
        Raises:
            ValueError: If the prompt path is not configured or placeholder is missing.
            FileNotFoundError: If the prompt file cannot be found.
            IOError: If there's an error reading the prompt file.
            OSError: If there's an error reading the prompt file.
        """
        prompt_file_path = current_app.config.get(self.PROMPT_CONFIG_KEY)
        if not prompt_file_path:
            logger.error("%s config not set", self.PROMPT_CONFIG_KEY)
            raise ValueError("LLM summarization prompt path not configured.")
        try:
            with open(prompt_file_path, encoding="utf-8") as file_handle:
                prompt_template = file_handle.read()
        except FileNotFoundError as exc:
            logger.error("Prompt file not found: %s", prompt_file_path)
            raise FileNotFoundError(
                f"LLM Prompt file not found: {prompt_file_path}"
            ) from exc
        except OSError as e:
            logger.error("Error reading prompt file: %s", e)
            raise OSError("Error reading LLM prompt file.") from e
        if "<EVENTS_JSON>" not in prompt_template:
            logger.error("Prompt template is missing the <EVENTS_JSON> placeholder")
            raise ValueError(
                "LLM summarization prompt template is missing the "
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
        datastore: Optional[OpenSearch] = None,
        timeline_ids: Optional[list] = None,
    ) -> pd.DataFrame:
        """Runs a timesketch query and returns results as a DataFrame.
        Args:
            sketch: The Sketch object to query.
            query_string: Search query string.
            query_filter: Dictionary with filter parameters.
            id_list: List of event IDs to retrieve.
            datastore: OpenSearch instance for querying.
            timeline_ids: List of timeline IDs to query.
        Returns:
            pd.DataFrame: DataFrame containing query results.
        Raises:
            ValueError: If datastore is not provided or no valid indices are found.
        """
        if datastore is None:
            raise ValueError("Datastore must be provided.")
        if not query_filter:
            query_filter = {}
        if id_list:
            id_query = " OR ".join([f'_id:"{event_id}"' for event_id in id_list])
            query_string = id_query
        all_indices = list({t.searchindex.index_name for t in sketch.timelines})
        indices_from_filter = query_filter.get("indices", all_indices)
        if "_all" in indices_from_filter:
            indices_from_filter = all_indices
        indices, timeline_ids = utils.get_validated_indices(indices_from_filter, sketch)
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

    def generate_prompt(self, sketch: Sketch, **kwargs: Any) -> str:
        """Generates the summarization prompt based on events from a query.
        Args:
            sketch: The Sketch object containing events to summarize.
            **kwargs: Additional arguments including:
                - form: Form data containing query and filter information.
                - datastore: OpenSearch instance for querying.
                - timeline_ids: List of timeline IDs to query.
        Returns:
            str: Generated prompt text with events to summarize.
        Raises:
            ValueError: If required parameters are missing or if no events are found.
        """
        form = kwargs.get("form")
        datastore = kwargs.get("datastore")
        timeline_ids = kwargs.get("timeline_ids")
        if not form:
            raise ValueError("Missing 'form' data in kwargs")
        query_filter = form.get("filter", {})
        query_string = form.get("query", "*") or "*"
        events_df = self._run_timesketch_query(
            sketch,
            query_string,
            query_filter,
            datastore=datastore,
            timeline_ids=timeline_ids,
        )
        if events_df is None or events_df.empty:
            return "No events to summarize based on the current filter."

        self._total_events_count = len(events_df)
        METRICS["llm_summary_events_processed_total"].labels(
            sketch_id=str(sketch.id)
        ).inc(self._total_events_count)

        unique_events_df = events_df[["message"]].drop_duplicates(
            subset="message", keep="first"
        )
        self._unique_events_count = len(unique_events_df)
        METRICS["llm_summary_unique_events_total"].labels(sketch_id=str(sketch.id)).inc(
            self._unique_events_count
        )

        events = unique_events_df.to_dict(orient="records")

        return self._get_prompt_text(events)

    def process_response(self, llm_response: Any, **kwargs: Any) -> dict[str, Any]:
        """Processes the LLM response and adds additional context information.
        Args:
            llm_response: The response from the LLM model, expected to be a dictionary.
            **kwargs: Additional arguments including:
                - sketch_id: ID of the sketch being processed.
                - sketch: The Sketch object.
        Returns:
            Dictionary containing the processed response with additional context:
                - response: The summary text.
                - summary_event_count: Total number of events summarized.
                - summary_unique_event_count: Number of unique events summarized.
        Raises:
            ValueError: If required parameters are missing or if the LLM response
                        is not in the expected format.
        """
        sketch_id = kwargs.get("sketch_id")
        if not sketch_id:
            raise ValueError("Missing 'sketch_id' in kwargs")

        if not isinstance(llm_response, dict):
            raise ValueError("LLM response is expected to be a dictionary")

        summary_text = llm_response.get("summary")
        if summary_text is None:
            raise ValueError("LLM response missing 'summary' key")

        return {
            "response": summary_text,
            "summary_event_count": self._total_events_count,
            "summary_unique_event_count": self._unique_events_count,
        }
