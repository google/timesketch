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
"""Entry point module for cypher transpilation."""
import pycypher

from timesketch.lib.cypher.restrict_query_to_sketch import \
    restrict_query_to_sketch
from timesketch.lib.cypher.append_return_clause import \
    append_return_clause
from timesketch.lib.cypher.unwind_timestamps import \
    unwind_timestamps


def transpile_query(input_query, sketch_id):
    """Entry point function for cypher transpilation. Given a Cypher query,
    this function parses it, inserts constraints (in match clauses, pattern
    expressions and pattern comprehensions) to restrict the query to only
    nodes and edges with given sketch_id property. Raises exceptions
    CypheParseError and InvalidQuery if the input does not parse or is not
    a read-only query or contains return clauses. Inserts return clauses
    generated from identifiers bound in match clauses. Inserts unwind clauses
    to handle the `timestamp` property of edges transparently (see docstring for
    unwind_timestamps for details).
    The generated query returns rows with 3 variables:
    - nodes - list of node ids
    - edges - list of edge ids
    - timestamps - list of lists of timestamps, can be zipped with edges
    """
    # TODO: take with clauses into account when generating return clauses
    query, = pycypher.parse_query(input_query)
    delimiters = []
    delimiters.append(0)
    for union_clause in query.find_nodes('CYPHER_AST_UNION'):
        delimiters.append(union_clause.start)
        delimiters.append(union_clause.end)
    delimiters.append(len(input_query))

    parts = [
        input_query[delimiters[i]:delimiters[i+1]]
        for i in range(len(delimiters) - 1)
    ]

    def transpile_part(part):
        if ' '.join(part.split()).strip() in ('UNION', 'UNION ALL'):
            return part.strip()
        part = restrict_query_to_sketch(part, sketch_id)
        part = append_return_clause(part)
        part = unwind_timestamps(part)
        return part.strip()

    return ' '.join(transpile_part(part) for part in parts)
