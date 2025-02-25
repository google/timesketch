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
"""Timeline resources for version 1 of the Timesketch API."""

import codecs
import json
import logging
import uuid

import opensearchpy
import six
from flask import abort, current_app, jsonify, request
from flask_login import current_user, login_required
from flask_restful import Resource

from timesketch.api.v1 import resources, utils
from timesketch.lib import forms
from timesketch.lib.aggregators import manager as aggregator_manager
from timesketch.lib.definitions import (
    HTTP_STATUS_CODE_BAD_REQUEST,
    HTTP_STATUS_CODE_CREATED,
    HTTP_STATUS_CODE_FORBIDDEN,
    HTTP_STATUS_CODE_INTERNAL_SERVER_ERROR,
    HTTP_STATUS_CODE_NOT_FOUND,
    HTTP_STATUS_CODE_OK,
)
from timesketch.models import db_session
from timesketch.models.sketch import SearchIndex, Sketch, Timeline

logger = logging.getLogger("timesketch.timeline_api")


class TimelineListResource(resources.ResourceMixin, Resource):
    """Resource to get all timelines for sketch."""

    @login_required
    def get(self, sketch_id):
        """Handles GET request to the resource.

        Returns:
            View in JSON (instance of flask.wrappers.Response)
        """
        sketch = Sketch.get_with_acl(sketch_id)
        if not sketch:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No sketch found with this ID.")
        if not sketch.has_permission(current_user, "read"):
            abort(
                HTTP_STATUS_CODE_FORBIDDEN,
                "User does not have read access controls on sketch.",
            )
        return self.to_json(sketch.timelines)

    @login_required
    def post(self, sketch_id):
        """Handles POST request to the resource.

        Returns:
            A sketch in JSON (instance of flask.wrappers.Response)
        """
        sketch = Sketch.get_with_acl(sketch_id)
        if not sketch:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No sketch found with this ID.")

        if not sketch.has_permission(current_user, "write"):
            abort(
                HTTP_STATUS_CODE_FORBIDDEN,
                "User does not have write access controls on sketch.",
            )

        form = request.json
        if not form:
            form = request.data

        metadata = {"created": True}

        searchindex_id = form.get("timeline", 0)
        if isinstance(searchindex_id, str) and searchindex_id.isdigit():
            searchindex_id = int(searchindex_id)

        if not isinstance(searchindex_id, int):
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                "The timeline (searchindex id) needs to be an integer.",
            )

        searchindex = SearchIndex.get_with_acl(searchindex_id)
        if searchindex.get_status.status == "deleted":
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                "Unable to create a timeline using a deleted search index",
            )

        timeline_name = form.get("timeline_name", searchindex.name)
        timeline = Timeline(
            name=timeline_name,
            description=searchindex.description,
            sketch=sketch,
            user=current_user,
            searchindex=searchindex,
        )
        sketch.timelines.append(timeline)
        labels_to_prevent_deletion = current_app.config.get(
            "LABELS_TO_PREVENT_DELETION", []
        )

        for label in sketch.get_labels:
            if label not in labels_to_prevent_deletion:
                continue
            timeline.add_label(label)
            searchindex.add_label(label)

        # Set status to ready so the timeline can be queried.
        timeline.set_status("ready")

        db_session.add(timeline)
        db_session.commit()
        return_code = HTTP_STATUS_CODE_CREATED

        # Run sketch analyzers when timeline is added. Import here to avoid
        # circular imports.

        if current_app.config.get("AUTO_SKETCH_ANALYZERS"):

            from timesketch.lib import tasks

            sketch_analyzer_group, _ = tasks.build_sketch_analysis_pipeline(
                sketch_id, searchindex_id, current_user.id, timeline_id=timeline.id
            )
            if sketch_analyzer_group:
                pipeline = (
                    tasks.run_sketch_init.s([searchindex.index_name])
                    | sketch_analyzer_group
                )
                pipeline.apply_async()

        # Update the last activity of a sketch.
        utils.update_sketch_last_activity(sketch)

        return self.to_json(timeline, meta=metadata, status_code=return_code)


