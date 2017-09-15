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


class TestListComprehensions(unittest.TestCase):
    def test_parse_empty_list_comprehension(self):
        result = pycypher.parse_query("RETURN [ x in list /* nothing */ ];")
        self.assertEqual(result[-1].end, 35)

        expected_ast_dump = [
            "@0   0..35  statement                   body=@1\n",
            "@1   0..35  > query                     clauses=[@2]\n",
            "@2   0..34  > > RETURN                  projections=[@3]\n",
            "@3   7..34  > > > projection            expression=@4, alias=@8\n",
            "@4   7..34  > > > > list comprehension  [@5 IN @6]\n",
            "@5   9..10  > > > > > identifier        `x`\n",
            "@6  14..18  > > > > > identifier        `list`\n",
            "@7  21..30  > > > > > block_comment     /* nothing */\n",
            "@8   7..34  > > > > identifier          `[ x in list /* nothing */ ]`\n",
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
        self.assertEqual(exp.type, "CYPHER_AST_LIST_COMPREHENSION")

        id = exp.get_identifier()
        self.assertEqual(id.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(id.get_name(), "x")

        node = exp.get_expression()
        self.assertEqual(node.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(node.get_name(), "list")

        self.assertIsNone(exp.get_predicate())
        self.assertIsNone(exp.get_eval())

    def test_parse_full_list_comprehension(self):
        result = pycypher.parse_query("RETURN [x in list WHERE x.foo < 10 | x.bar ];")
        self.assertEqual(result[-1].end, 45)

        expected_ast_dump = [
            " @0   0..45  statement                   body=@1\n",
            " @1   0..45  > query                     clauses=[@2]\n",
            " @2   0..44  > > RETURN                  projections=[@3]\n",
            " @3   7..44  > > > projection            expression=@4, alias=@15\n",
            " @4   7..44  > > > > list comprehension  [@5 IN @6 WHERE @7 | @12]\n",
            " @5   8..9   > > > > > identifier        `x`\n",
            " @6  13..17  > > > > > identifier        `list`\n",
            " @7  24..35  > > > > > comparison        @8 < @11\n",
            " @8  24..30  > > > > > > property        @9.@10\n",
            " @9  24..25  > > > > > > > identifier    `x`\n",
            "@10  26..29  > > > > > > > prop name     `foo`\n",
            "@11  32..34  > > > > > > integer         10\n",
            "@12  37..43  > > > > > property          @13.@14\n",
            "@13  37..38  > > > > > > identifier      `x`\n",
            "@14  39..42  > > > > > > prop name       `bar`\n",
            "@15   7..44  > > > > identifier          `[x in list WHERE x.foo < 10 | x.bar ]`\n",
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
        self.assertEqual(exp.type, "CYPHER_AST_LIST_COMPREHENSION")

        id = exp.get_identifier()
        self.assertEqual(id.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(id.get_name(), "x")

        node = exp.get_expression()
        self.assertEqual(node.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(node.get_name(), "list")

        pred = exp.get_predicate()
        self.assertEqual(pred.type, "CYPHER_AST_COMPARISON")

        eval = exp.get_eval()
        self.assertEqual(eval.type, "CYPHER_AST_PROPERTY_OPERATOR")

    def test_parse_filter(self):
        result = pycypher.parse_query("RETURN filter(x in list WHERE x.foo < 10);")
        self.assertEqual(result[-1].end, 42)

        expected_ast_dump = [
            " @0   0..42  statement                 body=@1\n",
            " @1   0..42  > query                   clauses=[@2]\n",
            " @2   0..41  > > RETURN                projections=[@3]\n",
            " @3   7..41  > > > projection          expression=@4, alias=@12\n",
            " @4   7..41  > > > > filter            [@5 IN @6 WHERE @7]\n",
            " @5  14..15  > > > > > identifier      `x`\n",
            " @6  19..23  > > > > > identifier      `list`\n",
            " @7  30..40  > > > > > comparison      @8 < @11\n",
            " @8  30..36  > > > > > > property      @9.@10\n",
            " @9  30..31  > > > > > > > identifier  `x`\n",
            "@10  32..35  > > > > > > > prop name   `foo`\n",
            "@11  38..40  > > > > > > integer       10\n",
            "@12   7..41  > > > > identifier        `filter(x in list WHERE x.foo < 10)`\n",
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
        self.assertTrue(exp.instanceof("CYPHER_AST_LIST_COMPREHENSION"))
        self.assertEqual(exp.type, "CYPHER_AST_FILTER")

        id = exp.get_identifier()
        self.assertEqual(id.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(id.get_name(), "x")

        node = exp.get_expression()
        self.assertEqual(node.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(node.get_name(), "list")

        pred = exp.get_predicate()
        self.assertEqual(pred.type, "CYPHER_AST_COMPARISON")

        self.assertIsNone(exp.get_eval())

    def test_parse_extract(self):
        result = pycypher.parse_query("RETURN extract(x in list | x.bar);")
        self.assertEqual(result[-1].end, 34)

        expected_ast_dump = [
            " @0   0..34  statement               body=@1\n",
            " @1   0..34  > query                 clauses=[@2]\n",
            " @2   0..33  > > RETURN              projections=[@3]\n",
            " @3   7..33  > > > projection        expression=@4, alias=@10\n",
            " @4   7..33  > > > > extract         [@5 IN @6 | @7]\n",
            " @5  15..16  > > > > > identifier    `x`\n",
            " @6  20..24  > > > > > identifier    `list`\n",
            " @7  27..32  > > > > > property      @8.@9\n",
            " @8  27..28  > > > > > > identifier  `x`\n",
            " @9  29..32  > > > > > > prop name   `bar`\n",
            "@10   7..33  > > > > identifier      `extract(x in list | x.bar)`\n",
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
        self.assertTrue(exp.instanceof("CYPHER_AST_LIST_COMPREHENSION"))
        self.assertEqual(exp.type, "CYPHER_AST_EXTRACT")

        id = exp.get_identifier()
        self.assertEqual(id.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(id.get_name(), "x")

        node = exp.get_expression()
        self.assertEqual(node.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(node.get_name(), "list")

        self.assertIsNone(exp.get_predicate())

        eval = exp.get_eval()
        self.assertEqual(eval.type, "CYPHER_AST_PROPERTY_OPERATOR")

    def test_parse_all(self):
        result = pycypher.parse_query("RETURN all(x in list WHERE x.foo < 10);")
        self.assertEqual(result[-1].end, 39)

        expected_ast_dump = [
            " @0   0..39  statement                 body=@1\n",
            " @1   0..39  > query                   clauses=[@2]\n",
            " @2   0..38  > > RETURN                projections=[@3]\n",
            " @3   7..38  > > > projection          expression=@4, alias=@12\n",
            " @4   7..38  > > > > all               [@5 IN @6 WHERE @7]\n",
            " @5  11..12  > > > > > identifier      `x`\n",
            " @6  16..20  > > > > > identifier      `list`\n",
            " @7  27..37  > > > > > comparison      @8 < @11\n",
            " @8  27..33  > > > > > > property      @9.@10\n",
            " @9  27..28  > > > > > > > identifier  `x`\n",
            "@10  29..32  > > > > > > > prop name   `foo`\n",
            "@11  35..37  > > > > > > integer       10\n",
            "@12   7..38  > > > > identifier        `all(x in list WHERE x.foo < 10)`\n",
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
        self.assertTrue(exp.instanceof("CYPHER_AST_LIST_COMPREHENSION"))
        self.assertEqual(exp.type, "CYPHER_AST_ALL")

        id = exp.get_identifier()
        self.assertEqual(id.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(id.get_name(), "x")

        node = exp.get_expression()
        self.assertEqual(node.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(node.get_name(), "list")

        pred = exp.get_predicate()
        self.assertEqual(pred.type, "CYPHER_AST_COMPARISON")

        self.assertIsNone(exp.get_eval())

    def test_parse_any(self):
        result = pycypher.parse_query("RETURN any(x in list WHERE x.foo < 10);")
        self.assertEqual(result[-1].end, 39)

        expected_ast_dump = [
            " @0   0..39  statement                 body=@1\n",
            " @1   0..39  > query                   clauses=[@2]\n",
            " @2   0..38  > > RETURN                projections=[@3]\n",
            " @3   7..38  > > > projection          expression=@4, alias=@12\n",
            " @4   7..38  > > > > any               [@5 IN @6 WHERE @7]\n",
            " @5  11..12  > > > > > identifier      `x`\n",
            " @6  16..20  > > > > > identifier      `list`\n",
            " @7  27..37  > > > > > comparison      @8 < @11\n",
            " @8  27..33  > > > > > > property      @9.@10\n",
            " @9  27..28  > > > > > > > identifier  `x`\n",
            "@10  29..32  > > > > > > > prop name   `foo`\n",
            "@11  35..37  > > > > > > integer       10\n",
            "@12   7..38  > > > > identifier        `any(x in list WHERE x.foo < 10)`\n",
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
        self.assertTrue(exp.instanceof("CYPHER_AST_LIST_COMPREHENSION"))
        self.assertEqual(exp.type, "CYPHER_AST_ANY")

        id = exp.get_identifier()
        self.assertEqual(id.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(id.get_name(), "x")

        node = exp.get_expression()
        self.assertEqual(node.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(node.get_name(), "list")

        pred = exp.get_predicate()
        self.assertEqual(pred.type, "CYPHER_AST_COMPARISON")

        self.assertIsNone(exp.get_eval())

    def test_parse_single(self):
        result = pycypher.parse_query("RETURN single(x in list WHERE x.foo < 10);")
        self.assertEqual(result[-1].end, 42)

        expected_ast_dump = [
            " @0   0..42  statement                 body=@1\n",
            " @1   0..42  > query                   clauses=[@2]\n",
            " @2   0..41  > > RETURN                projections=[@3]\n",
            " @3   7..41  > > > projection          expression=@4, alias=@12\n",
            " @4   7..41  > > > > single            [@5 IN @6 WHERE @7]\n",
            " @5  14..15  > > > > > identifier      `x`\n",
            " @6  19..23  > > > > > identifier      `list`\n",
            " @7  30..40  > > > > > comparison      @8 < @11\n",
            " @8  30..36  > > > > > > property      @9.@10\n",
            " @9  30..31  > > > > > > > identifier  `x`\n",
            "@10  32..35  > > > > > > > prop name   `foo`\n",
            "@11  38..40  > > > > > > integer       10\n",
            "@12   7..41  > > > > identifier        `single(x in list WHERE x.foo < 10)`\n",
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
        self.assertTrue(exp.instanceof("CYPHER_AST_LIST_COMPREHENSION"))
        self.assertEqual(exp.type, "CYPHER_AST_SINGLE")

        id = exp.get_identifier()
        self.assertEqual(id.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(id.get_name(), "x")

        node = exp.get_expression()
        self.assertEqual(node.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(node.get_name(), "list")

        pred = exp.get_predicate()
        self.assertEqual(pred.type, "CYPHER_AST_COMPARISON")

        self.assertIsNone(exp.get_eval())

    def test_parse_none(self):
        result = pycypher.parse_query("RETURN none(x in list WHERE x.foo < 10);")
        self.assertEqual(result[-1].end, 40)

        expected_ast_dump = [
            " @0   0..40  statement                 body=@1\n",
            " @1   0..40  > query                   clauses=[@2]\n",
            " @2   0..39  > > RETURN                projections=[@3]\n",
            " @3   7..39  > > > projection          expression=@4, alias=@12\n",
            " @4   7..39  > > > > none              [@5 IN @6 WHERE @7]\n",
            " @5  12..13  > > > > > identifier      `x`\n",
            " @6  17..21  > > > > > identifier      `list`\n",
            " @7  28..38  > > > > > comparison      @8 < @11\n",
            " @8  28..34  > > > > > > property      @9.@10\n",
            " @9  28..29  > > > > > > > identifier  `x`\n",
            "@10  30..33  > > > > > > > prop name   `foo`\n",
            "@11  36..38  > > > > > > integer       10\n",
            "@12   7..39  > > > > identifier        `none(x in list WHERE x.foo < 10)`\n",
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
        self.assertTrue(exp.instanceof("CYPHER_AST_LIST_COMPREHENSION"))
        self.assertEqual(exp.type, "CYPHER_AST_NONE")

        id = exp.get_identifier()
        self.assertEqual(id.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(id.get_name(), "x")

        node = exp.get_expression()
        self.assertEqual(node.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(node.get_name(), "list")

        pred = exp.get_predicate()
        self.assertEqual(pred.type, "CYPHER_AST_COMPARISON")

        self.assertIsNone(exp.get_eval())

