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
"""Tests for the helpers that scope a direct query to a sketch.

Read-only validation, index and timeline scoping, time range handling and the
cluster capability probe. The dialects, the request shell and the export paths
are covered by `direct_query_test.py`.
"""

import pytest
from unittest import mock

from flask import Flask

from timesketch.api.v1.resources.direct_query import base as base_module
from timesketch.api.v1.resources.direct_query.base import (
    configure_client,
    parse_time_range,
    time_range_predicate,
    validate_query,
)
from timesketch.api.v1.resources.direct_query import capability
from timesketch.api.v1.resources.direct_query.capability import (
    MINIMUM_OPENSEARCH_VERSION,
    _plugin_supported,
    _version_supported,
    direct_query_support,
)
from timesketch.api.v1.resources.direct_query.ppl import (
    _backtick_quote,
    _inject_ppl_filter,
    _ppl_timeline_predicate,
    _scope_ppl_query,
)
from timesketch.api.v1.resources.direct_query.registry import PPL_DIALECT
from timesketch.api.v1.resources.direct_query.registry import SQL_DIALECT
from timesketch.api.v1.resources.direct_query.sql import (
    _inject_sql_filter,
    _scope_sql_query,
    _sql_single_from_target,
    _sql_timeline_predicate,
)


# --------------------------------------------------------------------------
# _backtick_quote
# --------------------------------------------------------------------------
class TestBacktickQuote:
    def test_bare_name(self):
        assert _backtick_quote("abc123") == "`abc123`"

    def test_digit_starting_name(self):
        assert _backtick_quote("21819512ab7649eb") == "`21819512ab7649eb`"

    def test_already_quoted(self):
        assert _backtick_quote("`already_quoted`") == "`already_quoted`"

    def test_comma_separated(self):
        result = _backtick_quote("idx1,idx2")
        assert result == "`idx1,idx2`"


# --------------------------------------------------------------------------
# validate_query
# --------------------------------------------------------------------------
class TestValidateQuery:
    def test_empty_query(self):
        assert validate_query("", PPL_DIALECT) is not None
        assert validate_query("   ", "sql") is not None

    def test_valid_ppl(self):
        assert validate_query("stats count() by data_type", PPL_DIALECT) is None

    def test_valid_sql(self):
        assert validate_query("SELECT * LIMIT 10", SQL_DIALECT) is None

    def test_valid_sql_show(self):
        assert validate_query("SHOW TABLES LIKE foo", SQL_DIALECT) is None

    def test_valid_sql_describe(self):
        assert validate_query("DESCRIBE TABLES LIKE foo", SQL_DIALECT) is None

    def test_valid_sql_leading_whitespace_and_paren(self):
        assert validate_query("  (SELECT 1)", SQL_DIALECT) is None

    # Write/DDL statements are rejected because they do not begin with an
    # allowlisted read-only keyword (SELECT/SHOW/DESCRIBE).
    def test_forbidden_delete(self):
        result = validate_query("DELETE FROM foo", SQL_DIALECT)
        assert result is not None
        assert "read operations" in result.lower()

    def test_forbidden_drop(self):
        result = validate_query("DROP INDEX myindex", SQL_DIALECT)
        assert result is not None

    def test_forbidden_insert(self):
        result = validate_query("INSERT INTO foo VALUES (1)", SQL_DIALECT)
        assert result is not None

    def test_forbidden_update(self):
        result = validate_query("UPDATE foo SET bar=1", SQL_DIALECT)
        assert result is not None

    def test_forbidden_create_index(self):
        result = validate_query("CREATE INDEX idx ON foo", SQL_DIALECT)
        assert result is not None

    def test_forbidden_alter(self):
        result = validate_query("ALTER INDEX foo", SQL_DIALECT)
        assert result is not None

    def test_keyword_substring_allowed(self):
        """'updated' inside a field name should not trigger the filter."""
        assert validate_query("SELECT last_updated LIMIT 10", SQL_DIALECT) is None

    # A write verb is only a write verb in the leading keyword. Appearing in a
    # string literal or a value makes it data, and the query stays readable.
    def test_sql_literal_delete_allowed(self):
        assert (
            validate_query("SELECT message WHERE message LIKE '%delete%'", SQL_DIALECT)
            is None
        )

    def test_sql_literal_drop_in_value_allowed(self):
        assert (
            validate_query("SELECT message WHERE action = 'DROP'", SQL_DIALECT) is None
        )

    def test_ppl_literal_drop_allowed(self):
        """PPL is query-only; literals like 'drop' must not be rejected."""
        assert validate_query("where like(message, '%drop%')", PPL_DIALECT) is None

    def test_ppl_not_keyword_restricted(self):
        """PPL has no leading-keyword allowlist (many valid first commands)."""
        assert validate_query("stats count() by action", PPL_DIALECT) is None


