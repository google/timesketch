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


class TestForeach(unittest.TestCase):
    def test_parse_foreach(self):
        result = pycypher.parse_query("/*MATCH*/ FOREACH (x IN [1,2,3] | SET n.foo = x REMOVE n.bar)")
        self.assertEqual(result[-1].end, 61)

        expected_ast_dump = [
            " @0   2..7   block_comment            /*MATCH*/\n",
            " @1  10..61  statement                body=@2\n",
            " @2  10..61  > query                  clauses=[@3]\n",
            " @3  10..61  > > FOREACH              [@4 IN @5 | @9, @15]\n",
            " @4  19..20  > > > identifier         `x`\n",
            " @5  24..31  > > > collection         [@6, @7, @8]\n",
            " @6  25..26  > > > > integer          1\n",
            " @7  27..28  > > > > integer          2\n",
            " @8  29..30  > > > > integer          3\n",
            " @9  34..48  > > > SET                items=[@10]\n",
            "@10  38..48  > > > > set property     @11 = @14\n",
            "@11  38..44  > > > > > property       @12.@13\n",
            "@12  38..39  > > > > > > identifier   `n`\n",
            "@13  40..43  > > > > > > prop name    `foo`\n",
            "@14  46..47  > > > > > identifier     `x`\n",
            "@15  48..60  > > > REMOVE             items=[@16]\n",
            "@16  55..60  > > > > remove property  prop=@17\n",
            "@17  55..60  > > > > > property       @18.@19\n",
            "@18  55..56  > > > > > > identifier   `n`\n",
            "@19  57..60  > > > > > > prop name    `bar`\n",
        ]
        assert_ast_matches_ast_dump(result, expected_ast_dump)

        ast = result[1]
        query = ast.get_body()
        foreach = query.get_clauses()[0]
        self.assertEqual(foreach.type, "CYPHER_AST_FOREACH")

        id = foreach.get_identifier()
        self.assertEqual(id.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(id.get_name(), "x")

        expr = foreach.get_expression()
        self.assertEqual(expr.type, "CYPHER_AST_COLLECTION")

        self.assertEqual(len(foreach.get_clauses()), 2)

        clause = foreach.get_clauses()[0]
        self.assertEqual(clause.type, "CYPHER_AST_SET")

        clause = foreach.get_clauses()[1]
        self.assertEqual(clause.type, "CYPHER_AST_REMOVE")
