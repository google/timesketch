# Copyright 2020 Google Inc. All rights reserved.
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
"""Task resources for version 1 of the Timesketch API."""

import datetime

from flask import current_app
from flask import jsonify
from flask import request
from flask_restful import Resource
from flask_login import login_required
from flask_login import current_user

from timesketch.api.v1 import resources
from timesketch.models.sketch import SearchIndex


class TaskResource(resources.ResourceMixin, Resource):
    """Resource to get information on celery task."""

    # pylint: disable=import-outside-toplevel
    def __init__(self):
        super().__init__()
        # pylint: disable=import-outside-toplevel
        from timesketch.app import create_celery_app

        self.celery = create_celery_app()

    def _get_celery_information(self, job_id):
        # pylint: disable=too-many-function-args
        celery_task = self.celery.AsyncResult(job_id)
        task = dict(
            task_id=celery_task.task_id,
            state=celery_task.state,
            successful=celery_task.successful(),
            result=False,
        )

        if task.get("state", "") == "SUCCESS":
            task["result"] = celery_task.result
        return task

    @login_required
    def get(self):
        """Handles GET request to the resource.

        Returns:
            A view in JSON (instance of flask.wrappers.Response)
        """
        timeout_threshold_seconds = current_app.config.get("CELERY_TASK_TIMEOUT", 7200)

        schema = {"objects": [], "meta": {}}

        job_id = request.args.get("job_id", "")
        if job_id:
            task = self._get_celery_information(job_id)
            schema["objects"].append(task)
            return jsonify(schema)

        indices = (
            SearchIndex.query.filter(SearchIndex.status.any(status="processing"))
            .filter_by(user=current_user)
            .all()
        )
        for search_index in indices:
            if search_index.get_status.status == "deleted":
                continue
            task = self._get_celery_information(search_index.index_name)
            task["name"] = search_index.name

            if task.get("state", "") == "PENDING":
                time_pending = search_index.updated_at - datetime.datetime.now()
                if time_pending.seconds > timeout_threshold_seconds:
                    search_index.set_status("timeout")
            schema["objects"].append(task)
        return jsonify(schema)
