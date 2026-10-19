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
"""Shared infrastructure for the direct PPL / SQL query resources.

Everything in this module is dialect agnostic: OpenSearch connection details,
sketch index/timeline scoping, and response envelope construction. The
dialect-specific pieces live in `ppl.py` and `sql.py`.
"""

import datetime
import logging
import re
import threading
import time

from opensearchpy import exceptions as opensearch_exceptions

from timesketch.lib.datastores.opensearch import build_opensearch_client

logger = logging.getLogger("timesketch.direct_query_api")

# Rows requested per round trip when streaming an export. Both dialects
# paginate at the same size; only the per-request timeout differs, and that
# lives with the dialect that uses it.
DIRECT_QUERY_EXPORT_PAGE_SIZE = 10000

# Applies to the execute and explain endpoints, which are dialect agnostic.
EXECUTE_TIMEOUT_SECONDS = 30

# The mapping probe runs before the query it guards, so it is kept short.
MAPPING_TIMEOUT_SECONDS = 5

# Planning only, no execution, so this stays well under the execute timeout.
EXPLAIN_VERIFY_TIMEOUT_SECONDS = 10

# Field carrying the timeline a document belongs to. Indices written by older
# Timesketch versions predate it.
TIMELINE_FIELD = "__ts_timeline_id"

# Timesketch stores event time twice: `datetime` as a date and `timestamp` as
# microseconds since the epoch. Range filtering goes through the numeric field
# because date comparison in the SQL and PPL plugins depends on how the index
# declared its date format, and silently matches nothing when the two disagree.
# An integer comparison on a long has no such ambiguity.
TIME_RANGE_FIELD = "timestamp"

# An index only gains or loses the field when a timeline is (re)indexed, so a
# few minutes of staleness is harmless and keeps the probe off the hot path.
TIMELINE_FIELD_CACHE_TTL_SECONDS = 300

# Bounds cache growth across many sketches. Entries are cheap and the whole map
# is discarded on overflow rather than evicted one by one; refilling costs one
# mapping call per pattern still in use.
TIMELINE_FIELD_CACHE_MAX_ENTRIES = 1024

_timeline_field_cache = {}
_timeline_field_cache_lock = threading.Lock()

# One OpenSearch client for every call this package makes. The client is built
# once rather than per request: its transport holds the connection pool, and
# rebuilding it each time would pay TCP and TLS setup on every page of an
# export. The transport is thread safe, so it is shared across worker threads.
_client_holder = {"client": None}
_client_lock = threading.Lock()


def configure_client(app):
    """Build the shared client once, at startup.

    The datastore's builder is used rather than a second copy of the host,
    credential and TLS handling, so direct queries reach the cluster the way
    the rest of Timesketch does -- across every node in ``OPENSEARCH_HOSTS``
    rather than whichever one happens to be listed first.

    Args:
        app (Flask): application whose config carries the OpenSearch settings.
    """
    with app.app_context():
        with _client_lock:
            _client_holder["client"] = build_opensearch_client()


def get_client():
    """Return the shared OpenSearch client, building it on first use."""
    client = _client_holder["client"]
    if client is not None:
        return client

    with _client_lock:
        if _client_holder["client"] is None:
            _client_holder["client"] = build_opensearch_client()
        return _client_holder["client"]


def reset_client():
    """Drop the shared client. Used by tests and after a config change."""
    with _client_lock:
        _client_holder["client"] = None


def _parse_boundary(value, label, end_of_day):
    """Parse one ISO 8601 boundary into epoch microseconds.

    A date with no time part covers the whole day: a start snaps to 00:00:00
    and an end to the last microsecond before midnight, so ``2026-04-07`` to
    ``2026-04-07`` is that entire day rather than an empty instant.

    Raises:
        ValueError: if the value is not a string or not ISO 8601.
    """
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be an ISO 8601 date or datetime string.")

    text = value.strip()
    # `fromisoformat` reads "+00:00" but not the "Z" that browsers emit.
    normalised = text[:-1] + "+00:00" if text.endswith("Z") else text

    try:
        parsed = datetime.datetime.fromisoformat(normalised)
    except ValueError as e:
        raise ValueError(
            f"{label} is not a valid ISO 8601 date or datetime: {value}"
        ) from e

    date_only = len(text) == 10
    if date_only and end_of_day:
        parsed = parsed + datetime.timedelta(days=1, microseconds=-1)

    if parsed.tzinfo is None:
        # Timesketch timestamps are UTC, and an unqualified boundary that
        # silently took the server's zone would shift every result.
        parsed = parsed.replace(tzinfo=datetime.timezone.utc)

    return int(parsed.timestamp() * 1_000_000)


