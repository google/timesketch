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


class TestCall(unittest.TestCase):
    def test_parse_simple_call(self):
        result = pycypher.parse_query("CALL foo.bar.baz();")
        self.assertEqual(result[-1].end, 19)

        expected_ast_dump = [
            "@0  0..19  statement        body=@1\n",
            "@1  0..19  > query          clauses=[@2]\n",
            "@2  0..18  > > CALL         name=@3\n",
            "@3  5..16  > > > proc name  `foo.bar.baz`\n",
        ]
        assert_ast_matches_ast_dump(result, expected_ast_dump)

        ast = result[0]
        query = ast.get_body()
        clause = query.get_clauses()[0]
        self.assertEqual(clause.type, "CYPHER_AST_CALL")

        proc = clause.get_proc_name()
        self.assertEqual(proc.type, "CYPHER_AST_PROC_NAME")
        self.assertEqual(proc.get_value(), "foo.bar.baz")

        self.assertEqual(len(clause.get_arguments()), 0)
        self.assertEqual(len(clause.get_projections()), 0)

    def test_parse_call_with_args(self):
        result = pycypher.parse_query("CALL foo.bar.baz(1+n, 'foo');")
        self.assertEqual(result[-1].end, 29)

        expected_ast_dump = [
            "@0   0..29  statement              body=@1\n",
            "@1   0..29  > query                clauses=[@2]\n",
            "@2   0..28  > > CALL               name=@3, args=[@4, @7]\n",
            "@3   5..16  > > > proc name        `foo.bar.baz`\n",
            "@4  17..20  > > > binary operator  @5 + @6\n",
            "@5  17..18  > > > > integer        1\n",
            "@6  19..20  > > > > identifier     `n`\n",
            "@7  22..27  > > > string           \"foo\"\n",
        ]
        assert_ast_matches_ast_dump(result, expected_ast_dump)

        ast = result[0]
        query = ast.get_body()
        clause = query.get_clauses()[0]
        self.assertEqual(clause.type, "CYPHER_AST_CALL")

        proc = clause.get_proc_name()
        self.assertEqual(proc.type, "CYPHER_AST_PROC_NAME")
        self.assertEqual(proc.get_value(), "foo.bar.baz")

        self.assertEqual(len(clause.get_arguments()), 2)

        arg = clause.get_arguments()[0]
        self.assertEqual(arg.type, "CYPHER_AST_BINARY_OPERATOR")
        arg = clause.get_arguments()[1]
        self.assertEqual(arg.type, "CYPHER_AST_STRING")

        self.assertEqual(len(clause.get_projections()), 0)

    def test_parse_call_with_projections(self):
        result = pycypher.parse_query("CALL foo.bar.baz(1, 2) YIELD a AS x, b AS y;")
        self.assertEqual(result[-1].end, 44)

        expected_ast_dump = [
            " @0   0..44  statement           body=@1\n",
            " @1   0..44  > query             clauses=[@2]\n",
            " @2   0..43  > > CALL            name=@3, args=[@4, @5], YIELD=[@6, @9]\n",
            " @3   5..16  > > > proc name     `foo.bar.baz`\n",
            " @4  17..18  > > > integer       1\n",
            " @5  20..21  > > > integer       2\n",
            " @6  29..35  > > > projection    expression=@7, alias=@8\n",
            " @7  29..30  > > > > identifier  `a`\n",
            " @8  34..35  > > > > identifier  `x`\n",
            " @9  37..43  > > > projection    expression=@10, alias=@11\n",
            "@10  37..38  > > > > identifier  `b`\n",
            "@11  42..43  > > > > identifier  `y`\n",
        ]
        assert_ast_matches_ast_dump(result, expected_ast_dump)

        ast = result[0]
        query = ast.get_body()
        clause = query.get_clauses()[0]
        self.assertEqual(clause.type, "CYPHER_AST_CALL")

        proc = clause.get_proc_name()
        self.assertEqual(proc.type, "CYPHER_AST_PROC_NAME")
        self.assertEqual(proc.get_value(), "foo.bar.baz")

        self.assertEqual(len(clause.get_arguments()), 2)
        self.assertEqual(len(clause.get_projections()), 2)

        proj = clause.get_projections()[0]
        self.assertEqual(proj.type, "CYPHER_AST_PROJECTION")
        id = proj.get_expression()
        self.assertEqual(id.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(id.get_name(), "a")
        id = proj.get_alias()
        self.assertEqual(id.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(id.get_name(), "x")

        proj = clause.get_projections()[1]
        self.assertEqual(proj.type, "CYPHER_AST_PROJECTION")
        id = proj.get_expression()
        self.assertEqual(id.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(id.get_name(), "b")
        id = proj.get_alias()
        self.assertEqual(id.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(id.get_name(), "y")

    def test_parse_call_with_blank_projection(self):
        result = pycypher.parse_query("CALL foo.bar.baz(1, 2) YIELD -;")
        self.assertEqual(result[-1].end, 31)

        expected_ast_dump = [
            "@0   0..31  statement        body=@1\n",
            "@1   0..31  > query          clauses=[@2]\n",
            "@2   0..30  > > CALL         name=@3, args=[@4, @5]\n",
            "@3   5..16  > > > proc name  `foo.bar.baz`\n",
            "@4  17..18  > > > integer    1\n",
            "@5  20..21  > > > integer    2\n",
        ]
        assert_ast_matches_ast_dump(result, expected_ast_dump)

        ast = result[0]
        query = ast.get_body()
        clause = query.get_clauses()[0]
        self.assertEqual(clause.type, "CYPHER_AST_CALL")

        proc = clause.get_proc_name()
        self.assertEqual(proc.type, "CYPHER_AST_PROC_NAME")
        self.assertEqual(proc.get_value(), "foo.bar.baz")

        self.assertEqual(len(clause.get_arguments()), 2)
        self.assertEqual(len(clause.get_projections()), 0)

