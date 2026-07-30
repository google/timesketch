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
"""SQL dialect for direct queries."""

import json
import logging
import re

from opensearchpy import exceptions as opensearch_exceptions

from timesketch.api.v1.resources.direct_query.base import DIRECT_QUERY_EXPORT_PAGE_SIZE
from timesketch.api.v1.resources.direct_query.base import columns_from_schema
from timesketch.api.v1.resources.direct_query.base import error_message
from timesketch.api.v1.resources.direct_query.base import time_range_predicate
from timesketch.api.v1.resources.direct_query.dialect import DirectQueryDialect

logger = logging.getLogger("timesketch.direct_query_api")

# `fetch_size` is a SQL plugin concept; PPL has no equivalent.
DIRECT_QUERY_MAX_ROWS = 10000
DIRECT_QUERY_DEFAULT_FETCH_SIZE = 1000

# Cursor pages are served from a held context, so they return faster than a
# PPL export page, which re-runs the pipeline each time.
EXPORT_TIMEOUT_SECONDS = 60

# Read-only SQL allowlist: the _sql plugin only accepts SELECT/SHOW/DESCRIBE.
# Allowlisting the leading keyword avoids false-positiving on words like DELETE
# that appear as string literals (e.g. `WHERE message LIKE '%delete%'`).
_SQL_READ_ONLY_LEADING = re.compile(
    r"^\s*\(*\s*(SELECT|SHOW|DESCRIBE)\b", re.IGNORECASE
)

# Matches a FROM or JOIN keyword (the start of a table reference / list).
_SQL_FROM_JOIN = re.compile(r"\b(?:FROM|JOIN)\b", re.IGNORECASE)

# Keywords that terminate a FROM/JOIN table list.
_SQL_TABLE_LIST_STOP = re.compile(
    r"\b(WHERE|GROUP|ORDER|HAVING|LIMIT|ON|UNION)\b", re.IGNORECASE
)

# Leading identifier (backtick-quoted or bare) of a single table reference.
_SQL_TABLE_IDENT = re.compile(r"`([^`]+)`|([A-Za-z0-9_.*+-]+)")

# Opens a sub-query rather than naming a table, so the reference to validate is
# the one in its own nested FROM.
_SQL_SUBQUERY_HEAD = re.compile(r"(SELECT|VALUES|WITH)\b", re.IGNORECASE)

# Top-level SQL clause keywords used to position an injected FROM clause.
_SQL_CLAUSE_KEYWORD = re.compile(r"\b(WHERE|GROUP|ORDER|HAVING|LIMIT)\b", re.IGNORECASE)

_SQL_FROM = re.compile(r"\bFROM\b", re.IGNORECASE)
_SQL_WHERE = re.compile(r"\bWHERE\b", re.IGNORECASE)
_SQL_UNION_OR_JOIN = re.compile(r"\b(UNION|JOIN)\b", re.IGNORECASE)
_SQL_UNION = re.compile(r"\bUNION\b", re.IGNORECASE)
_SQL_FROM_STOP = re.compile(r"\b(WHERE|GROUP|HAVING|ORDER|LIMIT|ON)\b", re.IGNORECASE)
_SQL_WHERE_BOUNDARY = re.compile(r"\b(GROUP|HAVING|ORDER|LIMIT)\b", re.IGNORECASE)
_SQL_BACKTICKED = re.compile(r"`[^`]*`")

# A GROUP BY makes the response an aggregation, which the plugin will only
# return in full when fetch_size is 0 (cursor pagination does not apply).
_SQL_GROUP_BY = re.compile(r"\bGROUP\s+BY\b", re.IGNORECASE)


def _parse_fetch_size(raw):
    """Clamp a client-supplied ``fetch_size`` to a usable page size.

    Raises:
        ValueError: if the value is not a positive integer, so the resource can
            answer with a 400 rather than failing inside the comparison.
    """
    if raw is None:
        return DIRECT_QUERY_DEFAULT_FETCH_SIZE
    if isinstance(raw, bool) or not isinstance(raw, (int, str)):
        raise ValueError("fetch_size must be a positive integer.")
    try:
        fetch_size = int(raw)
    except ValueError as exc:
        raise ValueError("fetch_size must be a positive integer.") from exc
    if fetch_size < 1:
        raise ValueError("fetch_size must be a positive integer.")
    return min(fetch_size, DIRECT_QUERY_MAX_ROWS)


