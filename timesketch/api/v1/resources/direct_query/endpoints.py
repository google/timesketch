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
"""REST resources for direct PPL / SQL queries.

Each dialect gets its own endpoints (``/explore/ppl/``, ``/explore/sql/``),
mirroring how wildcard search is separated from query-string search
(`/explore/` and `/explore_wildcard/`). A resource pins its dialect as a class
attribute, so the language is fixed by the route and can never be steered by
the request body.

All six resources share one implementation, so ACL enforcement, query scoping,
and response shaping cannot drift between the dialects.
"""

import collections
import logging

from flask import Response
from flask import abort
from flask import request
from flask import stream_with_context
from flask_login import current_user
from flask_login import login_required
from flask_restful import Resource
from opensearchpy import exceptions as opensearch_exceptions

from timesketch.api.v1 import resources
from timesketch.api.v1.resources.direct_query.base import EXECUTE_TIMEOUT_SECONDS
from timesketch.api.v1.resources.direct_query.base import columns_from_schema
from timesketch.api.v1.resources.direct_query.base import empty_result
from timesketch.api.v1.resources.direct_query.base import error_message
from timesketch.api.v1.resources.direct_query.base import get_client
from timesketch.api.v1.resources.direct_query.base import get_sketch_scope
from timesketch.api.v1.resources.direct_query.base import parse_time_range
from timesketch.api.v1.resources.direct_query.base import (
    index_pattern_has_timeline_field,
)
from timesketch.api.v1.resources.direct_query.base import validate_query
from timesketch.api.v1.resources.direct_query.base import verify_scope_with_explain
from timesketch.api.v1.resources.direct_query.capability import direct_query_support
from timesketch.api.v1.resources.direct_query.registry import PPL_DIALECT
from timesketch.api.v1.resources.direct_query.registry import SQL_DIALECT
from timesketch.lib.definitions import HTTP_STATUS_CODE_BAD_REQUEST
from timesketch.lib.definitions import HTTP_STATUS_CODE_FORBIDDEN
from timesketch.lib.definitions import HTTP_STATUS_CODE_NOT_FOUND
from timesketch.models.sketch import Sketch

logger = logging.getLogger("timesketch.direct_query_api")

HTTP_STATUS_CODE_BAD_GATEWAY = 502

PreparedQuery = collections.namedtuple(
    "PreparedQuery", ["sketch", "dialect", "scoped_query", "index_pattern", "req_json"]
)


def _parse_timeline_ids(raw):
    """Normalise the request's ``timeline_ids`` to a list of ints, or None.

    These only ever narrow the sketch's own timelines, so a bad value is a
    client error. Aborts with a 400 rather than letting the value fail deeper
    in scoping.
    """
    if raw is None:
        return None
    if not isinstance(raw, list):
        abort(HTTP_STATUS_CODE_BAD_REQUEST, "timeline_ids must be a list of integers.")
    try:
        return [int(timeline_id) for timeline_id in raw]
    except (TypeError, ValueError):
        abort(HTTP_STATUS_CODE_BAD_REQUEST, "timeline_ids must be a list of integers.")
    return None


