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
"""Module containing the append_return_clause function."""
import pycypher


def append_return_clause(input_query):
    """Append a return clause to a query so that it returns 3 list-valued
    columns:
     - nodes - list of ids of all match-bound nodes in the query
     - edges - list of ids of all match-bound edges in the query
     - timestamps - list of lists of timestamps, can be zipped with edges
    """
    query, = pycypher.parse_query(input_query)
    nodes = []
    rels = []

    for match_clause in query.find_nodes('CYPHER_AST_MATCH'):
        if match_clause.get_pattern() is None:
            continue
        p = match_clause.get_pattern()
        for node_pattern in p.find_nodes('CYPHER_AST_NODE_PATTERN'):
            if node_pattern.get_identifier() is not None:
                nodes.append(node_pattern.get_identifier().get_name())

        for rel_pattern in p.find_nodes('CYPHER_AST_REL_PATTERN'):
            if rel_pattern.get_identifier() is not None:
                if rel_pattern.get_varlength() is not None:
                    continue
                rels.append(rel_pattern.get_identifier().get_name())

    nodes = sorted(nodes)
    rels = sorted(rels)

    result = input_query.strip() + ' RETURN '
    result += '[' + ', '.join('id(%s)' % node for node in nodes) + '] AS nodes'
    result += ', '
    result += '[' + ', '.join('id(%s)' % rel for rel in rels) + '] AS edges'
    result += ', '
    result += '[' + ', '.join('%s.timestamps' % rel for rel in rels) + ']'
    result += ' AS timestamps'
    result += ' LIMIT 10000'
    return result