class TimelineResource(resources.ResourceMixin, Resource):
    """Resource to get timeline."""

    def _add_label(self, timeline, label):
        """Add a label to the timeline."""
        if timeline.has_label(label):
            logger.warning(
                "Unable to apply the label [{0:s}] to timeline {1:s}, "
                "already exists.".format(label, timeline.name)
            )
            return False
        timeline.add_label(label, user=current_user)
        return True

    def _remove_label(self, timeline, label):
        """Removes a label from a timeline."""
        if not timeline.has_label(label):
            logger.warning(
                "Unable to remove the label [{0:s}] from timeline {1:s}, "
                "label does not exist.".format(label, timeline.name)
            )
            return False
        timeline.remove_label(label)
        return True

    @login_required
    def get(self, sketch_id, timeline_id):
        """Handles GET request to the resource.

        Args:
            sketch_id: Integer primary key for a sketch database model
            timeline_id: Integer primary key for a timeline database model
        """
        sketch = Sketch.get_with_acl(sketch_id)
        if not sketch:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No sketch found with this ID.")

        timeline = Timeline.get_by_id(timeline_id)
        if not timeline:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No Timeline found with this ID.")

        if timeline.sketch is None:
            abort(
                HTTP_STATUS_CODE_NOT_FOUND,
                f"The timeline {timeline_id} does not have an associated "
                "sketch, does it belong to a sketch?",
            )

        # Check that this timeline belongs to the sketch
        if timeline.sketch.id != sketch.id:
            abort(
                HTTP_STATUS_CODE_NOT_FOUND,
                "The sketch ID ({0:d}) does not match with the timeline "
                "sketch ID ({1:d})".format(sketch.id, timeline.sketch.id),
            )

        if not sketch.has_permission(user=current_user, permission="read"):
            abort(
                HTTP_STATUS_CODE_FORBIDDEN,
                "The user does not have read permission on the sketch.",
            )

        meta = {"lines_indexed": None}
        if timeline.get_status.status != "fail":
            result = self.datastore.search(
                sketch_id=timeline.searchindex.id,
                query_string="*",
                query_filter={
                    "from": 0,
                    "indices": [timeline.id],
                    "order": "asc",
                    "chips": [],
                },
                query_dsl=None,
                indices=[timeline.searchindex.index_name],
                timeline_ids=[timeline.id],
                count=True,
            )
            meta["lines_indexed"] = result

        return self.to_json(timeline, meta=meta)

    @login_required
    def post(self, sketch_id, timeline_id):
        """Handles POST request to the resource.

        Args:
            sketch_id: Integer primary key for a sketch database model
            timeline_id: Integer primary key for a timeline database model
        """
        sketch = Sketch.get_with_acl(sketch_id)
        if not sketch:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No sketch found with this ID.")
        timeline = Timeline.get_by_id(timeline_id)
        if not timeline:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No timeline found with this ID.")

        if timeline.sketch is None:
            abort(
                HTTP_STATUS_CODE_NOT_FOUND, "No sketch associated with this timeline."
            )

        # Check that this timeline belongs to the sketch
        if timeline.sketch.id != sketch.id:
            abort(
                HTTP_STATUS_CODE_NOT_FOUND,
                "The sketch ID ({0:d}) does not match with the timeline "
                "sketch ID ({1:d})".format(sketch.id, timeline.sketch.id),
            )

        if not sketch.has_permission(user=current_user, permission="write"):
            abort(
                HTTP_STATUS_CODE_FORBIDDEN,
                "The user does not have write permission on the sketch.",
            )

        form = forms.TimelineForm.build(request)
        if not form.validate_on_submit():
            abort(HTTP_STATUS_CODE_BAD_REQUEST, "Unable to validate form data.")

        if form.labels.data:
            label_string = form.labels.data
            labels = json.loads(label_string)
            if not isinstance(labels, (list, tuple)):
                abort(
                    HTTP_STATUS_CODE_BAD_REQUEST,
                    (
                        "Label needs to be a JSON string that "
                        "converts to a list of strings."
                    ),
                )
            if not all([isinstance(x, str) for x in labels]):
                abort(
                    HTTP_STATUS_CODE_BAD_REQUEST,
                    (
                        "Label needs to be a JSON string that "
                        "converts to a list of strings (not all strings)"
                    ),
                )

            label_action = form.label_action.data
            if label_action not in ("add", "remove"):
                abort(
                    HTTP_STATUS_CODE_BAD_REQUEST,
                    "Label action needs to be either add or remove.",
                )

            changed = False
            if label_action == "add":
                changes = []
                for label in labels:
                    changes.append(self._add_label(timeline=timeline, label=label))
                changed = any(changes)
            elif label_action == "remove":
                changes = []
                for label in labels:
                    changes.append(self._remove_label(timeline=timeline, label=label))
                changed = any(changes)

            if not changed:
                abort(
                    HTTP_STATUS_CODE_BAD_REQUEST,
                    "Label [{0:s}] not {1:s}".format(", ".join(labels), label_action),
                )

            db_session.add(timeline)
            db_session.commit()
            return HTTP_STATUS_CODE_OK

        timeline.name = form.name.data
        timeline.description = form.description.data
        timeline.color = form.color.data
        db_session.add(timeline)
        db_session.commit()

        # Update the last activity of a sketch.
        utils.update_sketch_last_activity(sketch)

        return HTTP_STATUS_CODE_OK

    @login_required
    def delete(self, sketch_id, timeline_id):
        """Handles DELETE request to the resource.

        Args:
            sketch_id: Integer primary key for a sketch database model
            timeline_id: Integer primary key for a timeline database model
        """
        sketch = Sketch.get_with_acl(sketch_id)
        if not sketch:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No sketch found with this ID.")

        timeline = Timeline.get_by_id(timeline_id)
        if not timeline:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No timeline found with this ID.")

        if timeline.sketch is None:
            abort(
                HTTP_STATUS_CODE_NOT_FOUND, "No sketch associated with this timeline."
            )

        # Check that this timeline belongs to the sketch
        if timeline.sketch.id != sketch.id:
            if not timeline:
                msg = "No timeline found with this ID."
            elif not sketch:
                msg = "No sketch found with this ID."
            else:
                sketch_use = sketch.id or "No sketch ID"
                sketch_string = str(sketch_use)

                timeline_use = timeline.sketch.id or (
                    "No sketch associated with the timeline."
                )
                timeline_string = str(timeline_use)

                msg = (
                    "The sketch ID ({0:s}) does not match with the timeline "
                    "sketch ID ({1:s})".format(sketch_string, timeline_string)
                )
            abort(HTTP_STATUS_CODE_NOT_FOUND, msg)

        if not sketch.has_permission(user=current_user, permission="write"):
            abort(
                HTTP_STATUS_CODE_FORBIDDEN,
                "The user does not have write permission on the sketch.",
            )

        not_delete_labels = current_app.config.get("LABELS_TO_PREVENT_DELETION", [])
        for label in not_delete_labels:
            if timeline.has_label(label):
                abort(
                    HTTP_STATUS_CODE_FORBIDDEN,
                    "Timelines with label [{0:s}] cannot be deleted.".format(label),
                )

        # Check if this searchindex is used in other sketches.
        close_index = True
        searchindex = timeline.searchindex
        index_name = searchindex.index_name
        search_indices = SearchIndex.query.filter_by(index_name=index_name).all()
        timelines = []
        for index in search_indices:
            timelines.extend(index.timelines)

        for timeline_ in timelines:
            if timeline_.sketch is None:
                continue

            if timeline_.sketch.id != sketch.id:
                close_index = False
                break

            if timeline_.id != timeline_id:
                # There are more than a single timeline using this index_name,
                # we can't close it (unless this timeline is archived).
                if timeline_.get_status.status != "archived":
                    close_index = False
                    break

            searchindex.set_status(status="archived")
            timeline.set_status(status="archived")

        sketch.timelines.remove(timeline)
        db_session.commit()

        # Update the last activity of a sketch.
        utils.update_sketch_last_activity(sketch)

        return HTTP_STATUS_CODE_OK