def _sql_timeline_predicate(timeline_ids):
    """SQL predicate scoping rows to the given timelines.

    Keeps rows whose ``__ts_timeline_id`` is in the set, plus legacy rows that
    predate the field, mirroring the explore datastore's behaviour. The caller
    only injects this when some index in the pattern maps the field; where none
    does, the predicate is both an error under Calcite and a no-op.
    """
    ids = ", ".join(str(int(t)) for t in timeline_ids)
    return f"(__ts_timeline_id IN ({ids}) OR __ts_timeline_id IS NULL)"


def _backtick_quote_sql(index_pattern):
    """Quote indices as one SQL multi-index pattern: ``FROM `idx1,idx2```.

    A single backtick-quoted comma list is a union scan in OpenSearch SQL.
    Separate-quoted identifiers (```idx1`, `idx2```) are treated as a JOIN,
    which makes GROUP BY/ORDER BY silently return zero rows on multi-index
    sketches while COUNT(*) still works -- a confusing partial failure.
    """
    indices = [idx.strip() for idx in index_pattern.split(",") if idx.strip()]
    return "`" + ",".join(indices) + "`"


def _mask_sql(query, mask_parens):
    """Blank out literals, comments (and parens if ``mask_parens``) with spaces.

    Offsets are preserved so regex matches map back onto ``query``. Masking
    strings stops a value like ``'%from table%'`` looking like SQL syntax, and
    masking comments stops ``FROM /*x*/ idx`` hiding a table reference from
    :func:`_referenced_indices`. Masking parens leaves only top-level keywords.

    Backtick-quoted identifiers are copied verbatim so index names stay
    readable, and so a name containing ``--`` cannot open a comment.
    """
    out = []
    depth = 0
    quote = None
    comment = None
    in_backtick = False
    i = 0
    end = len(query)

    while i < end:
        char = query[i]
        pair = query[i : i + 2]
        masked_here = mask_parens and depth > 0

        if comment == "line":
            # A newline ends the comment and is kept so line offsets survive.
            out.append(char if char == "\n" else " ")
            if char == "\n":
                comment = None
            i += 1
            continue

        if comment == "block":
            if pair == "*/":
                comment = None
                out.append("  ")
                i += 2
                continue
            out.append(char if char == "\n" else " ")
            i += 1
            continue

        if quote is not None:
            out.append(" ")
            if char == quote:
                quote = None
            i += 1
            continue

        if in_backtick:
            out.append(" " if masked_here else char)
            if char == "`":
                in_backtick = False
            i += 1
            continue

        if char == "`":
            in_backtick = True
            out.append(" " if masked_here else char)
            i += 1
            continue

        if char in ("'", '"'):
            quote = char
            out.append(" ")
            i += 1
            continue

        if pair == "--":
            comment = "line"
            out.append("  ")
            i += 2
            continue

        if pair == "/*":
            comment = "block"
            out.append("  ")
            i += 2
            continue

        if char == "(":
            depth += 1
            out.append(" " if mask_parens else char)
            i += 1
            continue

        if char == ")":
            if depth > 0:
                depth -= 1
            out.append(" " if mask_parens else char)
            i += 1
            continue

        out.append(" " if masked_here else char)
        i += 1

    return "".join(out)


def _split_table_list(segment):
    """Split a FROM/JOIN table list on commas outside backticks.

    ``FROM `a,b`` is one multi-index pattern rather than two tables, so its
    internal commas must not split the list.
    """
    parts = []
    current = []
    in_backtick = False
    for char in segment:
        if char == "`":
            in_backtick = not in_backtick
        elif char == "," and not in_backtick:
            parts.append("".join(current))
            current = []
            continue
        current.append(char)
    parts.append("".join(current))
    return parts


def _referenced_indices(query):
    """Return ``(indices, unresolved)`` for the query's FROM/JOIN clauses.

    Takes the leading identifier of each comma segment so every index in a list
    (``FROM a, b``) or aliased list (``FROM a x, b y``) is validated, not just
    the first. Strings and comments are masked, so neither a value nor a
    comment can pose as (or hide) a table reference.

    ``unresolved`` is True when a table reference could not be reduced to an
    identifier. Callers must treat that as a scoping failure: an empty index
    set means "nothing to check" only when nothing was unresolved, otherwise a
    reference the allowlist never saw would pass straight through.

    Parenthesised items are unwrapped rather than skipped. A nested SELECT is
    ignored here because its own FROM is matched separately by this same loop,
    but a parenthesised plain table (``FROM(idx)``) still has to be checked.
    """
    masked = _mask_sql(query, mask_parens=False)
    indices = set()
    unresolved = False

    for keyword in _SQL_FROM_JOIN.finditer(masked):
        rest = masked[keyword.end() :]
        # Cut the table list at the next clause keyword or nested FROM/JOIN.
        stop = _SQL_TABLE_LIST_STOP.search(rest)
        segment = rest[: stop.start()] if stop else rest
        nxt = _SQL_FROM_JOIN.search(segment)
        if nxt:
            segment = segment[: nxt.start()]

        if not segment.strip():
            unresolved = True
            continue

        for part in _split_table_list(segment):
            part = part.strip()
            if not part:
                continue
            while part.startswith("("):
                part = part[1:].lstrip()
            if not part:
                unresolved = True
                continue
            if _SQL_SUBQUERY_HEAD.match(part):
                continue
            match = _SQL_TABLE_IDENT.match(part)
            if match:
                indices.add(match.group(1) or match.group(2))
            else:
                unresolved = True

    return indices, unresolved


