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


class TestReturn(unittest.TestCase):
    def test_parse_simple_return(self):
        result = pycypher.parse_query("/* MATCH */ RETURN 1 AS x, 'bar' AS y")
        self.assertEqual(result[-1].end, 37)

        expected_ast_dump = [
            "@0   2..9   block_comment       /* MATCH */\n",
            "@1  12..37  statement           body=@2\n",
            "@2  12..37  > query             clauses=[@3]\n",
            "@3  12..37  > > RETURN          projections=[@4, @7]\n",
            "@4  19..25  > > > projection    expression=@5, alias=@6\n",
            "@5  19..20  > > > > integer     1\n",
            "@6  24..25  > > > > identifier  `x`\n",
            "@7  27..37  > > > projection    expression=@8, alias=@9\n",
            "@8  27..32  > > > > string      \"bar\"\n",
            "@9  36..37  > > > > identifier  `y`\n",
        ]
        assert_ast_matches_ast_dump(result, expected_ast_dump)

        ast = result[1]
        query = ast.get_body()
        clause = query.get_clauses()[0]
        self.assertEqual(clause.type, "CYPHER_AST_RETURN")

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

    def test_parse_distinct_return(self):
        result = pycypher.parse_query("/* MATCH */ RETURN DISTINCT 1 AS x, 'bar' AS y")
        self.assertEqual(result[-1].end, 46)

        expected_ast_dump = [
            "@0   2..9   block_comment       /* MATCH */\n",
            "@1  12..46  statement           body=@2\n",
            "@2  12..46  > query             clauses=[@3]\n",
            "@3  12..46  > > RETURN          DISTINCT, projections=[@4, @7]\n",
            "@4  28..34  > > > projection    expression=@5, alias=@6\n",
            "@5  28..29  > > > > integer     1\n",
            "@6  33..34  > > > > identifier  `x`\n",
            "@7  36..46  > > > projection    expression=@8, alias=@9\n",
            "@8  36..41  > > > > string      \"bar\"\n",
            "@9  45..46  > > > > identifier  `y`\n",
        ]
        assert_ast_matches_ast_dump(result, expected_ast_dump)

        ast = result[1]
        query = ast.get_body()
        clause = query.get_clauses()[0]
        self.assertEqual(clause.type, "CYPHER_AST_RETURN")

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

    def test_parse_return_including_existing(self):
        result = pycypher.parse_query("/* MATCH */ RETURN *, 1 AS x, 'bar' AS y")
        self.assertEqual(result[-1].end, 40)

        expected_ast_dump = [
            "@0   2..9   block_comment       /* MATCH */\n",
            "@1  12..40  statement           body=@2\n",
            "@2  12..40  > query             clauses=[@3]\n",
            "@3  12..40  > > RETURN          *, projections=[@4, @7]\n",
            "@4  22..28  > > > projection    expression=@5, alias=@6\n",
            "@5  22..23  > > > > integer     1\n",
            "@6  27..28  > > > > identifier  `x`\n",
            "@7  30..40  > > > projection    expression=@8, alias=@9\n",
            "@8  30..35  > > > > string      \"bar\"\n",
            "@9  39..40  > > > > identifier  `y`\n",
        ]
        assert_ast_matches_ast_dump(result, expected_ast_dump)

        ast = result[1]

        query = ast.get_body()
        clause = query.get_clauses()[0]
        self.assertEqual(clause.type, "CYPHER_AST_RETURN")

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

    def test_parse_return_and_order_by(self):
        result = pycypher.parse_query("RETURN 1 AS x, 'bar' AS y ORDER BY x DESC, y ASC, z.prop + 10")
        self.assertEqual(result[-1].end, 61)

        expected_ast_dump = [
            " @0   0..61  statement                  body=@1\n",
            " @1   0..61  > query                    clauses=[@2]\n",
            " @2   0..61  > > RETURN                 projections=[@3, @6], ORDER BY=@9\n",
            " @3   7..13  > > > projection           expression=@4, alias=@5\n",
            " @4   7..8   > > > > integer            1\n",
            " @5  12..13  > > > > identifier         `x`\n",
            " @6  15..26  > > > projection           expression=@7, alias=@8\n",
            " @7  15..20  > > > > string             \"bar\"\n",
            " @8  24..25  > > > > identifier         `y`\n",
            " @9  26..61  > > > ORDER BY             items=[@10, @12, @14]\n",
            "@10  35..41  > > > > sort item          expression=@11, DESCENDING\n",
            "@11  35..36  > > > > > identifier       `x`\n",
            "@12  43..48  > > > > sort item          expression=@13, ASCENDING\n",
            "@13  43..44  > > > > > identifier       `y`\n",
            "@14  50..61  > > > > sort item          expression=@15, ASCENDING\n",
            "@15  50..61  > > > > > binary operator  @16 + @19\n",
            "@16  50..57  > > > > > > property       @17.@18\n",
            "@17  50..51  > > > > > > > identifier   `z`\n",
            "@18  52..56  > > > > > > > prop name    `prop`\n",
            "@19  59..61  > > > > > > integer        10\n",
        ]
        assert_ast_matches_ast_dump(result, expected_ast_dump)

        ast = result[0]
        query = ast.get_body()
        clause = query.get_clauses()[0]
        self.assertEqual(clause.type, "CYPHER_AST_RETURN")

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

    def test_parse_return_and_skip(self):
        result = pycypher.parse_query("RETURN *, 1 AS x, 'bar' AS y SKIP 10")
        self.assertEqual(result[-1].end, 36)

        expected_ast_dump = [
            "@0   0..36  statement           body=@1\n",
            "@1   0..36  > query             clauses=[@2]\n",
            "@2   0..36  > > RETURN          *, projections=[@3, @6], SKIP=@9\n",
            "@3  10..16  > > > projection    expression=@4, alias=@5\n",
            "@4  10..11  > > > > integer     1\n",
            "@5  15..16  > > > > identifier  `x`\n",
            "@6  18..29  > > > projection    expression=@7, alias=@8\n",
            "@7  18..23  > > > > string      \"bar\"\n",
            "@8  27..28  > > > > identifier  `y`\n",
            "@9  34..36  > > > integer       10\n",
        ]
        assert_ast_matches_ast_dump(result, expected_ast_dump)

        ast = result[0]
        query = ast.get_body()
        clause = query.get_clauses()[0]
        self.assertEqual(clause.type, "CYPHER_AST_RETURN")

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

    def test_parse_return_and_skip_limit(self):
        result = pycypher.parse_query("RETURN *, 1 AS x, 'bar' AS y SKIP 10 LIMIT 5")
        self.assertEqual(result[-1].end, 44)

        expected_ast_dump = [
            " @0   0..44  statement           body=@1\n",
            " @1   0..44  > query             clauses=[@2]\n",
            " @2   0..44  > > RETURN          *, projections=[@3, @6], SKIP=@9, LIMIT=@10\n",
            " @3  10..16  > > > projection    expression=@4, alias=@5\n",
            " @4  10..11  > > > > integer     1\n",
            " @5  15..16  > > > > identifier  `x`\n",
            " @6  18..29  > > > projection    expression=@7, alias=@8\n",
            " @7  18..23  > > > > string      \"bar\"\n",
            " @8  27..28  > > > > identifier  `y`\n",
            " @9  34..36  > > > integer       10\n",
            "@10  43..44  > > > integer       5\n",
        ]
        assert_ast_matches_ast_dump(result, expected_ast_dump)

        ast = result[0]
        query = ast.get_body()
        clause = query.get_clauses()[0]
        self.assertEqual(clause.type, "CYPHER_AST_RETURN")

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