# --------------------------------------------------------------------------
# _scope_ppl_query
# --------------------------------------------------------------------------
class TestScopePplQuery:
    INDEX = "1111aaaa2222bbbb3333cccc4444dddd"

    def test_auto_prepend_source(self):
        query, err = _scope_ppl_query("stats count()", self.INDEX)
        assert err is None
        assert query.startswith("search source=`")
        assert self.INDEX in query
        assert "| stats count()" in query

    def test_auto_prepend_preserves_pipe(self):
        query, err = _scope_ppl_query(
            "where message LIKE '%error%' | head 10", self.INDEX
        )
        assert err is None
        assert "| where message" in query

    def test_existing_search_source_valid(self):
        raw = f"search source=`{self.INDEX}` | stats count()"
        query, err = _scope_ppl_query(raw, self.INDEX)
        assert err is None
        assert query == raw

    def test_existing_search_source_invalid(self):
        query, err = _scope_ppl_query(
            "search source=`otherindex` | stats count()", self.INDEX
        )
        assert query is None
        assert "outside this sketch" in err

    def test_source_shorthand(self):
        raw = f"source={self.INDEX} | head 100"
        query, err = _scope_ppl_query(raw, self.INDEX)
        assert err is None
        assert query.startswith("search source=")

    def test_source_shorthand_invalid(self):
        query, err = _scope_ppl_query("source=badindex | head 10", self.INDEX)
        assert query is None
        assert "outside this sketch" in err

    def test_multi_index_quoting(self):
        multi = "idx1,idx2,idx3"
        query, err = _scope_ppl_query("stats count()", multi)
        assert err is None
        assert "`idx1,idx2,idx3`" in query

    def test_existing_source_bare_unquoted(self):
        raw = f"search source={self.INDEX} | head 10"
        query, err = _scope_ppl_query(raw, self.INDEX)
        assert err is None
        assert query == raw


# --------------------------------------------------------------------------
# _scope_ppl_query: indices reached without the leading source=
#
# SECURITY: from OpenSearch 3.0 a pipeline can read a second index through
# lookup, join or a subsearch. Validating only the leading source= let those
# cross sketch boundaries, so every reference has to be checked.
# --------------------------------------------------------------------------
class TestScopePplCrossIndex:
    INDEX = "1111aaaa2222bbbb3333cccc4444dddd"
    OTHER = "aaaa1111bbbb2222cccc3333dddd4444"

    @pytest.mark.parametrize(
        "raw",
        [
            "search source=`{idx}` | lookup `{other}` message",
            "search source=`{idx}` | lookup {other} message",
            "search source=`{idx}` | join left=l right=r on l.a = r.a `{other}`",
            "search source=`{idx}` | left join on l.a = r.a {other}",
            "search source=`{idx}` | join left=l right=r on l.a = r.a "
            "[ source=`{other}` ]",
            "search source=`{idx}` | where a in [ source=`{other}` | fields a ]",
            "search source=`{idx}` | where a in [ search source={other} ]",
        ],
    )
    def test_foreign_index_rejected(self, raw):
        query, err = _scope_ppl_query(
            raw.format(idx=self.INDEX, other=self.OTHER), self.INDEX
        )
        assert query is None
        assert "outside this sketch" in err

    @pytest.mark.parametrize(
        "raw",
        [
            "search source=`{idx}` | lookup `{idx}` message",
            "search source=`{idx}` | join left=l right=r on l.a = r.a `{idx}`",
            "search source=`{idx}` | where a in [ source=`{idx}` | fields a ]",
        ],
    )
    def test_same_index_allowed(self, raw):
        query, err = _scope_ppl_query(raw.format(idx=self.INDEX), self.INDEX)
        assert err is None
        assert query is not None

    def test_join_without_a_dataset_is_rejected(self):
        """An unparseable reference fails closed, as on the SQL side."""
        query, err = _scope_ppl_query(
            f"search source=`{self.INDEX}` | join ", self.INDEX
        )
        assert query is None
        assert "Unable to determine which indices" in err

    # A join's ON criteria can hold its own subsearch, with the right-hand
    # dataset still trailing it. Both positions have to be checked.
    def test_join_with_subsearch_in_criteria_checks_trailing_index(self):
        query, err = _scope_ppl_query(
            f"search source=`{self.INDEX}` | join left=l right=r on l.a in "
            f"[ source=`{self.INDEX}` | fields a ] `{self.OTHER}`",
            self.INDEX,
        )
        assert query is None
        assert "outside this sketch" in err

    def test_join_with_subsearch_in_criteria_checks_the_subsearch(self):
        query, err = _scope_ppl_query(
            f"search source=`{self.INDEX}` | join left=l right=r on l.a in "
            f"[ source=`{self.OTHER}` | fields a ] `{self.INDEX}`",
            self.INDEX,
        )
        assert query is None
        assert "outside this sketch" in err

    def test_join_with_subsearch_in_criteria_allowed_when_both_in_sketch(self):
        query, err = _scope_ppl_query(
            f"search source=`{self.INDEX}` | join left=l right=r on l.a in "
            f"[ source=`{self.INDEX}` | fields a ] `{self.INDEX}`",
            self.INDEX,
        )
        assert err is None
        assert query is not None

    def test_describe_of_foreign_index_rejected(self):
        query, err = _scope_ppl_query(f"describe {self.OTHER}", self.INDEX)
        assert query is None
        assert "outside this sketch" in err

    # A command name inside a literal is data, not pipeline structure.
    @pytest.mark.parametrize(
        "raw",
        [
            "search source=`{idx}` | where message = 'x | lookup evil y'",
            'search source=`{idx}` | where message = "a | join on b evil"',
            "search source=`{idx}` | where message = 'source=evil'",
        ],
    )
    def test_literal_mentioning_a_command_is_not_a_reference(self, raw):
        query, err = _scope_ppl_query(raw.format(idx=self.INDEX), self.INDEX)
        assert err is None
        assert query is not None

    def test_field_named_source_is_not_a_reference(self):
        query, err = _scope_ppl_query(
            f"search source=`{self.INDEX}` | where source = 5", self.INDEX
        )
        assert err is None
        assert query is not None

    def test_multi_index_pattern_allowed_in_lookup(self):
        multi = f"{self.INDEX},{self.OTHER}"
        query, err = _scope_ppl_query(
            f"search source=`{multi}` | lookup `{self.OTHER}` message", multi
        )
        assert err is None
        assert query is not None


