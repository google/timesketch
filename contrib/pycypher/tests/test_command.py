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


class TestCommand(unittest.TestCase):
    def test_parse_single_command_with_no_args(self):
        result = pycypher.parse_query(":hunter\n")
        self.assertEqual(result[-1].end, 7)

        expected_ast_dump = [
            "@0  0..7  command   name=@1, args=[]\n",
            "@1  1..7  > string  \"hunter\"\n",
        ]
        assert_ast_matches_ast_dump(result, expected_ast_dump)

        self.assertEqual(len(result), 1)
        ast = result[0]
        self.assertEqual(ast.type, "CYPHER_AST_COMMAND")
        self.assertEqual(ast.start, 0)
        self.assertEqual(ast.end, 7)

        name = ast.get_name()
        self.assertEqual(name.type, "CYPHER_AST_STRING")
        self.assertEqual(name.start, 1)
        self.assertEqual(name.end, 7)
        self.assertEqual(name.get_value(), "hunter")

        self.assertEqual(len(ast.get_arguments()), 0)

    def test_parse_single_command_with_args(self):
        result = pycypher.parse_query(":hunter s thompson\n")
        self.assertEqual(result[-1].end, 18)

        expected_ast_dump = [
            "@0   0..18  command   name=@1, args=[@2, @3]\n",
            "@1   1..7   > string  \"hunter\"\n",
            "@2   8..9   > string  \"s\"\n",
            "@3  10..18  > string  \"thompson\"\n",
        ]
        assert_ast_matches_ast_dump(result, expected_ast_dump)

        self.assertEqual(len(result), 1)
        ast = result[0]
        self.assertEqual(ast.type, "CYPHER_AST_COMMAND")
        self.assertEqual(ast.start, 0)
        self.assertEqual(ast.end, 18)

        name = ast.get_name()
        self.assertEqual(name.type, "CYPHER_AST_STRING")
        self.assertEqual(name.start, 1)
        self.assertEqual(name.end, 7)
        self.assertEqual(name.get_value(), "hunter")

        self.assertEqual(len(ast.get_arguments()), 2)

        arg = ast.get_arguments()[0]
        self.assertEqual(arg.type, "CYPHER_AST_STRING")
        self.assertEqual(arg.start, 8)
        self.assertEqual(arg.end, 9)
        self.assertEqual(arg.get_value(), "s")

        arg = ast.get_arguments()[1]
        self.assertEqual(arg.type, "CYPHER_AST_STRING")
        self.assertEqual(arg.start, 10)
        self.assertEqual(arg.end, 18)
        self.assertEqual(arg.get_value(), "thompson")


    def test_parse_single_command_with_quoted_args(self):
        result = pycypher.parse_query(":thompson 'hunter s'\n")
        self.assertEqual(result[-1].end, 20)

        expected_ast_dump = [
            "@0   0..20  command   name=@1, args=[@2]\n",
            "@1   1..9   > string  \"thompson\"\n",
            "@2  10..20  > string  \"hunter s\"\n",
        ]
        assert_ast_matches_ast_dump(result, expected_ast_dump)

        self.assertEqual(len(result), 1)
        ast = result[0]
        self.assertEqual(ast.type, "CYPHER_AST_COMMAND")
        self.assertEqual(ast.start, 0)
        self.assertEqual(ast.end, 20)

        self.assertEqual(len(ast.get_arguments()), 1)

        name = ast.get_name()
        self.assertEqual(name.get_value(), "thompson")

        arg = ast.get_arguments()[0]
        self.assertEqual(arg.get_value(), "hunter s")

    def test_parse_single_command_with_partial_quoted_args(self):
        result = pycypher.parse_query(":thompson lastname='hunter s'\n")
        self.assertEqual(result[-1].end, 29)

        expected_ast_dump = [
            "@0   0..29  command   name=@1, args=[@2]\n",
            "@1   1..9   > string  \"thompson\"\n",
            "@2  10..29  > string  \"lastname=hunter s\"\n",
        ]
        assert_ast_matches_ast_dump(result, expected_ast_dump)

        self.assertEqual(len(result), 1)
        ast = result[0]
        self.assertEqual(ast.type, "CYPHER_AST_COMMAND")
        self.assertEqual(ast.start, 0)
        self.assertEqual(ast.end, 29)

        self.assertEqual(len(ast.get_arguments()), 1)

        name = ast.get_name()
        self.assertEqual(name.get_value(), "thompson")

        arg = ast.get_arguments()[0]
        self.assertEqual(arg.start, 10)
        self.assertEqual(arg.end, 29)
        self.assertEqual(arg.get_value(), "lastname=hunter s")

    def test_parse_multiple_commands(self):
        result = pycypher.parse_query(":hunter\n:s;:thompson // loathing")

        expected_ast_dump = [
            "@0   0..7   command       name=@1, args=[]\n",
            "@1   1..7   > string      \"hunter\"\n",
            "@2   8..10  command       name=@3, args=[]\n",
            "@3   9..10  > string      \"s\"\n",
            "@4  11..21  command       name=@5, args=[]\n",
            "@5  12..20  > string      \"thompson\"\n",
            "@6  23..32  line_comment  // loathing\n",
        ]
        assert_ast_matches_ast_dump(result, expected_ast_dump)

    def test_parse_multiline_command(self):
        result = pycypher.parse_query(":hunter \\ //firstname\ns \\\n  \\\n thompson //lastname\n")

        expected_ast_dump = [
            "@0   0..40  command         name=@1, args=[@3, @4]\n",
            "@1   1..7   > string        \"hunter\"\n",
            "@2  12..21  > line_comment  //firstname\n",
            "@3  22..23  > string        \"s\"\n",
            "@4  31..39  > string        \"thompson\"\n",
            "@5  42..50  line_comment    //lastname\n",
        ]
        assert_ast_matches_ast_dump(result, expected_ast_dump)

    def test_parse_command_with_escape_chars(self):
        result = pycypher.parse_query(":hunter\\;s\\\"thom\\\\\"pson;\"\n")

        expected_ast_dump = [
            "@0  0..25  command   name=@1, args=[]\n",
            "@1  1..25  > string  \"hunter;s\"thom\\pson;\"\n",
        ]
        assert_ast_matches_ast_dump(result, expected_ast_dump)

    def test_parse_command_with_block_comment(self):
        result = pycypher.parse_query(":hunter /*;s\n*/thompson\n")

        expected_ast_dump = [
            "@0   0..23  command          name=@1, args=[@3]\n",
            "@1   1..7   > string         \"hunter\"\n",
            "@2  10..13  > block_comment  /*;s\\n*/\n",
            "@3  15..23  > string         \"thompson\"\n",
        ]
        assert_ast_matches_ast_dump(result, expected_ast_dump)

    def test_parse_command_with_line_comment(self):
        result = pycypher.parse_query(":hunter //;s\n:thompson \"fear /*\"\n:and \"*/loathing\"")

        expected_ast_dump = [
            "@0   0..8   command       name=@1, args=[]\n",
            "@1   1..7   > string      \"hunter\"\n",
            "@2  10..12  line_comment  //;s\n",
            "@3  13..32  command       name=@4, args=[@5]\n",
            "@4  14..22  > string      \"thompson\"\n",
            "@5  23..32  > string      \"fear /*\"\n",
            "@6  33..50  command       name=@7, args=[@8]\n",
            "@7  34..37  > string      \"and\"\n",
            "@8  38..50  > string      \"*/loathing\"\n",
        ]
        assert_ast_matches_ast_dump(result, expected_ast_dump)
