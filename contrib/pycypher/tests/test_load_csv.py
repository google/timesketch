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


class TestLoadCsv(unittest.TestCase):
    def test_parse_load_csv(self):
        result = pycypher.parse_query("LOAD CSV FROM 'file:///movies.csv' AS m RETURN m;")
        self.assertEqual(result[-1].end, 49)

        expected_ast_dump = [
            "@0   0..49  statement           body=@1\n",
            "@1   0..49  > query             clauses=[@2, @5]\n",
            "@2   0..40  > > LOAD CSV        url=@3, identifier=@4\n",
            "@3  14..34  > > > string        \"file:///movies.csv\"\n",
            "@4  38..39  > > > identifier    `m`\n",
            "@5  40..48  > > RETURN          projections=[@6]\n",
            "@6  47..48  > > > projection    expression=@7\n",
            "@7  47..48  > > > > identifier  `m`\n",
        ]
        assert_ast_matches_ast_dump(result, expected_ast_dump)

        self.assertEqual(len(result), 1)
        ast = result[0]
        self.assertEqual(ast.type, "CYPHER_AST_STATEMENT")

        query = ast.get_body()
        self.assertEqual(query.type, "CYPHER_AST_QUERY")

        self.assertEqual(len(query.get_clauses()), 2)

        clause = query.get_clauses()[0]
        self.assertEqual(clause.type, "CYPHER_AST_LOAD_CSV")

        self.assertFalse(clause.has_with_headers())

        url = clause.get_url()
        self.assertEqual(url.type, "CYPHER_AST_STRING")
        self.assertEqual(url.get_value(), "file:///movies.csv")

        id = clause.get_identifier()
        self.assertEqual(id.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(id.get_name(), "m")

        field_terminator = clause.get_field_terminator()
        self.assertIsNone(field_terminator)

    def test_parse_load_csv_with_headers(self):
        result = pycypher.parse_query("LOAD CSV WITH HEADERS FROM {source} AS m RETURN m;")
        self.assertEqual(result[-1].end, 50)

        expected_ast_dump = [
            "@0   0..50  statement           body=@1\n",
            "@1   0..50  > query             clauses=[@2, @5]\n",
            "@2   0..41  > > LOAD CSV        WITH HEADERS, url=@3, identifier=@4\n",
            "@3  27..35  > > > parameter     $`source`\n",
            "@4  39..40  > > > identifier    `m`\n",
            "@5  41..49  > > RETURN          projections=[@6]\n",
            "@6  48..49  > > > projection    expression=@7\n",
            "@7  48..49  > > > > identifier  `m`\n",
        ]
        assert_ast_matches_ast_dump(result, expected_ast_dump)

        self.assertEqual(len(result), 1)
        ast = result[0]
        self.assertEqual(ast.type, "CYPHER_AST_STATEMENT")

        query = ast.get_body()
        self.assertEqual(query.type, "CYPHER_AST_QUERY")

        self.assertEqual(len(query.get_clauses()), 2)

        clause = query.get_clauses()[0]
        self.assertEqual(clause.type, "CYPHER_AST_LOAD_CSV")

        self.assertTrue(clause.has_with_headers())

        url = clause.get_url()
        self.assertEqual(url.type, "CYPHER_AST_PARAMETER")
        self.assertEqual(url.get_name(), "source")

        id = clause.get_identifier()
        self.assertEqual(id.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(id.get_name(), "m")

        field_terminator = clause.get_field_terminator()
        self.assertIsNone(field_terminator)

    def test_parse_load_csv_with_field_terminator(self):
        result = pycypher.parse_query("LOAD CSV FROM {source} AS m FIELDTERMINATOR '|' RETURN m;")
        self.assertEqual(result[-1].end, 57)

        expected_ast_dump = [
            "@0   0..57  statement           body=@1\n",
            "@1   0..57  > query             clauses=[@2, @6]\n",
            "@2   0..48  > > LOAD CSV        url=@3, identifier=@4, field_terminator=@5\n",
            "@3  14..22  > > > parameter     $`source`\n",
            "@4  26..27  > > > identifier    `m`\n",
            "@5  44..47  > > > string        \"|\"\n",
            "@6  48..56  > > RETURN          projections=[@7]\n",
            "@7  55..56  > > > projection    expression=@8\n",
            "@8  55..56  > > > > identifier  `m`\n",
        ]
        assert_ast_matches_ast_dump(result, expected_ast_dump)

        self.assertEqual(len(result), 1)
        ast = result[0]
        self.assertEqual(ast.type, "CYPHER_AST_STATEMENT")

        query = ast.get_body()
        self.assertEqual(query.type, "CYPHER_AST_QUERY")

        self.assertEqual(len(query.get_clauses()), 2)

        clause = query.get_clauses()[0]
        self.assertEqual(clause.type, "CYPHER_AST_LOAD_CSV")

        self.assertFalse(clause.has_with_headers())

        url = clause.get_url()
        self.assertEqual(url.type, "CYPHER_AST_PARAMETER")
        self.assertEqual(url.get_name(), "source")

        id = clause.get_identifier()
        self.assertEqual(id.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(id.get_name(), "m")

        field_terminator = clause.get_field_terminator()
        self.assertEqual(field_terminator.type, "CYPHER_AST_STRING")
        self.assertEqual(field_terminator.get_value(), "|")
