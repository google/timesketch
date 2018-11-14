# Copyright 2017 Google Inc. All rights reserved.
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
"""Module containing the unwind_timestamps function."""
import pycypher

from timesketch.lib.cypher.insertable_string import \
    InsertableString


def unwind_timestamps(input_query):
    """Simplified description:
    For each bound edge e, replaces all `e.timestamp` with `e_timestamp` and
    insert `UNWIND e.timestamps AS e_timestamp` before. Also, in the return
    clause, replace `e.timestamps` with `collect(e_timestamp)` for those edges.

    Additional magic involving nulls is done to account for missing timestamps
    so that if an edge has `e.timestamps_incomplete = true`, this edge will
    be included in query results even if none of it's unwound timestamps
    matches the conditions in where clauses. For exact and up-to-date reference
    and examples, please see the unit tests.
    """
    query, = pycypher.parse_query(input_query)
    q = InsertableString(input_query)
    unwound_rels = []

    def get_position_before_where(match_clause):
        result = 0
        for subclause in match_clause.children:
            # pylint: disable=protected-access
            if 'predicate' not in subclause._roles:
                result = max(result, subclause.end)
        return result

    def get_references_to_timestamp(rel, ast):
        for prop_access in ast.find_nodes('CYPHER_AST_PROPERTY_OPERATOR'):
            if prop_access.get_expression() is None:
                continue
            if prop_access.get_prop_name() is None:
                continue
            if prop_access.get_prop_name().get_value() != 'timestamp':
                continue
            expr = prop_access.get_expression()
            if not expr.instanceof('CYPHER_AST_IDENTIFIER'):
                continue
            if expr.get_name() != rel:
                continue
            yield prop_access

    def timestamp_of_rel_is_referenced_in(rel, ast):
        for _prop_access in get_references_to_timestamp(rel, ast):
            return True
        return False

    def decompose_predicate(pred):
        if pred is None:
            return []
        if pred.instanceof('CYPHER_AST_BINARY_OPERATOR'):
            if pred.get_operator() == 'CYPHER_OP_AND':
                arg1 = pred.get_argument1()
                arg2 = pred.get_argument2()
                return decompose_predicate(arg1) + decompose_predicate(arg2)
        return [pred]

    def insert_unwind_clauses():
        for match_clause in query.find_nodes('CYPHER_AST_MATCH'):
            if match_clause.get_pattern() is None:
                continue
            p = match_clause.get_pattern()
            rels_to_unwind = []
            constraints_to_repeat_before_unwind = []
            for rel_pattern in p.find_nodes('CYPHER_AST_REL_PATTERN'):
                if rel_pattern.get_identifier() is None:
                    continue
                rel = rel_pattern.get_identifier().get_name()
                if rel in unwound_rels:
                    continue
                if timestamp_of_rel_is_referenced_in(rel, query):
                    rels_to_unwind.append(rel)
            if match_clause.get_predicate() is not None:
                pred = match_clause.get_predicate()
                for part in decompose_predicate(pred):
                    is_safe = True
                    for rel in rels_to_unwind:
                        if timestamp_of_rel_is_referenced_in(rel, part):
                            is_safe = False
                    if is_safe:
                        constraints_to_repeat_before_unwind.append(part)
            def unwind(rel):
                return (
                    'UNWIND %s.timestamps + '
                    'filter(a IN [null] WHERE %s.timestamps_incomplete) '
                    'AS %s_timestamp' % (rel, rel, rel)
                )
            if rels_to_unwind:
                to_insert = ' '
                if constraints_to_repeat_before_unwind:
                    to_insert += 'WHERE ' + ' AND '.join(
                        input_query[c.start:c.end].strip()
                        for c in constraints_to_repeat_before_unwind
                    ) + ' '
                to_insert += ' '.join(
                    unwind(rel) for rel in rels_to_unwind)
                to_insert += ' WITH * '
                pos = get_position_before_where(match_clause)
                q.insert_at(pos, to_insert)
                unwound_rels.extend(rels_to_unwind)

    def amend_where_clauses_to_account_for_missing_timestamps():
        for clause in query.find_nodes('CYPHER_AST_QUERY_CLAUSE'):
            if clause.get_predicate() is None:
                continue
            pred = clause.get_predicate()
            rels_to_consider = [
                rel for rel in unwound_rels
                if timestamp_of_rel_is_referenced_in(rel, pred)
            ]
            if rels_to_consider:
                q.insert_at(pred.start, ' coalesce((')
                condition = ' OR '.join(
                    '%s_timestamp IS NULL' % rel for rel in rels_to_consider
                )
                q.insert_at(pred.end, '), %s)' % condition)

    def replace_timestamp_property_references():
        for rel in unwound_rels:
            for prop_access in get_references_to_timestamp(rel, query):
                q.replace_range(
                    prop_access.start, prop_access.end - 1, '%s_timestamp' % rel
                )

    def amend_return_clauses_for_unwound_timestamps():
        for return_clause in query.find_nodes('CYPHER_AST_RETURN'):
            for prop_access in return_clause.find_nodes(
                    'CYPHER_AST_PROPERTY_OPERATOR'):
                if prop_access.get_prop_name() is None:
                    continue
                if prop_access.get_prop_name().get_value() != 'timestamps':
                    continue
                expr = prop_access.get_expression()
                if expr is None:
                    continue
                if not expr.instanceof('CYPHER_AST_IDENTIFIER'):
                    continue
                if expr.get_name() in unwound_rels:
                    q.replace_range(
                        prop_access.start, prop_access.end,
                        'collect(%s_timestamp)' % expr.get_name(),
                    )

    insert_unwind_clauses()
    amend_where_clauses_to_account_for_missing_timestamps()
    replace_timestamp_property_references()
    amend_return_clauses_for_unwound_timestamps()
    result = q.apply_insertions()
    return result