# --------------------------------------------------------------------------
# _scope_sql_query
# --------------------------------------------------------------------------
class TestScopeSqlQuery:
    INDEX = "1111aaaa2222bbbb3333cccc4444dddd"

    def test_auto_inject_from(self):
        query, err = _scope_sql_query(
            "SELECT data_type, COUNT(*) GROUP BY data_type", self.INDEX
        )
        assert err is None
        assert f"FROM `{self.INDEX}`" in query

    def test_existing_from_valid(self):
        raw = f"SELECT * FROM {self.INDEX} LIMIT 10"
        query, err = _scope_sql_query(raw, self.INDEX)
        assert err is None
        assert query == raw

    def test_existing_from_invalid(self):
        query, err = _scope_sql_query("SELECT * FROM otherindex LIMIT 10", self.INDEX)
        assert query is None
        assert "outside this sketch" in err

    def test_select_with_where(self):
        query, err = _scope_sql_query(
            "SELECT message WHERE message LIKE '%error%' LIMIT 10", self.INDEX
        )
        assert err is None
        assert f"FROM `{self.INDEX}`" in query
        assert "WHERE" in query

    def test_select_with_order(self):
        query, err = _scope_sql_query(
            "SELECT datetime ORDER BY datetime DESC LIMIT 10", self.INDEX
        )
        assert err is None
        assert f"FROM `{self.INDEX}`" in query

    def test_select_with_group(self):
        query, err = _scope_sql_query(
            "SELECT data_type, COUNT(*) as cnt GROUP BY data_type", self.INDEX
        )
        assert err is None
        assert f"FROM `{self.INDEX}`" in query
        assert "GROUP BY" in query

    # --- clause ordering: an injected FROM has to precede HAVING ---
    def test_having_without_group_injects_from_before_having(self):
        query, err = _scope_sql_query(
            "SELECT COUNT(*) c HAVING COUNT(*) > 1", self.INDEX
        )
        assert err is None
        assert query == f"SELECT COUNT(*) c FROM `{self.INDEX}` HAVING COUNT(*) > 1"

    def test_no_clause_appends_from_at_end(self):
        query, err = _scope_sql_query("SELECT COUNT(*)", self.INDEX)
        assert err is None
        assert query == f"SELECT COUNT(*) FROM `{self.INDEX}`"

    # --- FROM-sub-query: the index sits in the inner FROM, not the outer ---
    def test_from_subquery_inner_index_valid(self):
        raw = (
            f"SELECT t.dt FROM (SELECT data_type AS dt FROM `{self.INDEX}` "
            "LIMIT 5) t LIMIT 2"
        )
        query, err = _scope_sql_query(raw, self.INDEX)
        assert err is None
        assert query == raw

    def test_from_subquery_inner_index_outside_sketch(self):
        raw = "SELECT t.dt FROM (SELECT data_type AS dt FROM `evilindex` LIMIT 5) t"
        query, err = _scope_sql_query(raw, self.INDEX)
        assert query is None
        assert "outside this sketch" in err

    # --- IN-sub-query without an outer FROM: outer SELECT must get a FROM ---
    def test_in_subquery_without_outer_from(self):
        raw = (
            "SELECT data_type WHERE data_type IN "
            f"(SELECT data_type FROM `{self.INDEX}` LIMIT 1) LIMIT 2"
        )
        query, err = _scope_sql_query(raw, self.INDEX)
        assert err is None
        assert query == (
            f"SELECT data_type FROM `{self.INDEX}` WHERE data_type IN "
            f"(SELECT data_type FROM `{self.INDEX}` LIMIT 1) LIMIT 2"
        )

    # --- UNION / JOIN with explicit FROMs pass through unchanged ---
    def test_union_with_explicit_from_passthrough(self):
        raw = (
            f"SELECT data_type FROM `{self.INDEX}` LIMIT 1 "
            f"UNION SELECT data_type FROM `{self.INDEX}` LIMIT 1"
        )
        query, err = _scope_sql_query(raw, self.INDEX)
        assert err is None
        assert query == raw

    def test_self_join_with_explicit_from_passthrough(self):
        raw = (
            f"SELECT a.data_type FROM `{self.INDEX}` a "
            f"JOIN `{self.INDEX}` b ON a.data_type=b.data_type LIMIT 1"
        )
        query, err = _scope_sql_query(raw, self.INDEX)
        assert err is None
        assert query == raw

    def test_join_outside_sketch_rejected(self):
        raw = (
            f"SELECT a.data_type FROM `{self.INDEX}` a "
            "JOIN `otherindex` b ON a.data_type=b.data_type"
        )
        query, err = _scope_sql_query(raw, self.INDEX)
        assert query is None
        assert "outside this sketch" in err

    # --- FROM-less UNION cannot be auto-scoped: clear error, no broken SQL ---
    def test_union_without_from_rejected(self):
        query, err = _scope_sql_query(
            "SELECT data_type LIMIT 1 UNION SELECT data_type LIMIT 1", self.INDEX
        )
        assert query is None
        assert "UNION" in err

    # --- string literals must never be treated as table refs / keywords ---
    def test_literal_from_in_value_not_a_table(self):
        query, err = _scope_sql_query(
            "SELECT message WHERE message LIKE '%from table%'", self.INDEX
        )
        assert err is None
        assert query == (
            f"SELECT message FROM `{self.INDEX}` WHERE message LIKE '%from table%'"
        )

    # --- multi-index: comma FROM list is a multi-index scan in OpenSearch ---
    INDEX_B = "9f1c2d3e4a5b6c7d8e9f0a1b2c3d4e5f"

    def test_multi_index_comma_list_all_validated(self):
        multi = f"{self.INDEX},{self.INDEX_B}"
        raw = f"SELECT count(*) FROM `{self.INDEX}`, `{self.INDEX_B}`"
        query, err = _scope_sql_query(raw, multi)
        assert err is None
        assert query == raw

    def test_multi_index_comma_list_with_aliases(self):
        multi = f"{self.INDEX},{self.INDEX_B}"
        raw = f"SELECT * FROM `{self.INDEX}` x, `{self.INDEX_B}` y LIMIT 1"
        query, err = _scope_sql_query(raw, multi)
        assert err is None
        assert query == raw

    def test_multi_index_injection(self):
        # Injected multi-index FROM must be a single backtick-quoted pattern
        # (`a,b`), a union scan. Separate-quoted identifiers (`a`, `b`) are a
        # JOIN in OpenSearch SQL and make GROUP BY silently return no rows.
        multi = f"{self.INDEX},{self.INDEX_B}"
        query, err = _scope_sql_query("SELECT count(*) c", multi)
        assert err is None
        assert query == f"SELECT count(*) c FROM `{self.INDEX},{self.INDEX_B}`"

    def test_single_pattern_identifier_passthrough(self):
        multi = f"{self.INDEX},{self.INDEX_B}"
        raw = f"SELECT count(*) FROM `{self.INDEX},{self.INDEX_B}`"
        query, err = _scope_sql_query(raw, multi)
        assert err is None
        assert query == raw

    # SECURITY: every index in a comma list is scanned, so checking only the
    # first would let the second read outside the sketch.
    def test_comma_list_second_index_outside_sketch_rejected(self):
        raw = f"SELECT count(*) FROM `{self.INDEX}`, `{self.INDEX_B}`"
        query, err = _scope_sql_query(raw, self.INDEX)  # sketch only has INDEX
        assert query is None
        assert "outside this sketch" in err

    # SECURITY: comments must not hide a table reference from the allowlist.
    @pytest.mark.parametrize(
        "raw",
        [
            "SELECT * FROM /*x*/ {other}",
            "SELECT * FROM {other} /*x*/",
            "SELECT * FROM\n-- pick one\n{other}",
            "SELECT * FROM /* multi\nline */ {other}",
            "SELECT * FROM `{allowed}`, /*x*/ {other}",
        ],
    )
    def test_commented_index_outside_sketch_rejected(self, raw):
        query, err = _scope_sql_query(
            raw.format(other=self.INDEX_B, allowed=self.INDEX), self.INDEX
        )
        assert query is None
        assert "outside this sketch" in err

    # SECURITY: a parenthesised plain table is a table, not a sub-query.
    @pytest.mark.parametrize(
        "raw", ["SELECT * FROM({other})", "SELECT * FROM ( {other} )"]
    )
    def test_parenthesised_index_outside_sketch_rejected(self, raw):
        query, err = _scope_sql_query(raw.format(other=self.INDEX_B), self.INDEX)
        assert query is None
        assert "outside this sketch" in err

    def test_parenthesised_index_inside_sketch_allowed(self):
        query, err = _scope_sql_query(f"SELECT * FROM ({self.INDEX})", self.INDEX)
        assert err is None
        assert query is not None

    # A comment is still allowed as long as the real table is in the sketch.
    def test_comment_with_allowed_index_passes(self):
        query, err = _scope_sql_query(
            f"SELECT * /* pick */ FROM `{self.INDEX}`", self.INDEX
        )
        assert err is None
        assert query is not None

    # SECURITY: an unparseable table reference must fail closed rather than
    # being read as "no indices referenced".
    def test_unresolvable_from_target_rejected(self):
        query, err = _scope_sql_query("SELECT * FROM ", self.INDEX)
        assert query is None
        assert "Unable to determine which indices" in err

    # A backticked name containing -- must not open a comment.
    def test_double_dash_inside_backticks_is_not_a_comment(self):
        odd = "idx--name"
        query, err = _scope_sql_query(f"SELECT * FROM `{odd}` LIMIT 1", odd)
        assert err is None
        assert query is not None


