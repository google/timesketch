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
"""PPL dialect for direct queries."""

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

# Each export page re-runs the pipeline with a new offset, so a page can take
# considerably longer than a single execute.
EXPORT_TIMEOUT_SECONDS = 120

# Leading "search source=<index>" clause of an already-scoped query.
_PPL_SOURCE_HEAD = re.compile(
    r"^(search\s+source\s*=\s*(?:`[^`]+`|\S+))(.*)$", re.IGNORECASE | re.DOTALL
)

# Same clause, but only the index identifier is captured.
_PPL_SEARCH_SOURCE = re.compile(r"^search\s+source\s*=\s*(`[^`]+`|\S+)", re.IGNORECASE)
_PPL_BARE_SOURCE = re.compile(r"^source\s*=\s*(`[^`]+`|\S+)", re.IGNORECASE)

# A user-supplied "| head" stage, which already bounds the result set.
_PPL_HEAD_STAGE = re.compile(r"\|\s*head\b", re.IGNORECASE)

# Commands that can name an index. Each is anchored to a command position --
# the start of the query, just after a pipe, or just inside a subsearch -- so a
# field that happens to be called `source` or `lookup` is not mistaken for one.
_PPL_COMMAND_HEAD = r"(?:^|\||\[)\s*"
_PPL_IDENTIFIER = r"(`[^`]+`|[^\s|\]]+)"

_PPL_SOURCE_REF = re.compile(
    rf"{_PPL_COMMAND_HEAD}(?:search\s+)?source\s*=\s*{_PPL_IDENTIFIER}", re.IGNORECASE
)
_PPL_LOOKUP_REF = re.compile(
    rf"{_PPL_COMMAND_HEAD}lookup\s+{_PPL_IDENTIFIER}", re.IGNORECASE
)
_PPL_DESCRIBE_REF = re.compile(
    rf"{_PPL_COMMAND_HEAD}describe\s+{_PPL_IDENTIFIER}", re.IGNORECASE
)

# A join, with any combination of the type keywords that may precede it.
_PPL_JOIN_HEAD = re.compile(
    rf"{_PPL_COMMAND_HEAD}"
    r"(?:(?:inner|left|right|full|cross|semi|anti|outer)\s+)*join\b",
    re.IGNORECASE,
)


def _mask_ppl(query):
    """Blank out quoted literals with spaces, preserving offsets.

    A value like ``'x | lookup other y'`` must not read as pipeline structure.
    OpenSearch rejects a quoted index name outright (only bare and backticked
    identifiers are accepted), so nothing an index reference needs is lost by
    masking, and backticks are left intact so names stay readable.
    """
    out = []
    quote = None
    for char in query:
        if quote is not None:
            out.append(" ")
            if char == quote:
                quote = None
            continue
        if char in ("'", '"'):
            quote = char
            out.append(" ")
            continue
        out.append(char)
    return "".join(out)


def _ppl_stage_end(segment):
    """Return the offset of the pipe ending this stage, ignoring subsearches.

    A pipe inside ``[ ... ]`` belongs to the subsearch, not to the stage that
    contains it.
    """
    depth = 0
    for offset, char in enumerate(segment):
        if char == "[":
            depth += 1
        elif char == "]":
            depth = max(depth - 1, 0)
        elif char == "|" and depth == 0:
            return offset
    return len(segment)


def _strip_subsearches(segment):
    """Blank out ``[ ... ]`` spans, leaving the enclosing stage's own tokens.

    A join's ON criteria may itself contain a subsearch, which would otherwise
    supply the trailing token where the right-hand dataset is expected.
    """
    out = []
    depth = 0
    for char in segment:
        if char == "[":
            depth += 1
            out.append(" ")
            continue
        if char == "]":
            depth = max(depth - 1, 0)
            out.append(" ")
            continue
        out.append(" " if depth else char)
    return "".join(out)