def _prepare_query(sketch_id, dialect):
    """Run ACL checks and scope the request's query to the sketch.

    Args:
        sketch_id (int): primary key for a sketch database model.
        dialect (DirectQueryDialect): dialect pinned by the resource handling
            the route.

    Returns:
        A PreparedQuery. Aborts with an HTTP error on failure.
    """
    sketch = Sketch.get_with_acl(sketch_id)
    if not sketch:
        abort(HTTP_STATUS_CODE_NOT_FOUND, "No sketch found with this ID.")

    if not sketch.has_permission(current_user, "read"):
        abort(
            HTTP_STATUS_CODE_FORBIDDEN,
            "User does not have read access controls on sketch.",
        )

    if sketch.get_status.status == "archived":
        abort(
            HTTP_STATUS_CODE_BAD_REQUEST,
            "Unable to query on an archived sketch.",
        )

    # The UI hides these languages on a cluster that cannot serve them, but an
    # API client reaches this route directly, and an explicit refusal reads
    # better than whatever the cluster would return.
    support = direct_query_support()
    if not support:
        abort(HTTP_STATUS_CODE_BAD_REQUEST, support.reason)

    req_json = request.get_json(silent=True)
    if not req_json:
        abort(HTTP_STATUS_CODE_BAD_REQUEST, "Request body must be JSON.")

    query = req_json.get("query", "")
    if not isinstance(query, str):
        abort(HTTP_STATUS_CODE_BAD_REQUEST, "Query must be a string.")
    query = query.strip()

    validation_error = validate_query(query, dialect)
    if validation_error:
        abort(HTTP_STATUS_CODE_BAD_REQUEST, validation_error)

    requested_timeline_ids = _parse_timeline_ids(req_json.get("timeline_ids"))

    try:
        time_range = parse_time_range(req_json)
    except ValueError as e:
        abort(HTTP_STATUS_CODE_BAD_REQUEST, str(e))

    # Scope to the active timelines (not just their indices) so shared/orphaned
    # rows from other or deleted timelines are excluded.
    index_pattern, filter_timeline_ids = get_sketch_scope(
        sketch, requested_timeline_ids
    )
    if not index_pattern:
        abort(
            HTTP_STATUS_CODE_BAD_REQUEST,
            "No valid indices found for this sketch. "
            "Make sure at least one timeline is selected.",
        )

    if filter_timeline_ids and not index_pattern_has_timeline_field(index_pattern):
        # No index here carries __ts_timeline_id, so the predicate cannot be
        # used: the Calcite engine treats an unmapped field as an error, not as
        # null. Dropping it loses nothing, because every row in such an index
        # predates the field and would match the predicate's isnull() branch.
        filter_timeline_ids = []

    scoped_query, scope_error = dialect.scope(
        query, index_pattern, filter_timeline_ids, time_range
    )
    if scope_error:
        abort(HTTP_STATUS_CODE_FORBIDDEN, scope_error)

    # Second opinion from the engine's own planner, which sees index references
    # the dialect's regexes may not know to look for.
    plan_error = verify_scope_with_explain(
        dialect,
        scoped_query,
        [name.strip() for name in index_pattern.split(",") if name.strip()],
    )
    if plan_error:
        abort(HTTP_STATUS_CODE_FORBIDDEN, plan_error)

    return PreparedQuery(sketch, dialect, scoped_query, index_pattern, req_json)


def _call_opensearch(call, dialect, sketch_id, action, result_type):
    """Run one plugin call and return ``(data, error_response)``.

    Exactly one of the tuple members is set. ``error_response`` is a ready to
    return ``(body, status)`` pair.
    """
    try:
        return call(), None
    except (
        opensearch_exceptions.ConnectionError,
        opensearch_exceptions.SerializationError,
    ) as e:
        logger.error(
            "OpenSearch %s %s failed for sketch %s: %s",
            dialect.name.upper(),
            action,
            sketch_id,
            e,
            exc_info=True,
        )
        return None, (
            empty_result(dialect, f"Failed to connect to OpenSearch: {e}", result_type),
            HTTP_STATUS_CODE_BAD_GATEWAY,
        )
    except opensearch_exceptions.TransportError as e:
        # A query the plugin rejects is a user error, not a gateway failure, so
        # it is reported in the envelope with a 200.
        return None, (
            empty_result(dialect, error_message(e), result_type),
            200,
        )


class _BaseDirectQueryResource(resources.ResourceMixin, Resource):
    """Shared ACL and scoping behaviour for the direct query endpoints.

    Subclasses pin ``dialect`` to the language their route serves.
    """

    dialect = None

    def prepare(self, sketch_id):
        return _prepare_query(sketch_id, self.dialect)


