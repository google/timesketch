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


class TestExpression(unittest.TestCase):
    def test_parse_simple_unary_operators(self):
        result = pycypher.parse_query("RETURN -1, +1, NOT false;")
        self.assertEqual(result[-1].end, 25)

        expected_ast_dump = [
            " @0   0..25  statement               body=@1\n",
            " @1   0..25  > query                 clauses=[@2]\n",
            " @2   0..24  > > RETURN              projections=[@3, @7, @11]\n",
            " @3   7..9   > > > projection        expression=@4, alias=@6\n",
            " @4   7..9   > > > > unary operator  - @5\n",
            " @5   8..9   > > > > > integer       1\n",
            " @6   7..9   > > > > identifier      `-1`\n",
            " @7  11..13  > > > projection        expression=@8, alias=@10\n",
            " @8  11..13  > > > > unary operator  + @9\n",
            " @9  12..13  > > > > > integer       1\n",
            "@10  11..13  > > > > identifier      `+1`\n",
            "@11  15..24  > > > projection        expression=@12, alias=@14\n",
            "@12  15..24  > > > > unary operator  NOT @13\n",
            "@13  19..24  > > > > > FALSE\n",
            "@14  15..24  > > > > identifier      `NOT false`\n",
        ]
        assert_ast_matches_ast_dump(result, expected_ast_dump)

        ast = result[0]
        query = ast.get_body()
        clause = query.get_clauses()[0]
        self.assertEqual(clause.type, "CYPHER_AST_RETURN")

        self.assertEqual(len(clause.get_projections()), 3)

        proj = clause.get_projections()[0]
        self.assertEqual(proj.type, "CYPHER_AST_PROJECTION")
        exp = proj.get_expression()
        self.assertEqual(exp.type, "CYPHER_AST_UNARY_OPERATOR")
        self.assertEqual(exp.get_operator(), "CYPHER_OP_UNARY_MINUS")
        arg = exp.get_argument()
        self.assertEqual(arg.type, "CYPHER_AST_INTEGER")

        proj = clause.get_projections()[1]
        self.assertEqual(proj.type, "CYPHER_AST_PROJECTION")
        exp = proj.get_expression()
        self.assertEqual(exp.type, "CYPHER_AST_UNARY_OPERATOR")
        self.assertEqual(exp.get_operator(), "CYPHER_OP_UNARY_PLUS")
        arg = exp.get_argument()
        self.assertEqual(arg.type, "CYPHER_AST_INTEGER")

        proj = clause.get_projections()[2]
        self.assertEqual(proj.type, "CYPHER_AST_PROJECTION")
        exp = proj.get_expression()
        self.assertEqual(exp.type, "CYPHER_AST_UNARY_OPERATOR")
        self.assertEqual(exp.get_operator(), "CYPHER_OP_NOT")
        arg = exp.get_argument()
        self.assertTrue(arg.instanceof("CYPHER_AST_BOOLEAN"))
        self.assertEqual(arg.type, "CYPHER_AST_FALSE")

    def test_parse_simple_binary_operators(self):
        result = pycypher.parse_query("RETURN a-1, 1 / b, c STARTS WITH 'foo';")
        self.assertEqual(result[-1].end, 39)

        expected_ast_dump = [
            " @0   0..39  statement                body=@1\n",
            " @1   0..39  > query                  clauses=[@2]\n",
            " @2   0..38  > > RETURN               projections=[@3, @8, @13]\n",
            " @3   7..10  > > > projection         expression=@4, alias=@7\n",
            " @4   7..10  > > > > binary operator  @5 - @6\n",
            " @5   7..8   > > > > > identifier     `a`\n",
            " @6   9..10  > > > > > integer        1\n",
            " @7   7..10  > > > > identifier       `a-1`\n",
            " @8  12..17  > > > projection         expression=@9, alias=@12\n",
            " @9  12..17  > > > > binary operator  @10 / @11\n",
            "@10  12..13  > > > > > integer        1\n",
            "@11  16..17  > > > > > identifier     `b`\n",
            "@12  12..17  > > > > identifier       `1 / b`\n",
            "@13  19..38  > > > projection         expression=@14, alias=@17\n",
            "@14  19..38  > > > > binary operator  @15 STARTS WITH @16\n",
            "@15  19..20  > > > > > identifier     `c`\n",
            "@16  33..38  > > > > > string         \"foo\"\n",
            "@17  19..38  > > > > identifier       `c STARTS WITH 'foo'`\n",
        ]
        assert_ast_matches_ast_dump(result, expected_ast_dump)

        ast = result[0]
        query = ast.get_body()
        clause = query.get_clauses()[0]
        self.assertEqual(clause.type, "CYPHER_AST_RETURN")

        self.assertEqual(len(clause.get_projections()), 3)

        proj = clause.get_projections()[0]
        self.assertEqual(proj.type, "CYPHER_AST_PROJECTION")
        exp = proj.get_expression()
        self.assertEqual(exp.type, "CYPHER_AST_BINARY_OPERATOR")
        self.assertEqual(exp.get_operator(), "CYPHER_OP_MINUS")
        arg = exp.get_argument1()
        self.assertEqual(arg.type, "CYPHER_AST_IDENTIFIER")
        arg = exp.get_argument2()
        self.assertEqual(arg.type, "CYPHER_AST_INTEGER")

        proj = clause.get_projections()[1]
        self.assertEqual(proj.type, "CYPHER_AST_PROJECTION")
        exp = proj.get_expression()
        self.assertEqual(exp.type, "CYPHER_AST_BINARY_OPERATOR")
        self.assertEqual(exp.get_operator(), "CYPHER_OP_DIV")
        arg = exp.get_argument1()
        self.assertEqual(arg.type, "CYPHER_AST_INTEGER")
        arg = exp.get_argument2()
        self.assertEqual(arg.type, "CYPHER_AST_IDENTIFIER")

        proj = clause.get_projections()[2]
        self.assertEqual(proj.type, "CYPHER_AST_PROJECTION")
        exp = proj.get_expression()
        self.assertEqual(exp.type, "CYPHER_AST_BINARY_OPERATOR")
        self.assertEqual(exp.get_operator(), "CYPHER_OP_STARTS_WITH")
        arg = exp.get_argument1()
        self.assertEqual(arg.type, "CYPHER_AST_IDENTIFIER")
        arg = exp.get_argument2()
        self.assertEqual(arg.type, "CYPHER_AST_STRING")

    def test_parse_unary_and_binary_operators(self):
        result = pycypher.parse_query("RETURN NOT 1 - 2 AND 3;")
        self.assertEqual(result[-1].end, 23)

        expected_ast_dump = [
            " @0   0..23  statement                    body=@1\n",
            " @1   0..23  > query                      clauses=[@2]\n",
            " @2   0..22  > > RETURN                   projections=[@3]\n",
            " @3   7..22  > > > projection             expression=@4, alias=@10\n",
            " @4   7..22  > > > > binary operator      @5 AND @9\n",
            " @5   7..17  > > > > > unary operator     NOT @6\n",
            " @6  11..17  > > > > > > binary operator  @7 - @8\n",
            " @7  11..12  > > > > > > > integer        1\n",
            " @8  15..16  > > > > > > > integer        2\n",
            " @9  21..22  > > > > > integer            3\n",
            "@10   7..22  > > > > identifier           `NOT 1 - 2 AND 3`\n",
        ]
        assert_ast_matches_ast_dump(result, expected_ast_dump)

    def test_parse_comparison_operators(self):
        result = pycypher.parse_query("RETURN a < 1, 4 > b > 2, 2 <= c >= 5;")
        self.assertEqual(result[-1].end, 37)

        expected_ast_dump = [
            " @0   0..37  statement             body=@1\n",
            " @1   0..37  > query               clauses=[@2]\n",
            " @2   0..36  > > RETURN            projections=[@3, @8, @14]\n",
            " @3   7..12  > > > projection      expression=@4, alias=@7\n",
            " @4   7..12  > > > > comparison    @5 < @6\n",
            " @5   7..8   > > > > > identifier  `a`\n",
            " @6  11..12  > > > > > integer     1\n",
            " @7   7..12  > > > > identifier    `a < 1`\n",
            " @8  14..23  > > > projection      expression=@9, alias=@13\n",
            " @9  14..23  > > > > comparison    @10 > @11 > @12\n",
            "@10  14..15  > > > > > integer     4\n",
            "@11  18..19  > > > > > identifier  `b`\n",
            "@12  22..23  > > > > > integer     2\n",
            "@13  14..23  > > > > identifier    `4 > b > 2`\n",
            "@14  25..36  > > > projection      expression=@15, alias=@19\n",
            "@15  25..36  > > > > comparison    @16 <= @17 >= @18\n",
            "@16  25..26  > > > > > integer     2\n",
            "@17  30..31  > > > > > identifier  `c`\n",
            "@18  35..36  > > > > > integer     5\n",
            "@19  25..36  > > > > identifier    `2 <= c >= 5`\n",
        ]
        assert_ast_matches_ast_dump(result, expected_ast_dump)

        ast = result[0]
        query = ast.get_body()
        clause = query.get_clauses()[0]
        self.assertEqual(clause.type, "CYPHER_AST_RETURN")

        self.assertEqual(len(clause.get_projections()), 3)

        proj = clause.get_projections()[0]
        self.assertEqual(proj.type, "CYPHER_AST_PROJECTION")
        exp = proj.get_expression()
        self.assertEqual(exp.type, "CYPHER_AST_COMPARISON")
        self.assertEqual(len(exp.get_operators()), 1)
        arg = exp.get_arguments()[0]
        self.assertEqual(arg.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(exp.get_operators()[0], "CYPHER_OP_LT")
        arg = exp.get_arguments()[1]
        self.assertEqual(arg.type, "CYPHER_AST_INTEGER")

        proj = clause.get_projections()[1]
        self.assertEqual(proj.type, "CYPHER_AST_PROJECTION")
        exp = proj.get_expression()
        self.assertEqual(exp.type, "CYPHER_AST_COMPARISON")
        self.assertEqual(len(exp.get_operators()), 2)
        arg = exp.get_arguments()[0]
        self.assertEqual(arg.type, "CYPHER_AST_INTEGER")
        self.assertEqual(exp.get_operators()[0], "CYPHER_OP_GT")
        arg = exp.get_arguments()[1]
        self.assertEqual(arg.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(exp.get_operators()[1], "CYPHER_OP_GT")
        arg = exp.get_arguments()[2]
        self.assertEqual(arg.type, "CYPHER_AST_INTEGER")

        proj = clause.get_projections()[2]
        self.assertEqual(proj.type, "CYPHER_AST_PROJECTION")
        exp = proj.get_expression()
        self.assertEqual(exp.type, "CYPHER_AST_COMPARISON")
        self.assertEqual(len(exp.get_operators()), 2)
        arg = exp.get_arguments()[0]
        self.assertEqual(arg.type, "CYPHER_AST_INTEGER")
        self.assertEqual(exp.get_operators()[0], "CYPHER_OP_LTE")
        arg = exp.get_arguments()[1]
        self.assertEqual(arg.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(exp.get_operators()[1], "CYPHER_OP_GTE")
        arg = exp.get_arguments()[2]
        self.assertEqual(arg.type, "CYPHER_AST_INTEGER")

    def test_parse_apply(self):
        result = pycypher.parse_query("RETURN foo(bar, baz), sum(DISTINCT a), count(*), count(DISTINCT *);")
        self.assertEqual(result[-1].end, 67)

        expected_ast_dump = [
            " @0   0..67  statement                body=@1\n",
            " @1   0..67  > query                  clauses=[@2]\n",
            " @2   0..66  > > RETURN               projections=[@3, @9, @14, @18]\n",
            " @3   7..20  > > > projection         expression=@4, alias=@8\n",
            " @4   7..20  > > > > apply            @5(@6, @7)\n",
            " @5   7..10  > > > > > function name  `foo`\n",
            " @6  11..14  > > > > > identifier     `bar`\n",
            " @7  16..19  > > > > > identifier     `baz`\n",
            " @8   7..20  > > > > identifier       `foo(bar, baz)`\n",
            " @9  22..37  > > > projection         expression=@10, alias=@13\n",
            "@10  22..37  > > > > apply            @11(DISTINCT @12)\n",
            "@11  22..25  > > > > > function name  `sum`\n",
            "@12  35..36  > > > > > identifier     `a`\n",
            "@13  22..37  > > > > identifier       `sum(DISTINCT a)`\n",
            "@14  39..47  > > > projection         expression=@15, alias=@17\n",
            "@15  39..47  > > > > apply all        @16(*)\n",
            "@16  39..44  > > > > > function name  `count`\n",
            "@17  39..47  > > > > identifier       `count(*)`\n",
            "@18  49..66  > > > projection         expression=@19, alias=@21\n",
            "@19  49..66  > > > > apply all        @20(DISTINCT *)\n",
            "@20  49..54  > > > > > function name  `count`\n",
            "@21  49..66  > > > > identifier       `count(DISTINCT *)`\n",
        ]
        assert_ast_matches_ast_dump(result, expected_ast_dump)

        ast = result[0]
        query = ast.get_body()
        clause = query.get_clauses()[0]
        self.assertEqual(clause.type, "CYPHER_AST_RETURN")

        self.assertEqual(len(clause.get_projections()), 4)

        proj = clause.get_projections()[0]
        self.assertEqual(proj.type, "CYPHER_AST_PROJECTION")
        exp = proj.get_expression()
        self.assertEqual(exp.type, "CYPHER_AST_APPLY_OPERATOR")

        func_name = exp.get_func_name()
        self.assertEqual(func_name.type, "CYPHER_AST_FUNCTION_NAME")
        self.assertEqual(func_name.get_value(), "foo")

        self.assertFalse(exp.get_distinct())
        self.assertEqual(len(exp.get_arguments()), 2)
        arg = exp.get_arguments()[0]
        self.assertEqual(arg.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(arg.get_name(), "bar")
        arg = exp.get_arguments()[1]
        self.assertEqual(arg.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(arg.get_name(), "baz")

        proj = clause.get_projections()[1]
        self.assertEqual(proj.type, "CYPHER_AST_PROJECTION")
        exp = proj.get_expression()
        self.assertEqual(exp.type, "CYPHER_AST_APPLY_OPERATOR")

        func_name = exp.get_func_name()
        self.assertEqual(func_name.type, "CYPHER_AST_FUNCTION_NAME")
        self.assertEqual(func_name.get_value(), "sum")

        self.assertTrue(exp.get_distinct())
        self.assertEqual(len(exp.get_arguments()), 1)
        arg = exp.get_arguments()[0]
        self.assertEqual(arg.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(arg.get_name(), "a")

        proj = clause.get_projections()[2]
        self.assertEqual(proj.type, "CYPHER_AST_PROJECTION")
        exp = proj.get_expression()
        self.assertEqual(exp.type, "CYPHER_AST_APPLY_ALL_OPERATOR")

        func_name = exp.get_func_name()
        self.assertEqual(func_name.type, "CYPHER_AST_FUNCTION_NAME")
        self.assertEqual(func_name.get_value(), "count")

        self.assertFalse(exp.get_distinct())

        proj = clause.get_projections()[3]
        self.assertEqual(proj.type, "CYPHER_AST_PROJECTION")
        exp = proj.get_expression()
        self.assertEqual(exp.type, "CYPHER_AST_APPLY_ALL_OPERATOR")

        func_name = exp.get_func_name()
        self.assertEqual(func_name.type, "CYPHER_AST_FUNCTION_NAME")
        self.assertEqual(func_name.get_value(), "count")

        self.assertTrue(exp.get_distinct())


    def test_parse_subscript(self):
        result = pycypher.parse_query("RETURN foo[n];")
        self.assertEqual(result[-1].end, 14)

        expected_ast_dump = [
            "@0   0..14  statement             body=@1\n",
            "@1   0..14  > query               clauses=[@2]\n",
            "@2   0..13  > > RETURN            projections=[@3]\n",
            "@3   7..13  > > > projection      expression=@4, alias=@7\n",
            "@4   7..13  > > > > subscript     @5[@6]\n",
            "@5   7..10  > > > > > identifier  `foo`\n",
            "@6  11..12  > > > > > identifier  `n`\n",
            "@7   7..13  > > > > identifier    `foo[n]`\n",
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
        self.assertEqual(exp.type, "CYPHER_AST_SUBSCRIPT_OPERATOR")

        node = exp.get_expression()
        self.assertEqual(node.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(node.get_name(), "foo")

        node = exp.get_subscript()
        self.assertEqual(node.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(node.get_name(), "n")

    def test_parse_slice(self):
        result = pycypher.parse_query("RETURN foo[1..5], bar[..n+5], baz[..];")
        self.assertEqual(result[-1].end, 38)

        expected_ast_dump = [
            " @0   0..38  statement                  body=@1\n",
            " @1   0..38  > query                    clauses=[@2]\n",
            " @2   0..37  > > RETURN                 projections=[@3, @9, @16]\n",
            " @3   7..16  > > > projection           expression=@4, alias=@8\n",
            " @4   7..16  > > > > slice              @5[@6..@7]\n",
            " @5   7..10  > > > > > identifier       `foo`\n",
            " @6  11..12  > > > > > integer          1\n",
            " @7  14..15  > > > > > integer          5\n",
            " @8   7..16  > > > > identifier         `foo[1..5]`\n",
            " @9  18..28  > > > projection           expression=@10, alias=@15\n",
            "@10  18..28  > > > > slice              @11[..@12]\n",
            "@11  18..21  > > > > > identifier       `bar`\n",
            "@12  24..27  > > > > > binary operator  @13 + @14\n",
            "@13  24..25  > > > > > > identifier     `n`\n",
            "@14  26..27  > > > > > > integer        5\n",
            "@15  18..28  > > > > identifier         `bar[..n+5]`\n",
            "@16  30..37  > > > projection           expression=@17, alias=@19\n",
            "@17  30..37  > > > > slice              @18[..]\n",
            "@18  30..33  > > > > > identifier       `baz`\n",
            "@19  30..37  > > > > identifier         `baz[..]`\n",
        ]
        assert_ast_matches_ast_dump(result, expected_ast_dump)

        ast = result[0]
        query = ast.get_body()
        clause = query.get_clauses()[0]
        self.assertEqual(clause.type, "CYPHER_AST_RETURN")

        self.assertEqual(len(clause.get_projections()), 3)

        proj = clause.get_projections()[0]
        self.assertEqual(proj.type, "CYPHER_AST_PROJECTION")
        exp = proj.get_expression()
        self.assertEqual(exp.type, "CYPHER_AST_SLICE_OPERATOR")

        node = exp.get_expression()
        self.assertEqual(node.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(node.get_name(), "foo")

        start = exp.get_start()
        self.assertEqual(start.type, "CYPHER_AST_INTEGER")
        self.assertEqual(start.get_valuestr(), "1")
        end = exp.get_end()
        self.assertEqual(end.type, "CYPHER_AST_INTEGER")
        self.assertEqual(end.get_valuestr(), "5")

        proj = clause.get_projections()[1]
        self.assertEqual(proj.type, "CYPHER_AST_PROJECTION")
        exp = proj.get_expression()
        self.assertEqual(exp.type, "CYPHER_AST_SLICE_OPERATOR")

        node = exp.get_expression()
        self.assertEqual(node.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(node.get_name(), "bar")

        start = exp.get_start()
        self.assertIsNone(start)
        end = exp.get_end()
        self.assertEqual(end.type, "CYPHER_AST_BINARY_OPERATOR")

        proj = clause.get_projections()[2]
        self.assertEqual(proj.type, "CYPHER_AST_PROJECTION")
        exp = proj.get_expression()
        self.assertEqual(exp.type, "CYPHER_AST_SLICE_OPERATOR")

        node = exp.get_expression()
        self.assertEqual(node.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(node.get_name(), "baz")

        start = exp.get_start()
        self.assertIsNone(start)
        end = exp.get_end()
        self.assertIsNone(end)
