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
"""Tests for the direct query dialects and resource shell.

Query scoping helpers are covered by `direct_query_scoping_test.py`; this module
covers the dialect objects, the shared request shell, and the export streaming
paths.
"""

import json
from unittest import mock

import pytest

from flask import Flask
from opensearchpy import exceptions as opensearch_exceptions
from werkzeug.exceptions import HTTPException

from timesketch.api.v1.resources.direct_query import (
    PplQueryExplainResource,
    PplQueryExportResource,
    PplQueryResource,
    SqlQueryExplainResource,
    SqlQueryExportResource,
    SqlQueryResource,
)
from timesketch.api.v1.resources.direct_query.base import (
    columns_from_schema,
    empty_result,
    format_opensearch_error,
    get_sketch_scope,
)
from timesketch.api.v1.resources.direct_query.registry import (
    PPL_DIALECT,
    SQL_DIALECT,
)
from timesketch.api.v1.resources.direct_query.sql import DIRECT_QUERY_MAX_ROWS
from timesketch.api.v1.resources.direct_query import base as base_module
from timesketch.api.v1.resources.direct_query import endpoints
from timesketch.api.v1.resources.direct_query import ppl as ppl_module


@pytest.fixture(autouse=True)
def _stub_opensearch_preflight():
    """Stub the two pre-flight calls _prepare_query makes to OpenSearch.

    Defaults are "field is mapped" and "the plan raises no objection", which is
    the ordinary case. Tests covering either path re-patch locally.
    """
    with mock.patch.object(
        endpoints, "index_pattern_has_timeline_field", return_value=True
    ), mock.patch.object(endpoints, "verify_scope_with_explain", return_value=None):
        yield


@pytest.fixture(autouse=True)
def _reset_shared_client():
    """Keep a client built by one test from leaking into the next."""
    base_module.reset_client()
    yield
    base_module.reset_client()


class _CountingList(list):
    """List that records how many times it has been iterated."""

    def __init__(self, items):
        super().__init__(items)
        self.iter_count = 0

    def __iter__(self):
        self.iter_count += 1
        return super().__iter__()


def _make_timeline(timeline_id, index_name):
    timeline = mock.MagicMock()
    timeline.id = timeline_id
    timeline.searchindex.index_name = index_name
    return timeline


def _make_sketch(timelines, archived=False):
    sketch = mock.MagicMock()
    sketch.timelines = timelines
    sketch.get_status.status = "archived" if archived else "ready"
    return sketch


def _make_client():
    """An OpenSearch client whose plugin namespaces the test drives."""
    return mock.MagicMock()


def _rejected(reason="bad query", status=400):
    """The exception the client raises when the plugin refuses a query."""
    return opensearch_exceptions.TransportError(
        status, "SyntaxError", {"error": {"type": "SyntaxError", "reason": reason}}
    )


def _unreachable(message="down"):
    """The exception the client raises when it cannot reach a node.

    Built the way the connection layer builds it, so that the status code and
    the underlying cause sit where the handling code looks for them.
    """
    return opensearch_exceptions.ConnectionError("N/A", message, Exception(message))


def _timed_out(message="too deep"):
    """The exception the client raises when a request exceeds its timeout."""
    return opensearch_exceptions.ConnectionTimeout(
        "TIMEOUT", message, Exception(message)
    )


# --------------------------------------------------------------------------
# Dialect registry
# --------------------------------------------------------------------------
class TestRegistry:
    def test_ppl_singleton_identity(self):
        assert PPL_DIALECT.name == "ppl"

    def test_sql_singleton_identity(self):
        assert SQL_DIALECT.name == "sql"

    def test_dialects_are_distinct(self):
        assert PPL_DIALECT is not SQL_DIALECT

    def test_reimport_returns_same_instances(self):
        """Resources bind these at import; a per-request instance would leak."""
        # pylint: disable=import-outside-toplevel,reimported
        from timesketch.api.v1.resources.direct_query.registry import (
            PPL_DIALECT as ppl_again,
        )
        from timesketch.api.v1.resources.direct_query.registry import (
            SQL_DIALECT as sql_again,
        )

        assert ppl_again is PPL_DIALECT
        assert sql_again is SQL_DIALECT


