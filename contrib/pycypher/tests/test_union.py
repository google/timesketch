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


class TestUnion(unittest.TestCase):
    def test_parse_union(self):
        result = pycypher.parse_query("RETURN 1 UNION RETURN 2;")
        self.assertEqual(result[-1].end, 24)

        expected_ast_dump = [
            " @0   0..24  statement           body=@1\n",
            " @1   0..24  > query             clauses=[@2, @6, @7]\n",
            " @2   0..9   > > RETURN          projections=[@3]\n",
            " @3   7..9   > > > projection    expression=@4, alias=@5\n",
            " @4   7..8   > > > > integer     1\n",
            " @5   7..9   > > > > identifier  `1`\n",
            " @6   9..15  > > UNION\n",
            " @7  15..23  > > RETURN          projections=[@8]\n",
            " @8  22..23  > > > projection    expression=@9, alias=@10\n",
            " @9  22..23  > > > > integer     2\n",
            "@10  22..23  > > > > identifier  `2`\n",
        ]
        assert_ast_matches_ast_dump(result, expected_ast_dump)

        ast = result[0]
        query = ast.get_body()
        self.assertEqual(len(query.get_clauses()), 3)
        clause = query.get_clauses()[0]
        self.assertEqual(clause.type, "CYPHER_AST_RETURN")

        clause = query.get_clauses()[1]
        self.assertEqual(clause.type, "CYPHER_AST_UNION")
        self.assertFalse(clause.has_all())

        clause = query.get_clauses()[2]
        self.assertEqual(clause.type, "CYPHER_AST_RETURN")

    def test_parse_union_all(self):
        result = pycypher.parse_query("MATCH (x:Foo) RETURN x UNION ALL MATCH (x:Bar) RETURN x;")
        self.assertEqual(result[-1].end, 56)

        expected_ast_dump = [
            " @0   0..56  statement               body=@1\n",
            " @1   0..56  > query                 clauses=[@2, @8, @11, @12, @18]\n",
            " @2   0..14  > > MATCH               pattern=@3\n",
            " @3   6..13  > > > pattern           paths=[@4]\n",
            " @4   6..13  > > > > pattern path    (@5)\n",
            " @5   6..13  > > > > > node pattern  (@6:@7)\n",
            " @6   7..8   > > > > > > identifier  `x`\n",
            " @7   8..12  > > > > > > label       :`Foo`\n",
            " @8  14..23  > > RETURN              projections=[@9]\n",
            " @9  21..23  > > > projection        expression=@10\n",
            "@10  21..22  > > > > identifier      `x`\n",
            "@11  23..33  > > UNION               ALL\n",
            "@12  33..47  > > MATCH               pattern=@13\n",
            "@13  39..46  > > > pattern           paths=[@14]\n",
            "@14  39..46  > > > > pattern path    (@15)\n",
            "@15  39..46  > > > > > node pattern  (@16:@17)\n",
            "@16  40..41  > > > > > > identifier  `x`\n",
            "@17  41..45  > > > > > > label       :`Bar`\n",
            "@18  47..55  > > RETURN              projections=[@19]\n",
            "@19  54..55  > > > projection        expression=@20\n",
            "@20  54..55  > > > > identifier      `x`\n",
        ]
        assert_ast_matches_ast_dump(result, expected_ast_dump)

        ast = result[0]
        query = ast.get_body()
        self.assertEqual(len(query.get_clauses()), 5)
        clause = query.get_clauses()[0]
        self.assertEqual(clause.type, "CYPHER_AST_MATCH")
        clause = query.get_clauses()[1]
        self.assertEqual(clause.type, "CYPHER_AST_RETURN")

        clause = query.get_clauses()[2]
        self.assertEqual(clause.type, "CYPHER_AST_UNION")
        self.assertTrue(clause.has_all())

        clause = query.get_clauses()[3]
        self.assertEqual(clause.type, "CYPHER_AST_MATCH")
        clause = query.get_clauses()[4]
        self.assertEqual(clause.type, "CYPHER_AST_RETURN")

