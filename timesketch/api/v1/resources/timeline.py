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
from flask import jsonify
from flask import request
from flask import abort
from flask import current_app
from flask_restful import Resource
from flask_login import login_required
from flask_login import current_user

from timesketch.api.v1 import resources
from timesketch.api.v1 import utils
from timesketch.lib import forms
from timesketch.lib.definitions import HTTP_STATUS_CODE_OK
from timesketch.lib.definitions import HTTP_STATUS_CODE_CREATED
from timesketch.lib.definitions import HTTP_STATUS_CODE_BAD_REQUEST
from timesketch.lib.definitions import HTTP_STATUS_CODE_FORBIDDEN
from timesketch.lib.definitions import HTTP_STATUS_CODE_NOT_FOUND
from timesketch.lib.definitions import HTTP_STATUS_CODE_INTERNAL_SERVER_ERROR
from timesketch.models import db_session
from timesketch.models.sketch import SearchIndex
from timesketch.models.sketch import Sketch
from timesketch.models.sketch import Timeline
from timesketch.lib.aggregators import manager as aggregator_manager


logger = logging.getLogger("timesketch.timeline_api")


class TimelineListResource(resources.ResourceMixin, Resource):
    """Resource to get all timelines for sketch."""

    @login_required
    def get(self, sketch_id):
        """Handles GET requests to retrieve a list of timelines associated with
        a sketch.

        This method fetches all timelines that are linked to a specific sketch.
        It verifies that the sketch exists and that the current user has read
        permissions for that sketch.

        Args:
            sketch_id (int): The ID of the sketch for which to retrieve timelines.

        Returns:
            flask.wrappers.Response: A JSON response containing a list of timeline
                objects associated with the sketch. Each timeline object includes
                details such as ID, name, description, and other relevant metadata.

        Raises:
            HTTP_STATUS_CODE_NOT_FOUND: If no sketch is found with the given ID.
            HTTP_STATUS_CODE_FORBIDDEN: If the current user does not have read
                access to the specified sketch.
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
        """Handles POST requests to create or associate a timeline with a sketch.

        This method either creates a new timeline and associates it with a sketch,
        or associates an existing timeline (identified by its search index ID)
        with a sketch. It handles the following scenarios:

        Creating a New Timeline: If a timeline with the given search index ID
            does not already exist within the sketch, a new timeline is created.
            The new timeline's name and description are derived from the search
            index, and it is associated with the provided sketch.
        Associating an Existing Timeline: If a timeline with the given
            search index ID already exists within the sketch, it is associated
            with the sketch.
        Running Sketch Analyzers: If the `AUTO_SKETCH_ANALYZERS` config is enabled,
            sketch analyzers will be run on the newly created or associated timeline.
        Adding Labels: If the sketch has labels that are in the
            `LABELS_TO_PREVENT_DELETION` config, those labels will be added
            to the timeline and search index.

        The method ensures that:
        - The sketch exists.
        - The current user has write access to the sketch.
        - The provided search index ID is valid and not associated with a deleted index.

        Args:
            sketch_id (int): The ID of the sketch to which the timeline should be
                associated.

        Returns:
            flask.wrappers.Response: A JSON response containing the timeline object
                and metadata.
                - HTTP_STATUS_CODE_CREATED (201): If a new timeline was created.
                - HTTP_STATUS_CODE_OK (200): If an existing timeline was associated.
                The metadata indicates whether a new timeline was created or not.

        Raises:
            HTTP_STATUS_CODE_NOT_FOUND: If no sketch is found with the given ID.
            HTTP_STATUS_CODE_FORBIDDEN: If the user does not have write access to
                the sketch.
            HTTP_STATUS_CODE_BAD_REQUEST: If the request data is invalid, such as:
                - The timeline (searchindex id) is not an integer.
                - The search index is deleted.
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

        timeline_id = [
            t.searchindex.id
            for t in sketch.timelines
            if t.searchindex.id == searchindex_id
        ]

        if not timeline_id:
            return_code = HTTP_STATUS_CODE_CREATED
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
        else:
            metadata["created"] = False
            return_code = HTTP_STATUS_CODE_OK
            timeline = Timeline.get_by_id(timeline_id)

        # Run sketch analyzers when timeline is added. Import here to avoid
        # circular imports.
        # pylint: disable=import-outside-toplevel
        if current_app.config.get("AUTO_SKETCH_ANALYZERS"):
            # pylint: disable=import-outside-toplevel
            from timesketch.lib import tasks

            sketch_analyzer_group, _ = tasks.build_sketch_analysis_pipeline(
                sketch_id, searchindex_id, current_user.id, timeline_id=timeline_id
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

    def _add_label(self, timeline: object, label: str) -> bool:
        """Adds a label to the timeline if it does not already exist.

        Args:
            timeline: The timeline object to add the label to.
            label: The label string to add.

        Returns:
            True if the label was successfully added, False otherwise.
            Returns False if the label already exists on the timeline.
        """
        if timeline.has_label(label):
            logger.warning(
                "Unable to apply the label [%s] to timeline (ID: %d), already exists.",
                label,
                timeline.id,
            )
            return False
        timeline.add_label(label, user=current_user)
        return True

    def _remove_label(self, timeline: object, label: str) -> bool:
        """Removes a label from a timeline.

        Args:
            timeline: The timeline object to remove the label from.
            label: The label string to remove.

        Returns:
            True if the label was successfully removed, False otherwise.
            Returns False if the label does not exist on the timeline.
        """
        if not timeline.has_label(label):
            logger.warning(
                "Unable to remove the label [%s] from timeline (ID: %d), label does "
                "not exist.",
                label,
                timeline.id,
            )
            return False
        timeline.remove_label(label)
        return True

    @login_required
    def get(self, sketch_id: int, timeline_id: int):
        """Handles GET requests for a specific timeline within a sketch.

        This method retrieves a specific timeline by its ID within a given sketch.
        It verifies that both the sketch and the timeline exist, that the timeline
        belongs to the sketch, and that the current user has read permission for
        the sketch. It also fetches metadata about the timeline, such as the number
        of indexed events.

        Args:
            sketch_id (int): The ID of the sketch.
            timeline_id (int): The ID of the timeline to retrieve.

        Returns:
            flask.wrappers.Response: A JSON response containing the timeline object
                and metadata. The metadata includes the number of indexed events
                in the timeline.

        Raises:
            HTTP_STATUS_CODE_NOT_FOUND: If the sketch or timeline is not found, or
                if the timeline does not belong to the sketch.
            HTTP_STATUS_CODE_FORBIDDEN: If the user does not have read permission
                on the sketch.
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
                f"The sketch ID ({sketch.id:d}) does not match with the timeline "
                f"sketch ID ({timeline.sketch.id:d})",
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
                    "fields": [{"field": "message", "type": "text"}],
                },
                query_dsl=None,
                indices=[timeline.searchindex.index_name],
                timeline_ids=[timeline.id],
                count=True,
            )
            meta["lines_indexed"] = result

        return self.to_json(timeline, meta=meta)

    @login_required
    def post(self, sketch_id: int, timeline_id: int):
        """Handles POST requests to modify an existing timeline.

        This method allows for updating the properties of a timeline, such as
        its name, description, and color. It also supports adding or removing
        labels from the timeline. The method verifies that the sketch and
        timeline exist, that the timeline belongs to the sketch, and that the
        current user has write permission on the sketch.

        Args:
            sketch_id (int): The ID of the sketch to which the timeline belongs.
            timeline_id (int): The ID of the timeline to modify.

        Returns:
            flask.wrappers.Response:
                - HTTP_STATUS_CODE_OK (200): If the timeline is successfully
                modified.
                - HTTP_STATUS_CODE_BAD_REQUEST (400): If the form data is
                invalid or if there's an issue with the label action or
                label format.
                - HTTP_STATUS_CODE_NOT_FOUND (404): If the sketch or timeline
                is not found.
                - HTTP_STATUS_CODE_FORBIDDEN (403): If the user does not have
                write permission on the sketch.

        Raises:
            HTTP_STATUS_CODE_BAD_REQUEST: If the form data is invalid, if the
                label action is not "add" or "remove", or if the label format
                is incorrect.
            HTTP_STATUS_CODE_NOT_FOUND: If the sketch or timeline is not found,
                or if the timeline does not belong to the sketch.
            HTTP_STATUS_CODE_FORBIDDEN: If the user does not have write
                permission on the sketch.
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
                f"The sketch ID ({sketch.id:d}) does not match with the timeline "
                f"sketch ID ({timeline.sketch.id:d})",
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
            if not all(isinstance(x, str) for x in labels):
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
                msg = ", ".join(labels)
                abort(
                    HTTP_STATUS_CODE_BAD_REQUEST,
                    f"Label [{msg:s}] not {label_action:s}",
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
    def delete(self, sketch_id: int, timeline_id: int):
        """Deletes a timeline from a sketch. If the timeline's search index is not
        used by any other timelines or in other sketches, the search index will
        also be closed and archived.

        Args:
            sketch_id: (int) Integer primary key for a sketch database model
            timeline_id: (int) Integer primary key for a timeline database model

        Raises:
            HTTP_STATUS_CODE_NOT_FOUND: If the sketch or timeline is not found.
            HTTP_STATUS_CODE_FORBIDDEN: If the user does not have write
                permission on the sketch or if the timeline has a label that
                prevents deletion.
            HTTP_STATUS_CODE_INTERNAL_SERVER_ERROR: If there is an error
                closing the search index.
        Returns:
            HTTP_STATUS_CODE_OK: If the timeline is successfully deleted.
        Behavior:
            - Checks if the sketch and timeline exist.
            - Verifies the user has write permission on the sketch.
            - Prevents deletion if the timeline has a label in the
              LABELS_TO_PREVENT_DELETION config.
            - Closes and archives the search index if it's not used by other
              timelines in other sketches.
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
                    f"The sketch ID ({sketch_string:s}) does not match with the "
                    f"timeline sketch ID ({timeline_string:s})"
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
                    f"Timelines with label [{label:s}] cannot be deleted.",
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

        if close_index:
            try:
                self.datastore.client.indices.close(index=searchindex.index_name)
            except opensearchpy.NotFoundError:
                logger.error(
                    "Unable to close index: %s - index not found",
                    searchindex.index_name,
                )
            except opensearchpy.RequestError as e:
                error_msg = (
                    f"RequestError when closing index {searchindex.index_name:s}"
                    " - please try again in 5 min or contact your admin. "
                    f"Error: {e:s}"
                )
                logger.error(error_msg)
                abort(HTTP_STATUS_CODE_INTERNAL_SERVER_ERROR, error_msg)

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
        """Handles POST requests to create a new timeline.

        This method processes a POST request to create a new timeline. It
        validates the incoming form data, creates a new search index, and
        optionally associates the timeline with an existing sketch.

        Returns:
            flask.wrappers.Response: A JSON response containing the newly
                created timeline or search index object.
                - HTTP_STATUS_CODE_CREATED (201): If the timeline or search
                  index is successfully created.
                - HTTP_STATUS_CODE_BAD_REQUEST (400): If the upload is not
                  enabled or if the form data is invalid.
                - HTTP_STATUS_CODE_NOT_FOUND (404): If the specified sketch
                  is not found.
                - HTTP_STATUS_CODE_FORBIDDEN (403): If the user does not have
                  write access to the sketch.

        Raises:
            HTTP_STATUS_CODE_BAD_REQUEST: If the upload is not enabled or if
                the form data is invalid.
            HTTP_STATUS_CODE_NOT_FOUND: If the specified sketch is not found.
            HTTP_STATUS_CODE_FORBIDDEN: If the user does not have write
                access to the sketch.
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
        if not isinstance(index_name, str):
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
        # pylint: disable=no-else-return
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
