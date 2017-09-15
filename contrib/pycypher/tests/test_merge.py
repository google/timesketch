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


class TestMerge(unittest.TestCase):
    def test_parse_simple_merge(self):
        result = pycypher.parse_query("MERGE (n)-[:KNOWS]->(f) RETURN f;")
        self.assertEqual(result[-1].end, 33)

        expected_ast_dump = [
            " @0   0..33  statement             body=@1\n",
            " @1   0..33  > query               clauses=[@2, @10]\n",
            " @2   0..24  > > MERGE             path=@3\n",
            " @3   6..23  > > > pattern path    (@4)-[@6]-(@8)\n",
            " @4   6..9   > > > > node pattern  (@5)\n",
            " @5   7..8   > > > > > identifier  `n`\n",
            " @6   9..20  > > > > rel pattern   -[:@7]->\n",
            " @7  11..17  > > > > > rel type    :`KNOWS`\n",
            " @8  20..23  > > > > node pattern  (@9)\n",
            " @9  21..22  > > > > > identifier  `f`\n",
            "@10  24..32  > > RETURN            projections=[@11]\n",
            "@11  31..32  > > > projection      expression=@12\n",
            "@12  31..32  > > > > identifier    `f`\n",
        ]
        assert_ast_matches_ast_dump(result, expected_ast_dump)

        ast = result[0]
        self.assertEqual(ast.type, "CYPHER_AST_STATEMENT")
        query = ast.get_body()
        self.assertEqual(query.type, "CYPHER_AST_QUERY")
        merge = query.get_clauses()[0]
        self.assertEqual(merge.type, "CYPHER_AST_MERGE")

        path = merge.get_pattern_path()
        self.assertEqual(path.type, "CYPHER_AST_PATTERN_PATH")
        self.assertEqual(len(path.get_elements()), 3)

        self.assertEqual(len(merge.get_actions()), 0)

    def test_parse_merge_with_on_match_action(self):
        result = pycypher.parse_query("MERGE (n:Foo) ON MATCH SET n.bar = 'baz' RETURN n;")
        self.assertEqual(result[-1].end, 50)

        expected_ast_dump = [
            " @0   0..50  statement               body=@1\n",
            " @1   0..50  > query                 clauses=[@2, @13]\n",
            " @2   0..41  > > MERGE               path=@3, action[@7]\n",
            " @3   6..13  > > > pattern path      (@4)\n",
            " @4   6..13  > > > > node pattern    (@5:@6)\n",
            " @5   7..8   > > > > > identifier    `n`\n",
            " @6   8..12  > > > > > label         :`Foo`\n",
            " @7  14..41  > > > ON MATCH          items=[@8]\n",
            " @8  27..41  > > > > set property    @9 = @12\n",
            " @9  27..33  > > > > > property      @10.@11\n",
            "@10  27..28  > > > > > > identifier  `n`\n",
            "@11  29..32  > > > > > > prop name   `bar`\n",
            "@12  35..40  > > > > > string        \"baz\"\n",
            "@13  41..49  > > RETURN              projections=[@14]\n",
            "@14  48..49  > > > projection        expression=@15\n",
            "@15  48..49  > > > > identifier      `n`\n",
        ]
        assert_ast_matches_ast_dump(result, expected_ast_dump)

        ast = result[0]
        self.assertEqual(ast.type, "CYPHER_AST_STATEMENT")
        query = ast.get_body()
        self.assertEqual(query.type, "CYPHER_AST_QUERY")
        merge = query.get_clauses()[0]
        self.assertEqual(merge.type, "CYPHER_AST_MERGE")

        path = merge.get_pattern_path()
        self.assertEqual(path.type, "CYPHER_AST_PATTERN_PATH")
        self.assertEqual(len(path.get_elements()), 1)

        self.assertEqual(len(merge.get_actions()), 1)

        action = merge.get_actions()[0]
        self.assertTrue(action.instanceof("CYPHER_AST_MERGE_ACTION"))
        self.assertEqual(action.type, "CYPHER_AST_ON_MATCH")

        self.assertEqual(len(action.get_items()), 1)

        item = action.get_items()[0]
        self.assertEqual(item.type, "CYPHER_AST_SET_PROPERTY")

    def test_parse_merge_with_on_create_action(self):
        result = pycypher.parse_query("MERGE (n:Foo) ON CREATE SET n.bar = 'baz', n:Bar RETURN n;")
        self.assertEqual(result[-1].end, 58)

        expected_ast_dump = [
            " @0   0..58  statement               body=@1\n",
            " @1   0..58  > query                 clauses=[@2, @16]\n",
            " @2   0..49  > > MERGE               path=@3, action[@7]\n",
            " @3   6..13  > > > pattern path      (@4)\n",
            " @4   6..13  > > > > node pattern    (@5:@6)\n",
            " @5   7..8   > > > > > identifier    `n`\n",
            " @6   8..12  > > > > > label         :`Foo`\n",
            " @7  14..49  > > > ON CREATE         items=[@8, @13]\n",
            " @8  28..41  > > > > set property    @9 = @12\n",
            " @9  28..34  > > > > > property      @10.@11\n",
            "@10  28..29  > > > > > > identifier  `n`\n",
            "@11  30..33  > > > > > > prop name   `bar`\n",
            "@12  36..41  > > > > > string        \"baz\"\n",
            "@13  43..49  > > > > set labels      @14:@15\n",
            "@14  43..44  > > > > > identifier    `n`\n",
            "@15  44..48  > > > > > label         :`Bar`\n",
            "@16  49..57  > > RETURN              projections=[@17]\n",
            "@17  56..57  > > > projection        expression=@18\n",
            "@18  56..57  > > > > identifier      `n`\n",
        ]
        assert_ast_matches_ast_dump(result, expected_ast_dump)

        ast = result[0]
        self.assertEqual(ast.type, "CYPHER_AST_STATEMENT")
        query = ast.get_body()
        self.assertEqual(query.type, "CYPHER_AST_QUERY")
        merge = query.get_clauses()[0]
        self.assertEqual(merge.type, "CYPHER_AST_MERGE")

        path = merge.get_pattern_path()
        self.assertEqual(path.type, "CYPHER_AST_PATTERN_PATH")
        self.assertEqual(len(path.get_elements()), 1)

        self.assertEqual(len(merge.get_actions()), 1)

        action = merge.get_actions()[0]
        self.assertTrue(action.instanceof("CYPHER_AST_MERGE_ACTION"))
        self.assertEqual(action.type, "CYPHER_AST_ON_CREATE")

        self.assertEqual(len(action.get_items()), 2)

        item = action.get_items()[0]
        self.assertEqual(item.type, "CYPHER_AST_SET_PROPERTY")

        item = action.get_items()[1]
        self.assertEqual(item.type, "CYPHER_AST_SET_LABELS")

    def test_parse_merge_with_multiple_actions(self):
        result = pycypher.parse_query("MERGE (n:Foo) ON CREATE SET n.bar = 'baz' ON MATCH SET n.bar = 'foo' RETURN n;")
        self.assertEqual(result[-1].end, 78)

        expected_ast_dump = [
            " @0   0..78  statement               body=@1\n",
            " @1   0..78  > query                 clauses=[@2, @19]\n",
            " @2   0..69  > > MERGE               path=@3, action[@7, @13]\n",
            " @3   6..13  > > > pattern path      (@4)\n",
            " @4   6..13  > > > > node pattern    (@5:@6)\n",
            " @5   7..8   > > > > > identifier    `n`\n",
            " @6   8..12  > > > > > label         :`Foo`\n",
            " @7  14..42  > > > ON CREATE         items=[@8]\n",
            " @8  28..42  > > > > set property    @9 = @12\n",
            " @9  28..34  > > > > > property      @10.@11\n",
            "@10  28..29  > > > > > > identifier  `n`\n",
            "@11  30..33  > > > > > > prop name   `bar`\n",
            "@12  36..41  > > > > > string        \"baz\"\n",
            "@13  42..69  > > > ON MATCH          items=[@14]\n",
            "@14  55..69  > > > > set property    @15 = @18\n",
            "@15  55..61  > > > > > property      @16.@17\n",
            "@16  55..56  > > > > > > identifier  `n`\n",
            "@17  57..60  > > > > > > prop name   `bar`\n",
            "@18  63..68  > > > > > string        \"foo\"\n",
            "@19  69..77  > > RETURN              projections=[@20]\n",
            "@20  76..77  > > > projection        expression=@21\n",
            "@21  76..77  > > > > identifier      `n`\n",
        ]
        assert_ast_matches_ast_dump(result, expected_ast_dump)

        ast = result[0]
        self.assertEqual(ast.type, "CYPHER_AST_STATEMENT")
        query = ast.get_body()
        self.assertEqual(query.type, "CYPHER_AST_QUERY")
        merge = query.get_clauses()[0]
        self.assertEqual(merge.type, "CYPHER_AST_MERGE")

        path = merge.get_pattern_path()
        self.assertEqual(path.type, "CYPHER_AST_PATTERN_PATH")
        self.assertEqual(len(path.get_elements()), 1)

        self.assertEqual(len(merge.get_actions()), 2)

        action = merge.get_actions()[0]
        self.assertTrue(action.instanceof("CYPHER_AST_MERGE_ACTION"))
        self.assertEqual(action.type, "CYPHER_AST_ON_CREATE")

        self.assertEqual(len(action.get_items()), 1)

        item = action.get_items()[0]
        self.assertEqual(item.type, "CYPHER_AST_SET_PROPERTY")

        action = merge.get_actions()[1]
        self.assertTrue(action.instanceof("CYPHER_AST_MERGE_ACTION"))
        self.assertEqual(action.type, "CYPHER_AST_ON_MATCH")

        self.assertEqual(len(action.get_items()), 1)

        item = action.get_items()[0]
        self.assertEqual(item.type, "CYPHER_AST_SET_PROPERTY")

