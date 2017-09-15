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


class TestCase(unittest.TestCase):
    def test_parse_simple_case(self):
        result = pycypher.parse_query("RETURN CASE x WHEN 1 THEN y WHEN 2 THEN z ELSE d END AS r")
        self.assertEqual(result[-1].end, 57)

        expected_ast_dump = [
            " @0   0..57  statement             body=@1\n",
            " @1   0..57  > query               clauses=[@2]\n",
            " @2   0..57  > > RETURN            projections=[@3]\n",
            " @3   7..57  > > > projection      expression=@4, alias=@11\n",
            " @4   7..52  > > > > case          expression=@5, alternatives=[(@6:@7), (@8:@9)], default=@10\n",
            " @5  12..13  > > > > > identifier  `x`\n",
            " @6  19..20  > > > > > integer     1\n",
            " @7  26..27  > > > > > identifier  `y`\n",
            " @8  33..34  > > > > > integer     2\n",
            " @9  40..41  > > > > > identifier  `z`\n",
            "@10  47..48  > > > > > identifier  `d`\n",
            "@11  56..57  > > > > identifier    `r`\n",
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
        self.assertEqual(exp.type, "CYPHER_AST_CASE")

        self.assertEqual(len(exp.get_predicates()), 2)

        id = exp.get_expression()
        self.assertEqual(id.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(id.get_name(), "x")

        pred = exp.get_predicates()[0]
        self.assertEqual(pred.type, "CYPHER_AST_INTEGER")
        self.assertEqual(pred.get_valuestr(), "1")

        value = exp.get_values()[0]
        self.assertEqual(value.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(value.get_name(), "y")

        pred = exp.get_predicates()[1]
        self.assertEqual(pred.type, "CYPHER_AST_INTEGER")
        self.assertEqual(pred.get_valuestr(), "2")

        value = exp.get_values()[1]
        self.assertEqual(value.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(value.get_name(), "z")

        deflt = exp.get_default()
        self.assertEqual(deflt.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(deflt.get_name(), "d")

    def test_parse_simple_case_without_default(self):
        result = pycypher.parse_query("RETURN CASE x WHEN 1 THEN y WHEN 2 THEN z END AS r")
        self.assertEqual(result[-1].end, 50)

        expected_ast_dump = [
            " @0   0..50  statement             body=@1\n",
            " @1   0..50  > query               clauses=[@2]\n",
            " @2   0..50  > > RETURN            projections=[@3]\n",
            " @3   7..50  > > > projection      expression=@4, alias=@10\n",
            " @4   7..45  > > > > case          expression=@5, alternatives=[(@6:@7), (@8:@9)]\n",
            " @5  12..13  > > > > > identifier  `x`\n",
            " @6  19..20  > > > > > integer     1\n",
            " @7  26..27  > > > > > identifier  `y`\n",
            " @8  33..34  > > > > > integer     2\n",
            " @9  40..41  > > > > > identifier  `z`\n",
            "@10  49..50  > > > > identifier    `r`\n",
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
        self.assertEqual(exp.type, "CYPHER_AST_CASE")

        self.assertEqual(len(exp.get_predicates()), 2)

        id = exp.get_expression()
        self.assertEqual(id.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(id.get_name(), "x")

        pred = exp.get_predicates()[0]
        self.assertEqual(pred.type, "CYPHER_AST_INTEGER")
        self.assertEqual(pred.get_valuestr(), "1")

        value = exp.get_values()[0]
        self.assertEqual(value.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(value.get_name(), "y")

        pred = exp.get_predicates()[1]
        self.assertEqual(pred.type, "CYPHER_AST_INTEGER")
        self.assertEqual(pred.get_valuestr(), "2")

        value = exp.get_values()[1]
        self.assertEqual(value.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(value.get_name(), "z")

        self.assertIsNone(exp.get_default())

    def test_parse_generic_case(self):
        result = pycypher.parse_query("RETURN CASE WHEN x=1 THEN y WHEN x=2 THEN z ELSE d END AS r")
        self.assertEqual(result[-1].end, 59)

        expected_ast_dump = [
            " @0   0..59  statement                  body=@1\n",
            " @1   0..59  > query                    clauses=[@2]\n",
            " @2   0..59  > > RETURN                 projections=[@3]\n",
            " @3   7..59  > > > projection           expression=@4, alias=@14\n",
            " @4   7..54  > > > > case               alternatives=[(@5:@8), (@9:@12)], default=@13\n",
            " @5  17..21  > > > > > binary operator  @6 = @7\n",
            " @6  17..18  > > > > > > identifier     `x`\n",
            " @7  19..20  > > > > > > integer        1\n",
            " @8  26..27  > > > > > identifier       `y`\n",
            " @9  33..37  > > > > > binary operator  @10 = @11\n",
            "@10  33..34  > > > > > > identifier     `x`\n",
            "@11  35..36  > > > > > > integer        2\n",
            "@12  42..43  > > > > > identifier       `z`\n",
            "@13  49..50  > > > > > identifier       `d`\n",
            "@14  58..59  > > > > identifier         `r`\n",
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
        self.assertEqual(exp.type, "CYPHER_AST_CASE")

        self.assertEqual(len(exp.get_predicates()), 2)

        self.assertIsNone(exp.get_expression())

        pred = exp.get_predicates()[0]
        self.assertEqual(pred.type, "CYPHER_AST_BINARY_OPERATOR")
        id = pred.get_argument2()
        self.assertEqual(id.type, "CYPHER_AST_INTEGER")
        self.assertEqual(id.get_valuestr(), "1")

        value = exp.get_values()[0]
        self.assertEqual(value.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(value.get_name(), "y")

        pred = exp.get_predicates()[1]
        self.assertEqual(pred.type, "CYPHER_AST_BINARY_OPERATOR")
        id = pred.get_argument2()
        self.assertEqual(id.type, "CYPHER_AST_INTEGER")
        self.assertEqual(id.get_valuestr(), "2")

        value = exp.get_values()[1]
        self.assertEqual(value.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(value.get_name(), "z")

        deflt = exp.get_default()
        self.assertEqual(deflt.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(deflt.get_name(), "d")

    def test_parse_generic_case_without_default(self):
        result = pycypher.parse_query("RETURN CASE WHEN x=1 THEN y WHEN x=2 THEN z END AS r")
        self.assertEqual(result[-1].end, 52)

        expected_ast_dump = [
            " @0   0..52  statement                  body=@1\n",
            " @1   0..52  > query                    clauses=[@2]\n",
            " @2   0..52  > > RETURN                 projections=[@3]\n",
            " @3   7..52  > > > projection           expression=@4, alias=@13\n",
            " @4   7..47  > > > > case               alternatives=[(@5:@8), (@9:@12)]\n",
            " @5  17..21  > > > > > binary operator  @6 = @7\n",
            " @6  17..18  > > > > > > identifier     `x`\n",
            " @7  19..20  > > > > > > integer        1\n",
            " @8  26..27  > > > > > identifier       `y`\n",
            " @9  33..37  > > > > > binary operator  @10 = @11\n",
            "@10  33..34  > > > > > > identifier     `x`\n",
            "@11  35..36  > > > > > > integer        2\n",
            "@12  42..43  > > > > > identifier       `z`\n",
            "@13  51..52  > > > > identifier         `r`\n",
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
        self.assertEqual(exp.type, "CYPHER_AST_CASE")

        self.assertEqual(len(exp.get_predicates()), 2)

        self.assertIsNone(exp.get_expression())

        pred = exp.get_predicates()[0]
        self.assertEqual(pred.type, "CYPHER_AST_BINARY_OPERATOR")
        id = pred.get_argument2()
        self.assertEqual(id.type, "CYPHER_AST_INTEGER")
        self.assertEqual(id.get_valuestr(), "1")

        value = exp.get_values()[0]
        self.assertEqual(value.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(value.get_name(), "y")

        pred = exp.get_predicates()[1]
        self.assertEqual(pred.type, "CYPHER_AST_BINARY_OPERATOR")
        id = pred.get_argument2()
        self.assertEqual(id.type, "CYPHER_AST_INTEGER")
        self.assertEqual(id.get_valuestr(), "2")

        value = exp.get_values()[1]
        self.assertEqual(value.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(value.get_name(), "z")

        self.assertIsNone(exp.get_default())
