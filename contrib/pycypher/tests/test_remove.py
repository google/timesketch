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


class TestRemove(unittest.TestCase):
    def test_parse_remove_label(self):
        result = pycypher.parse_query("/*MATCH*/ REMOVE n:Foo, m:Bar:Baz")
        self.assertEqual(result[-1].end, 33)

        expected_ast_dump = [
            " @0   2..7   block_comment        /*MATCH*/\n",
            " @1  10..33  statement            body=@2\n",
            " @2  10..33  > query              clauses=[@3]\n",
            " @3  10..33  > > REMOVE           items=[@4, @7]\n",
            " @4  17..22  > > > remove labels  @5:@6\n",
            " @5  17..18  > > > > identifier   `n`\n",
            " @6  18..22  > > > > label        :`Foo`\n",
            " @7  24..33  > > > remove labels  @8:@9:@10\n",
            " @8  24..25  > > > > identifier   `m`\n",
            " @9  25..29  > > > > label        :`Bar`\n",
            "@10  29..33  > > > > label        :`Baz`\n",
        ]
        assert_ast_matches_ast_dump(result, expected_ast_dump)

        ast = result[1]
        self.assertEqual(ast.type, "CYPHER_AST_STATEMENT")
        query = ast.get_body()
        self.assertEqual(query.type, "CYPHER_AST_QUERY")
        rem = query.get_clauses()[0]
        self.assertEqual(rem.type, "CYPHER_AST_REMOVE")

        self.assertEqual(len(rem.get_items()), 2)

        item = rem.get_items()[0]
        self.assertTrue(item.instanceof("CYPHER_AST_REMOVE_ITEM"))
        self.assertEqual(item.type, "CYPHER_AST_REMOVE_LABELS")

        id = item.get_identifier()
        self.assertEqual(id.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(id.get_name(), "n")

        self.assertEqual(len(item.get_labels()), 1)

        label = item.get_labels()[0]
        self.assertEqual(label.type, "CYPHER_AST_LABEL")
        self.assertEqual(label.get_name(), "Foo")

        item = rem.get_items()[1]
        self.assertTrue(item.instanceof("CYPHER_AST_REMOVE_ITEM"))
        self.assertEqual(item.type, "CYPHER_AST_REMOVE_LABELS")

        id = item.get_identifier()
        self.assertEqual(id.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(id.get_name(), "m")

        self.assertEqual(len(item.get_labels()), 2)

        label = item.get_labels()[0]
        self.assertEqual(label.type, "CYPHER_AST_LABEL")
        self.assertEqual(label.get_name(), "Bar")

        label = item.get_labels()[1]
        self.assertEqual(label.type, "CYPHER_AST_LABEL")
        self.assertEqual(label.get_name(), "Baz")

    def test_parse_remove_property(self):
        result = pycypher.parse_query("/*MATCH*/ REMOVE n.foo, m.bar.baz")
        self.assertEqual(result[-1].end, 33)

        expected_ast_dump = [
            " @0   2..7   block_comment           /*MATCH*/\n",
            " @1  10..33  statement               body=@2\n",
            " @2  10..33  > query                 clauses=[@3]\n",
            " @3  10..33  > > REMOVE              items=[@4, @8]\n",
            " @4  17..22  > > > remove property   prop=@5\n",
            " @5  17..22  > > > > property        @6.@7\n",
            " @6  17..18  > > > > > identifier    `n`\n",
            " @7  19..22  > > > > > prop name     `foo`\n",
            " @8  24..33  > > > remove property   prop=@9\n",
            " @9  24..33  > > > > property        @10.@13\n",
            "@10  24..29  > > > > > property      @11.@12\n",
            "@11  24..25  > > > > > > identifier  `m`\n",
            "@12  26..29  > > > > > > prop name   `bar`\n",
            "@13  30..33  > > > > > prop name     `baz`\n",
        ]
        assert_ast_matches_ast_dump(result, expected_ast_dump)

        ast = result[1]
        self.assertEqual(ast.type, "CYPHER_AST_STATEMENT")
        query = ast.get_body()
        self.assertEqual(query.type, "CYPHER_AST_QUERY")
        rem = query.get_clauses()[0]
        self.assertEqual(rem.type, "CYPHER_AST_REMOVE")

        self.assertEqual(len(rem.get_items()), 2)

        item = rem.get_items()[0]
        self.assertTrue(item.instanceof("CYPHER_AST_REMOVE_ITEM"))
        self.assertEqual(item.type, "CYPHER_AST_REMOVE_PROPERTY")

        prop = item.get_property()
        self.assertEqual(prop.type, "CYPHER_AST_PROPERTY_OPERATOR")
        id = prop.get_expression()
        self.assertEqual(id.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(id.get_name(), "n")
        propname = prop.get_prop_name()
        self.assertEqual(propname.type, "CYPHER_AST_PROP_NAME")
        self.assertEqual(propname.get_value(), "foo")

        item = rem.get_items()[1]
        self.assertTrue(item.instanceof("CYPHER_AST_REMOVE_ITEM"))
        self.assertEqual(item.type, "CYPHER_AST_REMOVE_PROPERTY")

        prop = item.get_property()
        self.assertEqual(prop.type, "CYPHER_AST_PROPERTY_OPERATOR")

        expr = prop.get_expression()
        self.assertEqual(expr.type, "CYPHER_AST_PROPERTY_OPERATOR")

        id = expr.get_expression()
        self.assertEqual(id.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(id.get_name(), "m")

        propname = expr.get_prop_name()
        self.assertEqual(propname.type, "CYPHER_AST_PROP_NAME")
        self.assertEqual(propname.get_value(), "bar")

        propname = prop.get_prop_name()
        self.assertEqual(propname.type, "CYPHER_AST_PROP_NAME")
        self.assertEqual(propname.get_value(), "baz")