def _ppl_join_targets(masked):
    """Return ``(indices, unresolved)`` for the query's join commands.

    A join names its right-hand dataset at the end of the clause, after the ON
    criteria, so the trailing token of the stage is the index. When the stage
    ends in ``]`` that dataset is a subsearch instead, and the index sits
    inside it where the ``source=`` scan picks it up.

    The ON criteria may also hold a subsearch of its own, with the dataset
    still trailing it (``join ... on l.a in [ ... ] idx``). Those spans are
    blanked before the trailing token is read, so the index is still found;
    the subsearch's own ``source=`` is validated separately.
    """
    indices = set()
    unresolved = False

    for match in _PPL_JOIN_HEAD.finditer(masked):
        segment = masked[match.end() :]
        segment = segment[: _ppl_stage_end(segment)].rstrip()
        if segment.endswith("]"):
            continue
        tokens = _strip_subsearches(segment).split()
        if not tokens:
            unresolved = True
            continue
        indices.add(tokens[-1].strip("`"))

    return indices, unresolved


def _ppl_index_references(query):
    """Return ``(indices, unresolved)`` for every index the query names.

    From OpenSearch 3.0 a pipeline can reach a second index through ``lookup``,
    ``join`` or a subsearch, none of which go through the leading ``source=``.
    Validating only the first reference would let any of those read an index
    outside the sketch, so every reference is collected here.

    ``unresolved`` is True when a reference could not be reduced to an
    identifier. Callers must treat that as a scoping failure, the same way the
    SQL dialect does: a reference the allowlist never saw would otherwise pass
    straight through.
    """
    masked = _mask_ppl(query)

    indices = set()
    for pattern in (_PPL_SOURCE_REF, _PPL_LOOKUP_REF, _PPL_DESCRIBE_REF):
        for match in pattern.finditer(masked):
            indices.add(match.group(1).strip("`"))

    join_indices, unresolved = _ppl_join_targets(masked)
    return indices | join_indices, unresolved


def _backtick_quote(index_name):
    """Backtick-quote an index name if it needs quoting for PPL."""
    if index_name.startswith("`") and index_name.endswith("`"):
        return index_name
    return f"`{index_name}`"


def _ppl_timeline_predicate(timeline_ids):
    """PPL predicate scoping rows to the given timelines.

    Keeps rows whose ``__ts_timeline_id`` is in the set, plus legacy rows that
    predate the field, mirroring the explore datastore's behaviour. The caller
    only injects this when some index in the pattern maps the field; where none
    does, the predicate is both an error under Calcite and a no-op.
    """
    ids = ", ".join(str(int(t)) for t in timeline_ids)
    return f"__ts_timeline_id in ({ids}) or isnull(__ts_timeline_id)"


def _ppl_scope_predicate(timeline_ids, time_range):
    """Combine the timeline and time-range predicates into one expression.

    Each part is parenthesised before being ANDed: the timeline predicate holds
    an ``or``, which would otherwise bind more loosely than the ``and`` joining
    it to the time bounds and widen the result set.
    """
    parts = []
    if timeline_ids:
        parts.append(_ppl_timeline_predicate(timeline_ids))
    range_predicate = time_range_predicate(time_range)
    if range_predicate:
        parts.append(range_predicate)

    if not parts:
        return ""
    if len(parts) == 1:
        return parts[0]
    return " and ".join(f"({part})" for part in parts)


def _inject_ppl_filter(query, timeline_ids, time_range):
    """Insert the scoping filter as the first PPL pipe stage.

    The scoped query always starts with ``search source=<...>``; the new
    ``| where`` runs before any user stage, so it filters orphaned/co-located
    rows and out-of-range rows regardless of the rest of the pipeline.
    """
    predicate = _ppl_scope_predicate(timeline_ids, time_range)
    if not predicate:
        return query
    match = _PPL_SOURCE_HEAD.match(query)
    if not match:
        return query
    head, rest = match.group(1), match.group(2).lstrip()
    if rest.startswith("|"):
        rest = rest[1:].lstrip()
    injected = f"{head} | where {predicate}"
    if rest:
        injected += f" | {rest}"
    return injected


