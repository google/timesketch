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

import logging
from flask import request, abort, jsonify, current_app
from flask_restful import Resource
from flask_login import login_required, current_user

from timesketch.api.v1 import resources, export
from timesketch.lib import definitions, llms, utils
from timesketch.models.sketch import Sketch
from typing import Dict, Optional
import json

logger = logging.getLogger("timesketch.api.llm_summarize")

summary_response_schema = {
    "type": "object",
    "properties": {"summary": {"type": "string"}},
    "required": ["summary"],
}

class LLMSummarizeResource(resources.ResourceMixin, Resource):
    """Resource to get LLM summary of events."""

    def _get_prompt_text(self, events_dict: list) -> str:
        """Reads the prompt template from file and injects events."""
        prompt_file_path = current_app.config.get("PROMPT_LLM_SUMMARIZATION")
        if not prompt_file_path:
            logger.error("PROMPT_LLM_SUMMARIZATION config not set in timesketch.conf")
            abort(
                definitions.HTTP_STATUS_CODE_INTERNAL_SERVER_ERROR,
                "LLM summarization prompt path not configured.",
            )

        try:
            with open(prompt_file_path, "r", encoding="utf-8") as f:
                prompt_template = f.read()
        except FileNotFoundError:
            logger.error(f"Prompt file not found: {prompt_file_path}")
            abort(
                definitions.HTTP_STATUS_CODE_INTERNAL_SERVER_ERROR,
                "LLM Prompt file not found on the server.",
            )
        except IOError as e:
            logger.error(f"Error reading prompt file: {e}")
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
            sketch_id: Integer primary key for a sketch database model
        Returns:
            JSON with event summary
        """
        sketch = Sketch.get_with_acl(sketch_id)
        if not sketch:
            abort(definitions.HTTP_STATUS_CODE_NOT_FOUND, "No sketch found with this ID.")
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

        # Removed use_response_schema flag

        query_filter = form.get("filter", {})
        query_string = form.get("query", "*")
        if not query_string:
            query_string = "*"

        events_df = self._run_timesketch_query(sketch, query_string, query_filter)
        new_df = events_df[["message"]]
        logger.info(f"Summarizing {len(new_df)} events")

        unique_df = new_df.drop_duplicates(subset="message", keep="first")
        events_dict = unique_df.to_dict(orient="records")
        logger.info(f"Reduced to {len(unique_df)} events")

        total_events_count = len(new_df) # Store total count
        unique_events_count = len(unique_df) 

        if not events_dict:
            return jsonify(
                {"summary": "No events to summarize based on the current filter."}
            )

        try:
            prompt_text = self._get_prompt_text(events_dict)

            # Use response_schema directly in the call to _get_content()
            response = self._get_content(
                prompt=prompt_text,
                response_schema=summary_response_schema
            )
        except Exception as e:
            print(f"Error: {e}")
            logger.error(
                f"Unable to call LLM to process events for summary. Error: {e!s}"
            )
            abort(
                definitions.HTTP_STATUS_CODE_BAD_REQUEST,
                "Unable to get LLM data, check server configuration for LLM.",
            )

        if summary_response_schema:
            if not response or not response.get("summary"):
                logger.error("No valid summary from LLM.")
                abort(
                    definitions.HTTP_STATUS_CODE_BAD_REQUEST,
                    "No valid summary from LLM.",
                )
            summary_text = response.get("summary")
        else: # This branch is technically unreachable in the current setup, but kept for potential future flexibility
            summary_text = response # Assuming response is the raw text if no schema -  Potentially remove if schema is always mandatory

        return jsonify({
            "summary": summary_text,
            "summary_event_count": total_events_count, # Include total count in response - ALWAYS
            "summary_unique_event_count": unique_events_count, # Include unique count in response - ALWAYS
        })

    def _get_content(self, prompt: str, response_schema: Optional[dict] = None) -> Optional[Dict]:
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
        """
        llm_provider = current_app.config.get("LLM_PROVIDER", "")
        if not llm_provider:
            logger.error(
                "No LLM provider was defined in the main configuration file"
            )
            abort(
                definitions.HTTP_STATUS_CODE_INTERNAL_SERVER_ERROR,
                "No LLM provider was defined in the main configuration file",
            )
        try:
            llm = llms.manager.LLMManager().get_provider(llm_provider)()
        except Exception as e:
            logger.error(f"Error LLM Provider: {e}")
            abort(
                definitions.HTTP_STATUS_CODE_BAD_REQUEST,
                "An error occurred with the configured LLM provider. "
                "Please check the logs and configuration file.",
            )

        prediction = llm.generate(prompt, response_schema=response_schema)
        return prediction

    def _run_timesketch_query(
        self, sketch: Sketch, query_string: str = "*", query_filter: Optional[dict] = None, id_list: Optional[list] = None
    ):
        """Runs a timesketch query."""
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
