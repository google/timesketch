# Copyright 2024 Google Inc. All rights reserved.
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

"""Timesketch API for LLM event summarization."""

import json
import logging
import multiprocessing
import multiprocessing.managers
import time
from typing import Dict, Optional

import pandas as pd
import prometheus_client
from flask import abort, current_app, jsonify, request
from flask_login import current_user, login_required
from flask_restful import Resource

from timesketch.api.v1 import export, resources
from timesketch.lib import definitions, llms, utils
from timesketch.lib.definitions import METRICS_NAMESPACE
from timesketch.models.sketch import Sketch

logger = logging.getLogger("timesketch.api.llm_summarize")

summary_response_schema = {
    "type": "object",
    "properties": {"summary": {"type": "string"}},
    "required": ["summary"],
}

# Metrics definitions
METRICS = {
    "llm_summary_requests_total": prometheus_client.Counter(
        "llm_summary_requests_total",
        "Total number of LLM summarization requests received",
        ["sketch_id"],
        namespace=METRICS_NAMESPACE,
    ),
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
    "llm_summary_errors_total": prometheus_client.Counter(
        "llm_summary_errors_total",
        "Total number of errors encountered during LLM summarization",
        ["sketch_id", "error_type"],
        namespace=METRICS_NAMESPACE,
    ),
    "llm_summary_duration_seconds": prometheus_client.Summary(
        "llm_summary_duration_seconds",
        "Time taken to process an LLM summarization request (in seconds)",
        ["sketch_id"],
        namespace=METRICS_NAMESPACE,
    ),
}

_LLM_TIMEOUT_WAIT_SECONDS = 30