# --------------------------------------------------------------------------
# Dialect / client binding
# --------------------------------------------------------------------------
class TestDialectApi:
    """A dialect is bound to its language by the namespace it selects."""

    def test_ppl_uses_the_ppl_namespace(self):
        client = _make_client()
        assert PPL_DIALECT.api(client) is client.plugins.ppl

    def test_sql_uses_the_sql_namespace(self):
        client = _make_client()
        assert SQL_DIALECT.api(client) is client.plugins.sql

    def test_dialects_do_not_share_a_namespace(self):
        client = _make_client()
        assert PPL_DIALECT.api(client) is not SQL_DIALECT.api(client)


# --------------------------------------------------------------------------
# Payload construction
# --------------------------------------------------------------------------
class TestPayloads:
    def test_ppl_execute_payload(self):
        assert PPL_DIALECT.execute_payload("search source=`a`", {}) == {
            "query": "search source=`a`"
        }

    def test_ppl_explain_payload(self):
        assert PPL_DIALECT.explain_payload("search source=`a`") == {
            "query": "search source=`a`"
        }

    def test_sql_group_by_uses_zero_fetch_size(self):
        """Aggregations are only returned in full when fetch_size is 0."""
        payload = SQL_DIALECT.execute_payload(
            "SELECT a, COUNT(*) FROM `i` GROUP BY a", {}
        )
        assert payload["fetch_size"] == 0

    def test_sql_group_by_case_and_spacing(self):
        payload = SQL_DIALECT.execute_payload("SELECT a FROM `i` group   by a", {})
        assert payload["fetch_size"] == 0

    def test_sql_default_fetch_size(self):
        payload = SQL_DIALECT.execute_payload("SELECT * FROM `i`", {})
        assert payload["fetch_size"] == 1000

    def test_sql_respects_requested_fetch_size(self):
        payload = SQL_DIALECT.execute_payload("SELECT * FROM `i`", {"fetch_size": 25})
        assert payload["fetch_size"] == 25

    def test_sql_clamps_fetch_size_to_max(self):
        payload = SQL_DIALECT.execute_payload(
            "SELECT * FROM `i`", {"fetch_size": 10_000_000}
        )
        assert payload["fetch_size"] == DIRECT_QUERY_MAX_ROWS

    def test_sql_null_fetch_size_falls_back_to_default(self):
        payload = SQL_DIALECT.execute_payload("SELECT * FROM `i`", {"fetch_size": None})
        assert payload["fetch_size"] == 1000

    def test_sql_numeric_string_fetch_size(self):
        payload = SQL_DIALECT.execute_payload("SELECT * FROM `i`", {"fetch_size": "25"})
        assert payload["fetch_size"] == 25

    @pytest.mark.parametrize("value", ["abc", "", 0, -5, 3.9, [10], {"n": 1}, True])
    def test_sql_unusable_fetch_size_raises_value_error(self, value):
        """A bad option must surface as a 400, not a comparison TypeError."""
        with pytest.raises(ValueError):
            SQL_DIALECT.execute_payload("SELECT * FROM `i`", {"fetch_size": value})


# --------------------------------------------------------------------------
# get_sketch_scope
# --------------------------------------------------------------------------
class TestGetSketchScope:
    def test_returns_pattern_and_timeline_ids(self):
        sketch = _make_sketch([_make_timeline(1, "aaa"), _make_timeline(2, "bbb")])
        pattern, timeline_ids = get_sketch_scope(sketch)
        assert pattern == "aaa,bbb"
        assert timeline_ids == [1, 2]

    def test_filters_by_timeline_ids(self):
        sketch = _make_sketch(
            [
                _make_timeline(1, "aaa"),
                _make_timeline(2, "bbb"),
                _make_timeline(3, "ccc"),
            ]
        )
        pattern, timeline_ids = get_sketch_scope(sketch, timeline_ids=[1, 3])
        assert pattern == "aaa,ccc"
        assert timeline_ids == [1, 3]

    def test_deduplicates_shared_index(self):
        """Two timelines can share one index; the pattern must list it once."""
        sketch = _make_sketch(
            [_make_timeline(1, "shared"), _make_timeline(2, "shared")]
        )
        pattern, timeline_ids = get_sketch_scope(sketch)
        assert pattern == "shared"
        assert timeline_ids == [1, 2]

    def test_skips_timeline_without_searchindex(self):
        orphan = mock.MagicMock()
        orphan.id = 9
        orphan.searchindex = None
        sketch = _make_sketch([orphan, _make_timeline(1, "aaa")])
        pattern, timeline_ids = get_sketch_scope(sketch)
        assert pattern == "aaa"
        assert timeline_ids == [1]

    def test_empty_sketch(self):
        assert get_sketch_scope(_make_sketch([])) == ("", [])

    def test_no_timeline_matches_the_filter(self):
        sketch = _make_sketch([_make_timeline(1, "aaa")])
        assert get_sketch_scope(sketch, timeline_ids=[99]) == ("", [])

    def test_walks_timelines_once(self):
        """The relationship is lazy-loaded, so it must not be iterated twice."""
        tracker = _CountingList([_make_timeline(1, "aaa")])
        sketch = mock.MagicMock()
        sketch.timelines = tracker
        get_sketch_scope(sketch)
        assert tracker.iter_count == 1


