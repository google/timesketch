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


class TestPatternComprehension(unittest.TestCase):
    def test_parse_simple_pattern_comprehension(self):
        result = pycypher.parse_query("RETURN [ (a)-->(b) | b.name ];")
        self.assertEqual(result[-1].end, 30)

        expected_ast_dump = [
            " @0   0..30  statement                      body=@1\n",
            " @1   0..30  > query                        clauses=[@2]\n",
            " @2   0..29  > > RETURN                     projections=[@3]\n",
            " @3   7..29  > > > projection               expression=@4, alias=@14\n",
            " @4   7..29  > > > > pattern comprehension  [@5 | @11]\n",
            " @5   9..18  > > > > > pattern path         (@6)-[@8]-(@9)\n",
            " @6   9..12  > > > > > > node pattern       (@7)\n",
            " @7  10..11  > > > > > > > identifier       `a`\n",
            " @8  12..15  > > > > > > rel pattern        -[]->\n",
            " @9  15..18  > > > > > > node pattern       (@10)\n",
            "@10  16..17  > > > > > > > identifier       `b`\n",
            "@11  21..28  > > > > > property             @12.@13\n",
            "@12  21..22  > > > > > > identifier         `b`\n",
            "@13  23..27  > > > > > > prop name          `name`\n",
            "@14   7..29  > > > > identifier             `[ (a)-->(b) | b.name ]`\n",
        ]
        assert_ast_matches_ast_dump(result, expected_ast_dump)

        ast = result[0]
        query = ast.get_body()
        clause = query.get_clauses()[0]
        self.assertEqual(clause.type, "CYPHER_AST_RETURN")
        self.assertEqual(len(clause.get_projections()), 1)

        proj = clause.get_projections()[0]
        self.assertEqual(proj.type, "CYPHER_AST_PROJECTION")
        exp = proj.get_expression()
        self.assertEqual(exp.type, "CYPHER_AST_PATTERN_COMPREHENSION")

        self.assertIsNone(exp.get_identifier())

        path = exp.get_pattern()
        self.assertEqual(path.type, "CYPHER_AST_PATTERN_PATH")
        self.assertEqual(len(path.get_elements()), 3)

        node = path.get_elements()[0]
        self.assertEqual(node.type, "CYPHER_AST_NODE_PATTERN")
        id = node.get_identifier()
        self.assertEqual(id.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(id.get_name(), "a")

        node = path.get_elements()[1]
        self.assertEqual(node.type, "CYPHER_AST_REL_PATTERN")

        node = path.get_elements()[2]
        self.assertEqual(node.type, "CYPHER_AST_NODE_PATTERN")
        id = node.get_identifier()
        self.assertEqual(id.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(id.get_name(), "b")

        self.assertIsNone(exp.get_predicate())

        eval = exp.get_eval()
        self.assertEqual(eval.type, "CYPHER_AST_PROPERTY_OPERATOR")
        id = eval.get_expression()
        self.assertEqual(id.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(id.get_name(), "b")
        name = eval.get_prop_name()
        self.assertEqual(name.type, "CYPHER_AST_PROP_NAME")
        self.assertEqual(name.get_value(), "name")