class TimelineCreateResource(resources.ResourceMixin, Resource):
    """Resource to create a timeline."""

    @login_required
    def post(self):
        """Handles POST request to the resource.

        Returns:
            A view in JSON (instance of flask.wrappers.Response)
        """
        upload_enabled = current_app.config["UPLOAD_ENABLED"]
        if not upload_enabled:
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                "Failed to create timeline, upload not enabled",
            )

        form = forms.CreateTimelineForm()
        if not form.validate_on_submit():
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                "Failed to create timeline, form data not validated",
            )

        sketch_id = form.sketch_id.data
        timeline_name = form.name.data

        sketch = None
        if sketch_id:
            sketch = Sketch.get_with_acl(sketch_id)
            if not sketch:
                abort(HTTP_STATUS_CODE_NOT_FOUND, "No sketch found with this ID.")

        # We do not need a human readable filename or
        # datastore index name, so we use UUIDs here.
        index_name = uuid.uuid4().hex
        if not isinstance(index_name, six.text_type):
            index_name = codecs.decode(index_name, "utf-8")

        # Create the search index in the Timesketch database
        searchindex = SearchIndex.get_or_create(
            name=timeline_name,
            description=timeline_name,
            user=current_user,
            index_name=index_name,
        )
        searchindex.grant_permission(permission="read", user=current_user)
        searchindex.grant_permission(permission="write", user=current_user)
        searchindex.grant_permission(permission="delete", user=current_user)
        searchindex.set_status("processing")
        db_session.add(searchindex)
        db_session.commit()

        timeline = None
        if sketch and sketch.has_permission(current_user, "write"):
            timeline = Timeline(
                name=searchindex.name,
                description=searchindex.description,
                sketch=sketch,
                user=current_user,
                searchindex=searchindex,
            )
            sketch.timelines.append(timeline)
            db_session.add(timeline)
            db_session.commit()

        # Return Timeline if it was created.

        if timeline:
            return self.to_json(timeline, status_code=HTTP_STATUS_CODE_CREATED)

        # Update the last activity of a sketch.
        utils.update_sketch_last_activity(sketch)

        return self.to_json(searchindex, status_code=HTTP_STATUS_CODE_CREATED)