def _sql_single_from_target(query):
    """Return the single top-level FROM table, or None if not scope-able.

    A ``__ts_timeline_id`` filter can only be injected safely when there is one
    plain index table at top level. JOINs (ambiguous column), UNIONs (multiple
    SELECTs), comma table lists, and sub-query FROMs are left untouched. Commas
    inside backticks (the ``\\`a,b\\``` multi-index pattern) are one table.
    """
    masked = _mask_sql(query, mask_parens=True)
    if _SQL_UNION_OR_JOIN.search(masked):
        return None
    from_match = _SQL_FROM.search(masked)
    if not from_match:
        return None
    stop = _SQL_FROM_STOP.search(masked[from_match.end() :])
    end = from_match.end() + stop.start() if stop else len(query)
    segment = query[from_match.end() : end].strip()
    if not segment or segment.startswith("("):
        return None
    if "," in _SQL_BACKTICKED.sub("", segment):
        return None
    return segment


def _sql_scope_predicate(timeline_ids, time_range):
    """Combine the timeline and time-range predicates into one expression.

    ``_sql_timeline_predicate`` already parenthesises itself, and the range is
    a conjunction of comparisons, so ANDing the two needs no further grouping.
    """
    parts = []
    if timeline_ids:
        parts.append(_sql_timeline_predicate(timeline_ids))
    range_predicate = time_range_predicate(time_range, conjunction="AND")
    if range_predicate:
        parts.append(range_predicate)
    return " AND ".join(parts)


def _inject_sql_filter(query, timeline_ids, time_range):
    """AND the scoping filter into a single-FROM SQL query.

    Merges into an existing top-level WHERE (wrapping the original predicate to
    preserve OR precedence) or inserts a new WHERE before GROUP/HAVING/ORDER/
    LIMIT. Queries that aren't a single plain-index SELECT are returned
    unchanged (see :func:`_sql_single_from_target`).
    """
    predicate = _sql_scope_predicate(timeline_ids, time_range)
    if not predicate or _sql_single_from_target(query) is None:
        return query
    masked = _mask_sql(query, mask_parens=True)

    where_match = _SQL_WHERE.search(masked)
    if where_match:
        stop = _SQL_WHERE_BOUNDARY.search(masked, where_match.end())
        end = stop.start() if stop else len(query)
        where_expr = query[where_match.end() : end].strip()
        rest = query[end:].strip()
        scoped = f"{query[: where_match.end()]} {predicate} AND ({where_expr})"
        return f"{scoped} {rest}" if rest else scoped

    from_match = _SQL_FROM.search(masked)
    stop = _SQL_WHERE_BOUNDARY.search(masked, from_match.end())
    insert_at = stop.start() if stop else len(query)
    head = query[:insert_at].rstrip()
    tail = query[insert_at:].strip()
    scoped = f"{head} WHERE {predicate}"
    return f"{scoped} {tail}" if tail else scoped


