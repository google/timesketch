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
"""This module holds archive API calls for version 1 of the Timesketch API."""


import datetime
import io
import json
import logging
import zipfile

import opensearchpy

from flask import abort
from flask import current_app
from flask import jsonify
from flask import request
from flask import send_file
from flask_login import current_user
from flask_login import login_required
from flask_restful import Resource

import pandas as pd

from timesketch import version
from timesketch.api.v1 import export
from timesketch.api.v1 import resources
from timesketch.api.v1 import utils
from timesketch.lib.definitions import HTTP_STATUS_CODE_BAD_REQUEST
from timesketch.lib.definitions import HTTP_STATUS_CODE_FORBIDDEN
from timesketch.lib.definitions import HTTP_STATUS_CODE_NOT_FOUND
from timesketch.lib.definitions import HTTP_STATUS_CODE_INTERNAL_SERVER_ERROR

from timesketch.lib.stories import manager as story_export_manager
from timesketch.models import db_session
from timesketch.models.sketch import Event
from timesketch.models.sketch import Sketch


logger = logging.getLogger("timesketch.api_archive")


class SketchArchiveResource(resources.ResourceMixin, Resource):
    """Resource to archive a sketch."""

    DEFAULT_QUERY_FILTER = {"size": 10000, "terminate_after": 10000}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._sketch = None
        self._sketch_indices = None

    @property
    def sketch_indices(self):
        """Returns a set of sketch indices that are ready."""
        if not self._sketch_indices:
            if not self._sketch:
                return set()

            self._sketch_indices = {
                t.searchindex.index_name
                for t in self._sketch.timelines
                if t.get_status.status.lower() == "ready"
            }
        return self._sketch_indices

    @login_required
    def get(self, sketch_id):
        """Handles GET request to the resource.

        Retrieves archiving status and basic information for a given sketch.
        This includes whether the sketch is archived, its ID, its name,
        and the archival status of its associated timelines.

        Returns:
            A flask.wrappers.Response object with a JSON payload.
            The JSON payload has a "meta" object containing:
                - is_archived (bool): True if the sketch is archived, False otherwise.
                - sketch_id (int): The ID of the sketch.
                - sketch_name (str): The name of the sketch.
                - timelines (dict): A dictionary where keys are timeline index names
                                    and values are booleans (True if archived).
            And an empty "objects" list.

        Raises:
            HTTP_STATUS_CODE_NOT_FOUND: If no sketch is found with the given ID.
            HTTP_STATUS_CODE_FORBIDDEN: If the user does not have read permission
                                        for the sketch (and is not an admin).
        """
        if current_user.admin:
            sketch = Sketch.get_by_id(sketch_id)
        else:
            sketch = Sketch.get_with_acl(sketch_id)

        if not sketch:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No sketch found with this ID.")

        if not sketch.has_permission(current_user, "read"):
            if not current_user.admin:
                abort(
                    HTTP_STATUS_CODE_FORBIDDEN,
                    (
                        "User does not have sufficient access rights to "
                        "read the sketch."
                    ),
                )

        timelines = {
            t.searchindex.index_name: t.get_status.status == "archived"
            for t in sketch.timelines
        }

        meta = {
            "is_archived": sketch.get_status.status == "archived",
            "sketch_id": sketch.id,
            "sketch_name": sketch.name,
            "timelines": timelines,
        }
        schema = {"meta": meta, "objects": []}
        return jsonify(schema)

    @login_required
    def post(self, sketch_id):
        """Handles POST request to the resource.

        Returns:
            A sketch in JSON (instance of flask.wrappers.Response)
        """
        if current_user.admin:
            sketch = Sketch.get_by_id(sketch_id)
        else:
            sketch = Sketch.get_with_acl(sketch_id)

        if not sketch:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No sketch found with this ID.")

        self._sketch = sketch
        form = request.json
        if not form:
            form = request.data

        action = form.get("action", "")
        if action == "archive":
            if not sketch.has_permission(current_user, "delete"):
                if not current_user.admin:
                    abort(
                        HTTP_STATUS_CODE_FORBIDDEN,
                        "User does not have sufficient access rights to "
                        "delete a sketch.",
                    )

            return self._archive_sketch(sketch)

        if action == "export":
            if not sketch.has_permission(current_user, "read"):
                abort(
                    HTTP_STATUS_CODE_FORBIDDEN,
                    "User does not have sufficient access rights to "
                    "read from a sketch.",
                )

            return self._export_sketch(sketch)

        if action == "unarchive":
            if not sketch.has_permission(current_user, "delete"):
                if not current_user.admin:
                    abort(
                        HTTP_STATUS_CODE_FORBIDDEN,
                        "User does not have sufficient access rights to "
                        "unarchive a sketch.",
                    )

            return self._unarchive_sketch(sketch)

        return abort(
            HTTP_STATUS_CODE_NOT_FOUND,
            f"The action: [{action:s}] is not supported.",
        )

    def _get_all_events_with_a_label(self, label: str, sketch: Sketch):
        """Returns a DataFrame with events in a sketch with a certain label.

        Args:
            label (string): the label string to search for.
            sketch (timesketch.models.sketch.Sketch): a sketch object.

        Returns:
            pd.DataFrame: a pandas DataFrame with all the events in the
                datastore that have a label.
        """
        query_dsl = {
            "query": {
                "nested": {
                    "path": "timesketch_label",
                    "query": {
                        "bool": {
                            "must": [
                                {"term": {"timesketch_label.name": label}},
                                {"term": {"timesketch_label.sketch_id": sketch.id}},
                            ]
                        }
                    },
                }
            }
        }
        result = self.datastore.search(
            sketch_id=sketch.id,
            query_string="",
            query_filter=self.DEFAULT_QUERY_FILTER,
            query_dsl=json.dumps(query_dsl),
            indices=self.sketch_indices,
        )

        return export.query_results_to_dataframe(result, sketch)

    def _export_events_with_comments(self, sketch, zip_file):
        """Export all events that have comments and store in a ZIP file."""
        db_events = Event.query.filter_by(sketch_id=sketch.id).all()
        lines = []
        for db_event in db_events:
            for comment in db_event.comments:
                line = {
                    "_index": db_event.searchindex.index_name,
                    "_id": db_event.document_id,
                    "comment": comment.comment,
                    "comment_date": comment.created_at,
                }
                if not comment.user:
                    line["username"] = "System"
                else:
                    line["username"] = comment.user.username
                lines.append(line)
        db_frame = pd.DataFrame(lines)

        size = db_frame.shape[0]
        if not size:
            return

        event_frame = self._get_all_events_with_a_label("__ts_comment", sketch)
        frame = event_frame.merge(db_frame, on=["_index", "_id"])

        string_io = io.StringIO()
        frame.to_csv(string_io, index=False)
        string_io.seek(0)
        zip_file.writestr("events/events_with_comments.csv", data=string_io.read())

    def _export_starred_events(self, sketch, zip_file):
        """Export all events that have been starred and store in a ZIP file."""
        event_frame = self._get_all_events_with_a_label("__ts_star", sketch)

        string_io = io.StringIO()
        event_frame.to_csv(string_io, index=False)
        string_io.seek(0)
        zip_file.writestr("events/starred_events.csv", data=string_io.read())

    def _export_tagged_events(self, sketch, zip_file):
        """Export all events that have been tagged and store in a ZIP file."""
        result = self.datastore.search(
            sketch_id=sketch.id,
            query_string="_exists_:tag",
            query_filter=self.DEFAULT_QUERY_FILTER,
            query_dsl="",
            indices=self.sketch_indices,
        )

        fh = export.query_results_to_filehandle(result, sketch)
        zip_file.writestr("events/tagged_events.csv", data=fh.read())

        parameters = {
            "limit": 100,
            "field": "tag",
        }
        result_obj, meta = utils.run_aggregator(
            sketch.id, aggregator_name="field_bucket", aggregator_parameters=parameters
        )

        zip_file.writestr("events/tagged_event_stats.meta", data=json.dumps(meta))

        html = result_obj.to_chart(
            chart_name="hbarchart",
            chart_title="Top 100 identified tags",
            interactive=True,
            as_html=True,
        )
        zip_file.writestr("events/tagged_event_stats.html", data=html)

        string_io = io.StringIO()
        data_frame = result_obj.to_pandas()
        data_frame.to_csv(string_io, index=False)
        string_io.seek(0)
        zip_file.writestr("events/tagged_event_stats.csv", data=string_io.read())

    def _export_sketch(self, sketch: Sketch):
        """Returns a ZIP file with the exported content of a sketch."""
        file_object = io.BytesIO()
        sketch_is_archived = sketch.get_status.status == "archived"

        if sketch_is_archived:
            _ = self._unarchive_sketch(sketch)

        story_exporter = story_export_manager.StoryExportManager.get_exporter("html")

        meta = {
            "user": current_user.username,
            "time": datetime.datetime.utcnow().isoformat(),
            "sketch_id": sketch.id,
            "sketch_name": sketch.name,
            "sketch_description": sketch.description,
            "timesketch_version": version.get_version(),
        }

        with zipfile.ZipFile(file_object, mode="w") as zip_file:
            zip_file.writestr("METADATA", data=json.dumps(meta))

            for story in sketch.stories:
                export.export_story(story, sketch, story_exporter, zip_file)

            for aggregation in sketch.aggregations:
                export.export_aggregation(aggregation, sketch, zip_file)

            for view in sketch.views:
                self._export_view(view, sketch, zip_file)

            for group in sketch.aggregationgroups:
                export.export_aggregation_group(group, sketch, zip_file)

            self._export_events_with_comments(sketch, zip_file)
            self._export_starred_events(sketch, zip_file)
            self._export_tagged_events(sketch, zip_file)

            # TODO (kiddi): Add in aggregation group support.

        if sketch_is_archived:
            _ = self._archive_sketch(sketch)

        file_object.seek(0)
        return send_file(
            file_object, mimetype="zip", download_name="timesketch_export.zip"
        )

    def _export_view(self, view, sketch, zip_file):
        """Export a view from a sketch and write it to a ZIP file.

        Args:
            view (timesketch.models.sketch.View): a View object.
            sketch (timesketch.models.sketch.Sketch): a sketch object.
            zip_file (ZipFile): a zip file handle that can be used to write
                content to.
        """
        name = f"{view.id:04d}_{view.name:s}"
        query_filter = None

        if view.query_filter:
            query_filter = json.loads(view.query_filter)

        if not query_filter:
            query_filter = self.DEFAULT_QUERY_FILTER

        indices = self.sketch_indices

        # Ignoring the size limits in views to reduce the amount of queries
        # needed to get all the data.
        query_filter["terminate_after"] = 10000
        query_filter["size"] = 10000

        query_dsl = view.query_dsl
        if query_dsl:
            query_dict = json.loads(query_dsl)
            if not query_dict:
                query_dsl = None

        result = self.datastore.search(
            sketch_id=sketch.id,
            query_string=view.query_string,
            query_filter=query_filter,
            query_dsl=query_dsl,
            enable_scroll=True,
            indices=indices,
        )

        scroll_id = result.get("_scroll_id", "")
        if scroll_id:
            data_frame = export.query_results_to_dataframe(result, sketch)

            total_count = result.get("hits", {}).get("total", {}).get("value", 0)

            if isinstance(total_count, str):
                try:
                    total_count = int(total_count, 10)
                except ValueError:
                    total_count = 0

            event_count = len(result["hits"]["hits"])

            while event_count < total_count:
                # pylint: disable=unexpected-keyword-arg
                result = self.datastore.client.scroll(scroll_id=scroll_id, scroll="1m")
                event_count += len(result["hits"]["hits"])
                add_frame = export.query_results_to_dataframe(result, sketch)
                if add_frame.shape[0]:
                    data_frame = pd.concat([data_frame, add_frame], sort=False)
                else:
                    logger.warning(
                        "Data Frame returned from a search operation was "
                        "empty, count {:d} out of {:d} total. Query is: "
                        '"{:s}"'.format(
                            event_count, total_count, view.query_string or query_dsl
                        )
                    )

            fh = io.StringIO()
            data_frame.to_csv(fh, index=False)
            fh.seek(0)
        else:
            fh = export.query_results_to_filehandle(result, sketch)

        zip_file.writestr(f"views/{name:s}.csv", data=fh.read())

        if not view.user:
            username = "System"
        else:
            username = view.user.username
        meta = {
            "name": view.name,
            "view_id": view.id,
            "description": view.description,
            "query_string": view.query_string,
            "query_filter": view.query_filter,
            "query_dsl": view.query_dsl,
            "username": username,
            "sketch_id": view.sketch_id,
        }
        zip_file.writestr(f"views/{name:s}.meta", data=json.dumps(meta))

    def _archive_sketch(self, sketch: Sketch):
        """Archives a sketch. This involves:

        1. Setting the sketch status to 'archived'.
        2. For each SearchIndex associated with the sketch:
          the system attempts to close the corresponding OpenSearch index.
           - If the OpenSearch index is successfully closed, the SearchIndex's
             database status is set to 'archived'.
           - If the OpenSearch index is not found, it's considered effectively
             closed, and the SearchIndex's database status is set to 'fail'.
           - If the OpenSearch index exists but an error occurs during the close
             operation (other than not found), the SearchIndex's database status
             remains unchanged (e.g., 'ready' or 'fail'). This discrepancy allows
             tools like `tsctl list-sketches --archived-with-open-indexes`
             to identify potential issues requiring administrative attention.

        This is a non-destructive operation; it does not delete any event data.

        Args:
            sketch (Sketch): Instance of timesketch.models.sketch.Sketch
        """
        # 1. Pre flight checks
        if sketch.get_status.status == "archived":
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                f"Sketch {sketch.id} is already archived.",
            )

        labels_to_prevent_deletion = current_app.config.get(
            "LABELS_TO_PREVENT_DELETION", []
        )

        for label in labels_to_prevent_deletion:
            if sketch.has_label(label):
                abort(
                    HTTP_STATUS_CODE_FORBIDDEN,
                    f"Sketch {sketch.id} has label '{label}'"
                    " and cannot be archived.",
                )

        errors_occurred = False
        error_details = []

        # Check if any timeline is in a state that prevents archiving.
        statuses_preventing_archival = ["processing", "fail", "timeout"]
        for timeline_to_check in sketch.timelines:
            timeline_status = timeline_to_check.get_status.status
            if timeline_status in statuses_preventing_archival:
                base_error_msg = (
                    f"Cannot archive sketch {sketch.id}. Timeline "
                    f" (ID: {timeline_to_check.id}) is in "
                    f"a non-archivable state: '{timeline_status}'."
                )
                suggestion = ""
                if timeline_status in ["fail", "timeout"]:
                    suggestion = " Please delete this timeline and try again."
                elif timeline_status == "processing":
                    suggestion = (
                        " Please wait for it to finish processing. If it seems to be "
                        "stuck, contact your system administrator to resolve the "
                        "issue."
                    )
                error_msg = f"{base_error_msg} {suggestion}"
                logger.error(error_msg)
                errors_occurred = True
                # Add the timeline name only to the error the user gets back
                error_msg = (
                    f"{base_error_msg} "
                    f"Timeline name: {timeline_to_check.name} {suggestion}"
                )
                abort(
                    HTTP_STATUS_CODE_BAD_REQUEST,
                    error_msg,
                )

        # 2. Determine which OpenSearch indices can be closed.
        search_indexes_to_evaluate = {t.searchindex for t in sketch.timelines}
        search_indexes_to_evaluate = {
            t.searchindex for t in sketch.timelines if t.searchindex
        }
        search_indexes_to_close = set()
        for search_index in search_indexes_to_evaluate:
            can_be_closed = True
            if not search_index:
                continue
            for timeline in search_index.timelines:
                # If the timeline is in the sketch we are currently archiving,
                # we can ignore its current status, as it's about to be archived.
                if timeline.sketch_id == sketch.id:
                    continue

                # If a timeline is in another sketch, it must already be archived.
                if timeline.get_status.status != "archived":
                    can_be_closed = False
                    logger.info(
                        "SearchIndex %s (ID: %s) will not be closed because "
                        "associated timeline %s (sketch %s) has status '%s'.",
                        search_index.index_name,
                        search_index.id,
                        timeline.id,
                        timeline.sketch_id,
                        timeline.get_status.status,
                    )
                    break
            if can_be_closed:
                search_indexes_to_close.add(search_index)

        # 3. Attempt to close all necessary OpenSearch indices first.
        successfully_closed_indexes = set()
        failed_to_find_indexes = set()

        # Re-check for non-archivable states before proceeding
        for timeline_to_check in sketch.timelines:
            timeline_status = timeline_to_check.get_status.status
            if timeline_status in statuses_preventing_archival:
                base_error_msg = (
                    f"Cannot archive sketch {sketch.id}. Timeline "
                    f"(ID: {timeline_to_check.id}) is in "
                    f"a non-archivable state: '{timeline_status}'."
                )
                suggestion = ""
                if timeline_status in ["fail", "timeout"]:
                    suggestion = " Please delete this timeline and try again."
                error_msg = f"{base_error_msg}{suggestion}"
                errors_occurred = True
                abort(
                    HTTP_STATUS_CODE_BAD_REQUEST,
                    error_msg,
                )

        for search_index in search_indexes_to_close:
            try:
                self.datastore.client.indices.close(index=search_index.index_name)
                successfully_closed_indexes.add(search_index)
            except opensearchpy.exceptions.NotFoundError:
                failed_to_find_indexes.add(search_index)
                error_message = (
                    "OpenSearch index %s not found while trying to close it.",
                    search_index.index_name,
                )
                logger.warning(error_message)
                error_details.append(error_message)
                errors_occurred = True
                abort(
                    HTTP_STATUS_CODE_BAD_REQUEST,
                    error_message,
                )
            except Exception as e:  # pylint: disable=broad-except
                errors_occurred = True
                error_details.append(
                    f"Failed to close index {search_index.index_name}: {e}"
                )
        # If any critical error occurred, abort before changing DB state.
        if errors_occurred:
            logger.error(error_details)
            abort(
                HTTP_STATUS_CODE_INTERNAL_SERVER_ERROR,
                f"Failed to archive sketch. Details: {'; '.join(error_details)}",
            )

        # 4. If all indices are closed, update the database statuses.
        sketch.set_status(status="archived")
        for timeline in sketch.timelines:
            timeline.set_status(status="archived")
            logger.debug(
                "Sketch %s Timeline %s status set to 'archived'.",
                sketch.id,
                timeline.id,
            )
        for search_index in successfully_closed_indexes:
            search_index.set_status(status="archived")
            logger.debug(
                "Sketch %s search_index %s status set to 'archived'.",
                sketch.id,
                search_index.id,
            )
        for search_index in failed_to_find_indexes:
            search_index.set_status(status="fail")
            logger.debug(
                "Sketch %s search_index %s status set to 'fail'.",
                sketch.id,
                search_index.id,
            )
        logger.info("Sketch %s status set to 'archived'.", sketch.id)

        # Commit changes after processing all indices
        db_session.commit()

        return jsonify({"message": f"Sketch {sketch.id} has been archived."})

    def _unarchive_sketch(self, sketch: Sketch):
        """Unarchives a sketch, making it and its data active again.

        This method follows a transactional approach to ensure data consistency.
        It first attempts to open all necessary OpenSearch indices associated
        with the sketch's archived timelines. If any index fails to open for a
        critical reason (e.g., not found), the entire operation is aborted,
        leaving the sketch in its archived state.

        If all indices are successfully opened (or confirmed to be already open),
        the method proceeds to update the database, setting the status of the
        sketch, its timelines, and the corresponding SearchIndex objects to 'ready'.

        Args:
            sketch: An instance of timesketch.models.sketch.Sketch to unarchive.

        Returns:
            An integer representing the HTTP status of the operation.
            - HTTP_STATUS_CODE_OK if successful.

        Raises:
            HTTPException:
                - If the sketch is not currently archived.
                - If a critical error occurs while opening an OpenSearch index.
        """
        logger.info("Unarchiving sketch '%s'.", sketch.id)

        # 1. Pre-flight checks
        if sketch.get_status.status != "archived":
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                "Unable to unarchive a sketch that wasn't already archived "
                f"(sketch: {sketch.id})",
            )

        errors_occurred = False
        error_details = []

        # Check if any timeline is in a state that would prevents unarchiving.
        # TODO enforce after 2026-01-01
        # https://github.com/google/timesketch/issues/3518
        statuses_preventing_unarchival = ["processing", "fail"]
        for timeline in sketch.timelines:
            timeline_status = timeline.get_status.status
            if timeline_status in statuses_preventing_unarchival:
                base_warning_msg = (
                    f"Unarchiving sketch {sketch.id}, but it contains timeline "
                    f" (ID: {timeline.id}) in a '{timeline_status}' "
                    "state. "
                )
                specific_advice = ""
                if timeline_status == "fail":
                    specific_advice = (
                        "It is recommended to fix this timeline (e.g., by deleting it) "
                        "because the sketch cannot be archived again in this state."
                    )
                elif timeline_status == "processing":
                    specific_advice = (
                        "It seems to be stuck, "
                        "contact your system administrator to resolve the issue."
                    )

                general_advice = " You can use 'tsctl find-inconsistent-archives' to find such sketches."  # pylint: disable=line-too-long
                warning_msg = f"{base_warning_msg}{specific_advice}{general_advice}"
                error_details.append(warning_msg)
                errors_occurred = True

        if errors_occurred:
            logger.error(
                "Unarchiving sketch %s failed because one or more indices could not "
                "be opened. Errors: %s",
                sketch.id,
                "; ".join(error_details),
            )
            # TODO: enforce here: https://github.com/google/timesketch/issues/3518
            # abort(...

        # Identify all SearchIndex objects that need to be opened.
        search_indexes_to_open = {
            tl.searchindex
            for tl in sketch.timelines
            if tl.searchindex and tl.searchindex.get_status.status == "archived"
        }

        # 3. Attempt to open all necessary OpenSearch indices first.
        successfully_opened_indexes = set()

        for search_index in search_indexes_to_open:
            try:
                logger.info(
                    "Attempting to open OpenSearch index: %s (DB ID: %s)"
                    " for sketch %s.",
                    search_index.index_name,
                    search_index.id,
                    sketch.id,
                )
                self.datastore.client.indices.open(index=search_index.index_name)
                logger.info(
                    "Successfully opened OpenSearch index: %s.",
                    search_index.index_name,
                )
                successfully_opened_indexes.add(search_index)
            except opensearchpy.exceptions.RequestError as e:
                if e.error == "index_not_closed_exception":
                    logger.warning(
                        "OpenSearch index %s was already open.",
                        search_index.index_name,
                    )
                    successfully_opened_indexes.add(search_index)
                else:
                    errors_occurred = True
                    error_details.append(
                        f"Failed to open OpenSearch index '{search_index.index_name}' "
                        f"(DB ID: {search_index.id}). Error: {str(e)}."
                    )
            except opensearchpy.exceptions.NotFoundError:
                errors_occurred = True
                error_details.append(
                    f"OpenSearch index '{search_index.index_name}' not found. "
                    "Cannot unarchive."
                )
            except Exception as e:  # pylint: disable=broad-except
                errors_occurred = True
                error_details.append(
                    "An unexpected error occurred while opening index "
                    f"'{search_index.index_name}' (DB ID: {search_index.id}): {str(e)}."
                )

        # If any critical error occurred, abort before changing DB state.
        if errors_occurred:
            logger.error(
                "Unarchiving sketch %s failed because one or more indices could not "
                "be opened. Errors: %s",
                sketch.id,
                "; ".join(error_details),
            )
            abort(
                HTTP_STATUS_CODE_INTERNAL_SERVER_ERROR,
                "Failed to unarchive sketch. One or more OpenSearch indices could not "
                f"be opened. Details: {'; '.join(error_details)}",
            )

        # 4. If all indices are open, update the database statuses.
        # Set all timelines in the sketch to ready.
        for timeline in sketch.timelines:
            if timeline.get_status.status != "archived":
                continue
            timeline.set_status(status="ready")
            logger.info(
                "Timeline '%s' status set to 'ready'.",
                timeline.id,
            )

        for search_index in successfully_opened_indexes:
            search_index.set_status(status="ready")
            logger.info(
                "SearchIndex DB object %s (ID: %s) status updated to 'ready'.",
                search_index.index_name,
                search_index.id,
            )

        sketch.set_status(status="ready")
        logger.info("Sketch %s status set to 'ready'.", sketch.id)

        db_session.commit()
        logger.info("Unarchiving of sketch %s complete.", sketch.id)

        return jsonify({"message": f"Sketch {sketch.id} has been unarchived."})