# --------------------------------------------------------------------------
# __ts_timeline_id filter injection (orphaned-record guard)
# --------------------------------------------------------------------------
class TestTimelinePredicates:
    def test_sql_predicate(self):
        assert _sql_timeline_predicate([3, 7]) == (
            "(__ts_timeline_id IN (3, 7) OR __ts_timeline_id IS NULL)"
        )

    def test_ppl_predicate(self):
        assert _ppl_timeline_predicate([3, 7]) == (
            "__ts_timeline_id in (3, 7) or isnull(__ts_timeline_id)"
        )

    def test_sql_predicate_coerces_int(self):
        # Guard against injection via non-numeric timeline IDs.
        assert _sql_timeline_predicate([3]) == (
            "(__ts_timeline_id IN (3) OR __ts_timeline_id IS NULL)"
        )


class TestSqlSingleFromTarget:
    IDX = "abc123"
    IDX_B = "def456"

    def test_single_index(self):
        assert _sql_single_from_target(f"SELECT * FROM `{self.IDX}` LIMIT 1")

    def test_multi_index_pattern_is_single(self):
        # `a,b` (comma inside one backtick) is one union-scan target.
        assert _sql_single_from_target(f"SELECT * FROM `{self.IDX},{self.IDX_B}`")

    def test_join_returns_none(self):
        raw = f"SELECT * FROM `{self.IDX}` x JOIN `{self.IDX_B}` y ON x.a=y.a"
        assert _sql_single_from_target(raw) is None

    def test_comma_table_list_returns_none(self):
        raw = f"SELECT * FROM `{self.IDX}`, `{self.IDX_B}`"
        assert _sql_single_from_target(raw) is None

    def test_subquery_from_returns_none(self):
        raw = f"SELECT t.c FROM (SELECT a c FROM `{self.IDX}`) t"
        assert _sql_single_from_target(raw) is None

    def test_no_from_returns_none(self):
        assert _sql_single_from_target("SELECT 1") is None