def parse_time_range(req_json):
    """Return ``(start_micros, end_micros)`` for the request, or ``None``.

    Either boundary may be omitted for an open-ended range. Returns None when
    neither is given.

    Raises:
        ValueError: if a boundary is unparseable or the range is inverted.
    """
    raw_start = req_json.get("start_time")
    raw_end = req_json.get("end_time")
    if raw_start is None and raw_end is None:
        return None

    start = (
        None if raw_start is None else _parse_boundary(raw_start, "start_time", False)
    )
    end = None if raw_end is None else _parse_boundary(raw_end, "end_time", True)

    if start is not None and end is not None and start > end:
        raise ValueError("start_time must not be later than end_time.")

    return start, end


def time_range_predicate(time_range, conjunction="and"):
    """Return a numeric range predicate for ``timestamp``, or an empty string.

    The expression itself is valid in both dialects: an integer comparison needs
    no quoting, casting or date-format agreement. Only the conjunction is
    spelled to match the surrounding dialect's style.
    """
    if not time_range:
        return ""
    start, end = time_range
    clauses = []
    if start is not None:
        clauses.append(f"{TIME_RANGE_FIELD} >= {start}")
    if end is not None:
        clauses.append(f"{TIME_RANGE_FIELD} <= {end}")
    return f" {conjunction} ".join(clauses)


def get_sketch_scope(sketch, timeline_ids=None):
    """Return ``(index_pattern, timeline_ids)`` for a sketch in one pass.

    ``sketch.timelines`` is a lazily loaded relationship, so the index pattern
    and the active timeline IDs are collected together rather than walking it
    twice.

    The timeline IDs drive the ``__ts_timeline_id`` filter that scopes results
    to the timelines actually in the sketch. Multiple timelines can share one
    index, and deleting a timeline does not delete its documents, so index-name
    scoping alone would surface events from co-located or removed timelines
    ("orphaned" records).

    Args:
        sketch (Sketch): the sketch whose timelines are being scoped.
        timeline_ids (list): optional timeline IDs to restrict to. If empty or
            None, all sketch timelines are used.
    """
    selected = set(timeline_ids) if timeline_ids else None
    seen = set()
    indices = []
    active_timeline_ids = []

    for timeline in sketch.timelines:
        if not timeline.searchindex:
            continue
        if selected is not None and timeline.id not in selected:
            continue
        active_timeline_ids.append(timeline.id)
        index_name = timeline.searchindex.index_name
        if index_name and index_name not in seen:
            seen.add(index_name)
            indices.append(index_name)

    return ",".join(indices), active_timeline_ids


def _probe_timeline_field(index_pattern):
    """Ask OpenSearch whether any index in the pattern maps the timeline field.

    Returns True when the mapping cannot be read. Injecting the predicate and
    risking a loud query error is safer than silently widening a query's scope
    because a mapping call happened to fail.
    """
    try:
        body = get_client().indices.get_field_mapping(
            fields=TIMELINE_FIELD,
            index=index_pattern,
            ignore_unavailable=True,
            request_timeout=MAPPING_TIMEOUT_SECONDS,
        )
    except opensearch_exceptions.OpenSearchException as e:
        logger.warning(
            "Mapping probe for %s failed (%s); assuming %s is present.",
            index_pattern,
            e,
            TIMELINE_FIELD,
        )
        return True

    if not isinstance(body, dict):
        return True
    # OpenSearch answers per index, and reports the field only where it exists.
    # One index carrying it is enough: a multi-index query resolves the field
    # from the union of the mappings.
    return any(
        isinstance(entry, dict) and entry.get("mappings") for entry in body.values()
    )


def index_pattern_has_timeline_field(index_pattern):
    """Return whether ``index_pattern`` maps the timeline field, with caching.

    The answer decides whether the ``__ts_timeline_id`` predicate can be used.
    Under the Calcite query engine (the default from OpenSearch 3.0, with V2
    fallback disabled) naming a field that no index maps is a hard error rather
    than a null comparison, so injecting it into a legacy index fails the whole
    query.
    """
    now = time.monotonic()
    cached = _timeline_field_cache.get(index_pattern)
    if cached and cached[0] > now:
        return cached[1]

    has_field = _probe_timeline_field(index_pattern)
    with _timeline_field_cache_lock:
        if len(_timeline_field_cache) >= TIMELINE_FIELD_CACHE_MAX_ENTRIES:
            _timeline_field_cache.clear()
        _timeline_field_cache[index_pattern] = (
            now + TIMELINE_FIELD_CACHE_TTL_SECONDS,
            has_field,
        )
    return has_field


