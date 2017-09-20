# Copyright 2016, Chris Leishman (http://github.com/cleishm)
# Copyright 2017, Google Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest
import pycypher
from .utils import assert_ast_matches_ast_dump


class TestUnwind(unittest.TestCase):
    def test_parse_unwind(self):
        result = pycypher.parse_query("UNWIND [1,2,3] AS x RETURN x;")
        self.assertEqual(result[-1].end, 29)

        expected_ast_dump = [
            " @0   0..29  statement           body=@1\n",
            " @1   0..29  > query             clauses=[@2, @8]\n",
            " @2   0..20  > > UNWIND          expression=@3, alias=@7\n",
            " @3   7..14  > > > collection    [@4, @5, @6]\n",
            " @4   8..9   > > > > integer     1\n",
            " @5  10..11  > > > > integer     2\n",
            " @6  12..13  > > > > integer     3\n",
            " @7  18..19  > > > identifier    `x`\n",
            " @8  20..28  > > RETURN          projections=[@9]\n",
            " @9  27..28  > > > projection    expression=@10\n",
            "@10  27..28  > > > > identifier  `x`\n",
        ]
        assert_ast_matches_ast_dump(result, expected_ast_dump)

        ast = result[0]
        query = ast.get_body()
        clause = query.get_clauses()[0]
        self.assertEqual(clause.type, "CYPHER_AST_UNWIND")

        exp = clause.get_expression()
        self.assertEqual(exp.type, "CYPHER_AST_COLLECTION")

        id = clause.get_alias()
        self.assertEqual(id.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(id.get_name(), "x")

