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


class TestFindNodes(unittest.TestCase):
    def setUp(self):
        self.result = pycypher.parse_query("START n = node(*) /* predicate */ WHERE n.foo > 1 RETURN n;")
        self.expected_ast_dump = [
            " @0   0..59  statement             body=@1\n",
            " @1   0..59  > query               clauses=[@2, @11]\n",
            " @2   0..50  > > START             points=[@3], WHERE=@6\n",
            " @3   6..17  > > > all nodes scan  identifier=@4\n",
            " @4   6..7   > > > > identifier    `n`\n",
            " @5  20..31  > > > block_comment   /* predicate */\n",
            " @6  40..50  > > > comparison      @7 > @10\n",
            " @7  40..46  > > > > property      @8.@9\n",
            " @8  40..41  > > > > > identifier  `n`\n",
            " @9  42..45  > > > > > prop name   `foo`\n",
            "@10  48..49  > > > > integer       1\n",
            "@11  50..58  > > RETURN            projections=[@12]\n",
            "@12  57..58  > > > projection      expression=@13\n",
            "@13  57..58  > > > > identifier    `n`\n",
        ]

    def test_find_by_type_and_instanceof(self):
        ast = self.result[0]

        statement, = ast.find_nodes(type="CYPHER_AST_STATEMENT")
        self.assertEqual(statement.type, "CYPHER_AST_STATEMENT")

        comparison, = ast.find_nodes(instanceof="CYPHER_AST_COMPARISON")
        self.assertEqual(comparison.type, "CYPHER_AST_COMPARISON")

        expressions_exact = list(ast.find_nodes(type="CYPHER_AST_EXPRESSION"))
        self.assertEqual(expressions_exact, [])

        expressions = list(ast.find_nodes(instanceof="CYPHER_AST_EXPRESSION"))
        self.assertEqual([e.type for e in expressions], [
            "CYPHER_AST_IDENTIFIER",
            "CYPHER_AST_COMPARISON",
            "CYPHER_AST_PROPERTY_OPERATOR",
            "CYPHER_AST_IDENTIFIER",
            "CYPHER_AST_INTEGER",
            "CYPHER_AST_IDENTIFIER",
        ])

    def test_find_by_role(self):
        ast = self.result[0]

        start_clause, return_clause = ast.find_nodes(role="clause")
        self.assertEqual(start_clause.role, "clause")
        self.assertEqual(return_clause.role, "clause")

        body, = ast.find_nodes(role="body")
        self.assertEqual(body.role, "body")

        return_clause, = ast.find_nodes(role="clause", type="CYPHER_AST_RETURN")
        self.assertEqual(return_clause.role, "clause")
        self.assertEqual(return_clause.type, "CYPHER_AST_RETURN")

        predicate, = ast.find_nodes(role="predicate")
        self.assertEqual(predicate.role, "predicate")

    def test_find_by_range(self):
        ast = self.result[0]

        prefix = list(ast.find_nodes(end=50))
        self.assertEqual(len(prefix), 9)
        self.assertIn("CYPHER_AST_BLOCK_COMMENT", [n.type for n in prefix])
        self.assertIn("CYPHER_AST_COMPARISON", [n.type for n in prefix])
        self.assertNotIn("CYPHER_AST_RETURN", [n.type for n in prefix])
        self.assertNotIn("CYPHER_AST_PROJECTION", [n.type for n in prefix])

        suffix = list(ast.find_nodes(start=50))
        self.assertEqual(len(suffix), 3)
        self.assertEqual([n.type for n in suffix], [
            "CYPHER_AST_RETURN",
            "CYPHER_AST_PROJECTION",
            "CYPHER_AST_IDENTIFIER",
        ])

        substring = list(ast.find_nodes(start=40, end=50))
        self.assertEqual(len(substring), 5)
        self.assertEqual([n.type for n in substring], [
            "CYPHER_AST_COMPARISON",
            "CYPHER_AST_PROPERTY_OPERATOR",
            "CYPHER_AST_IDENTIFIER",
            "CYPHER_AST_PROP_NAME",
            "CYPHER_AST_INTEGER",
        ])


class TestStrRepr(unittest.TestCase):
    def setUp(self):
        self.result = pycypher.parse_query("RETURN 1;")
        self.expected_ast_dump = [
            "@0  0..9  statement           body=@1\n",
            "@1  0..9  > query             clauses=[@2]\n",
            "@2  0..8  > > RETURN          projections=[@3]\n",
            "@3  7..8  > > > projection    expression=@4, alias=@5\n",
            "@4  7..8  > > > > integer     1\n",
            "@5  7..8  > > > > identifier  `1`\n",
        ]

    def test_repr(self):
        ast = self.result[0]
        nodes = list(ast.find_nodes())
        self.assertEqual([repr(n) for n in nodes], [
            "<CypherAstNode.CYPHER_AST_STATEMENT>",
            "<CypherAstNode.CYPHER_AST_QUERY>",
            "<CypherAstNode.CYPHER_AST_RETURN>",
            "<CypherAstNode.CYPHER_AST_PROJECTION>",
            "<CypherAstNode.CYPHER_AST_INTEGER>",
            "<CypherAstNode.CYPHER_AST_IDENTIFIER>",
        ])

    def test_str(self):
        ast = self.result[0]
        nodes = list(ast.find_nodes())
        self.assertEqual([str(n) for n in nodes], [
            "<CypherAstNode.CYPHER_AST_STATEMENT>",
            "<CypherAstNode.CYPHER_AST_QUERY>",
            "<CypherAstNode.CYPHER_AST_RETURN>",
            "<CypherAstNode.CYPHER_AST_PROJECTION>",
            "<CypherAstNode.CYPHER_AST_INTEGER>",
            "<CypherAstNode.CYPHER_AST_IDENTIFIER>",
        ])


class TestToJson(unittest.TestCase):
    def setUp(self):
        self.result = pycypher.parse_query("RETURN 1;")
        self.expected_ast_dump = [
            "@0  0..9  statement           body=@1\n",
            "@1  0..9  > query             clauses=[@2]\n",
            "@2  0..8  > > RETURN          projections=[@3]\n",
            "@3  7..8  > > > projection    expression=@4, alias=@5\n",
            "@4  7..8  > > > > integer     1\n",
            "@5  7..8  > > > > identifier  `1`\n",
        ]

    def test_to_json(self):
        ast = self.result[0]

        self.assertEqual(ast.to_json(), {
            "type": "CYPHER_AST_STATEMENT",
            "instanceof": ["CYPHER_AST_STATEMENT"],
            "children": [c.to_json() for c in ast.children],
            "props": {},
            "start": 0,
            "end": 9,
            "role": None,
        })

        alias = ast.get_body().get_clauses()[0] \
            .get_projections()[0].get_alias()
        self.assertEqual(alias.to_json(), {
            "type": "CYPHER_AST_IDENTIFIER",
            "instanceof": ["CYPHER_AST_EXPRESSION", "CYPHER_AST_IDENTIFIER"],
            "children": [],
            "props": {"name": "1"},
            "start": 7,
            "end": 8,
            "role": "alias",
        })