class TestInjectSqlTimelineFilter:
    IDX = "abc123"

    def test_no_timeline_ids_passthrough(self):
        raw = f"SELECT * FROM `{self.IDX}` LIMIT 1"
        assert _inject_sql_filter(raw, None, None) == raw

    def test_inject_without_where(self):
        out = _inject_sql_filter(f"SELECT COUNT(*) c FROM `{self.IDX}`", [5], None)
        assert out == (
            f"SELECT COUNT(*) c FROM `{self.IDX}` WHERE "
            "(__ts_timeline_id IN (5) OR __ts_timeline_id IS NULL)"
        )

    def test_inject_before_group_by(self):
        raw = f"SELECT data_type, COUNT(*) c FROM `{self.IDX}` GROUP BY data_type"
        out = _inject_sql_filter(raw, [5], None)
        assert out == (
            f"SELECT data_type, COUNT(*) c FROM `{self.IDX}` WHERE "
            "(__ts_timeline_id IN (5) OR __ts_timeline_id IS NULL) "
            "GROUP BY data_type"
        )

    def test_merge_existing_where_preserves_or_precedence(self):
        raw = f"SELECT * FROM `{self.IDX}` WHERE a=1 OR b=2 LIMIT 10"
        out = _inject_sql_filter(raw, [5], None)
        assert out == (
            f"SELECT * FROM `{self.IDX}` WHERE "
            "(__ts_timeline_id IN (5) OR __ts_timeline_id IS NULL) "
            "AND (a=1 OR b=2) LIMIT 10"
        )

    def test_join_left_unchanged(self):
        raw = f"SELECT * FROM `{self.IDX}` x JOIN `def456` y ON x.a=y.a LIMIT 1"
        assert _inject_sql_filter(raw, [5], None) == raw

    def test_subquery_left_unchanged(self):
        raw = f"SELECT t.c FROM (SELECT a c FROM `{self.IDX}`) t LIMIT 2"
        assert _inject_sql_filter(raw, [5], None) == raw

    def test_string_literal_not_mistaken_for_clause(self):
        raw = f"SELECT msg FROM `{self.IDX}` WHERE msg LIKE '%group by%' LIMIT 5"
        out = _inject_sql_filter(raw, [5], None)
        assert out == (
            f"SELECT msg FROM `{self.IDX}` WHERE "
            "(__ts_timeline_id IN (5) OR __ts_timeline_id IS NULL) "
            "AND (msg LIKE '%group by%') LIMIT 5"
        )


