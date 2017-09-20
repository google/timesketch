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


class TestSet(unittest.TestCase):
    def test_parse_set_property(self):
        result = pycypher.parse_query("/*MATCH*/ SET n.foo = bar;")
        self.assertEqual(result[-1].end, 26)

        expected_ast_dump = [
            "@0   2..7   block_comment         /*MATCH*/\n",
            "@1  10..26  statement             body=@2\n",
            "@2  10..26  > query               clauses=[@3]\n",
            "@3  10..25  > > SET               items=[@4]\n",
            "@4  14..25  > > > set property    @5 = @8\n",
            "@5  14..20  > > > > property      @6.@7\n",
            "@6  14..15  > > > > > identifier  `n`\n",
            "@7  16..19  > > > > > prop name   `foo`\n",
            "@8  22..25  > > > > identifier    `bar`\n",
        ]
        assert_ast_matches_ast_dump(result, expected_ast_dump)

        ast = result[1]
        self.assertEqual(ast.type, "CYPHER_AST_STATEMENT")
        query = ast.get_body()
        self.assertEqual(query.type, "CYPHER_AST_QUERY")
        set = query.get_clauses()[0]
        self.assertEqual(set.type, "CYPHER_AST_SET")

        self.assertEqual(len(set.get_items()), 1)

        item = set.get_items()[0]
        self.assertEqual(item.type, "CYPHER_AST_SET_PROPERTY")

        prop = item.get_property()
        self.assertEqual(prop.type, "CYPHER_AST_PROPERTY_OPERATOR")
        id = prop.get_expression()
        self.assertEqual(id.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(id.get_name(), "n")
        propname = prop.get_prop_name()
        self.assertEqual(propname.type, "CYPHER_AST_PROP_NAME")
        self.assertEqual(propname.get_value(), "foo")

        expr = item.get_expression()
        self.assertEqual(expr.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(expr.get_name(), "bar")

    def test_parse_set_all_properties(self):
        result = pycypher.parse_query("/*MATCH*/ SET n = {foo: bar};")
        self.assertEqual(result[-1].end, 29)

        expected_ast_dump = [
            "@0   2..7   block_comment             /*MATCH*/\n",
            "@1  10..29  statement                 body=@2\n",
            "@2  10..29  > query                   clauses=[@3]\n",
            "@3  10..28  > > SET                   items=[@4]\n",
            "@4  14..28  > > > set all properties  @5 = @6\n",
            "@5  14..15  > > > > identifier        `n`\n",
            "@6  18..28  > > > > map               {@7:@8}\n",
            "@7  19..22  > > > > > prop name       `foo`\n",
            "@8  24..27  > > > > > identifier      `bar`\n",
        ]
        assert_ast_matches_ast_dump(result, expected_ast_dump)

        ast = result[1]
        self.assertEqual(ast.type, "CYPHER_AST_STATEMENT")
        query = ast.get_body()
        self.assertEqual(query.type, "CYPHER_AST_QUERY")
        set = query.get_clauses()[0]
        self.assertEqual(set.type, "CYPHER_AST_SET")

        self.assertEqual(len(set.get_items()), 1)

        item = set.get_items()[0]
        self.assertEqual(item.type, "CYPHER_AST_SET_ALL_PROPERTIES")

        id = item.get_identifier()
        self.assertEqual(id.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(id.get_name(), "n")

        expr = item.get_expression()
        self.assertEqual(expr.type, "CYPHER_AST_MAP")

    def test_parse_set_nested_property(self):
        result = pycypher.parse_query("/*MATCH*/ SET n.foo.bar = baz;")
        self.assertEqual(result[-1].end, 30)

        expected_ast_dump = [
            " @0   2..7   block_comment           /*MATCH*/\n",
            " @1  10..30  statement               body=@2\n",
            " @2  10..30  > query                 clauses=[@3]\n",
            " @3  10..29  > > SET                 items=[@4]\n",
            " @4  14..29  > > > set property      @5 = @10\n",
            " @5  14..24  > > > > property        @6.@9\n",
            " @6  14..19  > > > > > property      @7.@8\n",
            " @7  14..15  > > > > > > identifier  `n`\n",
            " @8  16..19  > > > > > > prop name   `foo`\n",
            " @9  20..23  > > > > > prop name     `bar`\n",
            "@10  26..29  > > > > identifier      `baz`\n",
        ]
        assert_ast_matches_ast_dump(result, expected_ast_dump)

        ast = result[1]
        self.assertEqual(ast.type, "CYPHER_AST_STATEMENT")
        query = ast.get_body()
        self.assertEqual(query.type, "CYPHER_AST_QUERY")
        set = query.get_clauses()[0]
        self.assertEqual(set.type, "CYPHER_AST_SET")

        self.assertEqual(len(set.get_items()), 1)

        item = set.get_items()[0]
        self.assertEqual(item.type, "CYPHER_AST_SET_PROPERTY")

        prop = item.get_property()
        self.assertEqual(prop.type, "CYPHER_AST_PROPERTY_OPERATOR")

        exp = prop.get_expression()
        self.assertEqual(exp.type, "CYPHER_AST_PROPERTY_OPERATOR")

        id = exp.get_expression()
        self.assertEqual(id.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(id.get_name(), "n")
        propname = exp.get_prop_name()
        self.assertEqual(propname.type, "CYPHER_AST_PROP_NAME")
        self.assertEqual(propname.get_value(), "foo")

        propname = prop.get_prop_name()
        self.assertEqual(propname.type, "CYPHER_AST_PROP_NAME")
        self.assertEqual(propname.get_value(), "bar")

        expr = item.get_expression()
        self.assertEqual(expr.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(expr.get_name(), "baz")

    def test_parse_set_expression_property(self):
        result = pycypher.parse_query("/*MATCH*/ SET (n.foo).bar = baz;")
        self.assertEqual(result[-1].end, 32)

        expected_ast_dump = [
            " @0   2..7   block_comment           /*MATCH*/\n",
            " @1  10..32  statement               body=@2\n",
            " @2  10..32  > query                 clauses=[@3]\n",
            " @3  10..31  > > SET                 items=[@4]\n",
            " @4  14..31  > > > set property      @5 = @10\n",
            " @5  14..26  > > > > property        @6.@9\n",
            " @6  15..20  > > > > > property      @7.@8\n",
            " @7  15..16  > > > > > > identifier  `n`\n",
            " @8  17..20  > > > > > > prop name   `foo`\n",
            " @9  22..25  > > > > > prop name     `bar`\n",
            "@10  28..31  > > > > identifier      `baz`\n",
        ]
        assert_ast_matches_ast_dump(result, expected_ast_dump)

        ast = result[1]
        self.assertEqual(ast.type, "CYPHER_AST_STATEMENT")
        query = ast.get_body()
        self.assertEqual(query.type, "CYPHER_AST_QUERY")
        set = query.get_clauses()[0]
        self.assertEqual(set.type, "CYPHER_AST_SET")

        self.assertEqual(len(set.get_items()), 1)

        item = set.get_items()[0]
        self.assertEqual(item.type, "CYPHER_AST_SET_PROPERTY")

        prop = item.get_property()
        self.assertEqual(prop.type, "CYPHER_AST_PROPERTY_OPERATOR")

        exp = prop.get_expression()
        self.assertEqual(exp.type, "CYPHER_AST_PROPERTY_OPERATOR")

        id = exp.get_expression()
        self.assertEqual(id.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(id.get_name(), "n")
        propname = exp.get_prop_name()
        self.assertEqual(propname.type, "CYPHER_AST_PROP_NAME")
        self.assertEqual(propname.get_value(), "foo")

        propname = prop.get_prop_name()
        self.assertEqual(propname.type, "CYPHER_AST_PROP_NAME")
        self.assertEqual(propname.get_value(), "bar")

        expr = item.get_expression()
        self.assertEqual(expr.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(expr.get_name(), "baz")

    def test_parse_merge_properties(self):
        result = pycypher.parse_query("/*MATCH*/ SET n += {foo: bar};")
        self.assertEqual(result[-1].end, 30)

        expected_ast_dump = [
            "@0   2..7   block_comment           /*MATCH*/\n",
            "@1  10..30  statement               body=@2\n",
            "@2  10..30  > query                 clauses=[@3]\n",
            "@3  10..29  > > SET                 items=[@4]\n",
            "@4  14..29  > > > merge properties  @5 += @6\n",
            "@5  14..15  > > > > identifier      `n`\n",
            "@6  19..29  > > > > map             {@7:@8}\n",
            "@7  20..23  > > > > > prop name     `foo`\n",
            "@8  25..28  > > > > > identifier    `bar`\n",
        ]
        assert_ast_matches_ast_dump(result, expected_ast_dump)

        ast = result[1]
        self.assertEqual(ast.type, "CYPHER_AST_STATEMENT")
        query = ast.get_body()
        self.assertEqual(query.type, "CYPHER_AST_QUERY")
        set = query.get_clauses()[0]
        self.assertEqual(set.type, "CYPHER_AST_SET")

        self.assertEqual(len(set.get_items()), 1)

        item = set.get_items()[0]
        self.assertEqual(item.type, "CYPHER_AST_MERGE_PROPERTIES")

        id = item.get_identifier()
        self.assertEqual(id.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(id.get_name(), "n")

        expr = item.get_expression()
        self.assertEqual(expr.type, "CYPHER_AST_MAP")

    def test_parse_set_labels(self):
        result = pycypher.parse_query("/*MATCH*/ SET n:Foo:Bar;")
        self.assertEqual(result[-1].end, 24)

        expected_ast_dump = [
            "@0   2..7   block_comment       /*MATCH*/\n",
            "@1  10..24  statement           body=@2\n",
            "@2  10..24  > query             clauses=[@3]\n",
            "@3  10..23  > > SET             items=[@4]\n",
            "@4  14..23  > > > set labels    @5:@6:@7\n",
            "@5  14..15  > > > > identifier  `n`\n",
            "@6  15..19  > > > > label       :`Foo`\n",
            "@7  19..23  > > > > label       :`Bar`\n",
        ]
        assert_ast_matches_ast_dump(result, expected_ast_dump)

        ast = result[1]
        self.assertEqual(ast.type, "CYPHER_AST_STATEMENT")
        query = ast.get_body()
        self.assertEqual(query.type, "CYPHER_AST_QUERY")
        set = query.get_clauses()[0]
        self.assertEqual(set.type, "CYPHER_AST_SET")

        self.assertEqual(len(set.get_items()), 1)

        item = set.get_items()[0]
        self.assertEqual(item.type, "CYPHER_AST_SET_LABELS")

        self.assertEqual(len(item.get_labels()), 2)

        label = item.get_labels()[0]
        self.assertEqual(label.type, "CYPHER_AST_LABEL")
        self.assertEqual(label.get_name(), "Foo")

        label = item.get_labels()[1]
        self.assertEqual(label.type, "CYPHER_AST_LABEL")
        self.assertEqual(label.get_name(), "Bar")
