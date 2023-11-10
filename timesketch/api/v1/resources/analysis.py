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
"""Analysis resources for version 1 of the Timesketch API."""
import fnmatch
import collections
import logging

import prometheus_client

from flask import jsonify
from flask import request
from flask import abort
from flask_restful import Resource
from flask_restful import reqparse
from flask_login import login_required
from flask_login import current_user

from timesketch.api.v1 import resources
from timesketch.lib.analyzers import manager as analyzer_manager
from timesketch.lib.definitions import HTTP_STATUS_CODE_BAD_REQUEST
from timesketch.lib.definitions import HTTP_STATUS_CODE_FORBIDDEN
from timesketch.lib.definitions import HTTP_STATUS_CODE_NOT_FOUND
from timesketch.lib.definitions import METRICS_NAMESPACE
from timesketch.models.sketch import Analysis
from timesketch.models.sketch import AnalysisSession
from timesketch.models.sketch import Sketch
from timesketch.models.sketch import Timeline

# Metrics definitions
METRICS = {
    "analyzer_run": prometheus_client.Counter(
        "timesketch_analyzer_run",
        "Number of runs per analyzer",
        ["name"],
        namespace=METRICS_NAMESPACE,
    )
}

# Set up logging
logger = logging.getLogger("timesketch.analysis_api")


class AnalysisResource(resources.ResourceMixin, Resource):
    """Resource to get analyzer session."""

    @login_required
    def get(self, sketch_id, timeline_id):
        """Handles GET request to the resource.

        Returns:
            An analysis in JSON (instance of flask.wrappers.Response)
        """
        sketch = Sketch.get_with_acl(sketch_id)
        if not sketch:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No sketch found with this ID.")

        if not sketch.has_permission(current_user, "read"):
            abort(
                HTTP_STATUS_CODE_FORBIDDEN, "User does not have read access to sketch"
            )

        timeline = Timeline.get_by_id(timeline_id)
        if not timeline:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No timeline found with this ID.")

        analysis_history = Analysis.query.filter_by(timeline=timeline).all()

        return self.to_json(analysis_history)


class AnalyzerSessionActiveListResource(resources.ResourceMixin, Resource):
    """Resource to get active analyzer sessions."""

    def __init__(self):
        super().__init__()
        self.parser = reqparse.RequestParser()
        self.parser.add_argument(
            "include_details", type=str, required=False, location="args"
        )

    @login_required
    def get(self, sketch_id):
        """Handles GET request to the resource.

        Returns:
            A analyzer session in JSON (instance of flask.wrappers.Response)
        """
        sketch = Sketch.get_with_acl(sketch_id)

        if not sketch:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No sketch found with this ID.")

        if not sketch.has_permission(current_user, "read"):
            abort(
                HTTP_STATUS_CODE_FORBIDDEN, "User does not have read access to sketch"
            )

        # Retrive request argument
        args = self.parser.parse_args()
        include_details = False
        if args.get("include_details"):
            if args.get("include_details").lower() == "true":
                include_details = True

        counter = collections.Counter(PENDING=0, STARTED=0, ERROR=0, DONE=0)
        session_ids = set()
        detailed_sessions = [] if include_details else False

        active_sessions = sketch.get_active_analysis_sessions()
        for session in active_sessions:
            if include_details:
                detailed_sessions.append(self.to_json(session).get_json())
            session_ids.add(session.id)
            for analysis in session.analyses:
                counter[analysis.get_status.status] += 1

        if detailed_sessions:
            detailed_sessions = list(detailed_sessions)

        schema = {
            "objects": [
                {
                    "total_tasks": sum(counter.values()),
                    "total_sessions": len(active_sessions),
                    "tasks_status_count": counter,
                    "sessions": list(session_ids),
                    "detailed_sessions": detailed_sessions,
                }
            ]
        }
        return jsonify(schema)


class AnalyzerSessionResource(resources.ResourceMixin, Resource):
    """Resource to get analyzer session."""

    @login_required
    def get(self, sketch_id, session_id):
        """Handles GET request to the resource.

        Returns:
            A analyzer session in JSON (instance of flask.wrappers.Response)
        """
        sketch = Sketch.get_with_acl(sketch_id)

        if not sketch:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No sketch found with this ID.")

        if not sketch.has_permission(current_user, "read"):
            abort(
                HTTP_STATUS_CODE_FORBIDDEN, "User does not have read access to sketch"
            )

        analysis_session = AnalysisSession.get_by_id(session_id)

        return self.to_json(analysis_session)