class TestInjectPplTimelineFilter:
    IDX = "abc123"

    def test_no_timeline_ids_passthrough(self):
        raw = f"search source=`{self.IDX}` | stats count()"
        assert _inject_ppl_filter(raw, None, None) == raw

    def test_inject_first_stage(self):
        raw = f"search source=`{self.IDX}` | stats count() as c"
        out = _inject_ppl_filter(raw, [5], None)
        assert out == (
            f"search source=`{self.IDX}` | where "
            "__ts_timeline_id in (5) or isnull(__ts_timeline_id) | stats count() as c"
        )

    def test_inject_bare_source(self):
        out = _inject_ppl_filter(f"search source=`{self.IDX}`", [5], None)
        assert out == (
            f"search source=`{self.IDX}` | where "
            "__ts_timeline_id in (5) or isnull(__ts_timeline_id)"
        )


class TestScopeWithTimelineFilter:
    IDX = "abc123"

    def test_sql_scope_injects_filter(self):
        query, err = _scope_sql_query(
            "SELECT data_type, COUNT(*) c GROUP BY data_type", self.IDX, [5, 6]
        )
        assert err is None
        assert "__ts_timeline_id IN (5, 6)" in query
        assert query.index("WHERE") < query.index("GROUP BY")

    def test_sql_scope_no_filter_when_ids_none(self):
        query, err = _scope_sql_query("SELECT COUNT(*) c", self.IDX)
        assert err is None
        assert "__ts_timeline_id" not in query

    def test_ppl_scope_injects_filter(self):
        query, err = _scope_ppl_query("stats count() as c", self.IDX, [5, 6])
        assert err is None
        assert "where __ts_timeline_id in (5, 6)" in query

    def test_ppl_scope_no_filter_when_ids_none(self):
        query, err = _scope_ppl_query("stats count() as c", self.IDX)
        assert err is None
        assert "__ts_timeline_id" not in query


# --------------------------------------------------------------------------
# Time range parsing
# --------------------------------------------------------------------------

# 2026-04-07T00:00:00Z and the last microsecond of 2026-04-07, in the
# microsecond epoch Timesketch writes to the `timestamp` field.
APR_7_START = 1775520000000000
APR_7_END = 1775606399999999