class LLMSummarizeResource(resources.ResourceMixin, Resource):
    """Resource to get LLM summary of events."""

    def _get_prompt_text(self, events_dict: list) -> str:
        """Reads the prompt template from file and injects events.

        Args:
            events_dict: A list of dictionaries representing the events to summarize.

        Returns:
            The prompt text with the events injected.

        Raises:
             HTTP_STATUS_CODE_INTERNAL_SERVER_ERROR: If prompt template file
               is not configured, not found, or error when reading it.
        """
        prompt_file_path = current_app.config.get("PROMPT_LLM_SUMMARIZATION")
        if not prompt_file_path:
            logger.error("PROMPT_LLM_SUMMARIZATION config not set in timesketch.conf")
            abort(
                definitions.HTTP_STATUS_CODE_INTERNAL_SERVER_ERROR,
                "LLM summarization prompt path not configured.",
            )

        try:
            with open(prompt_file_path, "r", encoding="utf-8") as file_handle:
                prompt_template = file_handle.read()
        except FileNotFoundError:
            logger.error("Prompt file not found: %s", prompt_file_path)
            abort(
                definitions.HTTP_STATUS_CODE_INTERNAL_SERVER_ERROR,
                "LLM Prompt file not found on the server.",
            )
        except IOError as e:
            logger.error("Error reading prompt file: %s", e)
            abort(
                definitions.HTTP_STATUS_CODE_INTERNAL_SERVER_ERROR,
                "Error reading LLM prompt file.",
            )

        prompt_text = prompt_template.replace("<EVENTS_JSON>", json.dumps(events_dict))
        return prompt_text

    @login_required
    def post(self, sketch_id: int):
        """Handles POST request to the resource.

        Handler for /api/v1/sketches/:sketch_id/events/summary/

        Args:
            sketch_id: Integer primary key for a sketch database model.

        Returns:
            JSON response with event summary, total event count, and unique event count.

        Raises:
            HTTP_STATUS_CODE_NOT_FOUND: If no sketch is found with the given ID.
            HTTP_STATUS_CODE_FORBIDDEN: If the user does not
                have read access to the sketch.
            HTTP_STATUS_CODE_BAD_REQUEST: If the POST request does not contain data,
                if no events are found, or if there's an issue getting LLM data.
            HTTP_STATUS_CODE_INTERNAL_SERVER_ERROR: If LLM provider is not configured.
        """
        start_time = time.time()
        METRICS["llm_summary_requests_total"].labels(sketch_id=str(sketch_id)).inc()

        sketch = Sketch.get_with_acl(sketch_id)
        if not sketch:
            abort(
                definitions.HTTP_STATUS_CODE_NOT_FOUND, "No sketch found with this ID."
            )
        if not sketch.has_permission(current_user, "read"):
            abort(
                definitions.HTTP_STATUS_CODE_FORBIDDEN,
                "User does not have read access controls on sketch.",
            )

        form = request.json
        if not form:
            abort(
                definitions.HTTP_STATUS_CODE_BAD_REQUEST,
                "The POST request requires data",
            )

        query_filter = form.get("filter", {})
        query_string = form.get("query", "*")
        if not query_string:
            query_string = "*"

        events_df = self._run_timesketch_query(sketch, query_string, query_filter)
        if events_df is None or events_df.empty:
            return jsonify(
                {"summary": "No events to summarize based on the current filter."}
            )
        new_df = events_df[["message"]]
        unique_df = new_df.drop_duplicates(subset="message", keep="first")
        events_dict = unique_df.to_dict(orient="records")

        total_events_count = len(new_df)
        unique_events_count = len(unique_df)

        METRICS["llm_summary_events_processed_total"].labels(
            sketch_id=str(sketch_id)
        ).inc(total_events_count)
        METRICS["llm_summary_unique_events_total"].labels(sketch_id=str(sketch_id)).inc(
            unique_events_count
        )

        logger.debug("Summarizing %d events", total_events_count)
        logger.debug("Reduced to %d unique events", unique_events_count)

        if not events_dict:
            return jsonify(
                {"summary": "No events to summarize based on the current filter."}
            )

        try:
            prompt_text = self._get_prompt_text(events_dict)
            # TODO(itsmvd): Change to proper background worker such as celery in future
            with multiprocessing.Manager() as manager:
                shared_response = manager.dict()
                p = multiprocessing.Process(
                    target=self._get_content_with_timeout,
                    args=(prompt_text, summary_response_schema, shared_response),
                )
                p.start()
                p.join(timeout=_LLM_TIMEOUT_WAIT_SECONDS)

                if p.is_alive():
                    logger.warning(
                        "LLM call timed out after %d seconds.",
                        _LLM_TIMEOUT_WAIT_SECONDS,
                    )
                    p.terminate()
                    p.join()
                    METRICS["llm_summary_errors_total"].labels(
                        sketch_id=str(sketch_id), error_type="timeout"
                    ).inc()
                    abort(
                        definitions.HTTP_STATUS_CODE_BAD_REQUEST,
                        "LLM call timed out.",
                    )

                response = dict(shared_response)

        except Exception as e:
            logger.error(
                "Unable to call LLM to process events for summary. Error: %s", e
            )
            METRICS["llm_summary_errors_total"].labels(
                sketch_id=str(sketch_id), error_type="llm_api_error"
            ).inc()
            abort(
                definitions.HTTP_STATUS_CODE_BAD_REQUEST,
                "Unable to get LLM data, check server configuration for LLM.",
            )

        if not response or not response.get("summary"):
            logger.error("No valid summary from LLM.")
            METRICS["llm_summary_errors_total"].labels(
                sketch_id=str(sketch_id), error_type="no_summary_error"
            ).inc()
            abort(
                definitions.HTTP_STATUS_CODE_BAD_REQUEST,
                "No valid summary from LLM.",
            )
        summary_text = response.get("summary")

        duration = time.time() - start_time
        METRICS["llm_summary_duration_seconds"].labels(
            sketch_id=str(sketch_id)
        ).observe(duration)

        # TODO: Add runtime seconds
        return jsonify(
            {
                "summary": summary_text,
                "summary_event_count": total_events_count,
                "summary_unique_event_count": unique_events_count,
            }
        )

    def _get_content_with_timeout(
        self,
        prompt: str,
        response_schema: Optional[dict],
        shared_response: multiprocessing.managers.DictProxy,
    ) -> None:
        """Send a prompt to the LLM and get a response within a process.

        Args:
            prompt: The prompt to send to the LLM.
            response_schema: If set, the LLM will attempt to return a structured
                response that conforms to this schema. If set to None, the LLM
                will return an unstructured response
            shared_response: A shared dictionary to store the response.
        """
        try:
            response = self._get_content(prompt, response_schema)
            shared_response.update(response)
        except Exception as e:
            logger.error("Error in LLM call within process: %s", e)
            shared_response.update({"error": str(e)})

    def _get_content(
        self, prompt: str, response_schema: Optional[dict] = None
    ) -> Optional[Dict]:
        """Send a prompt to the LLM and get a response.

        Args:
            prompt: The prompt to send to the LLM.
            response_schema: If set, the LLM will attempt to return a structured
                response that conforms to this schema. If set to None, the LLM
                will return an unstructured response

        Returns:
            If response_schema is set, a dictionary representing the structured
            response will be returned. If response_schema is None, the raw text
            response from the LLM will be returned as a string.

        Raises:
            HTTP_STATUS_CODE_INTERNAL_SERVER_ERROR: If no LLM provider is defined
            in the configuration file
            HTTP_STATUS_CODE_BAD_REQUEST: If an error occurs with the
                configured LLM provider
        """
        try:
            feature_name = "llm_summarization"
            llm = llms.manager.LLMManager.create_provider(feature_name=feature_name)
        except Exception as e:
            logger.error("Error LLM Provider: %s", e)
            abort(
                definitions.HTTP_STATUS_CODE_BAD_REQUEST,
                "An error occurred with the configured LLM provider. "
                "Please check the logs and configuration file.",
            )

        prediction = llm.generate(prompt, response_schema=response_schema)
        return prediction

    def _run_timesketch_query(
        self,
        sketch: Sketch,
        query_string: str = "*",
        query_filter: Optional[dict] = None,
        id_list: Optional[list] = None,
    ) -> pd.DataFrame:
        """Runs a timesketch query.

        Args:
            sketch: The Sketch object to query.
            query_string: The query string to use.
            query_filter: The query filter to use.
            id_list: A list of event IDs to use.

        Returns:
            A pandas DataFrame containing the query results.

         Raises:
            HTTP_STATUS_CODE_BAD_REQUEST: If no valid search indices were found
                to perform the search on.
        """
        if not query_filter:
            query_filter = {}

        if id_list:
            id_query = " OR ".join([f'_id:"{event_id}"' for event_id in id_list])
            query_string = id_query

        all_indices = list({t.searchindex.index_name for t in sketch.timelines})
        indices = query_filter.get("indices", all_indices)

        if "_all" in indices:
            indices = all_indices

        indices, timeline_ids = utils.get_validated_indices(indices, sketch)

        if not indices:
            abort(
                definitions.HTTP_STATUS_CODE_BAD_REQUEST,
                "No valid search indices were found to perform the search on.",
            )

        result = self.datastore.search(
            sketch_id=sketch.id,
            query_string=query_string,
            query_filter=query_filter,
            query_dsl="",
            indices=indices,
            timeline_ids=timeline_ids,
        )

        return export.query_results_to_dataframe(result, sketch)
