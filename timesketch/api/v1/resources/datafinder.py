# Copyright 2021 Google Inc. All rights reserved.
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
"""Various data related resources for version 1 of the Timesketch API."""

import logging
import uuid

from flask import jsonify
from flask import request
from flask import abort
from flask_restful import Resource
from flask_login import login_required

from timesketch.api.v1 import resources
from timesketch.lib.definitions import HTTP_STATUS_CODE_BAD_REQUEST
from timesketch.lib.definitions import HTTP_STATUS_CODE_NOT_FOUND
from timesketch.models.sketch import Sketch


logger = logging.getLogger("timesketch.data_api")


class DataFinderResource(resources.ResourceMixin, Resource):
    """Resource for finding data within a Sketch."""

    @login_required
    def post(self, sketch_id):
        """Handles POST request to the resource.

        Args:
          sketch_id (int): Identifier for the Sketch the datasource belongs to.

        Returns:
            A list of JSON representations of the data sources.
        """
        sketch = Sketch.get_with_acl(sketch_id)
        if not sketch:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No sketch found with this ID.")

        if sketch.get_status.status == "archived":
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                "Unable to search for data sources from an archived sketch.",
            )

        form = request.json
        if not form:
            form = request.data

        start_date = form.get("start_date")
        if not start_date:
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST, "Need a start date for discovering data."
            )

        end_date = form.get("end_date")
        if not end_date:
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST, "Need an end date for discovering data."
            )

        rule_names = form.get("rule_names", [])
        if not rule_names:
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                "Need a list of rule names to be able to start the data discovery.",
            )

        if not isinstance(rule_names, (list, tuple)):
            abort(HTTP_STATUS_CODE_BAD_REQUEST, "Rule names needs to a list")

        if any([not isinstance(x, str) for x in rule_names]):
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                "Rule names needs to a list of string values.",
            )

        timeline_ids_read = form.get("timeline_ids", [])
        timeline_ids = []
        for timeline in sketch.active_timelines:
            if timeline.id in timeline_ids_read:
                timeline_ids.append(timeline.id)

        parameters = form.get("parameters")
        if parameters and not isinstance(parameters, dict):
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                "If parameters are provided, it needs to be a dict.",
            )

        # Start Celery pipeline for indexing and analysis.
        # Import here to avoid circular imports.
        # pylint: disable=import-outside-toplevel
        from timesketch.lib import tasks

        pipeline = tasks.run_data_finder(
            rule_names=rule_names,
            sketch_id=sketch.id,
            start_date=start_date,
            end_date=end_date,
            timeline_ids=timeline_ids,
            parameters=parameters,
        )
        task_id = uuid.uuid4().hex
        pipeline.apply_async(task_id=task_id)

        result = pipeline.delay()
        results = result.join()

        schema = {
            "meta": {"rules": rule_names},
            "objects": results,
        }
        return jsonify(schema)
