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


class TestMatch(unittest.TestCase):
    def test_parse_simple_match(self):
        result = pycypher.parse_query("MATCH (n)-[:KNOWS]->(f) RETURN f;")
        self.assertEqual(result[-1].end, 33)

        expected_ast_dump = [
            " @0   0..33  statement               body=@1\n",
            " @1   0..33  > query                 clauses=[@2, @11]\n",
            " @2   0..24  > > MATCH               pattern=@3\n",
            " @3   6..23  > > > pattern           paths=[@4]\n",
            " @4   6..23  > > > > pattern path    (@5)-[@7]-(@9)\n",
            " @5   6..9   > > > > > node pattern  (@6)\n",
            " @6   7..8   > > > > > > identifier  `n`\n",
            " @7   9..20  > > > > > rel pattern   -[:@8]->\n",
            " @8  11..17  > > > > > > rel type    :`KNOWS`\n",
            " @9  20..23  > > > > > node pattern  (@10)\n",
            "@10  21..22  > > > > > > identifier  `f`\n",
            "@11  24..32  > > RETURN              projections=[@12]\n",
            "@12  31..32  > > > projection        expression=@13\n",
            "@13  31..32  > > > > identifier      `f`\n",
        ]
        assert_ast_matches_ast_dump(result, expected_ast_dump)

        ast = result[0]
        self.assertEqual(ast.type, "CYPHER_AST_STATEMENT")
        query = ast.get_body()
        self.assertEqual(query.type, "CYPHER_AST_QUERY")
        match = query.get_clauses()[0]
        self.assertEqual(match.type, "CYPHER_AST_MATCH")

        self.assertFalse(match.is_optional())

        pattern = match.get_pattern()
        self.assertEqual(pattern.type, "CYPHER_AST_PATTERN")
        self.assertEqual(len(pattern.get_paths()), 1)

        self.assertEqual(len(match.get_hints()), 0)
        self.assertIsNone(match.get_predicate())

    def test_parse_simple_optional_match(self):
        result = pycypher.parse_query("OPTIONAL MATCH (n) RETURN n;")
        self.assertEqual(result[-1].end, 28)

        expected_ast_dump = [
            "@0   0..28  statement               body=@1\n",
            "@1   0..28  > query                 clauses=[@2, @7]\n",
            "@2   0..19  > > MATCH               OPTIONAL, pattern=@3\n",
            "@3  15..18  > > > pattern           paths=[@4]\n",
            "@4  15..18  > > > > pattern path    (@5)\n",
            "@5  15..18  > > > > > node pattern  (@6)\n",
            "@6  16..17  > > > > > > identifier  `n`\n",
            "@7  19..27  > > RETURN              projections=[@8]\n",
            "@8  26..27  > > > projection        expression=@9\n",
            "@9  26..27  > > > > identifier      `n`\n",
        ]
        assert_ast_matches_ast_dump(result, expected_ast_dump)

        ast = result[0]
        self.assertEqual(ast.type, "CYPHER_AST_STATEMENT")
        query = ast.get_body()
        self.assertEqual(query.type, "CYPHER_AST_QUERY")
        match = query.get_clauses()[0]
        self.assertEqual(match.type, "CYPHER_AST_MATCH")

        self.assertTrue(match.is_optional())

        pattern = match.get_pattern()
        self.assertEqual(pattern.type, "CYPHER_AST_PATTERN")
        self.assertEqual(len(pattern.get_paths()), 1)

        self.assertEqual(len(match.get_hints()), 0)
        self.assertIsNone(match.get_predicate())

    def test_parse_match_with_predicate(self):
        result = pycypher.parse_query("MATCH (n) WHERE n:Foo RETURN n;")
        self.assertEqual(result[-1].end, 31)

        expected_ast_dump = [
            " @0   0..31  statement               body=@1\n",
            " @1   0..31  > query                 clauses=[@2, @10]\n",
            " @2   0..22  > > MATCH               pattern=@3, where=@7\n",
            " @3   6..9   > > > pattern           paths=[@4]\n",
            " @4   6..9   > > > > pattern path    (@5)\n",
            " @5   6..9   > > > > > node pattern  (@6)\n",
            " @6   7..8   > > > > > > identifier  `n`\n",
            " @7  16..22  > > > has labels        @8:@9\n",
            " @8  16..17  > > > > identifier      `n`\n",
            " @9  17..21  > > > > label           :`Foo`\n",
            "@10  22..30  > > RETURN              projections=[@11]\n",
            "@11  29..30  > > > projection        expression=@12\n",
            "@12  29..30  > > > > identifier      `n`\n",
        ]
        assert_ast_matches_ast_dump(result, expected_ast_dump)

        ast = result[0]
        self.assertEqual(ast.type, "CYPHER_AST_STATEMENT")
        query = ast.get_body()
        self.assertEqual(query.type, "CYPHER_AST_QUERY")
        match = query.get_clauses()[0]
        self.assertEqual(match.type, "CYPHER_AST_MATCH")

        self.assertFalse(match.is_optional())

        pattern = match.get_pattern()
        self.assertEqual(pattern.type, "CYPHER_AST_PATTERN")
        self.assertEqual(len(pattern.get_paths()), 1)

        self.assertEqual(len(match.get_hints()), 0)

        pred = match.get_predicate()
        self.assertEqual(pred.type, "CYPHER_AST_LABELS_OPERATOR")

        id = pred.get_expression()
        self.assertEqual(id.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(id.get_name(), "n")

        self.assertEqual(len(pred.get_labels()), 1)
        label = pred.get_labels()[0]
        self.assertEqual(label.type, "CYPHER_AST_LABEL")
        self.assertEqual(label.get_name(), "Foo")

    def test_parse_match_with_using_index_hint(self):
        result = pycypher.parse_query("MATCH (n:Foo) USING INDEX n:Foo(bar) RETURN n;")
        self.assertEqual(result[-1].end, 46)

        expected_ast_dump = [
            " @0   0..46  statement               body=@1\n",
            " @1   0..46  > query                 clauses=[@2, @12]\n",
            " @2   0..37  > > MATCH               pattern=@3, hints=[@8]\n",
            " @3   6..13  > > > pattern           paths=[@4]\n",
            " @4   6..13  > > > > pattern path    (@5)\n",
            " @5   6..13  > > > > > node pattern  (@6:@7)\n",
            " @6   7..8   > > > > > > identifier  `n`\n",
            " @7   8..12  > > > > > > label       :`Foo`\n",
            " @8  14..37  > > > USING INDEX       @9:@10(@11)\n",
            " @9  26..27  > > > > identifier      `n`\n",
            "@10  27..31  > > > > label           :`Foo`\n",
            "@11  32..35  > > > > prop name       `bar`\n",
            "@12  37..45  > > RETURN              projections=[@13]\n",
            "@13  44..45  > > > projection        expression=@14\n",
            "@14  44..45  > > > > identifier      `n`\n",
        ]
        assert_ast_matches_ast_dump(result, expected_ast_dump)

        ast = result[0]
        self.assertEqual(ast.type, "CYPHER_AST_STATEMENT")
        query = ast.get_body()
        self.assertEqual(query.type, "CYPHER_AST_QUERY")
        match = query.get_clauses()[0]
        self.assertEqual(match.type, "CYPHER_AST_MATCH")

        self.assertFalse(match.is_optional())

        pattern = match.get_pattern()
        self.assertEqual(pattern.type, "CYPHER_AST_PATTERN")
        self.assertEqual(len(pattern.get_paths()), 1)

        path = pattern.get_paths()[0]
        self.assertEqual(path.type, "CYPHER_AST_PATTERN_PATH")
        self.assertEqual(len(path.get_elements()), 1)

        self.assertEqual(len(match.get_hints()), 1)

        hint = match.get_hints()[0]
        self.assertTrue(hint.instanceof("CYPHER_AST_MATCH_HINT"))
        self.assertEqual(hint.type, "CYPHER_AST_USING_INDEX")

        id = hint.get_identifier()
        self.assertEqual(id.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(id.get_name(), "n")

        label = hint.get_label()
        self.assertEqual(label.type, "CYPHER_AST_LABEL")
        self.assertEqual(label.get_name(), "Foo")

        prop_name = hint.get_prop_name()
        self.assertEqual(prop_name.type, "CYPHER_AST_PROP_NAME")
        self.assertEqual(prop_name.get_value(), "bar")

        self.assertIsNone(match.get_predicate())

    def test_parse_match_with_using_join_hint(self):
        result = pycypher.parse_query("MATCH (n), (m) USING JOIN ON n, m RETURN n;")
        self.assertEqual(result[-1].end, 43)

        expected_ast_dump = [
            " @0   0..43  statement               body=@1\n",
            " @1   0..43  > query                 clauses=[@2, @13]\n",
            " @2   0..34  > > MATCH               pattern=@3, hints=[@10]\n",
            " @3   6..14  > > > pattern           paths=[@4, @7]\n",
            " @4   6..9   > > > > pattern path    (@5)\n",
            " @5   6..9   > > > > > node pattern  (@6)\n",
            " @6   7..8   > > > > > > identifier  `n`\n",
            " @7  11..14  > > > > pattern path    (@8)\n",
            " @8  11..14  > > > > > node pattern  (@9)\n",
            " @9  12..13  > > > > > > identifier  `m`\n",
            "@10  15..34  > > > USING JOIN        on=[@11, @12]\n",
            "@11  29..30  > > > > identifier      `n`\n",
            "@12  32..33  > > > > identifier      `m`\n",
            "@13  34..42  > > RETURN              projections=[@14]\n",
            "@14  41..42  > > > projection        expression=@15\n",
            "@15  41..42  > > > > identifier      `n`\n",
        ]
        assert_ast_matches_ast_dump(result, expected_ast_dump)

        ast = result[0]
        self.assertEqual(ast.type, "CYPHER_AST_STATEMENT")
        query = ast.get_body()
        self.assertEqual(query.type, "CYPHER_AST_QUERY")
        match = query.get_clauses()[0]
        self.assertEqual(match.type, "CYPHER_AST_MATCH")

        self.assertFalse(match.is_optional())

        pattern = match.get_pattern()
        self.assertEqual(pattern.type, "CYPHER_AST_PATTERN")
        self.assertEqual(len(pattern.get_paths()), 2)
        path = pattern.get_paths()[0]
        self.assertEqual(path.type, "CYPHER_AST_PATTERN_PATH")
        path = pattern.get_paths()[1]
        self.assertEqual(path.type, "CYPHER_AST_PATTERN_PATH")

        self.assertEqual(len(match.get_hints()), 1)

        hint = match.get_hints()[0]
        self.assertTrue(hint.instanceof("CYPHER_AST_MATCH_HINT"))
        self.assertEqual(hint.type, "CYPHER_AST_USING_JOIN")

        self.assertEqual(len(hint.get_identifiers()), 2)

        id = hint.get_identifiers()[0]
        self.assertEqual(id.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(id.get_name(), "n")

        id = hint.get_identifiers()[1]
        self.assertEqual(id.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(id.get_name(), "m")

        self.assertIsNone(match.get_predicate())

    def test_parse_match_with_using_scan_hint(self):
        result = pycypher.parse_query("MATCH (n:Foo) USING SCAN n:Foo RETURN n;")
        self.assertEqual(result[-1].end, 40)

        expected_ast_dump = [
            " @0   0..40  statement               body=@1\n",
            " @1   0..40  > query                 clauses=[@2, @11]\n",
            " @2   0..31  > > MATCH               pattern=@3, hints=[@8]\n",
            " @3   6..13  > > > pattern           paths=[@4]\n",
            " @4   6..13  > > > > pattern path    (@5)\n",
            " @5   6..13  > > > > > node pattern  (@6:@7)\n",
            " @6   7..8   > > > > > > identifier  `n`\n",
            " @7   8..12  > > > > > > label       :`Foo`\n",
            " @8  14..31  > > > USING SCAN        @9:@10\n",
            " @9  25..26  > > > > identifier      `n`\n",
            "@10  26..30  > > > > label           :`Foo`\n",
            "@11  31..39  > > RETURN              projections=[@12]\n",
            "@12  38..39  > > > projection        expression=@13\n",
            "@13  38..39  > > > > identifier      `n`\n",
        ]
        assert_ast_matches_ast_dump(result, expected_ast_dump)

        ast = result[0]
        self.assertEqual(ast.type, "CYPHER_AST_STATEMENT")
        query = ast.get_body()
        self.assertEqual(query.type, "CYPHER_AST_QUERY")
        match = query.get_clauses()[0]
        self.assertEqual(match.type, "CYPHER_AST_MATCH")

        self.assertFalse(match.is_optional())

        pattern = match.get_pattern()
        self.assertEqual(pattern.type, "CYPHER_AST_PATTERN")
        self.assertEqual(len(pattern.get_paths()), 1)

        self.assertEqual(len(match.get_hints()), 1)

        hint = match.get_hints()[0]
        self.assertTrue(hint.instanceof("CYPHER_AST_MATCH_HINT"))
        self.assertEqual(hint.type, "CYPHER_AST_USING_SCAN")

        id = hint.get_identifier()
        self.assertEqual(id.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(id.get_name(), "n")

        label = hint.get_label()
        self.assertEqual(label.type, "CYPHER_AST_LABEL")
        self.assertEqual(label.get_name(), "Foo")

        self.assertIsNone(match.get_predicate())

