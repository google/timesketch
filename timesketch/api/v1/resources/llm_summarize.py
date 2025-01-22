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
from flask import request, abort, jsonify
from flask_restful import Resource
from flask_login import login_required, current_user
from timesketch.api.v1 import resources
from timesketch.lib.definitions import HTTP_STATUS_CODE_BAD_REQUEST
from timesketch.lib.definitions import HTTP_STATUS_CODE_FORBIDDEN
from timesketch.lib.definitions import HTTP_STATUS_CODE_NOT_FOUND
from timesketch.lib.definitions import HTTP_STATUS_CODE_INTERNAL_SERVER_ERROR
from timesketch.models.sketch import Sketch
from timesketch.lib.llms import manager
from flask import current_app
from timesketch.lib import utils
from timesketch.api.v1 import export
from typing import Dict, Optional


logger = logging.getLogger("timesketch.api.llm_summarize")

summary_response_schema = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
    },
    "required": ["summary"],
}


class LLMSummarizeResource(resources.ResourceMixin, Resource):
    """Resource to get LLM summary of events."""

    @login_required
    def post(self, sketch_id):
        """Handles POST request to the resource.
        Handler for /api/v1/sketches/:sketch_id/events/summary/
        Args:
            sketch_id: Integer primary key for a sketch database model
        Returns:
            JSON with event summary
        """
        sketch = Sketch.get_with_acl(sketch_id)
        if not sketch:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No sketch found with this ID.")
        if not sketch.has_permission(current_user, "read"):
            abort(
                HTTP_STATUS_CODE_FORBIDDEN,
                "User does not have read access controls on sketch.",
            )

        form = request.json
        if not form:
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST, "The POST request requires data"
            )

        query_filter = form.get("filter", {})
        query_string = form.get("query", "*")

        events_df = self._run_timesketch_query(sketch, query_string, query_filter)

        # TODO (mvd): Add tags for extra context
        new_df = events_df[["message"]] # Only need message for summary

        logger.info(f'Summarizing {len(new_df)} events')

        unique_df = new_df.drop_duplicates(subset="message", keep="first")
        events_dict = unique_df.to_dict(orient="records")

        logger.info(f'Reduced to {len(unique_df)} events')

        if not events_dict:
            return jsonify({"summary": "No events to summarize based on the current filter."})

        try:
            response = self._get_structured_content(
                prompt=f"Summarize the following events to understand the overall context or pattern. Additionally, if you think there is an attack attempt, determine whether it was succesful or not and why. Highlight observables such as IP addresses, filenames etc. using HTML <strong> tags. Events: <events>{events_dict}</events>.",
                response_schema=summary_response_schema,
            )
        except Exception as e:  # pylint: disable=broad-except
            print(f'Error: {e}')
            logger.error(f"Unable to call LLM to process events for summary. Error: {e!s}")
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                "Unable to get LLM data, check server configuration for LLM.",
            )

        if not response or not response.get("summary"):
            logger.error("No valid summary from LLM.")
            abort(
                    HTTP_STATUS_CODE_BAD_REQUEST,
                    "No valid summary from LLM.",
                )

        summary_text = response.get("summary")
        schema = {"summary": summary_text}
        return jsonify(schema)


    def _get_structured_content(self, prompt: str, response_schema) -> Optional[Dict]:
        """Send a prompt to the LLM and enforce a structured output."""
        llm_provider = current_app.config.get("LLM_PROVIDER", "")
        if not llm_provider:
            logger.error("No LLM provider was defined in the main configuration file")
            abort(
                HTTP_STATUS_CODE_INTERNAL_SERVER_ERROR,
                "No LLM provider was defined in the main configuration file",
            )
        try:
            llm = manager.LLMManager.get_provider(llm_provider)(config=current_app.config.get("LLM_PROVIDERS",{}).get(llm_provider))
        except Exception as e:  # pylint: disable=broad-except
            logger.error("Error LLM Provider: {}".format(e))
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                "An error occurred with the configured LLM provider. "
                "Please check the logs and configuration file.",
            )

        prediction = llm.generate(prompt, response_schema=response_schema)
        return prediction
    
    def _run_timesketch_query(self, sketch, query_string="*", query_filter=None, id_list=None):
        """Runs a timesketch query."""
        if not query_filter:
            query_filter = {}

        if id_list:
            id_query = " OR ".join([f'_id:"{event_id}"' for event_id in id_list])
            query_string = id_query

        # Make sure that the indices in the filter are part of the sketch.
        all_indices = list({t.searchindex.index_name for t in sketch.timelines})
        indices = query_filter.get("indices", all_indices)

        # If _all in indices then execute the query on all indices
        if "_all" in indices:
            indices = all_indices

        indices, timeline_ids = utils.get_validated_indices(indices, sketch)

        if not indices:
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
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