class TestParseTimeRange:
    def test_absent_returns_none(self):
        assert parse_time_range({}) is None

    def test_date_only_start_snaps_to_midnight(self):
        assert parse_time_range({"start_time": "2026-04-07"}) == (APR_7_START, None)

    def test_date_only_end_covers_the_whole_day(self):
        # An end of "2026-04-07" means through the end of the 7th, not the
        # instant it began, otherwise a single-day range matches nothing.
        assert parse_time_range({"end_time": "2026-04-07"}) == (None, APR_7_END)

    def test_datetime_with_zulu_suffix(self):
        parsed = parse_time_range({"start_time": "2026-04-07T00:00:00Z"})
        assert parsed == (APR_7_START, None)

    def test_datetime_with_offset(self):
        parsed = parse_time_range({"start_time": "2026-04-07T01:00:00+01:00"})
        assert parsed == (APR_7_START, None)

    def test_naive_datetime_is_read_as_utc(self):
        parsed = parse_time_range({"start_time": "2026-04-07T00:00:00"})
        assert parsed == (APR_7_START, None)

    def test_both_boundaries(self):
        parsed = parse_time_range(
            {"start_time": "2026-04-07", "end_time": "2026-04-07"}
        )
        assert parsed == (APR_7_START, APR_7_END)

    def test_inverted_range_rejected(self):
        with pytest.raises(ValueError, match="not be later than"):
            parse_time_range({"start_time": "2026-04-08", "end_time": "2026-04-07"})

    def test_unparseable_rejected(self):
        with pytest.raises(ValueError, match="not a valid ISO 8601"):
            parse_time_range({"start_time": "last tuesday"})

    def test_non_string_rejected(self):
        with pytest.raises(ValueError, match="must be an ISO 8601"):
            parse_time_range({"start_time": 1775520000})


class TestTimeRangePredicate:
    def test_none_is_empty(self):
        assert time_range_predicate(None) == ""

    def test_open_ended_start(self):
        assert time_range_predicate((APR_7_START, None)) == (
            f"timestamp >= {APR_7_START}"
        )

    def test_open_ended_end(self):
        assert time_range_predicate((None, APR_7_END)) == f"timestamp <= {APR_7_END}"

    def test_both_bounds(self):
        assert time_range_predicate((APR_7_START, APR_7_END)) == (
            f"timestamp >= {APR_7_START} and timestamp <= {APR_7_END}"
        )

    def test_conjunction_is_configurable(self):
        assert time_range_predicate((APR_7_START, APR_7_END), conjunction="AND") == (
            f"timestamp >= {APR_7_START} AND timestamp <= {APR_7_END}"
        )


class TestScopeWithTimeRange:
    IDX = "abc123"
    RANGE = (APR_7_START, APR_7_END)

    def test_ppl_range_only(self):
        query, err = _scope_ppl_query("stats count() as c", self.IDX, None, self.RANGE)
        assert err is None
        assert query == (
            f"search source=`{self.IDX}` | where timestamp >= {APR_7_START} "
            f"and timestamp <= {APR_7_END} | stats count() as c"
        )

    def test_ppl_range_and_timelines_are_parenthesised(self):
        # The timeline predicate contains an `or`; without the parentheses it
        # would bind more loosely than the `and` and widen the result set.
        query, err = _scope_ppl_query("stats count() as c", self.IDX, [5], self.RANGE)
        assert err is None
        assert query == (
            f"search source=`{self.IDX}` | where "
            "(__ts_timeline_id in (5) or isnull(__ts_timeline_id)) "
            f"and (timestamp >= {APR_7_START} and timestamp <= {APR_7_END}) "
            "| stats count() as c"
        )

    def test_sql_range_only(self):
        query, err = _scope_sql_query("SELECT COUNT(*) c", self.IDX, None, self.RANGE)
        assert err is None
        assert query == (
            f"SELECT COUNT(*) c FROM `{self.IDX}` WHERE "
            f"timestamp >= {APR_7_START} AND timestamp <= {APR_7_END}"
        )

    def test_sql_range_and_timelines(self):
        query, err = _scope_sql_query("SELECT COUNT(*) c", self.IDX, [5], self.RANGE)
        assert err is None
        assert query == (
            f"SELECT COUNT(*) c FROM `{self.IDX}` WHERE "
            "(__ts_timeline_id IN (5) OR __ts_timeline_id IS NULL) "
            f"AND timestamp >= {APR_7_START} AND timestamp <= {APR_7_END}"
        )

    def test_sql_range_merges_with_user_where(self):
        query, err = _scope_sql_query(
            "SELECT * WHERE a=1 OR b=2 LIMIT 10", self.IDX, None, self.RANGE
        )
        assert err is None
        assert query == (
            f"SELECT * FROM `{self.IDX}` WHERE "
            f"timestamp >= {APR_7_START} AND timestamp <= {APR_7_END} "
            "AND (a=1 OR b=2) LIMIT 10"
        )

    def test_no_range_leaves_query_untouched(self):
        query, err = _scope_ppl_query("stats count() as c", self.IDX, None, None)
        assert err is None
        assert "timestamp" not in query