# --------------------------------------------------------------------------
# Response helpers
# --------------------------------------------------------------------------
class TestResponseHelpers:
    def test_columns_from_schema(self):
        data = {"schema": [{"name": "a"}, {"name": "b"}]}
        assert columns_from_schema(data) == ["a", "b"]

    def test_columns_fallback_for_unnamed(self):
        data = {"schema": [{}, {"name": "b"}]}
        assert columns_from_schema(data) == ["col_0", "b"]

    def test_columns_missing_schema(self):
        assert columns_from_schema({}) == []

    def test_format_error_with_details(self):
        data = {
            "error": {
                "type": "SyntaxError",
                "reason": "bad token",
                "details": "line 1",
            }
        }
        assert format_opensearch_error(data) == "SyntaxError: bad token\nline 1"

    def test_format_error_without_details(self):
        data = {"error": {"type": "SyntaxError", "reason": "bad token"}}
        assert format_opensearch_error(data) == "SyntaxError: bad token"

    def test_format_error_non_dict(self):
        assert format_opensearch_error({"error": "boom"}) == "boom"

    def test_empty_result_direct_has_row_fields(self):
        envelope = empty_result(PPL_DIALECT, "boom", "direct")
        assert envelope["language"] == "ppl"
        assert envelope["error"] == "boom"
        assert envelope["columns"] == []
        assert envelope["datarows"] == []
        assert envelope["total"] == 0
        assert envelope["size"] == 0

    def test_empty_result_explain_omits_row_fields(self):
        envelope = empty_result(SQL_DIALECT, "boom", "direct_explain")
        assert envelope["result_type"] == "direct_explain"
        assert envelope["language"] == "sql"
        assert "datarows" not in envelope


# --------------------------------------------------------------------------
# Resource wiring
# --------------------------------------------------------------------------
class TestResourceWiring:
    @pytest.mark.parametrize(
        "resource",
        [PplQueryResource, PplQueryExplainResource, PplQueryExportResource],
    )
    def test_ppl_resources_pin_ppl(self, resource):
        assert resource.dialect is PPL_DIALECT

    @pytest.mark.parametrize(
        "resource",
        [SqlQueryResource, SqlQueryExplainResource, SqlQueryExportResource],
    )
    def test_sql_resources_pin_sql(self, resource):
        assert resource.dialect is SQL_DIALECT


class TestExecuteResourceOptions:
    """The execute resource turns unusable request options into a 400."""

    def setup_method(self):
        self.app = Flask(__name__)
        # Short-circuits @login_required without wiring a LoginManager.
        self.app.config["LOGIN_DISABLED"] = True
        # Short-circuits the cluster capability probe: there is no cluster
        # here for it to ask.
        self.app.config["TESTING"] = True
        self.sketch = _make_sketch([_make_timeline(1, "idx")])

    def _post(self, body):
        with self.app.test_request_context(json=body):
            with mock.patch.object(
                endpoints.Sketch, "get_with_acl", return_value=self.sketch
            ):
                return SqlQueryResource().post(1)

    def test_bad_fetch_size_is_bad_request(self):
        with pytest.raises(HTTPException) as excinfo:
            self._post({"query": "SELECT a", "fetch_size": "abc"})
        assert excinfo.value.code == 400

    def test_negative_fetch_size_is_bad_request(self):
        with pytest.raises(HTTPException) as excinfo:
            self._post({"query": "SELECT a", "fetch_size": -1})
        assert excinfo.value.code == 400


