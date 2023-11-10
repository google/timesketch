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
"""Data Source resources for version 1 of the Timesketch API."""

import logging

from flask import jsonify
from flask import request
from flask import abort
from flask_restful import Resource
from flask_login import login_required
from flask_login import current_user

from timesketch.api.v1 import resources
from timesketch.lib.definitions import HTTP_STATUS_CODE_CREATED
from timesketch.lib.definitions import HTTP_STATUS_CODE_BAD_REQUEST
from timesketch.lib.definitions import HTTP_STATUS_CODE_FORBIDDEN
from timesketch.lib.definitions import HTTP_STATUS_CODE_NOT_FOUND
from timesketch.models import db_session
from timesketch.models.sketch import Sketch
from timesketch.models.sketch import Timeline
from timesketch.models.sketch import DataSource


logger = logging.getLogger("timesketch.datasource_api")


class DataSourceListResource(resources.ResourceMixin, Resource):
    """Resource for listing DataSources associated with a Sketch."""

    @login_required
    def get(self, sketch_id):
        """Handles GET request to the resource.

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
                "Unable to fetch data sources from an archived sketch.",
            )

        number_of_timelines = 0
        data_sources = []
        for timeline in sketch.active_timelines:
            number_of_timelines += 1
            for data_source in timeline.datasources:
                data_sources.append(data_source)

        schema = {
            "meta": {
                "number_of_timelines": number_of_timelines,
                "number_of_sources": len(data_sources),
            },
            "objects": data_sources,
        }
        return jsonify(schema)

    @login_required
    def post(self, sketch_id):
        """Handles POST request to the resource.

        Args:
          sketch_id (int): Identifier for the Sketch the datasource belongs to.

        Returns:
            A datasource in JSON (instance of flask.wrappers.Response)
        """
        sketch = Sketch.get_with_acl(sketch_id)
        if not sketch:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No sketch found with this ID.")

        if sketch.get_status.status == "archived":
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                "Unable to fetch data sources from an archived sketch.",
            )

        if not sketch.has_permission(current_user, "write"):
            abort(
                HTTP_STATUS_CODE_FORBIDDEN,
                ("User does not have sufficient write access to " "to the sketch."),
            )

        form = request.json
        if not form:
            form = request.data

        timeline_id = form.get("timeline_id")
        if not timeline_id:
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                "Unable to create a data source without a timeline " "identifier.",
            )

        timeline = Timeline.get_by_id(timeline_id)
        if not timeline:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No timeline found with this ID.")

        if timeline not in sketch.active_timelines:
            abort(
                HTTP_STATUS_CODE_NOT_FOUND,
                "The timeline is not part of the active timelines in " "the sketch.",
            )

        datasource = DataSource(
            timeline=timeline,
            user=current_user,
            provider=form.get("provider", "N/A"),
            context=form.get("context", "N/A"),
            file_on_disk="",
            file_size=0,
            original_filename=form.get("original_filename", ""),
            data_label=form.get("data_label", "data"),
        )

        timeline.datasources.append(datasource)
        db_session.add(datasource)
        db_session.add(timeline)
        db_session.commit()

        return self.to_json(datasource, status_code=HTTP_STATUS_CODE_CREATED)


class DataSourceResource(resources.ResourceMixin, Resource):
    """Resource for accessing data sources."""

    def _verify_sketch_and_datasource(self, sketch_id, datasource_id):
        """Verify and abort if unable to proceed.

        This function aborts if the ACLs on the sketch are not sufficient and
        the data source does not belong to the sketch in question.
        """
        sketch = Sketch.get_with_acl(sketch_id)
        if not sketch:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No sketch found with this ID.")

        if sketch.get_status.status == "archived":
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                "Unable to fetch data sources from an archived sketch.",
            )

        data_source = DataSource.get_by_id(datasource_id)
        if not data_source:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No DataSource found with this ID.")

        if data_source.timeline.sketch.id != sketch.id:
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                "Data Source does not match the Sketch ID.",
            )

    @login_required
    def get(self, sketch_id, datasource_id):
        """Handles GET request to the resource.

        Args:
          sketch_id (int): Identifier for the Sketch the datasource belongs to.
          datasource_id (int): Identifier for the datasource.

        Returns:
            A JSON representation of the data source.
        """
        self._verify_sketch_and_datasource(sketch_id, datasource_id)
        data_source = DataSource.get_by_id(datasource_id)
        return self.to_json(data_source)

    @login_required
    def post(self, sketch_id, datasource_id):
        """Handles POST request to the resource.

        Args:
          sketch_id (int): Identifier for the Sketch the datasource belongs to.
          datasource_id (int): Identifier for the datasource.

        Returns:
            A sketch in JSON (instance of flask.wrappers.Response)
        """
        self._verify_sketch_and_datasource(sketch_id, datasource_id)

        data_source = DataSource.get_by_id(datasource_id)
        changed = False

        form = request.json
        if not form:
            form = request.data

        provider = form.get("provider")
        if provider:
            changed = True
            data_source.provider = provider

        context = form.get("context")
        if context:
            changed = True
            data_source.context = context

        if changed:
            db_session.add(data_source)
            db_session.commit()

        return self.to_json(data_source)
