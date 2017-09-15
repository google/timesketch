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


class TestWith(unittest.TestCase):
    def test_parse_simple_with(self):
        result = pycypher.parse_query("WITH 1 AS x, 'bar' AS y RETURN x, y")
        self.assertEqual(result[-1].end, 35)

        expected_ast_dump = [
            " @0   0..35  statement           body=@1\n",
            " @1   0..35  > query             clauses=[@2, @9]\n",
            " @2   0..24  > > WITH            projections=[@3, @6]\n",
            " @3   5..11  > > > projection    expression=@4, alias=@5\n",
            " @4   5..6   > > > > integer     1\n",
            " @5  10..11  > > > > identifier  `x`\n",
            " @6  13..24  > > > projection    expression=@7, alias=@8\n",
            " @7  13..18  > > > > string      \"bar\"\n",
            " @8  22..23  > > > > identifier  `y`\n",
            " @9  24..35  > > RETURN          projections=[@10, @12]\n",
            "@10  31..32  > > > projection    expression=@11\n",
            "@11  31..32  > > > > identifier  `x`\n",
            "@12  34..35  > > > projection    expression=@13\n",
            "@13  34..35  > > > > identifier  `y`\n",
        ]
        assert_ast_matches_ast_dump(result, expected_ast_dump)

        ast = result[0]
        query = ast.get_body()
        clause = query.get_clauses()[0]
        self.assertEqual(clause.type, "CYPHER_AST_WITH")

        self.assertFalse(clause.is_distinct())
        self.assertFalse(clause.has_include_existing())

        self.assertEqual(len(clause.get_projections()), 2)

        proj = clause.get_projections()[0]
        self.assertEqual(proj.type, "CYPHER_AST_PROJECTION")
        exp = proj.get_expression()
        self.assertEqual(exp.type, "CYPHER_AST_INTEGER")
        self.assertEqual(exp.get_valuestr(), "1")
        alias = proj.get_alias()
        self.assertEqual(alias.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(alias.get_name(), "x")

        proj = clause.get_projections()[1]
        self.assertEqual(proj.type, "CYPHER_AST_PROJECTION")
        exp = proj.get_expression()
        self.assertEqual(exp.type, "CYPHER_AST_STRING")
        self.assertEqual(exp.get_value(), "bar")
        alias = proj.get_alias()
        self.assertEqual(alias.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(alias.get_name(), "y")

        self.assertIsNone(clause.get_order_by())
        self.assertIsNone(clause.get_skip())
        self.assertIsNone(clause.get_limit())
        self.assertIsNone(clause.get_predicate())

    def test_parse_distinct_with(self):
        result = pycypher.parse_query("WITH DISTINCT 1 AS x, 'bar' AS y RETURN x, y")
        self.assertEqual(result[-1].end, 44)

        expected_ast_dump = [
            " @0   0..44  statement           body=@1\n",
            " @1   0..44  > query             clauses=[@2, @9]\n",
            " @2   0..33  > > WITH            DISTINCT, projections=[@3, @6]\n",
            " @3  14..20  > > > projection    expression=@4, alias=@5\n",
            " @4  14..15  > > > > integer     1\n",
            " @5  19..20  > > > > identifier  `x`\n",
            " @6  22..33  > > > projection    expression=@7, alias=@8\n",
            " @7  22..27  > > > > string      \"bar\"\n",
            " @8  31..32  > > > > identifier  `y`\n",
            " @9  33..44  > > RETURN          projections=[@10, @12]\n",
            "@10  40..41  > > > projection    expression=@11\n",
            "@11  40..41  > > > > identifier  `x`\n",
            "@12  43..44  > > > projection    expression=@13\n",
            "@13  43..44  > > > > identifier  `y`\n",
        ]
        assert_ast_matches_ast_dump(result, expected_ast_dump)

        ast = result[0]
        query = ast.get_body()
        clause = query.get_clauses()[0]
        self.assertEqual(clause.type, "CYPHER_AST_WITH")

        self.assertTrue(clause.is_distinct())
        self.assertFalse(clause.has_include_existing())

        self.assertEqual(len(clause.get_projections()), 2)

        proj = clause.get_projections()[0]
        self.assertEqual(proj.type, "CYPHER_AST_PROJECTION")
        exp = proj.get_expression()
        self.assertEqual(exp.type, "CYPHER_AST_INTEGER")
        self.assertEqual(exp.get_valuestr(), "1")
        alias = proj.get_alias()
        self.assertEqual(alias.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(alias.get_name(), "x")

        proj = clause.get_projections()[1]
        self.assertEqual(proj.type, "CYPHER_AST_PROJECTION")
        exp = proj.get_expression()
        self.assertEqual(exp.type, "CYPHER_AST_STRING")
        self.assertEqual(exp.get_value(), "bar")
        alias = proj.get_alias()
        self.assertEqual(alias.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(alias.get_name(), "y")

        self.assertIsNone(clause.get_order_by())
        self.assertIsNone(clause.get_skip())
        self.assertIsNone(clause.get_limit())
        self.assertIsNone(clause.get_predicate())

    def test_parse_with_including_existing(self):
        result = pycypher.parse_query("WITH *, 1 AS x, 'bar' AS y RETURN x, y")
        self.assertEqual(result[-1].end, 38)

        expected_ast_dump = [
            " @0   0..38  statement           body=@1\n",
            " @1   0..38  > query             clauses=[@2, @9]\n",
            " @2   0..27  > > WITH            *, projections=[@3, @6]\n",
            " @3   8..14  > > > projection    expression=@4, alias=@5\n",
            " @4   8..9   > > > > integer     1\n",
            " @5  13..14  > > > > identifier  `x`\n",
            " @6  16..27  > > > projection    expression=@7, alias=@8\n",
            " @7  16..21  > > > > string      \"bar\"\n",
            " @8  25..26  > > > > identifier  `y`\n",
            " @9  27..38  > > RETURN          projections=[@10, @12]\n",
            "@10  34..35  > > > projection    expression=@11\n",
            "@11  34..35  > > > > identifier  `x`\n",
            "@12  37..38  > > > projection    expression=@13\n",
            "@13  37..38  > > > > identifier  `y`\n",
        ]
        assert_ast_matches_ast_dump(result, expected_ast_dump)

        ast = result[0]
        query = ast.get_body()
        clause = query.get_clauses()[0]
        self.assertEqual(clause.type, "CYPHER_AST_WITH")

        self.assertFalse(clause.is_distinct())
        self.assertTrue(clause.has_include_existing())

        self.assertEqual(len(clause.get_projections()), 2)

        proj = clause.get_projections()[0]
        self.assertEqual(proj.type, "CYPHER_AST_PROJECTION")
        exp = proj.get_expression()
        self.assertEqual(exp.type, "CYPHER_AST_INTEGER")
        self.assertEqual(exp.get_valuestr(), "1")
        alias = proj.get_alias()
        self.assertEqual(alias.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(alias.get_name(), "x")

        proj = clause.get_projections()[1]
        self.assertEqual(proj.type, "CYPHER_AST_PROJECTION")
        exp = proj.get_expression()
        self.assertEqual(exp.type, "CYPHER_AST_STRING")
        self.assertEqual(exp.get_value(), "bar")
        alias = proj.get_alias()
        self.assertEqual(alias.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(alias.get_name(), "y")

        self.assertIsNone(clause.get_order_by())
        self.assertIsNone(clause.get_skip())
        self.assertIsNone(clause.get_limit())
        self.assertIsNone(clause.get_predicate())

    def test_parse_with_and_order_by(self):
        result = pycypher.parse_query("WITH 1 AS x, 'bar' AS y ORDER BY x DESC, y ASC, z.prop + 10")
        self.assertEqual(result[-1].end, 59)

        expected_ast_dump = [
            " @0   0..59  statement                  body=@1\n",
            " @1   0..59  > query                    clauses=[@2]\n",
            " @2   0..59  > > WITH                   projections=[@3, @6], ORDER BY=@9\n",
            " @3   5..11  > > > projection           expression=@4, alias=@5\n",
            " @4   5..6   > > > > integer            1\n",
            " @5  10..11  > > > > identifier         `x`\n",
            " @6  13..24  > > > projection           expression=@7, alias=@8\n",
            " @7  13..18  > > > > string             \"bar\"\n",
            " @8  22..23  > > > > identifier         `y`\n",
            " @9  24..59  > > > ORDER BY             items=[@10, @12, @14]\n",
            "@10  33..39  > > > > sort item          expression=@11, DESCENDING\n",
            "@11  33..34  > > > > > identifier       `x`\n",
            "@12  41..46  > > > > sort item          expression=@13, ASCENDING\n",
            "@13  41..42  > > > > > identifier       `y`\n",
            "@14  48..59  > > > > sort item          expression=@15, ASCENDING\n",
            "@15  48..59  > > > > > binary operator  @16 + @19\n",
            "@16  48..55  > > > > > > property       @17.@18\n",
            "@17  48..49  > > > > > > > identifier   `z`\n",
            "@18  50..54  > > > > > > > prop name    `prop`\n",
            "@19  57..59  > > > > > > integer        10\n",
        ]
        assert_ast_matches_ast_dump(result, expected_ast_dump)

        ast = result[0]
        query = ast.get_body()
        clause = query.get_clauses()[0]
        self.assertEqual(clause.type, "CYPHER_AST_WITH")

        self.assertFalse(clause.is_distinct())
        self.assertFalse(clause.has_include_existing())

        self.assertEqual(len(clause.get_projections()), 2)

        proj = clause.get_projections()[0]
        self.assertEqual(proj.type, "CYPHER_AST_PROJECTION")
        exp = proj.get_expression()
        self.assertEqual(exp.type, "CYPHER_AST_INTEGER")
        self.assertEqual(exp.get_valuestr(), "1")
        alias = proj.get_alias()
        self.assertEqual(alias.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(alias.get_name(), "x")

        proj = clause.get_projections()[1]
        self.assertEqual(proj.type, "CYPHER_AST_PROJECTION")
        exp = proj.get_expression()
        self.assertEqual(exp.type, "CYPHER_AST_STRING")
        self.assertEqual(exp.get_value(), "bar")
        alias = proj.get_alias()
        self.assertEqual(alias.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(alias.get_name(), "y")

        order = clause.get_order_by()
        self.assertEqual(order.type, "CYPHER_AST_ORDER_BY")
        self.assertEqual(len(order.get_items()), 3)

        item = order.get_items()[0]
        self.assertEqual(item.type, "CYPHER_AST_SORT_ITEM")
        exp = item.get_expression()
        self.assertEqual(exp.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(exp.get_name(), "x")
        self.assertFalse(item.is_ascending())

        item = order.get_items()[1]
        self.assertEqual(item.type, "CYPHER_AST_SORT_ITEM")
        exp = item.get_expression()
        self.assertEqual(exp.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(exp.get_name(), "y")
        self.assertTrue(item.is_ascending())

        item = order.get_items()[2]
        self.assertEqual(item.type, "CYPHER_AST_SORT_ITEM")
        exp = item.get_expression()
        self.assertEqual(exp.type, "CYPHER_AST_BINARY_OPERATOR")
        self.assertTrue(item.is_ascending())

        self.assertIsNone(clause.get_skip())
        self.assertIsNone(clause.get_limit())
        self.assertIsNone(clause.get_predicate())

    def test_parse_with_and_skip(self):
        result = pycypher.parse_query("WITH *, 1 AS x, 'bar' AS y SKIP 10")
        self.assertEqual(result[-1].end, 34)

        expected_ast_dump = [
            "@0   0..34  statement           body=@1\n",
            "@1   0..34  > query             clauses=[@2]\n",
            "@2   0..34  > > WITH            *, projections=[@3, @6], SKIP=@9\n",
            "@3   8..14  > > > projection    expression=@4, alias=@5\n",
            "@4   8..9   > > > > integer     1\n",
            "@5  13..14  > > > > identifier  `x`\n",
            "@6  16..27  > > > projection    expression=@7, alias=@8\n",
            "@7  16..21  > > > > string      \"bar\"\n",
            "@8  25..26  > > > > identifier  `y`\n",
            "@9  32..34  > > > integer       10\n",
        ]
        assert_ast_matches_ast_dump(result, expected_ast_dump)

        ast = result[0]
        query = ast.get_body()
        clause = query.get_clauses()[0]
        self.assertEqual(clause.type, "CYPHER_AST_WITH")

        self.assertFalse(clause.is_distinct())
        self.assertTrue(clause.has_include_existing())

        self.assertEqual(len(clause.get_projections()), 2)

        proj = clause.get_projections()[0]
        self.assertEqual(proj.type, "CYPHER_AST_PROJECTION")
        exp = proj.get_expression()
        self.assertEqual(exp.type, "CYPHER_AST_INTEGER")
        self.assertEqual(exp.get_valuestr(), "1")
        alias = proj.get_alias()
        self.assertEqual(alias.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(alias.get_name(), "x")

        proj = clause.get_projections()[1]
        self.assertEqual(proj.type, "CYPHER_AST_PROJECTION")
        exp = proj.get_expression()
        self.assertEqual(exp.type, "CYPHER_AST_STRING")
        self.assertEqual(exp.get_value(), "bar")
        alias = proj.get_alias()
        self.assertEqual(alias.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(alias.get_name(), "y")

        self.assertIsNone(clause.get_order_by())

        skip = clause.get_skip()
        self.assertEqual(skip.type, "CYPHER_AST_INTEGER")
        self.assertEqual(skip.get_valuestr(), "10")

        self.assertIsNone(clause.get_limit())
        self.assertIsNone(clause.get_predicate())

    def test_parse_with_and_skip_limit(self):
        result = pycypher.parse_query("WITH *, 1 AS x, 'bar' AS y SKIP 10 LIMIT 5")
        self.assertEqual(result[-1].end, 42)

        expected_ast_dump = [
            " @0   0..42  statement           body=@1\n",
            " @1   0..42  > query             clauses=[@2]\n",
            " @2   0..42  > > WITH            *, projections=[@3, @6], SKIP=@9, LIMIT=@10\n",
            " @3   8..14  > > > projection    expression=@4, alias=@5\n",
            " @4   8..9   > > > > integer     1\n",
            " @5  13..14  > > > > identifier  `x`\n",
            " @6  16..27  > > > projection    expression=@7, alias=@8\n",
            " @7  16..21  > > > > string      \"bar\"\n",
            " @8  25..26  > > > > identifier  `y`\n",
            " @9  32..34  > > > integer       10\n",
            "@10  41..42  > > > integer       5\n",
        ]
        assert_ast_matches_ast_dump(result, expected_ast_dump)

        ast = result[0]
        query = ast.get_body()
        clause = query.get_clauses()[0]
        self.assertEqual(clause.type, "CYPHER_AST_WITH")

        self.assertFalse(clause.is_distinct())
        self.assertTrue(clause.has_include_existing())

        self.assertEqual(len(clause.get_projections()), 2)

        proj = clause.get_projections()[0]
        self.assertEqual(proj.type, "CYPHER_AST_PROJECTION")
        exp = proj.get_expression()
        self.assertEqual(exp.type, "CYPHER_AST_INTEGER")
        self.assertEqual(exp.get_valuestr(), "1")
        alias = proj.get_alias()
        self.assertEqual(alias.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(alias.get_name(), "x")

        proj = clause.get_projections()[1]
        self.assertEqual(proj.type, "CYPHER_AST_PROJECTION")
        exp = proj.get_expression()
        self.assertEqual(exp.type, "CYPHER_AST_STRING")
        self.assertEqual(exp.get_value(), "bar")
        alias = proj.get_alias()
        self.assertEqual(alias.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(alias.get_name(), "y")

        self.assertIsNone(clause.get_order_by())

        skip = clause.get_skip()
        self.assertEqual(skip.type, "CYPHER_AST_INTEGER")
        self.assertEqual(skip.get_valuestr(), "10")

        limit = clause.get_limit()
        self.assertEqual(limit.type, "CYPHER_AST_INTEGER")
        self.assertEqual(limit.get_valuestr(), "5")

        self.assertIsNone(clause.get_predicate())

    def test_parse_with_and_predicate(self):
        result = pycypher.parse_query("WITH * WHERE n.foo > 10")
        self.assertEqual(result[-1].end, 23)

        expected_ast_dump = [
            "@0   0..23  statement             body=@1\n",
            "@1   0..23  > query               clauses=[@2]\n",
            "@2   0..23  > > WITH              *, projections=[], WHERE=@3\n",
            "@3  13..23  > > > comparison      @4 > @7\n",
            "@4  13..19  > > > > property      @5.@6\n",
            "@5  13..14  > > > > > identifier  `n`\n",
            "@6  15..18  > > > > > prop name   `foo`\n",
            "@7  21..23  > > > > integer       10\n",
        ]
        assert_ast_matches_ast_dump(result, expected_ast_dump)

        ast = result[0]
        query = ast.get_body()
        clause = query.get_clauses()[0]
        self.assertEqual(clause.type, "CYPHER_AST_WITH")

        self.assertFalse(clause.is_distinct())
        self.assertTrue(clause.has_include_existing())

        self.assertEqual(len(clause.get_projections()), 0)

        self.assertIsNone(clause.get_order_by())
        self.assertIsNone(clause.get_skip())
        self.assertIsNone(clause.get_limit())

        pred = clause.get_predicate()
        self.assertEqual(pred.type, "CYPHER_AST_COMPARISON")