# --------------------------------------------------------------------------
# _prepare_query
# --------------------------------------------------------------------------
class TestPrepareQuery:
    def setup_method(self):
        self.app = Flask(__name__)
        # Short-circuits the cluster capability probe: there is no cluster
        # here for it to ask.
        self.app.config["TESTING"] = True
        self.sketch = _make_sketch([_make_timeline(1, "idx")])

    def _prepare(self, body, dialect=PPL_DIALECT, sketch=None):
        with self.app.test_request_context(json=body):
            with mock.patch.object(
                endpoints.Sketch, "get_with_acl", return_value=sketch or self.sketch
            ):
                return endpoints._prepare_query(1, dialect)

    def test_scopes_ppl_query(self):
        prepared = self._prepare({"query": "stats count()"})
        assert prepared.dialect is PPL_DIALECT
        assert prepared.scoped_query.startswith("search source=`idx`")
        assert "__ts_timeline_id in (1)" in prepared.scoped_query

    def test_scopes_sql_query(self):
        prepared = self._prepare({"query": "SELECT a"}, dialect=SQL_DIALECT)
        assert prepared.dialect is SQL_DIALECT
        assert "FROM `idx`" in prepared.scoped_query
        assert "__ts_timeline_id IN (1)" in prepared.scoped_query

    def test_body_language_is_ignored(self):
        """The route pins the dialect; a `language` field must not re-point it."""
        prepared = self._prepare(
            {"query": "stats count()", "language": "sql"}, dialect=PPL_DIALECT
        )
        assert prepared.dialect is PPL_DIALECT

    def test_empty_query_is_bad_request(self):
        with pytest.raises(HTTPException) as excinfo:
            self._prepare({"query": "   "})
        assert excinfo.value.code == 400

    def test_sql_write_is_bad_request(self):
        with pytest.raises(HTTPException) as excinfo:
            self._prepare({"query": "DELETE FROM idx"}, dialect=SQL_DIALECT)
        assert excinfo.value.code == 400

    def test_missing_sketch_is_not_found(self):
        with self.app.test_request_context(json={"query": "x"}):
            with mock.patch.object(endpoints.Sketch, "get_with_acl", return_value=None):
                with pytest.raises(HTTPException) as excinfo:
                    endpoints._prepare_query(1, PPL_DIALECT)
        assert excinfo.value.code == 404

    def test_archived_sketch_is_bad_request(self):
        archived = _make_sketch([_make_timeline(1, "idx")], archived=True)
        with pytest.raises(HTTPException) as excinfo:
            self._prepare({"query": "x"}, sketch=archived)
        assert excinfo.value.code == 400

    def test_sketch_without_indices_is_bad_request(self):
        with pytest.raises(HTTPException) as excinfo:
            self._prepare({"query": "x"}, sketch=_make_sketch([]))
        assert excinfo.value.code == 400

    def test_out_of_sketch_index_is_forbidden(self):
        with pytest.raises(HTTPException) as excinfo:
            self._prepare({"query": "source=other | head 1"})
        assert excinfo.value.code == 403

    @pytest.mark.parametrize("query", [5, ["stats count()"], {"q": 1}, True])
    def test_non_string_query_is_bad_request(self, query):
        """A wrong-typed query must 400, not fail inside .strip()."""
        with pytest.raises(HTTPException) as excinfo:
            self._prepare({"query": query})
        assert excinfo.value.code == 400

    @pytest.mark.parametrize("timeline_ids", [1, "1", {"a": 1}, ["abc"], [None]])
    def test_bad_timeline_ids_is_bad_request(self, timeline_ids):
        with pytest.raises(HTTPException) as excinfo:
            self._prepare({"query": "stats count()", "timeline_ids": timeline_ids})
        assert excinfo.value.code == 400

    def test_numeric_string_timeline_ids_are_accepted(self):
        prepared = self._prepare({"query": "stats count()", "timeline_ids": ["1"]})
        assert "__ts_timeline_id in (1)" in prepared.scoped_query

    def test_timeline_ids_may_be_omitted(self):
        prepared = self._prepare({"query": "stats count()"})
        assert "__ts_timeline_id in (1)" in prepared.scoped_query

    def _prepare_without_field(self, body, dialect=PPL_DIALECT):
        with mock.patch.object(
            endpoints, "index_pattern_has_timeline_field", return_value=False
        ):
            return self._prepare(body, dialect=dialect)

    def test_ppl_predicate_dropped_when_index_lacks_the_field(self):
        """Naming an unmapped field is a hard error under Calcite."""
        prepared = self._prepare_without_field({"query": "stats count()"})
        assert "__ts_timeline_id" not in prepared.scoped_query
        assert prepared.scoped_query.startswith("search source=`idx`")

    def test_sql_predicate_dropped_when_index_lacks_the_field(self):
        prepared = self._prepare_without_field(
            {"query": "SELECT a"}, dialect=SQL_DIALECT
        )
        assert "__ts_timeline_id" not in prepared.scoped_query
        assert "FROM `idx`" in prepared.scoped_query

    def test_plan_objection_is_forbidden(self):
        """The plan check can veto even when the dialect was satisfied."""
        with mock.patch.object(
            endpoints,
            "verify_scope_with_explain",
            return_value="PPL query targets indices outside this sketch.",
        ):
            with pytest.raises(HTTPException) as excinfo:
                self._prepare({"query": "stats count()"})
        assert excinfo.value.code == 403

    def test_plan_check_sees_the_scoped_query_and_allowlist(self):
        with mock.patch.object(
            endpoints, "verify_scope_with_explain", return_value=None
        ) as verify:
            self._prepare({"query": "stats count()"})
        scoped_query, allowed = verify.call_args[0][1:]
        assert scoped_query.startswith("search source=`idx`")
        assert allowed == ["idx"]

    def test_probe_is_asked_about_the_sketch_indices(self):
        with mock.patch.object(
            endpoints, "index_pattern_has_timeline_field", return_value=True
        ) as probe:
            self._prepare({"query": "stats count()"})
        assert probe.call_args[0][0] == "idx"

    def test_non_json_body_is_bad_request(self):
        with self.app.test_request_context(data="not json"):
            with mock.patch.object(
                endpoints.Sketch, "get_with_acl", return_value=self.sketch
            ):
                with pytest.raises(HTTPException) as excinfo:
                    endpoints._prepare_query(1, PPL_DIALECT)
        assert excinfo.value.code == 400


