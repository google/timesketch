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


class TestReduce(unittest.TestCase):
    def test_parse_reduce(self):
        result = pycypher.parse_query("RETURN reduce(a = 0, b in list | a + b);")
        self.assertEqual(result[-1].end, 40)

        expected_ast_dump = [
            " @0   0..40  statement                  body=@1\n",
            " @1   0..40  > query                    clauses=[@2]\n",
            " @2   0..39  > > RETURN                 projections=[@3]\n",
            " @3   7..39  > > > projection           expression=@4, alias=@12\n",
            " @4   7..39  > > > > reduce             [@5=@6, @7 IN @8 | @9]\n",
            " @5  14..15  > > > > > identifier       `a`\n",
            " @6  18..19  > > > > > integer          0\n",
            " @7  21..22  > > > > > identifier       `b`\n",
            " @8  26..30  > > > > > identifier       `list`\n",
            " @9  33..38  > > > > > binary operator  @10 + @11\n",
            "@10  33..34  > > > > > > identifier     `a`\n",
            "@11  37..38  > > > > > > identifier     `b`\n",
            "@12   7..39  > > > > identifier         `reduce(a = 0, b in list | a + b)`\n",
        ]
        assert_ast_matches_ast_dump(result, expected_ast_dump)

        ast = result[0]
        query = ast.get_body()
        clause = query.get_clauses()[0]
        self.assertEqual(clause.type, "CYPHER_AST_RETURN")
        self.assertEqual(len(clause.get_projections()), 1)

        proj = clause.get_projections()[0]
        self.assertEqual(proj.type, "CYPHER_AST_PROJECTION")
        exp = proj.get_expression()
        self.assertEqual(exp.type, "CYPHER_AST_REDUCE")

        id = exp.get_accumulator()
        self.assertEqual(id.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(id.get_name(), "a")

        node = exp.get_init()
        self.assertEqual(node.type, "CYPHER_AST_INTEGER")
        self.assertEqual(node.get_valuestr(), "0")

        id = exp.get_identifier()
        self.assertEqual(id.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(id.get_name(), "b")

        node = exp.get_expression()
        self.assertEqual(node.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(node.get_name(), "list")

        eval = exp.get_eval()
        self.assertEqual(eval.type, "CYPHER_AST_BINARY_OPERATOR")

