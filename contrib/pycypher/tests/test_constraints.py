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


class TestConstraints(unittest.TestCase):
    def test_parse_create_unique_node_prop_constraint(self):
        result = pycypher.parse_query("CREATE CONSTRAINT ON (f:Foo) ASSERT f.bar IS UNIQUE;")
        self.assertEqual(result[-1].end, 52)

        expected_ast_dump = [
            "@0   0..52  statement                      body=@1\n",
            "@1   0..51  > create node prop constraint  ON=(@2:@3), expression=@4, IS UNIQUE\n",
            "@2  22..23  > > identifier                 `f`\n",
            "@3  23..27  > > label                      :`Foo`\n",
            "@4  36..42  > > property                   @5.@6\n",
            "@5  36..37  > > > identifier               `f`\n",
            "@6  38..41  > > > prop name                `bar`\n",
        ]
        assert_ast_matches_ast_dump(result, expected_ast_dump)

        self.assertEqual(len(result), 1)
        ast = result[0]
        self.assertEqual(ast.type, "CYPHER_AST_STATEMENT")
        self.assertEqual(ast.start, 0)
        self.assertEqual(ast.end, 52)

        self.assertEqual(len(ast.get_options()), 0)

        body = ast.get_body()
        self.assertEqual(body.type, "CYPHER_AST_CREATE_NODE_PROP_CONSTRAINT")
        self.assertEqual(body.start, 0)
        self.assertEqual(body.end, 51)

        id = body.get_identifier()
        self.assertEqual(id.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(id.get_name(), "f")

        label = body.get_label()
        self.assertEqual(label.type, "CYPHER_AST_LABEL")
        self.assertEqual(label.get_name(), "Foo")

        expr = body.get_expression()
        self.assertTrue(expr.instanceof("CYPHER_AST_EXPRESSION"))
        self.assertEqual(expr.type, "CYPHER_AST_PROPERTY_OPERATOR")

        eid = expr.get_expression()
        self.assertEqual(eid.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(eid.get_name(), "f")

        prop_name = expr.get_prop_name()
        self.assertEqual(prop_name.type, "CYPHER_AST_PROP_NAME")
        self.assertEqual(prop_name.get_value(), "bar")

        self.assertTrue(body.is_unique())

    def test_parse_drop_unique_node_prop_constraint(self):
        result = pycypher.parse_query("DROP CONSTRAINT ON (f:Foo) ASSERT f.bar IS UNIQUE;")
        self.assertEqual(result[-1].end, 50)

        expected_ast_dump = [
            "@0   0..50  statement                    body=@1\n",
            "@1   0..49  > drop node prop constraint  ON=(@2:@3), expression=@4, IS UNIQUE\n",
            "@2  20..21  > > identifier               `f`\n",
            "@3  21..25  > > label                    :`Foo`\n",
            "@4  34..40  > > property                 @5.@6\n",
            "@5  34..35  > > > identifier             `f`\n",
            "@6  36..39  > > > prop name              `bar`\n",
        ]
        assert_ast_matches_ast_dump(result, expected_ast_dump)

        self.assertEqual(len(result), 1)
        ast = result[0]
        self.assertEqual(ast.type, "CYPHER_AST_STATEMENT")
        self.assertEqual(ast.start, 0)
        self.assertEqual(ast.end, 50)

        self.assertEqual(len(ast.get_options()), 0)

        body = ast.get_body()
        self.assertEqual(body.type, "CYPHER_AST_DROP_NODE_PROP_CONSTRAINT")
        self.assertEqual(body.start, 0)
        self.assertEqual(body.end, 49)

        id = body.get_identifier()
        self.assertEqual(id.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(id.get_name(), "f")

        label = body.get_label()
        self.assertEqual(label.type, "CYPHER_AST_LABEL")
        self.assertEqual(label.get_name(), "Foo")

        expr = body.get_expression()
        self.assertTrue(expr.instanceof("CYPHER_AST_EXPRESSION"))
        self.assertEqual(expr.type, "CYPHER_AST_PROPERTY_OPERATOR")

        eid = expr.get_expression()
        self.assertEqual(eid.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(eid.get_name(), "f")

        prop_name = expr.get_prop_name()
        self.assertEqual(prop_name.type, "CYPHER_AST_PROP_NAME")
        self.assertEqual(prop_name.get_value(), "bar")

        self.assertTrue(body.is_unique())

    def test_parse_create_node_prop_constraint(self):
        result = pycypher.parse_query("CREATE CONSTRAINT ON (f:Foo) ASSERT exists(f.bar);")
        self.assertEqual(result[-1].end, 50)

        expected_ast_dump = [
            "@0   0..50  statement                      body=@1\n",
            "@1   0..49  > create node prop constraint  ON=(@2:@3), expression=@4\n",
            "@2  22..23  > > identifier                 `f`\n",
            "@3  23..27  > > label                      :`Foo`\n",
            "@4  36..49  > > apply                      @5(@6)\n",
            "@5  36..42  > > > function name            `exists`\n",
            "@6  43..48  > > > property                 @7.@8\n",
            "@7  43..44  > > > > identifier             `f`\n",
            "@8  45..48  > > > > prop name              `bar`\n",
        ]
        assert_ast_matches_ast_dump(result, expected_ast_dump)

        self.assertEqual(len(result), 1)
        ast = result[0]
        self.assertEqual(ast.type, "CYPHER_AST_STATEMENT")
        self.assertEqual(ast.start, 0)
        self.assertEqual(ast.end, 50)

        self.assertEqual(len(ast.get_options()), 0)

        body = ast.get_body()
        self.assertEqual(body.type, "CYPHER_AST_CREATE_NODE_PROP_CONSTRAINT")
        self.assertEqual(body.start, 0)
        self.assertEqual(body.end, 49)

        id = body.get_identifier()
        self.assertEqual(id.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(id.get_name(), "f")

        label = body.get_label()
        self.assertEqual(label.type, "CYPHER_AST_LABEL")
        self.assertEqual(label.get_name(), "Foo")

        apply = body.get_expression()
        self.assertEqual(apply.type, "CYPHER_AST_APPLY_OPERATOR")

        func_name = apply.get_func_name()
        self.assertEqual(func_name.type, "CYPHER_AST_FUNCTION_NAME")
        self.assertEqual(func_name.get_value(), "exists")

        property = apply.get_arguments()[0]
        self.assertEqual(property.type, "CYPHER_AST_PROPERTY_OPERATOR")

        expr = property.get_expression()
        self.assertEqual(expr.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(expr.get_name(), "f")

        prop_name = property.get_prop_name()
        self.assertEqual(prop_name.type, "CYPHER_AST_PROP_NAME")
        self.assertEqual(prop_name.get_value(), "bar")

        self.assertFalse(body.is_unique())

    def test_parse_drop_node_prop_constraint(self):
        result = pycypher.parse_query("DROP CONSTRAINT ON (f:Foo) ASSERT exists(f.bar);")
        self.assertEqual(result[-1].end, 48)

        expected_ast_dump = [
            "@0   0..48  statement                    body=@1\n",
            "@1   0..47  > drop node prop constraint  ON=(@2:@3), expression=@4\n",
            "@2  20..21  > > identifier               `f`\n",
            "@3  21..25  > > label                    :`Foo`\n",
            "@4  34..47  > > apply                    @5(@6)\n",
            "@5  34..40  > > > function name          `exists`\n",
            "@6  41..46  > > > property               @7.@8\n",
            "@7  41..42  > > > > identifier           `f`\n",
            "@8  43..46  > > > > prop name            `bar`\n",
        ]
        assert_ast_matches_ast_dump(result, expected_ast_dump)

        self.assertEqual(len(result), 1)
        ast = result[0]
        self.assertEqual(ast.type, "CYPHER_AST_STATEMENT")
        self.assertEqual(ast.start, 0)
        self.assertEqual(ast.end, 48)

        self.assertEqual(len(ast.get_options()), 0)

        body = ast.get_body()
        self.assertEqual(body.type, "CYPHER_AST_DROP_NODE_PROP_CONSTRAINT")
        self.assertEqual(body.start, 0)
        self.assertEqual(body.end, 47)

        id = body.get_identifier()
        self.assertEqual(id.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(id.get_name(), "f")

        label = body.get_label()
        self.assertEqual(label.type, "CYPHER_AST_LABEL")
        self.assertEqual(label.get_name(), "Foo")

        apply = body.get_expression()
        self.assertEqual(apply.type, "CYPHER_AST_APPLY_OPERATOR")

        func_name = apply.get_func_name()
        self.assertEqual(func_name.type, "CYPHER_AST_FUNCTION_NAME")
        self.assertEqual(func_name.get_value(), "exists")

        property = apply.get_arguments()[0]
        self.assertEqual(property.type, "CYPHER_AST_PROPERTY_OPERATOR")

        expr = property.get_expression()
        self.assertEqual(expr.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(expr.get_name(), "f")

        prop_name = property.get_prop_name()
        self.assertEqual(prop_name.type, "CYPHER_AST_PROP_NAME")
        self.assertEqual(prop_name.get_value(), "bar")

        self.assertFalse(body.is_unique())

    def test_parse_create_rel_prop_constraint(self):
        result = pycypher.parse_query("CREATE CONSTRAINT ON ()-[f:Foo]-() ASSERT exists(f.bar);")
        self.assertEqual(result[-1].end, 56)

        expected_ast_dump = [
            "@0   0..56  statement                     body=@1\n",
            "@1   0..55  > create rel prop constraint  ON=(@2:@3), expression=@4\n",
            "@2  25..26  > > identifier                `f`\n",
            "@3  26..30  > > rel type                  :`Foo`\n",
            "@4  42..55  > > apply                     @5(@6)\n",
            "@5  42..48  > > > function name           `exists`\n",
            "@6  49..54  > > > property                @7.@8\n",
            "@7  49..50  > > > > identifier            `f`\n",
            "@8  51..54  > > > > prop name             `bar`\n",
        ]
        assert_ast_matches_ast_dump(result, expected_ast_dump)

        self.assertEqual(len(result), 1)
        ast = result[0]
        self.assertEqual(ast.type, "CYPHER_AST_STATEMENT")
        self.assertEqual(ast.start, 0)
        self.assertEqual(ast.end, 56)

        self.assertEqual(len(ast.get_options()), 0)

        body = ast.get_body()
        self.assertEqual(body.type, "CYPHER_AST_CREATE_REL_PROP_CONSTRAINT")
        self.assertEqual(body.start, 0)
        self.assertEqual(body.end, 55)

        id = body.get_identifier()
        self.assertEqual(id.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(id.get_name(), "f")

        reltype = body.get_reltype()
        self.assertEqual(reltype.type, "CYPHER_AST_RELTYPE")
        self.assertEqual(reltype.get_name(), "Foo")

        apply = body.get_expression()
        self.assertEqual(apply.type, "CYPHER_AST_APPLY_OPERATOR")

        func_name = apply.get_func_name()
        self.assertEqual(func_name.type, "CYPHER_AST_FUNCTION_NAME")
        self.assertEqual(func_name.get_value(), "exists")

        property = apply.get_arguments()[0]
        self.assertEqual(property.type, "CYPHER_AST_PROPERTY_OPERATOR")

        expr = property.get_expression()
        self.assertEqual(expr.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(expr.get_name(), "f")

        prop_name = property.get_prop_name()
        self.assertEqual(prop_name.type, "CYPHER_AST_PROP_NAME")
        self.assertEqual(prop_name.get_value(), "bar")

        self.assertFalse(body.is_unique())

    def test_parse_drop_rel_prop_constraint(self):
        result = pycypher.parse_query("DROP CONSTRAINT ON ()-[f:Foo]-() ASSERT exists(f.bar);")
        self.assertEqual(result[-1].end, 54)

        expected_ast_dump = [
            "@0   0..54  statement                   body=@1\n",
            "@1   0..53  > drop rel prop constraint  ON=(@2:@3), expression=@4\n",
            "@2  23..24  > > identifier              `f`\n",
            "@3  24..28  > > rel type                :`Foo`\n",
            "@4  40..53  > > apply                   @5(@6)\n",
            "@5  40..46  > > > function name         `exists`\n",
            "@6  47..52  > > > property              @7.@8\n",
            "@7  47..48  > > > > identifier          `f`\n",
            "@8  49..52  > > > > prop name           `bar`\n",
        ]
        assert_ast_matches_ast_dump(result, expected_ast_dump)

        self.assertEqual(len(result), 1)
        ast = result[0]
        self.assertEqual(ast.type, "CYPHER_AST_STATEMENT")
        self.assertEqual(ast.start, 0)
        self.assertEqual(ast.end, 54)

        self.assertEqual(len(ast.get_options()), 0)

        body = ast.get_body()
        self.assertEqual(body.type, "CYPHER_AST_DROP_REL_PROP_CONSTRAINT")
        self.assertEqual(body.start, 0)
        self.assertEqual(body.end, 53)

        id = body.get_identifier()
        self.assertEqual(id.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(id.get_name(), "f")

        reltype = body.get_reltype()
        self.assertEqual(reltype.type, "CYPHER_AST_RELTYPE")
        self.assertEqual(reltype.get_name(), "Foo")

        apply = body.get_expression()
        self.assertEqual(apply.type, "CYPHER_AST_APPLY_OPERATOR")

        func_name = apply.get_func_name()
        self.assertEqual(func_name.type, "CYPHER_AST_FUNCTION_NAME")
        self.assertEqual(func_name.get_value(), "exists")

        property = apply.get_arguments()[0]
        self.assertEqual(property.type, "CYPHER_AST_PROPERTY_OPERATOR")

        expr = property.get_expression()
        self.assertEqual(expr.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(expr.get_name(), "f")

        prop_name = property.get_prop_name()
        self.assertEqual(prop_name.type, "CYPHER_AST_PROP_NAME")
        self.assertEqual(prop_name.get_value(), "bar")

        self.assertFalse(body.is_unique())