# Index references as they appear in an OpenSearch execution plan. The Calcite
# engine writes a text plan; the V2 engine writes a JSON tree that names the
# index either in a request string or, for joins, in a `tableName` field.
_PLAN_CALCITE_SCAN = re.compile(
    r"CalciteLogicalIndexScan\(table=\[\[OpenSearch,\s*([^\]]+?)\s*\]\]"
)
_PLAN_INDEX_NAME = re.compile(r"indexName=([^\s,]+(?:,[^\s,]+)*)")


def plan_indices(plan):
    """Return every index named in an OpenSearch execution plan.

    The plan is walked rather than pattern matched as a whole, because the
    shape differs by engine and by query: Calcite emits a text plan, the V2 SQL
    engine emits a JSON tree, and a V2 join names its tables in `tableName`
    fields instead of a request string. A comma-joined multi-index pattern is
    split, so the result is always individual index names.
    """
    found = set()

    def walk(node):
        if isinstance(node, dict):
            for key, value in node.items():
                if key == "tableName" and isinstance(value, str):
                    found.add(value)
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)
        elif isinstance(node, str):
            for pattern in (_PLAN_CALCITE_SCAN, _PLAN_INDEX_NAME):
                for match in pattern.finditer(node):
                    found.add(match.group(1))

    walk(plan)

    indices = set()
    for name in found:
        indices.update(part.strip() for part in name.split(",") if part.strip())
    return indices


def verify_scope_with_explain(dialect, scoped_query, allowed):
    """Ask OpenSearch which indices the scoped query really reads.

    This is a second, independent check on top of the dialect's own scoping.
    The dialect works from the query text with regexes, so it can only look for
    syntax it knows about; the plan comes from the engine's own parser and
    names every index the query will actually touch, including those reached
    through PPL's `lookup`, `join` and subsearch commands.

    Returns an error message when the plan names an index outside the sketch,
    otherwise None.

    A plan that cannot be read raises no objection, and the dialect's own
    result stands. That keeps an unfamiliar plan format from taking the feature
    down on an OpenSearch upgrade, at the cost of quietly falling back to
    text-based scoping -- which is why it is logged. Note the dialect layer is
    itself fail-closed, so this is a narrowing of defence in depth rather than
    a hole.
    """
    try:
        plan = dialect.api(get_client()).explain(
            body=dialect.explain_payload(scoped_query),
            request_timeout=EXPLAIN_VERIFY_TIMEOUT_SECONDS,
        )
    except (
        opensearch_exceptions.ConnectionError,
        opensearch_exceptions.SerializationError,
    ) as e:
        logger.warning("Could not verify query scope against the plan: %s", e)
        return None
    except opensearch_exceptions.TransportError:
        # Usually a query the plugin rejects outright; executing it will
        # surface the real error to the user.
        return None

    named = plan_indices(plan)
    if not named:
        logger.warning(
            "No index found in the %s execution plan; falling back to "
            "text-based scoping. The plan format may have changed.",
            dialect.name.upper(),
        )
        return None

    outside = sorted(named - set(allowed))
    if outside:
        logger.warning(
            "%s plan reads indices outside the sketch: %s",
            dialect.name.upper(),
            ", ".join(outside),
        )
        return f"{dialect.name.upper()} query targets indices outside this sketch."
    return None


def validate_query(query, dialect):
    """Validate a query for non-emptiness and dialect read-only safety.

    Returns None if valid, else an error message.
    """
    if not query or not query.strip():
        return "Query cannot be empty."
    return dialect.validate(query)


def format_opensearch_error(data):
    """Flatten an OpenSearch error body into a single message string."""
    error = data.get("error", {})
    if not isinstance(error, dict):
        return str(error)
    reason = error.get("reason", str(error))
    error_type = error.get("type", "")
    details = error.get("details", "")
    message = f"{error_type}: {reason}"
    if details:
        message += f"\n{details}"
    return message


def error_message(exc):
    """Return a readable message for an exception raised by the client.

    A query the plugin rejects carries its error document on the exception,
    which names the syntax problem. A connection failure carries the
    underlying exception there instead, and reads better as its own message.
    """
    try:
        info = exc.info
    except (AttributeError, LookupError):
        # `info` is a property over the third argument, which not every
        # exception class carries. This runs on the error path, so it must not
        # raise an error of its own.
        info = None

    if isinstance(info, dict) and info.get("error"):
        return format_opensearch_error(info)
    return str(exc)


def empty_result(dialect, error, result_type="direct"):
    """Build a result envelope carrying an error and no rows."""
    envelope = {
        "result_type": result_type,
        "language": dialect.name,
        "error": str(error),
    }
    if result_type == "direct":
        envelope.update({"columns": [], "datarows": [], "total": 0, "size": 0})
    return envelope


def columns_from_schema(data):
    """Extract column names from an OpenSearch PPL/SQL response schema."""
    return [col.get("name", f"col_{i}") for i, col in enumerate(data.get("schema", []))]
