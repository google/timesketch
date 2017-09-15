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


class TestIndexes(unittest.TestCase):
    def test_parse_create_node_prop_index(self):
        result = pycypher.parse_query("CREATE INDEX ON :Foo(bar);")
        self.assertEqual(result[-1].end, 26)

        expected_ast_dump = [
            "@0   0..26  statement       body=@1\n",
            "@1   0..25  > CREATE INDEX  ON=:@2(@3)\n",
            "@2  16..20  > > label       :`Foo`\n",
            "@3  21..24  > > prop name   `bar`\n",
        ]
        assert_ast_matches_ast_dump(result, expected_ast_dump)

        self.assertEqual(len(result), 1)
        ast = result[0]
        self.assertEqual(ast.type, "CYPHER_AST_STATEMENT")
        self.assertEqual(ast.start, 0)
        self.assertEqual(ast.end, 26)

        self.assertEqual(len(ast.get_options()), 0)

        body = ast.get_body()
        self.assertEqual(body.type, "CYPHER_AST_CREATE_NODE_PROP_INDEX")
        self.assertEqual(body.start, 0)
        self.assertEqual(body.end, 25)

        label = body.get_label()
        self.assertEqual(label.type, "CYPHER_AST_LABEL")
        self.assertEqual(label.get_name(), "Foo")

        prop_name = body.get_prop_name()
        self.assertEqual(prop_name.type, "CYPHER_AST_PROP_NAME")
        self.assertEqual(prop_name.get_value(), "bar")

    def test_parse_drop_node_prop_index(self):
        result = pycypher.parse_query("/* drop! */DROP INDEX ON /* a label */ :Foo(bar);")
        self.assertEqual(result[-1].end, 49)

        expected_ast_dump = [
            "@0   2..9   block_comment      /* drop! */\n",
            "@1  11..49  statement          body=@2\n",
            "@2  11..48  > DROP INDEX       ON=:@4(@5)\n",
            "@3  27..36  > > block_comment  /* a label */\n",
            "@4  39..43  > > label          :`Foo`\n",
            "@5  44..47  > > prop name      `bar`\n",
        ]
        assert_ast_matches_ast_dump(result, expected_ast_dump)

        self.assertEqual(len(result), 2)
        ast = result[1]
        self.assertEqual(ast.type, "CYPHER_AST_STATEMENT")
        self.assertEqual(ast.start, 11)
        self.assertEqual(ast.end, 49)

        self.assertEqual(len(ast.get_options()), 0)

        body = ast.get_body()
        self.assertEqual(body.type, "CYPHER_AST_DROP_NODE_PROP_INDEX")
        self.assertEqual(body.start, 11)
        self.assertEqual(body.end, 48)

        label = body.get_label()
        self.assertEqual(label.type, "CYPHER_AST_LABEL")
        self.assertEqual(label.get_name(), "Foo")

        prop_name = body.get_prop_name()
        self.assertEqual(prop_name.type, "CYPHER_AST_PROP_NAME")
        self.assertEqual(prop_name.get_value(), "bar")