# --------------------------------------------------------------------------
# Timeline field mapping probe
# --------------------------------------------------------------------------
class TestTimelineFieldProbe:
    def setup_method(self):
        base_module._timeline_field_cache.clear()

    teardown_method = setup_method

    @staticmethod
    def _mapping(*present):
        return {
            name: {"mappings": {"__ts_timeline_id": {}} if is_present else {}}
            for name, is_present in present
        }

    @staticmethod
    def _client(mapping=None, error=None):
        client = _make_client()
        if error is not None:
            client.indices.get_field_mapping.side_effect = error
        else:
            client.indices.get_field_mapping.return_value = mapping
        return client

    def _probe(self, index_pattern="idx", **client_kwargs):
        client = self._client(**client_kwargs)
        with mock.patch.object(base_module, "get_client", return_value=client):
            result = base_module.index_pattern_has_timeline_field(index_pattern)
        return result, client.indices.get_field_mapping

    def test_true_when_the_index_maps_the_field(self):
        result, _ = self._probe(mapping=self._mapping(("idx", True)))
        assert result is True

    def test_false_when_no_index_maps_the_field(self):
        result, _ = self._probe(mapping=self._mapping(("idx", False)))
        assert result is False

    def test_false_when_the_response_is_empty(self):
        result, _ = self._probe(mapping={})
        assert result is False

    def test_true_when_any_index_in_the_pattern_maps_it(self):
        """A multi-index query resolves the field from the union of mappings."""
        result, _ = self._probe(
            index_pattern="a,b", mapping=self._mapping(("a", False), ("b", True))
        )
        assert result is True

    # Failing open keeps the predicate on: a loud query error beats silently
    # widening a query's scope because a mapping call did not come back.
    def test_true_when_opensearch_errors(self):
        result, _ = self._probe(error=_rejected(status=500))
        assert result is True

    def test_true_when_the_response_cannot_be_deserialised(self):
        result, _ = self._probe(
            error=opensearch_exceptions.SerializationError("not json")
        )
        assert result is True

    def test_true_when_the_request_raises(self):
        result, _ = self._probe(error=_unreachable("no"))
        assert result is True

    def _cached_probe(self, *patterns):
        """Run the probe over several patterns against one client."""
        client = self._client(mapping=self._mapping(("idx", True)))
        with mock.patch.object(base_module, "get_client", return_value=client):
            for pattern in patterns:
                base_module.index_pattern_has_timeline_field(pattern)
        return client.indices.get_field_mapping

    def test_result_is_cached(self):
        assert self._cached_probe("idx", "idx", "idx").call_count == 1

    def test_distinct_patterns_are_cached_separately(self):
        assert self._cached_probe("a", "b").call_count == 2

    def test_expired_entry_is_refetched(self):
        client = self._client(mapping=self._mapping(("idx", True)))
        with mock.patch.object(base_module, "get_client", return_value=client):
            base_module.index_pattern_has_timeline_field("idx")
            expires_at, value = base_module._timeline_field_cache["idx"]
            base_module._timeline_field_cache["idx"] = (expires_at - 10_000, value)
            base_module.index_pattern_has_timeline_field("idx")
        assert client.indices.get_field_mapping.call_count == 2

    def test_cache_growth_is_bounded(self):
        limit = base_module.TIMELINE_FIELD_CACHE_MAX_ENTRIES
        self._cached_probe(*[f"idx{i}" for i in range(limit + 5)])
        assert len(base_module._timeline_field_cache) <= limit

    def test_probe_asks_only_for_the_timeline_field(self):
        _, get_field_mapping = self._probe(mapping=self._mapping(("idx", True)))
        assert get_field_mapping.call_args.kwargs == {
            "fields": "__ts_timeline_id",
            "index": "idx",
            "ignore_unavailable": True,
            "request_timeout": base_module.MAPPING_TIMEOUT_SECONDS,
        }


