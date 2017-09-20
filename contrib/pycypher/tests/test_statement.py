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


class TestStatement(unittest.TestCase):
    def test_parse_statement_with_no_options(self):
        result = pycypher.parse_query("RETURN 1;")
        self.assertEqual(result[-1].end, 9)

        expected_ast_dump = [
            "@0  0..9  statement           body=@1\n",
            "@1  0..9  > query             clauses=[@2]\n",
            "@2  0..8  > > RETURN          projections=[@3]\n",
            "@3  7..8  > > > projection    expression=@4, alias=@5\n",
            "@4  7..8  > > > > integer     1\n",
            "@5  7..8  > > > > identifier  `1`\n",
        ]
        assert_ast_matches_ast_dump(result, expected_ast_dump)

        self.assertEqual(len(result), 1)
        ast = result[0]
        self.assertEqual(ast.type, "CYPHER_AST_STATEMENT")
        self.assertEqual(ast.start, 0)
        self.assertEqual(ast.end, 9)

        body = ast.get_body()
        self.assertEqual(body.type, "CYPHER_AST_QUERY")
        self.assertEqual(body.start, 0)
        self.assertEqual(body.end, 9)

        self.assertEqual(len(ast.get_options()), 0)

    def test_parse_statement_with_cypher_option(self):
        result = pycypher.parse_query("CYPHER RETURN 1;")

        expected_ast_dump = [
            "@0   0..16  statement           options=[@1], body=@2\n",
            "@1   0..7   > CYPHER\n",
            "@2   7..16  > query             clauses=[@3]\n",
            "@3   7..15  > > RETURN          projections=[@4]\n",
            "@4  14..15  > > > projection    expression=@5, alias=@6\n",
            "@5  14..15  > > > > integer     1\n",
            "@6  14..15  > > > > identifier  `1`\n",
        ]
        assert_ast_matches_ast_dump(result, expected_ast_dump)

        self.assertEqual(len(result), 1)
        ast = result[0]
        self.assertEqual(ast.type, "CYPHER_AST_STATEMENT")

        self.assertEqual(len(ast.get_options()), 1)
        option = ast.get_options()[0]
        self.assertTrue(option.instanceof("CYPHER_AST_STATEMENT_OPTION"))
        self.assertEqual(option.type, "CYPHER_AST_CYPHER_OPTION")

        self.assertIsNone(option.get_version())
        self.assertEqual(len(option.get_params()), 0)

    def test_parse_statement_with_cypher_option_containing_version(self):
        result = pycypher.parse_query("CYPHER 3.0 RETURN 1;")

        expected_ast_dump = [
            "@0   0..20  statement           options=[@1], body=@3\n",
            "@1   0..10  > CYPHER            version=@2\n",
            "@2   7..10  > > string          \"3.0\"\n",
            "@3  11..20  > query             clauses=[@4]\n",
            "@4  11..19  > > RETURN          projections=[@5]\n",
            "@5  18..19  > > > projection    expression=@6, alias=@7\n",
            "@6  18..19  > > > > integer     1\n",
            "@7  18..19  > > > > identifier  `1`\n",
        ]
        assert_ast_matches_ast_dump(result, expected_ast_dump)

        self.assertEqual(len(result), 1)
        ast = result[0]
        self.assertEqual(ast.type, "CYPHER_AST_STATEMENT")

        self.assertEqual(len(ast.get_options()), 1)
        option = ast.get_options()[0]
        self.assertTrue(option.instanceof("CYPHER_AST_STATEMENT_OPTION"))
        self.assertEqual(option.type, "CYPHER_AST_CYPHER_OPTION")

        version = option.get_version()
        self.assertEqual(version.type, "CYPHER_AST_STRING")
        self.assertEqual(version.get_value(), "3.0")

        self.assertEqual(len(option.get_params()), 0)

    def test_parse_statement_with_cypher_option_containing_params(self):
        result = pycypher.parse_query("CYPHER runtime=fast RETURN 1;")

        expected_ast_dump = [
            "@0   0..29  statement             options=[@1], body=@5\n",
            "@1   0..19  > CYPHER              params=[@2]\n",
            "@2   7..19  > > cypher parameter  @3 = @4\n",
            "@3   7..14  > > > string          \"runtime\"\n",
            "@4  15..19  > > > string          \"fast\"\n",
            "@5  20..29  > query               clauses=[@6]\n",
            "@6  20..28  > > RETURN            projections=[@7]\n",
            "@7  27..28  > > > projection      expression=@8, alias=@9\n",
            "@8  27..28  > > > > integer       1\n",
            "@9  27..28  > > > > identifier    `1`\n",
        ]
        assert_ast_matches_ast_dump(result, expected_ast_dump)

        self.assertEqual(len(result), 1)
        ast = result[0]
        self.assertEqual(ast.type, "CYPHER_AST_STATEMENT")

        self.assertEqual(len(ast.get_options()), 1)
        option = ast.get_options()[0]
        self.assertTrue(option.instanceof("CYPHER_AST_STATEMENT_OPTION"))
        self.assertEqual(option.type, "CYPHER_AST_CYPHER_OPTION")

        self.assertIsNone(option.get_version())

        self.assertEqual(len(option.get_params()), 1)
        param = option.get_params()[0]
        self.assertEqual(param.type, "CYPHER_AST_CYPHER_OPTION_PARAM")

        name = param.get_name()
        self.assertEqual(name.type, "CYPHER_AST_STRING")
        value = param.get_value()
        self.assertEqual(value.type, "CYPHER_AST_STRING")

        self.assertEqual(name.get_value(), "runtime")
        self.assertEqual(value.get_value(), "fast")

    def test_parse_statement_with_cypher_option_containing_version_and_params(self):
        result = pycypher.parse_query("CYPHER 2.3 runtime=fast planner=slow RETURN 1;")

        expected_ast_dump = [
            " @0   0..46  statement             options=[@1], body=@9\n",
            " @1   0..36  > CYPHER              version=@2, params=[@3, @6]\n",
            " @2   7..10  > > string            \"2.3\"\n",
            " @3  11..23  > > cypher parameter  @4 = @5\n",
            " @4  11..18  > > > string          \"runtime\"\n",
            " @5  19..23  > > > string          \"fast\"\n",
            " @6  24..36  > > cypher parameter  @7 = @8\n",
            " @7  24..31  > > > string          \"planner\"\n",
            " @8  32..36  > > > string          \"slow\"\n",
            " @9  37..46  > query               clauses=[@10]\n",
            "@10  37..45  > > RETURN            projections=[@11]\n",
            "@11  44..45  > > > projection      expression=@12, alias=@13\n",
            "@12  44..45  > > > > integer       1\n",
            "@13  44..45  > > > > identifier    `1`\n",
        ]
        assert_ast_matches_ast_dump(result, expected_ast_dump)

        self.assertEqual(len(result), 1)
        ast = result[0]
        self.assertEqual(ast.type, "CYPHER_AST_STATEMENT")

        self.assertEqual(len(ast.get_options()), 1)
        option = ast.get_options()[0]
        self.assertTrue(option.instanceof("CYPHER_AST_STATEMENT_OPTION"))
        self.assertEqual(option.type, "CYPHER_AST_CYPHER_OPTION")

        version = option.get_version()
        self.assertEqual(version.type, "CYPHER_AST_STRING")
        self.assertEqual(version.get_value(), "2.3")

        self.assertEqual(len(option.get_params()), 2)

        param = option.get_params()[0]
        self.assertEqual(param.type, "CYPHER_AST_CYPHER_OPTION_PARAM")

        name = param.get_name()
        self.assertEqual(name.type, "CYPHER_AST_STRING")
        value = param.get_value()
        self.assertEqual(value.type, "CYPHER_AST_STRING")

        self.assertEqual(name.get_value(), "runtime")
        self.assertEqual(value.get_value(), "fast")

        param = option.get_params()[1]
        self.assertEqual(param.type, "CYPHER_AST_CYPHER_OPTION_PARAM")

        name = param.get_name()
        self.assertEqual(name.type, "CYPHER_AST_STRING")
        value = param.get_value()
        self.assertEqual(value.type, "CYPHER_AST_STRING")

        self.assertEqual(name.get_value(), "planner")
        self.assertEqual(value.get_value(), "slow")

    def test_parse_statement_with_explain_option(self):
        result = pycypher.parse_query("EXPLAIN RETURN 1;")

        expected_ast_dump = [
            "@0   0..17  statement           options=[@1], body=@2\n",
            "@1   0..7   > EXPLAIN\n",
            "@2   8..17  > query             clauses=[@3]\n",
            "@3   8..16  > > RETURN          projections=[@4]\n",
            "@4  15..16  > > > projection    expression=@5, alias=@6\n",
            "@5  15..16  > > > > integer     1\n",
            "@6  15..16  > > > > identifier  `1`\n",
        ]
        assert_ast_matches_ast_dump(result, expected_ast_dump)

        self.assertEqual(len(result), 1)
        ast = result[0]
        self.assertEqual(ast.type, "CYPHER_AST_STATEMENT")

        self.assertEqual(len(ast.get_options()), 1)
        option = ast.get_options()[0]
        self.assertTrue(option.instanceof("CYPHER_AST_STATEMENT_OPTION"))
        self.assertEqual(option.type, "CYPHER_AST_EXPLAIN_OPTION")

    def test_parse_statement_with_profile_option(self):
        result = pycypher.parse_query("PROFILE RETURN 1;")

        expected_ast_dump = [
            "@0   0..17  statement           options=[@1], body=@2\n",
            "@1   0..7   > PROFILE\n",
            "@2   8..17  > query             clauses=[@3]\n",
            "@3   8..16  > > RETURN          projections=[@4]\n",
            "@4  15..16  > > > projection    expression=@5, alias=@6\n",
            "@5  15..16  > > > > integer     1\n",
            "@6  15..16  > > > > identifier  `1`\n",
        ]
        assert_ast_matches_ast_dump(result, expected_ast_dump)

        self.assertEqual(len(result), 1)
        ast = result[0]
        self.assertEqual(ast.type, "CYPHER_AST_STATEMENT")

        self.assertEqual(len(ast.get_options()), 1)
        option = ast.get_options()[0]
        self.assertTrue(option.instanceof("CYPHER_AST_STATEMENT_OPTION"))
        self.assertEqual(option.type, "CYPHER_AST_PROFILE_OPTION")

    def test_parse_statement_with_multiple_options(self):
        result = pycypher.parse_query("CYPHER 3.0 PROFILE RETURN 1;")

        expected_ast_dump = [
            "@0   0..28  statement           options=[@1, @3], body=@4\n",
            "@1   0..10  > CYPHER            version=@2\n",
            "@2   7..10  > > string          \"3.0\"\n",
            "@3  11..18  > PROFILE\n",
            "@4  19..28  > query             clauses=[@5]\n",
            "@5  19..27  > > RETURN          projections=[@6]\n",
            "@6  26..27  > > > projection    expression=@7, alias=@8\n",
            "@7  26..27  > > > > integer     1\n",
            "@8  26..27  > > > > identifier  `1`\n",
        ]
        assert_ast_matches_ast_dump(result, expected_ast_dump)

        self.assertEqual(len(result), 1)
        ast = result[0]
        self.assertEqual(ast.type, "CYPHER_AST_STATEMENT")

        self.assertEqual(len(ast.get_options()), 2)
        option = ast.get_options()[0]
        self.assertTrue(option.instanceof("CYPHER_AST_STATEMENT_OPTION"))
        self.assertEqual(option.type, "CYPHER_AST_CYPHER_OPTION")

        option = ast.get_options()[1]
        self.assertTrue(option.instanceof("CYPHER_AST_STATEMENT_OPTION"))
        self.assertEqual(option.type, "CYPHER_AST_PROFILE_OPTION")