# TODO(Issue 3200): Research more efficient ways to gather unique fields.
class TimelineFieldsResource(resources.ResourceMixin, Resource):
    """Resource to retrieve unique fields present in a timeline.

    This resource aggregates data types within a timeline and then queries
    OpenSearch to retrieve all unique fields present across those data types,
    excluding default Timesketch fields.
    """

    @login_required
    def get(self, sketch_id, timeline_id):
        """Handles GET request to retrieve unique fields in a timeline.

        Args:
            sketch_id (int): The ID of the sketch.
            timeline_id (int): The ID of the timeline.

        Returns:
            flask.wrappers.Response: A JSON response containing a list of
                unique fields in the timeline, sorted alphabetically. Returns
                an empty list if no fields are found or if there's an error.
                Possible error codes: 400, 403, 404.
        """

        sketch = Sketch.get_with_acl(sketch_id)
        if not sketch:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No sketch found with this ID.")
        if not sketch.has_permission(current_user, "read"):
            abort(
                HTTP_STATUS_CODE_FORBIDDEN,
                "User does not have read access controls on sketch.",
            )

        timeline = Timeline.get_by_id(timeline_id)
        if not timeline:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No timeline found with this ID.")

        # Check that this timeline belongs to the sketch
        if timeline.sketch.id != sketch.id:
            abort(
                HTTP_STATUS_CODE_NOT_FOUND,
                "The timeline does not belong to the sketch.",
            )

        index_name = timeline.searchindex.index_name
        timeline_fields = set()

        # 1. Get distinct data types for the timeline using aggregation
        aggregator_name = "field_bucket"
        aggregator_parameters = {
            "field": "data_type",
            "limit": "10000",  # Get all data types
        }

        agg_class = aggregator_manager.AggregatorManager.get_aggregator(aggregator_name)
        if not agg_class:
            abort(HTTP_STATUS_CODE_NOT_FOUND, f"Aggregator {aggregator_name} not found")

        aggregator = agg_class(
            sketch_id=sketch_id, indices=[index_name], timeline_ids=[timeline_id]
        )
        result_obj = aggregator.run(**aggregator_parameters)

        if not result_obj:
            abort(HTTP_STATUS_CODE_BAD_REQUEST, "Error running data type aggregation.")

        data_types = sorted([bucket["data_type"] for bucket in result_obj.values])

        # 2. For each data type, query for a single event to get fields
        for data_type in data_types:
            query_filter = {"indices": [timeline_id], "size": 1}

            try:
                result = self.datastore.search(
                    sketch_id=sketch_id,
                    query_string=f'data_type:"{data_type}"',
                    query_filter=query_filter,
                    query_dsl=None,
                    indices=[index_name],
                    timeline_ids=[timeline_id],
                )
            except ValueError as e:
                abort(HTTP_STATUS_CODE_BAD_REQUEST, str(e))

            if isinstance(result, dict) and result.get("hits", {}).get("hits", []):
                event = result["hits"]["hits"][0]["_source"]
                for field in event:
                    if field not in [
                        "datetime",
                        "timestamp",
                        "__ts_timeline_id",
                    ]:
                        timeline_fields.add(field)

        return jsonify({"objects": sorted(list(timeline_fields))})