# --------------------------------------------------------------------------
# Execution-plan index extraction
#
# The plan bodies below are trimmed copies of real 3.7.0 responses, so the
# extractor is tested against shapes the cluster actually returns.
# --------------------------------------------------------------------------
def _calcite_plan(*indices):
    scans = "\n".join(
        f"  CalciteLogicalIndexScan(table=[[OpenSearch, {name}]])" for name in indices
    )
    return {"calcite": {"logical": f"LogicalAggregate(group=[{{}}])\n{scans}\n"}}


class TestPlanIndices:
    def test_calcite_single_index(self):
        assert base_module.plan_indices(_calcite_plan("idx")) == {"idx"}

    def test_calcite_multi_index_pattern_is_split(self):
        """One scan over `a,b` is two indices, both of which need checking."""
        assert base_module.plan_indices(_calcite_plan("a,b")) == {"a", "b"}

    def test_calcite_join_reports_both_scans(self):
        assert base_module.plan_indices(_calcite_plan("a", "b")) == {"a", "b"}

    def test_v2_request_string(self):
        plan = {
            "root": {
                "name": "ProjectOperator",
                "children": [
                    {
                        "name": "OpenSearchIndexScan",
                        "description": {
                            "request": "OpenSearchQueryRequest(indexName=idx, "
                            'sourceBuilder={"from":0})'
                        },
                    }
                ],
            }
        }
        assert base_module.plan_indices(plan) == {"idx"}

    def test_v2_request_string_multi_index(self):
        plan = {
            "root": {
                "description": {
                    "request": "OpenSearchQueryRequest(indexName=a,b, "
                    'sourceBuilder={"from":0})'
                }
            }
        }
        assert base_module.plan_indices(plan) == {"a", "b"}

    def test_v2_join_table_names(self):
        """A SQL join names its tables in tableName, not a request string."""
        plan = {
            "Logical Plan": {
                "Join [ conditions=( a.m = b.m ) ]": {
                    "Group": [
                        {"TableScan": {"tableAlias": "a", "tableName": "idx_a"}},
                        {"TableScan": {"tableAlias": "b", "tableName": "idx_b"}},
                    ]
                }
            }
        }
        assert base_module.plan_indices(plan) == {"idx_a", "idx_b"}

    def test_unrecognised_plan_yields_nothing(self):
        assert base_module.plan_indices({"something": "else"}) == set()


class TestVerifyScopeWithExplain:
    @staticmethod
    def _verify(allowed, plan=None, error=None):
        client = _make_client()
        if error is not None:
            client.plugins.ppl.explain.side_effect = error
        else:
            client.plugins.ppl.explain.return_value = plan
        with mock.patch.object(base_module, "get_client", return_value=client):
            result = base_module.verify_scope_with_explain(
                PPL_DIALECT, "search source=`idx`", allowed
            )
        return result, client

    def test_no_objection_when_plan_stays_in_the_sketch(self):
        result, _ = self._verify(["idx"], plan=_calcite_plan("idx"))
        assert result is None

    # SECURITY: this is the case the dialect regexes can miss.
    def test_rejects_an_index_the_dialect_did_not_catch(self):
        error, _ = self._verify(["idx"], plan=_calcite_plan("idx", "other"))
        assert error is not None
        assert "outside this sketch" in error

    def test_multi_index_pattern_all_in_sketch(self):
        result, _ = self._verify(["a", "b"], plan=_calcite_plan("a,b"))
        assert result is None

    def test_multi_index_pattern_partly_outside(self):
        result, _ = self._verify(["a"], plan=_calcite_plan("a,b"))
        assert result is not None

    # Falling back to the dialect's own (fail-closed) result beats taking the
    # feature down when a plan cannot be read.
    def test_unreadable_plan_raises_no_objection(self):
        result, _ = self._verify(["idx"], plan={"unknown": "shape"})
        assert result is None

    def test_explain_error_raises_no_objection(self):
        result, _ = self._verify(["idx"], error=_rejected())
        assert result is None

    def test_undeserialisable_plan_raises_no_objection(self):
        result, _ = self._verify(
            ["idx"], error=opensearch_exceptions.SerializationError("not json")
        )
        assert result is None

    def test_connection_failure_raises_no_objection(self):
        result, _ = self._verify(["idx"], error=_unreachable("no"))
        assert result is None

    def test_it_explains_rather_than_executing(self):
        _, client = self._verify(["idx"], plan=_calcite_plan("idx"))
        client.plugins.ppl.explain.assert_called_once()
        client.plugins.ppl.query.assert_not_called()


