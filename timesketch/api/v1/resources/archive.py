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

from __future__ import unicode_literals

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
from timesketch.lib.definitions import HTTP_STATUS_CODE_OK
from timesketch.lib.stories import manager as story_export_manager
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

        Returns:
            A sketch in JSON (instance of flask.wrappers.Response)
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
            "The action: [{0:s}] is not supported.".format(action),
        )

    def _get_all_events_with_a_label(self, label, sketch):
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

    def _export_sketch(self, sketch):
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
        name = "{0:04d}_{1:s}".format(view.id, view.name)

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
                        "empty, count {0:d} out of {1:d} total. Query is: "
                        '"{2:s}"'.format(
                            event_count, total_count, view.query_string or query_dsl
                        )
                    )

            fh = io.StringIO()
            data_frame.to_csv(fh, index=False)
            fh.seek(0)
        else:
            fh = export.query_results_to_filehandle(result, sketch)

        zip_file.writestr("views/{0:s}.csv".format(name), data=fh.read())

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
        zip_file.writestr("views/{0:s}.meta".format(name), data=json.dumps(meta))

    def _unarchive_sketch(self, sketch):
        """Unarchives a sketch by opening up all indices and removing labels.

        Args:
            sketch: Instance of timesketch.models.sketch.Sketch
        """
        if sketch.get_status.status != "archived":
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                "Unable to unarchive a sketch that wasn't already archived "
                "(sketch: {0:d})".format(sketch.id),
            )

        sketch.set_status(status="ready")

        indexes_to_open = []
        for timeline in sketch.timelines:
            if timeline.get_status.status != "archived":
                continue
            timeline.set_status(status="ready")
            search_index = timeline.searchindex
            search_index.set_status(status="ready")
            indexes_to_open.append(search_index.index_name)

        # TODO (kiddi): Move this to lib/datastores/opensearch.py.
        if indexes_to_open:
            try:
                self.datastore.client.indices.open(",".join(indexes_to_open))
            except opensearchpy.NotFoundError:
                logger.error(
                    "Unable to open index, not found: {0:s}".format(
                        ",".join(indexes_to_open)
                    )
                )

        return HTTP_STATUS_CODE_OK

    def _archive_sketch(self, sketch):
        """Unarchives a sketch by opening up all indices and removing labels.

        Args:
            sketch: Instance of timesketch.models.sketch.Sketch
        """
        if sketch.get_status.status == "archived":
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                "Unable to archive a sketch that was already archived "
                "(sketch: {0:d})".format(sketch.id),
            )

        labels_to_prevent_deletion = current_app.config.get(
            "LABELS_TO_PREVENT_DELETION", []
        )

        for label in labels_to_prevent_deletion:
            if sketch.has_label(label):
                abort(
                    HTTP_STATUS_CODE_FORBIDDEN,
                    "A sketch with the label {0:s} cannot be "
                    "archived.".format(label),
                )

        sketch.set_status(status="archived")

        # Go through all timelines in a sketch.
        #    Each timeline has only a single search index, however
        #    each search index can be part of multiple timelines.
        #    Only archive a search index if all of it's timelines
        #    are archived.
        indexes_to_close = []
        for timeline in sketch.timelines:
            if timeline.get_status.status != "ready":
                continue
            timeline.set_status(status="archived")
            search_index = timeline.searchindex

            if not all(
                [x.get_status.status == "archived" for x in search_index.timelines]
            ):
                continue
            search_index.set_status(status="archived")
            indexes_to_close.append(search_index.index_name)

        # TODO (kiddi): Move this to lib/datastores/opensearch.py.
        if indexes_to_close:
            try:
                self.datastore.client.indices.close(",".join(indexes_to_close))
            except opensearchpy.NotFoundError:
                logger.error(
                    "Unable to close indices, not found: {0:s}".format(
                        ",".join(indexes_to_close)
                    )
                )
        return HTTP_STATUS_CODE_OK
