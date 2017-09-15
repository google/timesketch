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


class TestQuery(unittest.TestCase):
    def test_parse_query_with_no_options(self):
        result = pycypher.parse_query("MATCH (n) RETURN n;")
        self.assertEqual(result[-1].end, 19)

        expected_ast_dump = [
            "@0   0..19  statement               body=@1\n",
            "@1   0..19  > query                 clauses=[@2, @7]\n",
            "@2   0..10  > > MATCH               pattern=@3\n",
            "@3   6..9   > > > pattern           paths=[@4]\n",
            "@4   6..9   > > > > pattern path    (@5)\n",
            "@5   6..9   > > > > > node pattern  (@6)\n",
            "@6   7..8   > > > > > > identifier  `n`\n",
            "@7  10..18  > > RETURN              projections=[@8]\n",
            "@8  17..18  > > > projection        expression=@9\n",
            "@9  17..18  > > > > identifier      `n`\n",
        ]
        assert_ast_matches_ast_dump(result, expected_ast_dump)

        self.assertEqual(len(result), 1)
        ast = result[0]
        self.assertEqual(ast.type, "CYPHER_AST_STATEMENT")
        self.assertEqual(ast.start, 0)
        self.assertEqual(ast.end, 19)

        query = ast.get_body()
        self.assertEqual(query.type, "CYPHER_AST_QUERY")
        self.assertEqual(query.start, 0)
        self.assertEqual(query.end, 19)

        self.assertEqual(len(query.get_options()), 0)

        self.assertEqual(len(query.get_clauses()), 2)

        clause = query.get_clauses()[0]
        self.assertEqual(clause.type, "CYPHER_AST_MATCH")
        clause = query.get_clauses()[1]
        self.assertEqual(clause.type, "CYPHER_AST_RETURN")

    def test_parse_query_with_periodic_commit_option(self):
        result = pycypher.parse_query("USING PERIODIC COMMIT 500 CREATE (n);")
        self.assertEqual(result[-1].end, 37)

        expected_ast_dump = [
            "@0   0..37  statement                  body=@1\n",
            "@1   0..37  > query                    clauses=[@4]\n",
            "@2   0..26  > > USING PERIODIC_COMMIT  limit=@3\n",
            "@3  22..25  > > > integer              500\n",
            "@4  26..36  > > CREATE                 pattern=@5\n",
            "@5  33..36  > > > pattern              paths=[@6]\n",
            "@6  33..36  > > > > pattern path       (@7)\n",
            "@7  33..36  > > > > > node pattern     (@8)\n",
            "@8  34..35  > > > > > > identifier     `n`\n",
        ]
        assert_ast_matches_ast_dump(result, expected_ast_dump)

        self.assertEqual(len(result), 1)
        ast = result[0]
        self.assertEqual(ast.type, "CYPHER_AST_STATEMENT")
        self.assertEqual(ast.start, 0)
        self.assertEqual(ast.end, 37)

        query = ast.get_body()
        self.assertEqual(query.type, "CYPHER_AST_QUERY")
        self.assertEqual(query.start, 0)
        self.assertEqual(query.end, 37)

        self.assertEqual(len(query.get_options()), 1)
        option = query.get_options()[0]
        self.assertEqual(option.type, "CYPHER_AST_USING_PERIODIC_COMMIT")

        limit = option.get_limit()
        self.assertEqual(limit.type, "CYPHER_AST_INTEGER")
        self.assertEqual(limit.get_valuestr(), "500")


        self.assertEqual(len(query.get_clauses()), 1)

        clause = query.get_clauses()[0]
        self.assertEqual(clause.type, "CYPHER_AST_CREATE")

    def test_parse_query_with_periodic_commit_option_with_no_limit(self):
        result = pycypher.parse_query("USING PERIODIC COMMIT CREATE (n);")
        self.assertEqual(result[-1].end, 33)

        expected_ast_dump = [
            "@0   0..33  statement                  body=@1\n",
            "@1   0..33  > query                    clauses=[@3]\n",
            "@2   0..22  > > USING PERIODIC_COMMIT\n",
            "@3  22..32  > > CREATE                 pattern=@4\n",
            "@4  29..32  > > > pattern              paths=[@5]\n",
            "@5  29..32  > > > > pattern path       (@6)\n",
            "@6  29..32  > > > > > node pattern     (@7)\n",
            "@7  30..31  > > > > > > identifier     `n`\n",
        ]
        assert_ast_matches_ast_dump(result, expected_ast_dump)

        self.assertEqual(len(result), 1)
        ast = result[0]
        self.assertEqual(ast.type, "CYPHER_AST_STATEMENT")
        self.assertEqual(ast.start, 0)
        self.assertEqual(ast.end, 33)

        query = ast.get_body()
        self.assertEqual(query.type, "CYPHER_AST_QUERY")
        self.assertEqual(query.start, 0)
        self.assertEqual(query.end, 33)

        self.assertEqual(len(query.get_options()), 1)
        option = query.get_options()[0]
        self.assertEqual(option.type, "CYPHER_AST_USING_PERIODIC_COMMIT")
        self.assertIsNone(option.get_limit())

        self.assertEqual(len(query.get_clauses()), 1)

        clause = query.get_clauses()[0]
        self.assertEqual(clause.type, "CYPHER_AST_CREATE")