# --------------------------------------------------------------------------
# PPL export streaming
# --------------------------------------------------------------------------
class TestPplStream:
    @staticmethod
    def _client(pages=None, error=None):
        client = _make_client()
        if error is not None:
            client.plugins.ppl.query.side_effect = error
        elif isinstance(pages, list):
            client.plugins.ppl.query.side_effect = pages
        else:
            client.plugins.ppl.query.return_value = pages
        return client

    def test_single_page(self):
        client = self._client({"schema": [{"name": "a"}], "datarows": [["x"], ["y"]]})
        lines = list(PPL_DIALECT.stream(client, "search source=`i`"))
        assert json.loads(lines[0]) == {"columns": ["a"]}
        assert json.loads(lines[1]) == {"a": "x"}
        assert json.loads(lines[2]) == {"a": "y"}

    def test_paginates_until_short_page(self):
        client = self._client(
            [
                {"schema": [{"name": "a"}], "datarows": [["1"], ["2"]]},
                {"schema": [{"name": "a"}], "datarows": [["3"]]},
            ]
        )
        with mock.patch.object(ppl_module, "DIRECT_QUERY_EXPORT_PAGE_SIZE", 2):
            lines = list(PPL_DIALECT.stream(client, "search source=`i`"))

        assert [json.loads(x) for x in lines[1:]] == [
            {"a": "1"},
            {"a": "2"},
            {"a": "3"},
        ]
        first, second = client.plugins.ppl.query.call_args_list
        assert "head 2 from 0" in first.kwargs["body"]["query"]
        assert "head 2 from 2" in second.kwargs["body"]["query"]

    def test_user_head_is_not_paginated(self):
        """A user-supplied head already bounds the result set."""
        client = self._client({"schema": [{"name": "a"}], "datarows": [["1"], ["2"]]})
        with mock.patch.object(ppl_module, "DIRECT_QUERY_EXPORT_PAGE_SIZE", 2):
            list(PPL_DIALECT.stream(client, "search source=`i` | head 2"))
        query = client.plugins.ppl.query
        assert query.call_count == 1
        assert "head 2 from" not in query.call_args.kwargs["body"]["query"]

    def test_rejected_query_yields_error_line(self):
        client = self._client(error=_rejected("bad query"))
        lines = list(PPL_DIALECT.stream(client, "search source=`i`"))
        assert "bad query" in json.loads(lines[0])["error"]

    def test_failure_mid_export_is_marked_incomplete(self):
        """A short download must not be mistakable for a finished one."""
        client = self._client(
            [
                {"schema": [{"name": "a"}], "datarows": [[i] for i in range(2)]},
                _timed_out(),
            ]
        )
        with mock.patch.object(ppl_module, "DIRECT_QUERY_EXPORT_PAGE_SIZE", 2):
            lines = list(PPL_DIALECT.stream(client, "search source=`i`"))

        trailer = json.loads(lines[-1])
        assert trailer["incomplete"] is True
        assert trailer["rows_returned"] == 2
        assert trailer["failed_at_offset"] == 2
        assert "SQL export" in trailer["detail"]

    def test_connection_error_yields_error_line(self):
        client = self._client(error=_unreachable())
        lines = list(PPL_DIALECT.stream(client, "search source=`i`"))
        assert "down" in json.loads(lines[0])["error"]

    def test_stream_is_lazy(self):
        """Building the generator must not issue a request."""
        client = self._client({})
        PPL_DIALECT.stream(client, "search source=`i`")
        client.plugins.ppl.query.assert_not_called()


