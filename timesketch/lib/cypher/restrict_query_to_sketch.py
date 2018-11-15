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
"""Module containing the restrict_query_to_sketch function."""
import pycypher

from timesketch.lib.cypher.insertable_string import \
    InsertableString
from timesketch.lib.cypher.invalid_query import InvalidQuery


def query_is_restricted_to_sketch(query, sketch_id):
    """Verify that a query only accesses subgraph corresponding to given sketch.
    """
    def sketch_id_present_in(properties):
        for k, v in zip(properties.get_keys(), properties.get_values()):
            if k.get_value() == 'sketch_id':
                return v.get_valuestr() == str(sketch_id)
        return False

    for node_pattern in query.find_nodes('CYPHER_AST_NODE_PATTERN'):
        properties = node_pattern.get_properties()
        if properties is None or not sketch_id_present_in(properties):
            return False

    for rel_pattern in query.find_nodes('CYPHER_AST_REL_PATTERN'):
        properties = rel_pattern.get_properties()
        if properties is None or not sketch_id_present_in(properties):
            return False
    return True


def restrict_query_to_sketch(input_query, sketch_id):
    """Insert constraints in MATCH clauses, pattern expressions and pattern
    comprehensions so that the query can access only nodes and edges that have
    sketch_id property equal given sketch_id.

    Raises:
        InvalidQuery, pycypher.CypherParseError
    """
    forbidden = [
        'CYPHER_AST_CALL', 'CYPHER_AST_START', 'CYPHER_AST_LOAD_CSV',
        'CYPHER_AST_RETURN', 'CYPHER_AST_MERGE', 'CYPHER_AST_CREATE',
        'CYPHER_AST_SET', 'CYPHER_AST_DELETE', 'CYPHER_AST_REMOVE',
        'CYPHER_AST_SCHEMA_COMMAND',
    ]
    query, = pycypher.parse_query(input_query)
    for ast_type in forbidden:
        if list(query.find_nodes(ast_type)) != []:
            raise InvalidQuery('%s is not allowed.' % type)

    for prop_name in query.find_nodes('CYPHER_AST_PROP_NAME'):
        if prop_name.get_value() == 'sketch_id':
            raise InvalidQuery('Accessing sketch_id property is not allowed.')

    q = InsertableString(input_query)

    for node_pattern in query.find_nodes('CYPHER_AST_NODE_PATTERN'):
        properties = node_pattern.get_properties()
        if properties is not None:
            if not properties.get_keys():
                q.insert_at(properties.start + 1, 'sketch_id: %d' % sketch_id)
            else:
                q.insert_at(properties.start + 1, 'sketch_id: %d, ' % sketch_id)
        else:
            q.insert_at(node_pattern.end - 1, '{sketch_id: %d}' % sketch_id)

    for rel_pattern in query.find_nodes('CYPHER_AST_REL_PATTERN'):
        properties = rel_pattern.get_properties()
        if properties is not None:
            if not properties.get_keys():
                q.insert_at(properties.start + 1, 'sketch_id: %d' % sketch_id)
            else:
                q.insert_at(properties.start + 1, 'sketch_id: %d, ' % sketch_id)
        elif rel_pattern.end - rel_pattern.start == 2:
            q.insert_at(rel_pattern.end - 1, '[{sketch_id: %d}]' % sketch_id)
        elif rel_pattern.end - rel_pattern.start == 3:
            if rel_pattern.get_direction() == 'CYPHER_REL_OUTBOUND':
                pos = rel_pattern.end - 2
                q.insert_at(pos, '[{sketch_id: %d}]' % sketch_id)
            else:
                pos = rel_pattern.end - 1
                q.insert_at(pos, '[{sketch_id: %d}]' % sketch_id)
        else:
            if rel_pattern.get_direction() == 'CYPHER_REL_OUTBOUND':
                q.insert_at(rel_pattern.end - 3, '{sketch_id: %d}' % sketch_id)
            else:
                q.insert_at(rel_pattern.end - 2, '{sketch_id: %d}' % sketch_id)

    result = q.apply_insertions()

    try:
        parsed_result, = pycypher.parse_query(result)
        is_ok = query_is_restricted_to_sketch(parsed_result, sketch_id)
    except pycypher.CypherParseError:
        is_ok = False
    if not is_ok:
        raise InvalidQuery(
            'Your query probably has spaces in relationship pattern or it'
            'has other non-standard constructs which are not allowed.'
        )
    return result