def _scope_ppl_query(query, index_pattern, timeline_ids=None, time_range=None):
    """Ensure PPL query targets the sketch indices (and timelines).

    Every index the pipeline names is validated, including those reached by
    ``lookup``, ``join`` or a subsearch. If the query doesn't start with
    'search source=', prepend it. Index names are backtick-quoted for PPL
    compatibility (UUID-style names starting with digits are not valid bare
    identifiers). When timeline_ids is given, a ``__ts_timeline_id`` filter is
    injected so results are scoped to those timelines, not the whole (possibly
    shared) index. A time_range adds a numeric bound on ``timestamp`` in the
    same stage.
    """
    stripped = query.strip()
    allowed = set(index_pattern.split(","))

    # Validate every index the pipeline names, not just the leading source, so
    # a lookup/join/subsearch cannot reach outside the sketch.
    referenced, unresolved = _ppl_index_references(stripped)
    if unresolved:
        return None, (
            "Unable to determine which indices this PPL query targets. "
            "Name the sketch index explicitly."
        )
    for index_name in referenced:
        if index_name not in allowed and index_name != index_pattern:
            return None, "PPL query targets indices outside this sketch."

    if _PPL_SEARCH_SOURCE.match(stripped):
        return _inject_ppl_filter(stripped, timeline_ids, time_range), None

    if stripped.lower().startswith("source") and _PPL_BARE_SOURCE.match(stripped):
        return (
            _inject_ppl_filter(f"search {stripped}", timeline_ids, time_range),
            None,
        )

    quoted = _backtick_quote(index_pattern)
    scoped = f"search source={quoted} | {stripped}"
    return _inject_ppl_filter(scoped, timeline_ids, time_range), None


def _truncated_export(error, emitted, offset):
    """Build the trailing NDJSON line for an export that stopped early.

    Every page re-runs the pipeline and throws away ``offset`` rows, so a deep
    export gets slower page by page until it exceeds the timeout. That failure
    would otherwise look like a completed download, so the line says plainly
    that the file is short, how many rows it holds, and what to do instead.
    """
    logger.warning(
        "PPL export stopped at offset %s after %s rows: %s", offset, emitted, error
    )
    return (
        json.dumps(
            {
                "error": str(error),
                "incomplete": True,
                "rows_returned": emitted,
                "failed_at_offset": offset,
                "detail": (
                    "This export is incomplete. PPL has no cursor, so each page "
                    "re-runs the whole query and skips the rows before it, which "
                    "gets slower the deeper it goes. Narrow the query, or use the "
                    "SQL export, which pages through a cursor instead."
                ),
            }
        )
        + "\n"
    )


class PplDialect(DirectQueryDialect):
    """OpenSearch Piped Processing Language."""

    name = "ppl"

    def api(self, client):
        return client.plugins.ppl

    def validate(self, query):
        """PPL has no write commands, so any non-empty query is read-only."""
        return None

    def scope(self, query, index_pattern, timeline_ids, time_range=None):
        return _scope_ppl_query(query, index_pattern, timeline_ids, time_range)

    def stream(self, client, scoped_query):
        """Stream results using ``head N from M`` pagination."""
        api = self.api(client)
        page_size = DIRECT_QUERY_EXPORT_PAGE_SIZE
        offset = 0
        emitted = 0
        columns = None
        # A user-supplied head already bounds the result set, so paginating on
        # top of it would silently re-run the same rows.
        has_user_head = bool(_PPL_HEAD_STAGE.search(scoped_query))

        try:
            while True:
                if has_user_head:
                    paginated = scoped_query
                else:
                    paginated = f"{scoped_query} | head {page_size} from {offset}"

                data = api.query(
                    body={"query": paginated},
                    request_timeout=EXPORT_TIMEOUT_SECONDS,
                )

                if columns is None:
                    columns = columns_from_schema(data)
                    yield json.dumps({"columns": columns}) + "\n"

                rows = data.get("datarows", [])
                for row in rows:
                    yield json.dumps(dict(zip(columns, row))) + "\n"
                emitted += len(rows)

                if has_user_head or len(rows) < page_size:
                    break
                offset += page_size

        except opensearch_exceptions.OpenSearchException as e:
            yield _truncated_export(error_message(e), emitted, offset)
