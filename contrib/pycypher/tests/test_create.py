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


class TestCreate(unittest.TestCase):
    def test_parse_simple_create(self):
        result = pycypher.parse_query("CREATE (n)-[:KNOWS]->(f);")
        self.assertEqual(result[-1].end, 25)

        expected_ast_dump = [
            " @0   0..25  statement               body=@1\n",
            " @1   0..25  > query                 clauses=[@2]\n",
            " @2   0..24  > > CREATE              pattern=@3\n",
            " @3   7..24  > > > pattern           paths=[@4]\n",
            " @4   7..24  > > > > pattern path    (@5)-[@7]-(@9)\n",
            " @5   7..10  > > > > > node pattern  (@6)\n",
            " @6   8..9   > > > > > > identifier  `n`\n",
            " @7  10..21  > > > > > rel pattern   -[:@8]->\n",
            " @8  12..18  > > > > > > rel type    :`KNOWS`\n",
            " @9  21..24  > > > > > node pattern  (@10)\n",
            "@10  22..23  > > > > > > identifier  `f`\n",
        ]
        assert_ast_matches_ast_dump(result, expected_ast_dump)

        ast = result[0]
        self.assertEqual(ast.type, "CYPHER_AST_STATEMENT")
        query = ast.get_body()
        self.assertEqual(query.type, "CYPHER_AST_QUERY")
        create = query.get_clauses()[0]
        self.assertEqual(create.type, "CYPHER_AST_CREATE")

        self.assertFalse(create.is_unique())

        pattern = create.get_pattern()
        self.assertEqual(pattern.type, "CYPHER_AST_PATTERN")
        self.assertEqual(len(pattern.get_paths()), 1)

    def test_parse_create_unique(self):
        result = pycypher.parse_query("CREATE UNIQUE (n)-[:KNOWS]->(f);")
        self.assertEqual(result[-1].end, 32)

        expected_ast_dump = [
            " @0   0..32  statement               body=@1\n",
            " @1   0..32  > query                 clauses=[@2]\n",
            " @2   0..31  > > CREATE              UNIQUE, pattern=@3\n",
            " @3  14..31  > > > pattern           paths=[@4]\n",
            " @4  14..31  > > > > pattern path    (@5)-[@7]-(@9)\n",
            " @5  14..17  > > > > > node pattern  (@6)\n",
            " @6  15..16  > > > > > > identifier  `n`\n",
            " @7  17..28  > > > > > rel pattern   -[:@8]->\n",
            " @8  19..25  > > > > > > rel type    :`KNOWS`\n",
            " @9  28..31  > > > > > node pattern  (@10)\n",
            "@10  29..30  > > > > > > identifier  `f`\n",
        ]
        assert_ast_matches_ast_dump(result, expected_ast_dump)

        ast = result[0]
        self.assertEqual(ast.type, "CYPHER_AST_STATEMENT")
        query = ast.get_body()
        self.assertEqual(query.type, "CYPHER_AST_QUERY")
        create = query.get_clauses()[0]
        self.assertEqual(create.type, "CYPHER_AST_CREATE")

        self.assertTrue(create.is_unique())

        pattern = create.get_pattern()
        self.assertEqual(pattern.type, "CYPHER_AST_PATTERN")
        self.assertEqual(len(pattern.get_paths()), 1)

