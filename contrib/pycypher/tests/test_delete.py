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


class TestDelete(unittest.TestCase):
    def test_parse_delete(self):
        result = pycypher.parse_query("/*MATCH*/ DELETE n, CASE WHEN exists(n.foo) THEN m ELSE n END;")
        self.assertEqual(result[-1].end, 62)

        expected_ast_dump = [
            " @0   2..7   block_comment            /*MATCH*/\n",
            " @1  10..62  statement                body=@2\n",
            " @2  10..62  > query                  clauses=[@3]\n",
            " @3  10..61  > > DELETE               expressions=[@4, @5]\n",
            " @4  17..18  > > > identifier         `n`\n",
            " @5  20..61  > > > case               alternatives=[(@6:@11)], default=@12\n",
            " @6  30..43  > > > > apply            @7(@8)\n",
            " @7  30..36  > > > > > function name  `exists`\n",
            " @8  37..42  > > > > > property       @9.@10\n",
            " @9  37..38  > > > > > > identifier   `n`\n",
            "@10  39..42  > > > > > > prop name    `foo`\n",
            "@11  49..50  > > > > identifier       `m`\n",
            "@12  56..57  > > > > identifier       `n`\n",
        ]
        assert_ast_matches_ast_dump(result, expected_ast_dump)

        ast = result[1]
        self.assertEqual(ast.type, "CYPHER_AST_STATEMENT")
        query = ast.get_body()
        self.assertEqual(query.type, "CYPHER_AST_QUERY")
        delete = query.get_clauses()[0]
        self.assertEqual(delete.type, "CYPHER_AST_DELETE")

        self.assertFalse(delete.has_detach())

        self.assertEqual(len(delete.get_expressions()), 2)

        expr = delete.get_expressions()[0]
        self.assertEqual(expr.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(expr.get_name(), "n")

        expr = delete.get_expressions()[1]
        self.assertEqual(expr.type, "CYPHER_AST_CASE")

    def test_parse_detach_delete(self):
        result = pycypher.parse_query("/*MATCH*/ DETACH DELETE n, CASE WHEN exists(n.foo) THEN m ELSE n END;")
        self.assertEqual(result[-1].end, 69)

        expected_ast_dump = [
            " @0   2..7   block_comment            /*MATCH*/\n",
            " @1  10..69  statement                body=@2\n",
            " @2  10..69  > query                  clauses=[@3]\n",
            " @3  10..68  > > DELETE               DETACH, expressions=[@4, @5]\n",
            " @4  24..25  > > > identifier         `n`\n",
            " @5  27..68  > > > case               alternatives=[(@6:@11)], default=@12\n",
            " @6  37..50  > > > > apply            @7(@8)\n",
            " @7  37..43  > > > > > function name  `exists`\n",
            " @8  44..49  > > > > > property       @9.@10\n",
            " @9  44..45  > > > > > > identifier   `n`\n",
            "@10  46..49  > > > > > > prop name    `foo`\n",
            "@11  56..57  > > > > identifier       `m`\n",
            "@12  63..64  > > > > identifier       `n`\n",
        ]
        assert_ast_matches_ast_dump(result, expected_ast_dump)

        ast = result[1]
        self.assertEqual(ast.type, "CYPHER_AST_STATEMENT")
        query = ast.get_body()
        self.assertEqual(query.type, "CYPHER_AST_QUERY")
        delete = query.get_clauses()[0]
        self.assertEqual(delete.type, "CYPHER_AST_DELETE")

        self.assertTrue(delete.has_detach())

        self.assertEqual(len(delete.get_expressions()), 2)

        expr = delete.get_expressions()[0]
        self.assertEqual(expr.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(expr.get_name(), "n")

        expr = delete.get_expressions()[1]
        self.assertEqual(expr.type, "CYPHER_AST_CASE")
