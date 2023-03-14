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
        sketch = Sketch.query.get_with_acl(sketch_id)
        if not sketch:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No sketch found with this ID.")

        if not sketch.has_permission(current_user, "read"):
            abort(
                HTTP_STATUS_CODE_FORBIDDEN, "User does not have read access to sketch"
            )

        timeline = Timeline.query.get(timeline_id)
        if not timeline:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No timeline found with this ID.")

        analysis_history = Analysis.query.filter_by(timeline=timeline).all()

        return self.to_json(analysis_history)


class AnalyzerSessionListResource(resources.ResourceMixin, Resource):
    """Resource to get all analyzer sessions for a given sketch."""

    @login_required
    def get(self, sketch_id):
      """Handles GET request to the resource.

      Returns:
          A list of analyzer sessions and their timelines in JSON (instance of flask.wrappers.Response)
      """
      sketch = Sketch.query.get_with_acl(sketch_id)

      if not sketch:
          abort(HTTP_STATUS_CODE_NOT_FOUND, "No sketch found with this ID.")

      if not sketch.has_permission(current_user, "read"):
          abort(
              HTTP_STATUS_CODE_FORBIDDEN, "User does not have read access to sketch"
          )

      # Get general available analyzers. Returns a list of dict entries
      available_analyzers = AnalyzerRunResource.get(self, sketch_id)

      sketch_analyzer_sessions = sketch.analysissessions

      analyzer_sessions_list = []

      for session in sketch_analyzer_sessions:
          for analysis in session.analyses:
              analyzer_name_short = analysis.name
              analyzer_name = analysis.name
              # Get the full name from the analyzer list. Fall back to the short name
              for analyzer in available_analyzers:
                  if analyzer["name"] == analysis.name:
                      analyzer_name = analyzer["display_name"]
                      break
              # Check if there is already and entry in the results for this analyzer
              analyzer_exists = False
              for analyzer in analyzer_sessions_list:
                  if analyzer["analyzer_name_short"] == analyzer_name_short:
                      # TODO: Check if timeline is already in the list and update if las_run is newer
                      analyzer["timelines"].append({
                          "last_run": analysis.created_at,
                          "analyzer_verdict": analysis.result,
                          "timeline_id": analysis.timeline.id,
                          "timeline_name": analysis.timeline.name,
                          "timeline_color": "#"+analysis.timeline.color,
                          "analyzer_status": analysis.status[0].status,
                      })
                      analyzer_exists = True
                      break
              if not analyzer_exists:
                  analyzer_sessions_list.append({
                      "analyzer_name": analyzer_name,
                      "analyzer_name_short": analyzer_name_short,
                      "timelines": [{
                          "last_run": analysis.created_at,
                          "analyzer_verdict": analysis.result,
                          "timeline_id": analysis.timeline.id,
                          "timeline_name": analysis.timeline.name,
                          "timeline_color": "#"+analysis.timeline.color,
                          "analyzer_status": analysis.status[0].status,
                      }]
                  })

      return jsonify(analyzer_sessions_list)

      # final data schema:
      # schema = [
      #   {
      #     "analyzer_name": "Windows logon/logoff events", // get name and description from AnalyzerRunResource.get()
      #     "analyzer_name_short": "login",
      #     "timelines": [ // only return the last run for a timeline
      #       {
      #         "last_run": "Mon, 13 Mar 2023 15:18:51 GMT", // from analyzer.created_at
      #         "analyzer_verdict": "Total number of login events processed: 2840 and logoff events: 646",
      #         "timeline_id": 2,
      #         "timeline_name": "WinSecurityLog_2022",
      #         "timeline_color": "79F3EF",
      #         "analyzer_status": "DONE"
      #       }
      #     ]
      #   },
      #   {
      #     "analyzer_name": "Feature extractor",
      #     "analyzer_name_short": "feature_extraction",
      #     "timelines": [ // except for multi analyzers like feature extractor and sigma
      #       {
      #         "analyzerLastRun": "Mon, 13 Mar 2023 15:19:00 GMT",
      #         "analyzerVerdict": "Feature extraction [ssh_client_password_ipv4_addresses] extracted 0 features.",
      #         "timelineId": 1,
      #         "timelineName": "test_firefox_evidence",
      #         "analyzer_status": "DONE"
      #       },
      #       {
      #         "analyzerLastRun": "Mon, 13 Mar 2023 15:18:59 GMT",
      #         "analyzerVerdict": "Feature extraction [gmail_accounts] extracted 0 features.",
      #         "timelineId": 1,
      #         "timelineName": "test_firefox_evidence",
      #         "analyzer_status": "DONE"
      #       }
      #     ]
      #   }
      # ]


class AnalyzerSessionActiveListResource(resources.ResourceMixin, Resource):
    """Resource to get active analyzer sessions."""

    @login_required
    def get(self, sketch_id):
        """Handles GET request to the resource.

        Returns:
            A analyzer session in JSON (instance of flask.wrappers.Response)
        """
        sketch = Sketch.query.get_with_acl(sketch_id)

        if not sketch:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No sketch found with this ID.")

        if not sketch.has_permission(current_user, "read"):
            abort(
                HTTP_STATUS_CODE_FORBIDDEN, "User does not have read access to sketch"
            )

        counter = collections.Counter(PENDING=0, STARTED=0, ERROR=0, DONE=0)
        session_ids = set()

        active_sessions = sketch.get_active_analysis_sessions()
        for session in active_sessions:
            session_ids.add(session.id)
            for analysis in session.analyses:
                counter[analysis.get_status.status] += 1

        schema = {
            "objects": [
                {
                    "total_tasks": sum(counter.values()),
                    "total_sessions": len(active_sessions),
                    "tasks_status_count": counter,
                    "sessions": list(session_ids),
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
        sketch = Sketch.query.get_with_acl(sketch_id)

        if not sketch:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No sketch found with this ID.")

        if not sketch.has_permission(current_user, "read"):
            abort(
                HTTP_STATUS_CODE_FORBIDDEN, "User does not have read access to sketch"
            )

        analysis_session = AnalysisSession.query.get(session_id)

        return self.to_json(analysis_session)


class AnalyzerRunResource(resources.ResourceMixin, Resource):
    """Resource to list or run analyzers for sketch."""

    @login_required
    def get(self, sketch_id):
        """Handles GET request to the resource.

        Returns:
            A list of all available analyzer names.
        """
        sketch = Sketch.query.get_with_acl(sketch_id)
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
            analyzers_detail.append(
                {
                    "name": analyzer_name,
                    "display_name": analyzer_class.DISPLAY_NAME,
                    "description": analyzer_class.DESCRIPTION,
                }
            )

        return analyzers_detail

    @login_required
    def post(self, sketch_id):
        """Handles POST request to the resource.

        Returns:
            A string with the response from running the analyzer.
        """
        sketch = Sketch.query.get_with_acl(sketch_id)
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
            timeline = Timeline.query.get(timeline_id)
            if not timeline:
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

            sessions.append(session)

        return self.to_json(sessions)