# --------------------------------------------------------------------------
# Cluster capability
# --------------------------------------------------------------------------
class TestVersionSupported:
    def test_meets_minimum(self):
        assert _version_supported(MINIMUM_OPENSEARCH_VERSION)

    def test_newer_is_supported(self):
        assert _version_supported("3.9.1")

    def test_older_is_not(self):
        support = _version_supported("2.16.0")
        assert not support
        assert "3.7.0" in support.reason
        assert "2.16.0" in support.reason

    def test_prerelease_below_minimum_is_not(self):
        assert not _version_supported("3.6.0-rc1")

    # An unreadable version must not take a working feature away.
    @pytest.mark.parametrize("raw", [None, "", "not-a-version", 3.7])
    def test_unreadable_version_assumes_support(self, raw):
        assert _version_supported(raw)


class TestPluginSupported:
    def test_sql_plugin_present(self):
        assert _plugin_supported([{"component": "opensearch-sql"}])

    def test_sql_plugin_absent(self):
        support = _plugin_supported([{"component": "opensearch-alerting"}])
        assert not support
        assert "SQL plugin" in support.reason

    def test_unreadable_list_assumes_support(self):
        assert _plugin_supported(None)

    def test_null_component_is_skipped(self):
        assert not _plugin_supported([{"component": None}])


class TestDirectQuerySupport:
    def setup_method(self):
        capability.reset_cache()

    def teardown_method(self):
        capability.reset_cache()

    @staticmethod
    def _app():
        app = Flask(__name__)
        app.config["OPENSEARCH_HOST"] = "localhost"
        app.config["OPENSEARCH_PORT"] = 9200
        return app

    def test_supported_cluster(self):
        responses = [
            {"version": {"number": "3.7.0"}},
            [{"component": "opensearch-sql"}],
        ]
        with self._app().app_context():
            with mock.patch.object(capability, "_probe_call", side_effect=responses):
                assert direct_query_support()

    def test_old_cluster_is_refused_without_probing_plugins(self):
        with self._app().app_context():
            with mock.patch.object(
                capability,
                "_probe_call",
                side_effect=[{"version": {"number": "2.16.0"}}],
            ) as probe:
                support = direct_query_support()
        assert not support
        assert "2.16.0" in support.reason
        # The plugin list is irrelevant once the version has ruled the cluster out.
        assert probe.call_count == 1

    def test_result_is_cached(self):
        responses = [
            {"version": {"number": "3.7.0"}},
            [{"component": "opensearch-sql"}],
        ]
        with self._app().app_context():
            with mock.patch.object(
                capability, "_probe_call", side_effect=responses
            ) as probe:
                direct_query_support()
                direct_query_support()
        assert probe.call_count == 2

    def test_unreachable_cluster_assumes_support(self):
        with self._app().app_context():
            with mock.patch.object(capability, "_probe_call", return_value=None):
                assert direct_query_support()


# --------------------------------------------------------------------------
# The shared OpenSearch client
#
# Credentials, TLS and the node list are the datastore's to derive. What
# matters here is that the direct-query path uses the client it hands back,
# and holds a single one rather than building a fresh pool per request.
# --------------------------------------------------------------------------
class TestSharedClient:
    def setup_method(self):
        base_module.reset_client()

    teardown_method = setup_method

    @staticmethod
    def _patch_builder():
        """Stand in for the datastore's client builder."""
        return mock.patch.object(
            base_module, "build_opensearch_client", return_value=mock.MagicMock()
        )

    def test_configure_client_uses_the_datastore_builder(self):
        with self._patch_builder() as builder:
            configure_client(Flask(__name__))
        assert base_module.get_client() is builder.return_value

    def test_the_client_is_built_once_and_reused(self):
        with self._patch_builder() as builder:
            configure_client(Flask(__name__))
            for _ in range(3):
                base_module.get_client()
        assert builder.call_count == 1

    def test_first_use_builds_a_client_when_startup_did_not(self):
        with self._patch_builder() as builder:
            with Flask(__name__).app_context():
                assert base_module.get_client() is builder.return_value

    def test_reset_forces_a_rebuild(self):
        with self._patch_builder() as builder:
            configure_client(Flask(__name__))
            base_module.reset_client()
            configure_client(Flask(__name__))
        assert builder.call_count == 2
