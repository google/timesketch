# Copyright 2026 Google Inc. All rights reserved.
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
"""Dialect interface for direct PPL / SQL queries.

A dialect owns everything that differs between the OpenSearch query languages:
read-only validation, sketch scoping, request payload shape, and export
pagination. The resource shell in `endpoints.py` owns everything they share.

Dialect instances are created once at import time and reused for every
request, so dispatch costs a single dict lookup.
"""


class DirectQueryDialect:
    """Base class describing one OpenSearch query language."""

    # Language identifier used on the wire (request body and response).
    name = ""

    def api(self, client):
        """Return the plugin client namespace that serves this dialect.

        Both languages are served by the OpenSearch SQL plugin, which the
        client exposes as two namespaces carrying the same ``query`` and
        ``explain`` calls. Selecting one here is what binds a dialect to its
        endpoints.
        """
        raise NotImplementedError

    def validate(self, query):
        """Return an error message if the query is not read-only, else None.

        The shared shell has already rejected empty queries.
        """
        raise NotImplementedError

    def scope(self, query, index_pattern, timeline_ids, time_range=None):
        """Restrict a query to the sketch's indices, timelines and time range.

        ``time_range`` is a ``(start_micros, end_micros)`` pair, either side of
        which may be None for an open end. It is applied here rather than left
        to the caller's query text so the predicate is built the one way that
        is reliable across both plugins.

        Returns:
            Tuple of (scoped_query, error_message). Exactly one is set.
        """
        raise NotImplementedError

    def execute_payload(
        self, scoped_query, req_json
    ):  # pylint: disable=unused-argument
        """Build the request body for executing a query.

        Dialects that honour request options such as ``fetch_size`` read them
        from ``req_json``.

        Raises:
            ValueError: if a request option is unusable. The resource shell
                turns this into a 400.
        """
        return {"query": scoped_query}

    def explain_payload(self, scoped_query):
        """Build the request body for explaining a query."""
        return {"query": scoped_query}

    def stream(self, client, scoped_query):
        """Yield NDJSON lines for the full result set.

        Implementations must stay generators so results are streamed to the
        client rather than buffered in memory.
        """
        raise NotImplementedError
