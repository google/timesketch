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


class TestMapProjection(unittest.TestCase):
    def test_parse_map_project_none(self):
        result = pycypher.parse_query("RETURN a{} AS x")
        self.assertEqual(result[-1].end, 15)

        expected_ast_dump = [
            "@0   0..15  statement               body=@1\n",
            "@1   0..15  > query                 clauses=[@2]\n",
            "@2   0..15  > > RETURN              projections=[@3]\n",
            "@3   7..15  > > > projection        expression=@4, alias=@6\n",
            "@4   7..11  > > > > map projection  @5{}\n",
            "@5   7..8   > > > > > identifier    `a`\n",
            "@6  14..15  > > > > identifier      `x`\n",
        ]
        assert_ast_matches_ast_dump(result, expected_ast_dump)

        ast = result[0]
        self.assertEqual(ast.type, "CYPHER_AST_STATEMENT")
        query = ast.get_body()
        self.assertEqual(query.type, "CYPHER_AST_QUERY")
        clause = query.get_clauses()[0]
        self.assertEqual(clause.type, "CYPHER_AST_RETURN")

        self.assertEqual(len(clause.get_projections()), 1)

        proj = clause.get_projections()[0]
        self.assertEqual(proj.type, "CYPHER_AST_PROJECTION")

        exp = proj.get_expression()
        self.assertEqual(exp.type, "CYPHER_AST_MAP_PROJECTION")

        id = exp.get_expression()
        self.assertEqual(id.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(id.get_name(), "a")

        self.assertEqual(len(exp.get_selectors()), 0)

    def test_parse_map_project_multiple_selectors(self):
        result = pycypher.parse_query("RETURN map{x: 1, .y, z, .*}")

        expected_ast_dump = [
            " @0   0..27  statement                            body=@1\n",
            " @1   0..27  > query                              clauses=[@2]\n",
            " @2   0..27  > > RETURN                           projections=[@3]\n",
            " @3   7..27  > > > projection                     expression=@4, alias=@14\n",
            " @4   7..27  > > > > map projection               @5{@6, @9, @11, @13}\n",
            " @5   7..10  > > > > > identifier                 `map`\n",
            " @6  11..15  > > > > > literal projection         @7: @8\n",
            " @7  11..12  > > > > > > prop name                `x`\n",
            " @8  14..15  > > > > > > integer                  1\n",
            " @9  17..19  > > > > > property projection        .@10\n",
            "@10  18..19  > > > > > > prop name                `y`\n",
            "@11  21..22  > > > > > identifier projection      @12\n",
            "@12  21..22  > > > > > > identifier               `z`\n",
            "@13  24..26  > > > > > all properties projection  .*\n",
            "@14   7..27  > > > > identifier                   `map{x: 1, .y, z, .*}`\n",
        ]
        assert_ast_matches_ast_dump(result, expected_ast_dump)

        ast = result[0]
        self.assertEqual(ast.type, "CYPHER_AST_STATEMENT")
        query = ast.get_body()
        self.assertEqual(query.type, "CYPHER_AST_QUERY")
        clause = query.get_clauses()[0]
        self.assertEqual(clause.type, "CYPHER_AST_RETURN")

        self.assertEqual(len(clause.get_projections()), 1)

        proj = clause.get_projections()[0]
        self.assertEqual(proj.type, "CYPHER_AST_PROJECTION")

        exp = proj.get_expression()
        self.assertEqual(exp.type, "CYPHER_AST_MAP_PROJECTION")

        id = exp.get_expression()
        self.assertEqual(id.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(id.get_name(), "map")

        self.assertEqual(len(exp.get_selectors()), 4)

        sel = exp.get_selectors()[0]
        self.assertEqual(sel.type, "CYPHER_AST_MAP_PROJECTION_LITERAL")
        pname = sel.get_prop_name()
        self.assertEqual(pname.type, "CYPHER_AST_PROP_NAME")
        self.assertEqual(pname.get_value(), "x")
        lexp = sel.get_expression()
        self.assertEqual(lexp.type, "CYPHER_AST_INTEGER")
        self.assertEqual(lexp.get_valuestr(), "1")

        sel = exp.get_selectors()[1]
        self.assertEqual(sel.type, "CYPHER_AST_MAP_PROJECTION_PROPERTY")
        pname = sel.get_prop_name()
        self.assertEqual(pname.type, "CYPHER_AST_PROP_NAME")
        self.assertEqual(pname.get_value(), "y")

        sel = exp.get_selectors()[2]
        self.assertEqual(sel.type, "CYPHER_AST_MAP_PROJECTION_IDENTIFIER")
        id = sel.get_identifier()
        self.assertEqual(id.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(id.get_name(), "z")

        sel = exp.get_selectors()[3]
        self.assertEqual(sel.type, "CYPHER_AST_MAP_PROJECTION_ALL_PROPERTIES")