class AnalyzerRunResource(resources.ResourceMixin, Resource):
    """Resource to list or run analyzers for sketch."""

    @login_required
    def get(self, sketch_id):
        """Handles GET request to the resource.

        Returns:
            A list of dicts with all available analyzers with the following fields:
              * name: Short name of the analyzer
              * display_name: Display name of the analyzer for the UI
              * description: Description of the analyzer provided in the class
              * is_multi: Boolean indicating if the analyzer is a multi analyzer
        """
        sketch = Sketch.get_with_acl(sketch_id)
        if not sketch:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No sketch found with this ID.")
        if not sketch.has_permission(current_user, "read"):
            abort(
                HTTP_STATUS_CODE_FORBIDDEN, "User does not have read access to sketch"
            )
        analyzers = [x for x, y in analyzer_manager.AnalysisManager.get_analyzers()]

        analyzers = analyzer_manager.AnalysisManager.get_analyzers()
        analyzers_detail = []
        for analyzer_name, analyzer_class in analyzers:
            # TODO: update the multi_analyzer detection logic for edgecases
            # where analyzers are using custom parameters (e.g. misp)
            multi = False
            if len(analyzer_class.get_kwargs()) > 0:
                multi = True
            analyzers_detail.append(
                {
                    "name": analyzer_name,
                    "display_name": analyzer_class.DISPLAY_NAME,
                    "description": analyzer_class.DESCRIPTION,
                    "is_multi": multi,
                }
            )

        return analyzers_detail

    @login_required
    def post(self, sketch_id):
        """Handles POST request to the resource.

        Returns:
            A string with the response from running the analyzer.
        """
        sketch = Sketch.get_with_acl(sketch_id)
        if not sketch:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No sketch found with this ID.")

        if not sketch.has_permission(current_user, "write"):
            return abort(
                HTTP_STATUS_CODE_FORBIDDEN,
                "User does not have write permission on the sketch.",
            )

        form = request.json
        if not form:
            form = request.data

        if not form:
            return abort(
                HTTP_STATUS_CODE_FORBIDDEN,
                "Unable to run an analyzer without any data submitted.",
            )

        timeline_ids = form.get("timeline_ids")
        if not timeline_ids:
            return abort(HTTP_STATUS_CODE_BAD_REQUEST, "Need to provide a timeline ID")

        sketch_timelines = {t.id for t in sketch.timelines}
        if not set(timeline_ids).issubset(sketch_timelines):
            return abort(
                HTTP_STATUS_CODE_FORBIDDEN, "Timeline is not part of this sketch"
            )

        analyzer_names = form.get("analyzer_names")
        if analyzer_names:
            if not isinstance(analyzer_names, (tuple, list)):
                return abort(
                    HTTP_STATUS_CODE_BAD_REQUEST,
                    "Analyzer names needs to be a list of analyzers.",
                )

        analyzer_kwargs = form.get("analyzer_kwargs")
        if analyzer_kwargs:
            if not isinstance(analyzer_kwargs, dict):
                return abort(
                    HTTP_STATUS_CODE_BAD_REQUEST,
                    "Kwargs needs to be a dictionary of parameters.",
                )

        analyzer_force_run = False
        if form.get("analyzer_force_run"):
            analyzer_force_run = True

        analyzers = []
        all_analyzers = [x for x, _ in analyzer_manager.AnalysisManager.get_analyzers()]
        for analyzer in analyzer_names:
            for correct_name in all_analyzers:
                if fnmatch.fnmatch(correct_name, analyzer):
                    METRICS["analyzer_run"].labels(name=correct_name).inc()
                    analyzers.append(correct_name)

        if not analyzers:
            return abort(HTTP_STATUS_CODE_BAD_REQUEST, "No analyzers found to run.")

        # Import here to avoid circular imports.
        # pylint: disable=import-outside-toplevel
        from timesketch.lib import tasks

        # TODO: Change to run on Timeline instead of Index
        sessions = []
        for timeline_id in timeline_ids:
            timeline = Timeline.get_by_id(timeline_id)
            if not timeline:
                continue
            if not timeline.status[0].status == "ready":
                continue
            searchindex_id = timeline.searchindex.id
            searchindex_name = timeline.searchindex.index_name

            try:
                analyzer_group, session = tasks.build_sketch_analysis_pipeline(
                    sketch_id=sketch_id,
                    searchindex_id=searchindex_id,
                    user_id=current_user.id,
                    analyzer_names=analyzers,
                    analyzer_kwargs=analyzer_kwargs,
                    timeline_id=timeline_id,
                    analyzer_force_run=analyzer_force_run,
                )
            except KeyError as e:
                logger.warning(
                    "Unable to build analyzer pipeline, analyzer does not "
                    "exists. Error message: {0!s}".format(e)
                )
                continue

            if analyzer_group:
                pipeline = tasks.run_sketch_init.s([searchindex_name]) | analyzer_group
                pipeline.apply_async()

            if session:
                sessions.append(session)

        return self.to_json(sessions)
