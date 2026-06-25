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
"""Export stream resources for version 1 of the Timesketch API."""

import json
import logging

from flask import request
from flask import abort
from flask import Response
from flask import stream_with_context
from flask import current_app
from flask_restful import Resource
from flask_login import login_required
from flask_login import current_user

from timesketch.api.v1 import resources
from timesketch.lib import utils
from timesketch.lib import forms
from timesketch.lib.definitions import HTTP_STATUS_CODE_NOT_FOUND
from timesketch.lib.definitions import HTTP_STATUS_CODE_FORBIDDEN
from timesketch.lib.definitions import HTTP_STATUS_CODE_BAD_REQUEST
from timesketch.lib.definitions import DEFAULT_SOURCE_FIELDS
from timesketch.lib.datastores.opensearch import OpenSearchDataStore
from timesketch.models.sketch import Sketch

logger = logging.getLogger("timesketch.api.exportstream")

DEFAULT_POOL_MAXSIZE = 60


class ExportStreamListResource(resources.ResourceMixin, Resource):
    """Resource to export all events for a sketch."""

    @property
    def datastore(self):
        """Property to get an instance of the datastore backend.

        We override the default datastore property to ensure we have a
        connection pool large enough to support the multiple threads
        used during sliced export.

        Returns:
            Instance of lib.datastores.opensearch.OpenSearchDatastore
        """
        # Default to 60 connections to align with the LLM Log Analyzer implementation
        pool_maxsize = current_app.config.get(
            "OPENSEARCH_SLICED_EXPORT_POOL_MAXSIZE", DEFAULT_POOL_MAXSIZE
        )
        return OpenSearchDataStore(pool_maxsize=pool_maxsize)

    @login_required
    def post(self, sketch_id):
        """Handles POST request to export stream events.

        Handler for /api/v1/sketches/:sketch_id/exportstream/

        Note:
            This endpoint is optimized for streaming large volumes of event
            data and is not intended as a substitute for the interactive
            `/explore` endpoint. While it supports basic filtering to narrow
            down the export scope, advanced search features (like filtering for
            labels and pagination) are not available.

        Args:
            sketch_id (int): Integer primary key for a sketch database model.

        Returns:
            Streamed response of events in JSONL format.

        Raises:
            HTTPException:
                - 400 (BAD_REQUEST): If the form data is invalid or if no
                  valid search indices are found for the export.
                - 403 (FORBIDDEN): If the user does not have read permissions
                  for the sketch, or if the sketch is archived.
                - 404 (NOT_FOUND): If the sketch with the given ID does not
                  exist.
        """
        sketch = Sketch.get_with_acl(sketch_id)
        if not sketch:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No sketch found with this ID.")

        if not sketch.has_permission(current_user, "read"):
            abort(
                HTTP_STATUS_CODE_FORBIDDEN,
                "User does not have read access controls on sketch.",
            )

        if sketch.get_status.status == "archived":
            abort(HTTP_STATUS_CODE_FORBIDDEN, "Unable to query on an archived sketch.")

        form = forms.ExploreForm.build(request)
        if not form.validate_on_submit():
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                "Unable to export data, unable to validate form data",
            )

        query_dsl = form.dsl.data
        query_filter = request.json.get("filter") or {}
        return_field_string = form.fields.data

        # Resolve return fields
        if return_field_string:
            return_fields = [x.strip() for x in return_field_string.split(",")]
        else:
            return_fields = query_filter.get("fields", [])
            return_fields = [field["field"] for field in return_fields]
            if not return_fields:
                return_fields = DEFAULT_SOURCE_FIELDS

        # Resolve Indices
        all_timeline_ids = [t.id for t in sketch.timelines]
        indices = query_filter.get("indices", all_timeline_ids)
        if "_all" in indices:
            indices = all_timeline_ids

        # Validate indices and get timeline IDs (checks permissions implicitly)
        indices, timeline_ids = utils.get_validated_indices(indices, sketch)

        # Map to actual OpenSearch index names for the PIT
        timeline_ids_set = set(timeline_ids)
        indices_for_pit = [
            t.searchindex.index_name
            for t in sketch.timelines
            if t.id in timeline_ids_set
        ]

        # Final check to ensure indices exist in backend
        indices_for_pit = utils.validate_indices(indices_for_pit, self.datastore)

        if not indices_for_pit:
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                "No valid search indices were found to perform the export on.",
            )

        # Build the base query DSL using standard logic to ensure timeline isolation
        full_query_dsl = self.datastore.build_query(
            sketch.id,
            form.query.data,
            query_filter,
            query_dsl,
            None,  # No aggregations
            timeline_ids,
        )

        # Prepare the lightweight body for slicing.
        # Slicing handles sort/size/pagination, so we only extract query/filter/source.
        base_query_body = {
            "query": full_query_dsl.get("query", {}),
        }

        if return_fields:
            base_query_body["_source"] = return_fields

        post_filter = full_query_dsl.get("post_filter")
        if post_filter:
            base_query_body["post_filter"] = post_filter

        def generate():
            try:
                event_generator = self.datastore.export_events_with_slicing(
                    indices_for_pit=indices_for_pit,
                    base_query_body=base_query_body,
                )

                for event in event_generator:
                    yield json.dumps(event) + "\n"
            except Exception as e:
                logger.error(
                    "Error during streaming export for sketch %s on timelines %s: %s",
                    sketch_id,
                    ",".join(map(str, timeline_ids)),
                    e,
                    exc_info=True,
                )
                raise

        return Response(
            stream_with_context(generate()), mimetype="application/x-json-stream"
        )