# --------------------------------------------------------------------------
# SQL export streaming
# --------------------------------------------------------------------------
class TestSqlStream:
    @staticmethod
    def _client(pages=None, error=None):
        client = _make_client()
        if error is not None:
            client.plugins.sql.query.side_effect = error
        elif isinstance(pages, list):
            client.plugins.sql.query.side_effect = pages
        else:
            client.plugins.sql.query.return_value = pages
        return client

    def test_single_page(self):
        client = self._client({"schema": [{"name": "a"}], "datarows": [["x"]]})
        lines = list(SQL_DIALECT.stream(client, "SELECT a FROM `i`"))
        assert json.loads(lines[0]) == {"columns": ["a"]}
        assert json.loads(lines[1]) == {"a": "x"}

    def test_follows_cursor(self):
        client = self._client(
            [
                {"schema": [{"name": "a"}], "datarows": [["1"]], "cursor": "c1"},
                {"datarows": [["2"]], "cursor": "c2"},
                {"datarows": [["3"]]},
            ]
        )
        lines = list(SQL_DIALECT.stream(client, "SELECT a FROM `i`"))

        assert [json.loads(x) for x in lines[1:]] == [
            {"a": "1"},
            {"a": "2"},
            {"a": "3"},
        ]
        calls = client.plugins.sql.query.call_args_list
        assert calls[1].kwargs["body"] == {"cursor": "c1"}
        assert calls[2].kwargs["body"] == {"cursor": "c2"}

    def test_cursor_reuses_first_page_columns(self):
        client = self._client(
            [
                {"schema": [{"name": "a"}], "datarows": [], "cursor": "c1"},
                {"datarows": [["2"]]},
            ]
        )
        lines = list(SQL_DIALECT.stream(client, "SELECT a FROM `i`"))
        assert json.loads(lines[-1]) == {"a": "2"}

    def test_rejected_query_yields_error_line(self):
        client = self._client(error=_rejected("bad sql"))
        lines = list(SQL_DIALECT.stream(client, "SELECT a FROM `i`"))
        assert "bad sql" in json.loads(lines[0])["error"]

    def test_cursor_failure_is_marked_incomplete(self):
        """Rows already streamed are counted, so a short file is obvious."""
        client = self._client(
            [
                {"schema": [{"name": "a"}], "datarows": [["1"]], "cursor": "c1"},
                _rejected("cursor is gone", status=500),
            ]
        )
        lines = list(SQL_DIALECT.stream(client, "SELECT a FROM `i`"))

        trailer = json.loads(lines[-1])
        assert "cursor is gone" in trailer["error"]
        assert trailer["incomplete"] is True
        assert trailer["rows_returned"] == 1

    def test_connection_error_yields_error_line(self):
        client = self._client(error=_unreachable())
        lines = list(SQL_DIALECT.stream(client, "SELECT a FROM `i`"))
        assert "down" in json.loads(lines[0])["error"]

    def test_stream_is_lazy(self):
        client = self._client({})
        SQL_DIALECT.stream(client, "SELECT a FROM `i`")
        client.plugins.sql.query.assert_not_called()

    def test_exhausted_cursor_needs_no_closing(self):
        """The last page returns no cursor, so there is no context left."""
        client = self._client(
            [
                {"schema": [{"name": "a"}], "datarows": [["1"]], "cursor": "c1"},
                {"datarows": [["2"]]},
            ]
        )
        list(SQL_DIALECT.stream(client, "SELECT a FROM `i`"))
        client.plugins.sql.close.assert_not_called()

    @pytest.mark.parametrize(
        "consumed,expected_cursor",
        # Abandoning during the first page must close it too, not only a page
        # reached through the cursor loop.
        [(1, "c1"), (2, "c1"), (3, "c2")],
    )
    def test_abandoned_download_closes_the_live_cursor(self, consumed, expected_cursor):
        """A cancelled export must not leave a context held on the cluster."""
        client = self._client(
            [
                {"schema": [{"name": "a"}], "datarows": [["1"]], "cursor": "c1"},
                {"datarows": [["2"]], "cursor": "c2"},
            ]
        )
        generator = SQL_DIALECT.stream(client, "SELECT a FROM `i`")
        for _ in range(consumed):
            next(generator)
        generator.close()

        client.plugins.sql.close.assert_called_once_with(
            body={"cursor": expected_cursor}
        )

    def test_a_failed_close_does_not_break_the_export(self):
        client = self._client(
            [
                {"schema": [{"name": "a"}], "datarows": [["1"]], "cursor": "c1"},
                _unreachable(),
            ]
        )
        client.plugins.sql.close.side_effect = _unreachable("also down")
        lines = list(SQL_DIALECT.stream(client, "SELECT a FROM `i`"))
        assert json.loads(lines[-1])["incomplete"] is True