class _BaseExecuteResource(_BaseDirectQueryResource):
    """Execute a query and return a tabular result set."""

    @login_required
    def post(self, sketch_id):
        """Handles POST request to execute a PPL or SQL query.

        Args:
            sketch_id (int): primary key for a sketch database model

        Returns:
            JSON with query results in a tabular format
        """
        prepared = self.prepare(sketch_id)
        dialect = prepared.dialect

        try:
            payload = dialect.execute_payload(prepared.scoped_query, prepared.req_json)
        except ValueError as e:
            # A dialect rejects unusable request options (e.g. fetch_size) this
            # way, which is a client error rather than a server fault.
            abort(HTTP_STATUS_CODE_BAD_REQUEST, str(e))

        data, error_response = _call_opensearch(
            lambda: dialect.api(get_client()).query(
                body=payload, request_timeout=EXECUTE_TIMEOUT_SECONDS
            ),
            dialect,
            sketch_id,
            "query",
            "direct",
        )
        if error_response:
            return error_response

        columns = columns_from_schema(data)
        datarows = data.get("datarows", [])
        return {
            "result_type": "direct",
            "language": dialect.name,
            "columns": columns,
            "datarows": datarows,
            "total": data.get("total", len(datarows)),
            "size": data.get("size", len(datarows)),
            "error": None,
        }


class _BaseExplainResource(_BaseDirectQueryResource):
    """Return the OpenSearch execution plan without running the query."""

    @login_required
    def post(self, sketch_id):
        """Handles POST request to explain a PPL or SQL query.

        Applies the same ACL checks and query scoping as the execute endpoint.

        Args:
            sketch_id (int): primary key for a sketch database model

        Returns:
            JSON with the query execution plan
        """
        prepared = self.prepare(sketch_id)
        dialect = prepared.dialect

        data, error_response = _call_opensearch(
            lambda: dialect.api(get_client()).explain(
                body=dialect.explain_payload(prepared.scoped_query),
                request_timeout=EXECUTE_TIMEOUT_SECONDS,
            ),
            dialect,
            sketch_id,
            "explain",
            "direct_explain",
        )
        if error_response:
            return error_response

        return {
            "result_type": "direct_explain",
            "language": dialect.name,
            "plan": data,
            "error": None,
        }


class _BaseExportResource(_BaseDirectQueryResource):
    """Stream a full result set as NDJSON."""

    @login_required
    def post(self, sketch_id):
        """Handles POST request to stream PPL/SQL results.

        Uses SQL cursor-based pagination or PPL size/from pagination to stream
        all results as NDJSON.

        Args:
            sketch_id: Integer primary key for a sketch database model

        Returns:
            Streaming NDJSON response
        """
        prepared = self.prepare(sketch_id)
        generator = prepared.dialect.stream(get_client(), prepared.scoped_query)
        return Response(
            stream_with_context(generator),
            mimetype="application/x-ndjson",
        )


# ---------------------------------------------------------------------------
# PPL resources (/explore/ppl/)
# ---------------------------------------------------------------------------
class PplQueryResource(_BaseExecuteResource):
    """Handler for /api/v1/sketches/:sketch_id/explore/ppl/"""

    dialect = PPL_DIALECT


class PplQueryExplainResource(_BaseExplainResource):
    """Handler for /api/v1/sketches/:sketch_id/explore/ppl/explain/"""

    dialect = PPL_DIALECT


class PplQueryExportResource(_BaseExportResource):
    """Handler for /api/v1/sketches/:sketch_id/explore/ppl/export/"""

    dialect = PPL_DIALECT


# ---------------------------------------------------------------------------
# SQL resources (/explore/sql/)
# ---------------------------------------------------------------------------
class SqlQueryResource(_BaseExecuteResource):
    """Handler for /api/v1/sketches/:sketch_id/explore/sql/"""

    dialect = SQL_DIALECT


class SqlQueryExplainResource(_BaseExplainResource):
    """Handler for /api/v1/sketches/:sketch_id/explore/sql/explain/"""

    dialect = SQL_DIALECT


class SqlQueryExportResource(_BaseExportResource):
    """Handler for /api/v1/sketches/:sketch_id/explore/sql/export/"""

    dialect = SQL_DIALECT
