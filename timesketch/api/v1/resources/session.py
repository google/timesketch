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
"""Session resources for version 1 of the Timesketch API."""

from flask import abort
from flask_restful import Resource
from flask_login import login_required
from flask_login import current_user

from timesketch.api.v1 import resources
from timesketch.lib.definitions import HTTP_STATUS_CODE_FORBIDDEN
from timesketch.lib.definitions import HTTP_STATUS_CODE_NOT_FOUND
from timesketch.models.sketch import Sketch


class SessionResource(resources.ResourceMixin, Resource):
    """Resource to get sessions."""

    @login_required
    def get(self, sketch_id, timeline_index):
        """Handles GET request to the resource.

        Returns:
            A list of objects representing sessions.
        """
        max_ids = 10000  # More than the number of sessions we expect to return
        max_sessions = 100

        session_types = [
            "all_events",
            "web_activity",
            "logon_session",
            "ssh_bruteforce_session",
            "ssh_session",
        ]
        sessions = []
        is_truncated = False

        sketch = Sketch.get_with_acl(sketch_id)
        if not sketch:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No sketch found with this ID.")
        if not sketch.has_permission(current_user, "read"):
            abort(
                HTTP_STATUS_CODE_FORBIDDEN,
                "User does not have read access controls on sketch.",
            )

        # Check the timeline belongs to the sketch
        sketch_indices = {
            t.searchindex.index_name
            for t in sketch.timelines
            if t.searchindex.index_name == timeline_index
        }

        id_agg_spec = {
            "aggregations": {"term_count": {"terms": {"field": "", "size": max_ids}}}
        }

        ts_agg_spec = {
            "aggregations": {
                "timestamp_range": {
                    "filter": {"bool": {"must": [{"query_string": {"query": ""}}]}},
                    "aggregations": {
                        "min_timestamp": {"min": {"field": "timestamp"}},
                        "max_timestamp": {"max": {"field": "timestamp"}},
                    },
                }
            }
        }

        id_terms = id_agg_spec["aggregations"]["term_count"]["terms"]
        ts_filter = ts_agg_spec["aggregations"]["timestamp_range"]["filter"]
        ts_query_string = ts_filter["bool"]["must"][0]["query_string"]

        for session_type in session_types:
            id_terms["field"] = "session_id.{}.keyword".format(session_type)
            # pylint: disable=unexpected-keyword-arg
            id_agg = self.datastore.client.search(
                index=list(sketch_indices), body=id_agg_spec, size=0
            )
            buckets = id_agg["aggregations"]["term_count"]["buckets"]
            session_count = 0

            for bucket in buckets:
                if session_count == max_sessions:
                    is_truncated = True
                    break
                session_count += 1

                session_id = bucket["key"]
                ts_query_string["query"] = "session_id.{}:{}".format(
                    session_type, session_id
                )
                ts_agg = self.datastore.client.search(
                    index=list(sketch_indices), body=ts_agg_spec, size=0
                )
                start_timestamp = (
                    int(
                        ts_agg["aggregations"]["timestamp_range"]["min_timestamp"][
                            "value"
                        ]
                    )
                    / 1000
                )
                end_timestamp = (
                    int(
                        ts_agg["aggregations"]["timestamp_range"]["max_timestamp"][
                            "value"
                        ]
                    )
                    / 1000
                )

                sessions.append(
                    {
                        "session_type": session_type,
                        "session_id": session_id,
                        "start_timestamp": start_timestamp,
                        "end_timestamp": end_timestamp,
                    }
                )

        sessions.append({"truncated": is_truncated})
        return sessions