def _scope_sql_query(query, index_pattern, timeline_ids=None, time_range=None):
    """Ensure an SQL query only targets the sketch's own indices (and timelines).

    Supports sub-queries, JOIN, UNION and window functions (a naive first-FROM
    match would mis-scope these). Validates every referenced index, then either
    passes through a self-scoped query or injects a FROM clause. When
    timeline_ids is given, a ``__ts_timeline_id`` filter is added so a shared
    index returns only the requested timelines' rows. A time_range adds a
    numeric bound on ``timestamp`` to the same WHERE clause.
    """
    allowed = set(idx.strip() for idx in index_pattern.split(",") if idx.strip())

    # Validate every referenced index (a one-identifier pattern matches
    # index_pattern directly). A reference we could not parse is rejected
    # rather than ignored, so an unfamiliar FROM shape cannot slip past the
    # allowlist unchecked.
    referenced, unresolved = _referenced_indices(query)
    if unresolved:
        return None, (
            "Unable to determine which indices this SQL query targets. "
            "Name the sketch index explicitly in the FROM clause."
        )
    for table in referenced:
        if table not in allowed and table != index_pattern:
            return None, "SQL query targets indices outside this sketch."

    top_level = _mask_sql(query, mask_parens=True)
    if _SQL_FROM.search(top_level):
        # A top-level FROM means the query already scopes itself.
        scoped = query
    elif _SQL_UNION.search(top_level):
        # A FROM-less UNION has multiple SELECTs that cannot be auto-scoped.
        return None, (
            "UNION queries must include an explicit FROM `<index>` clause for "
            "each SELECT."
        )
    else:
        # Single SELECT without a FROM: inject one before the first clause
        # keyword (or at the end) to keep clause ordering valid.
        clause_match = _SQL_CLAUSE_KEYWORD.search(top_level)
        insert_at = clause_match.start() if clause_match else len(query)
        quoted = _backtick_quote_sql(index_pattern)
        head = query[:insert_at].rstrip()
        tail = query[insert_at:].strip()
        scoped = f"{head} FROM {quoted}"
        if tail:
            scoped += f" {tail}"

    return _inject_sql_filter(scoped, timeline_ids, time_range), None


def _truncated_export(error, emitted):
    """Build the trailing NDJSON line for an export that stopped early.

    A half-finished download otherwise looks like a finished one, so the line
    states outright that the file is short and how many rows it holds.
    """
    logger.warning("SQL export stopped after %s rows: %s", emitted, error)
    return (
        json.dumps(
            {
                "error": str(error),
                "incomplete": True,
                "rows_returned": emitted,
                "detail": (
                    "This export is incomplete. The cursor stopped returning "
                    "pages before the result set was exhausted."
                ),
            }
        )
        + "\n"
    )


def _close_cursor(api, cursor):
    """Release a cursor's search context on the cluster.

    An export that is cancelled or fails part way leaves its cursor holding a
    context until the cluster's keep-alive expires it. Closing is best effort:
    every row it was going to deliver has already been sent or lost, so a
    failure here is nothing the caller can act on.
    """
    if not cursor:
        return
    try:
        api.close(body={"cursor": cursor})
    except opensearch_exceptions.OpenSearchException as e:
        logger.warning("Could not close the SQL export cursor: %s", e)


class SqlDialect(DirectQueryDialect):
    """OpenSearch SQL."""

    name = "sql"

    def api(self, client):
        return client.plugins.sql

    def validate(self, query):
        if not _SQL_READ_ONLY_LEADING.match(query):
            return (
                "SQL queries must begin with SELECT, SHOW, or DESCRIBE. "
                "Only read operations are allowed."
            )
        return None

    def scope(self, query, index_pattern, timeline_ids, time_range=None):
        return _scope_sql_query(query, index_pattern, timeline_ids, time_range)

    def execute_payload(self, scoped_query, req_json):
        if _SQL_GROUP_BY.search(scoped_query):
            return {"query": scoped_query, "fetch_size": 0}
        return {
            "query": scoped_query,
            "fetch_size": _parse_fetch_size(req_json.get("fetch_size")),
        }

    def stream(self, client, scoped_query):
        """Stream results using cursor-based pagination."""
        api = self.api(client)
        emitted = 0
        cursor = None
        try:
            data = api.query(
                body={
                    "query": scoped_query,
                    "fetch_size": DIRECT_QUERY_EXPORT_PAGE_SIZE,
                },
                request_timeout=EXPORT_TIMEOUT_SECONDS,
            )
            # Taken from every page before its rows are handed out, so that a
            # download abandoned mid-page leaves the live cursor here rather
            # than the spent one that fetched the rows being yielded.
            cursor = data.get("cursor")

            columns = columns_from_schema(data)
            yield json.dumps({"columns": columns}) + "\n"

            rows = data.get("datarows", [])
            for row in rows:
                yield json.dumps(dict(zip(columns, row))) + "\n"
            emitted += len(rows)

            while cursor:
                data = api.query(
                    body={"cursor": cursor},
                    request_timeout=EXPORT_TIMEOUT_SECONDS,
                )
                cursor = data.get("cursor")
                rows = data.get("datarows", [])
                for row in rows:
                    yield json.dumps(dict(zip(columns, row))) + "\n"
                emitted += len(rows)

        except opensearch_exceptions.OpenSearchException as e:
            yield _truncated_export(error_message(e), emitted)
        finally:
            # Reached on a cancelled download too, which is the case that would
            # otherwise hold a context open for nothing.
            _close_cursor(api, cursor)
