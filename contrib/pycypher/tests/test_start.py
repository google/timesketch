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


class TestStart(unittest.TestCase):
    def test_parse_node_index_lookup(self):
        result = pycypher.parse_query("START n=node:index(foo = 'bar');")
        self.assertEqual(result[-1].end, 32)

        expected_ast_dump = [
            "@0   0..32  statement                body=@1\n",
            "@1   0..32  > query                  clauses=[@2]\n",
            "@2   0..31  > > START                points=[@3]\n",
            "@3   6..31  > > > node index lookup  @4 = node:@5(@6 = @7)\n",
            "@4   6..7   > > > > identifier       `n`\n",
            "@5  13..18  > > > > index name       `index`\n",
            "@6  19..22  > > > > prop name        `foo`\n",
            "@7  25..30  > > > > string           \"bar\"\n",
        ]
        assert_ast_matches_ast_dump(result, expected_ast_dump)

        ast = result[0]
        self.assertEqual(ast.type, "CYPHER_AST_STATEMENT")
        query = ast.get_body()
        self.assertEqual(query.type, "CYPHER_AST_QUERY")
        start = query.get_clauses()[0]
        self.assertEqual(start.type, "CYPHER_AST_START")

        self.assertIsNone(start.get_predicate())

        self.assertEqual(len(start.get_points()), 1)
        lookup = start.get_points()[0]
        self.assertEqual(lookup.type, "CYPHER_AST_NODE_INDEX_LOOKUP")

        id = lookup.get_identifier()
        self.assertEqual(id.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(id.get_name(), "n")

        index_name = lookup.get_index_name()
        self.assertEqual(index_name.type, "CYPHER_AST_INDEX_NAME")
        self.assertEqual(index_name.get_value(), "index")

        prop_name = lookup.get_prop_name()
        self.assertEqual(prop_name.type, "CYPHER_AST_PROP_NAME")
        self.assertEqual(prop_name.get_value(), "foo")

        str = lookup.get_lookup()
        self.assertEqual(str.type, "CYPHER_AST_STRING")
        self.assertEqual(str.get_value(), "bar")

    def test_parse_node_index_query(self):
        result = pycypher.parse_query("START n=node:index('bar');")
        self.assertEqual(result[-1].end, 26)

        expected_ast_dump = [
            "@0   0..26  statement               body=@1\n",
            "@1   0..26  > query                 clauses=[@2]\n",
            "@2   0..25  > > START               points=[@3]\n",
            "@3   6..25  > > > node index query  @4 = node:@5(@6)\n",
            "@4   6..7   > > > > identifier      `n`\n",
            "@5  13..18  > > > > index name      `index`\n",
            "@6  19..24  > > > > string          \"bar\"\n",
        ]
        assert_ast_matches_ast_dump(result, expected_ast_dump)

        ast = result[0]
        self.assertEqual(ast.type, "CYPHER_AST_STATEMENT")
        query = ast.get_body()
        self.assertEqual(query.type, "CYPHER_AST_QUERY")
        start = query.get_clauses()[0]
        self.assertEqual(start.type, "CYPHER_AST_START")

        self.assertIsNone(start.get_predicate())

        self.assertEqual(len(start.get_points()), 1)
        iquery = start.get_points()[0]
        self.assertEqual(iquery.type, "CYPHER_AST_NODE_INDEX_QUERY")

        id = iquery.get_identifier()
        self.assertEqual(id.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(id.get_name(), "n")

        index_name = iquery.get_index_name()
        self.assertEqual(index_name.type, "CYPHER_AST_INDEX_NAME")
        self.assertEqual(index_name.get_value(), "index")

        str = iquery.get_query()
        self.assertEqual(str.type, "CYPHER_AST_STRING")
        self.assertEqual(str.get_value(), "bar")

    def test_parse_node_id_lookup(self):
        result = pycypher.parse_query("START n=node(65, 78, 3, 0) // find nodes\nRETURN n;")
        self.assertEqual(result[-1].end, 50)

        expected_ast_dump = [
            " @0   0..50  statement             body=@1\n",
            " @1   0..50  > query               clauses=[@2, @10]\n",
            " @2   0..41  > > START             points=[@3]\n",
            " @3   6..26  > > > node id lookup  @4 = node(@5, @6, @7, @8)\n",
            " @4   6..7   > > > > identifier    `n`\n",
            " @5  13..15  > > > > integer       65\n",
            " @6  17..19  > > > > integer       78\n",
            " @7  21..22  > > > > integer       3\n",
            " @8  24..25  > > > > integer       0\n",
            " @9  29..40  > > > line_comment    // find nodes\n",
            "@10  41..49  > > RETURN            projections=[@11]\n",
            "@11  48..49  > > > projection      expression=@12\n",
            "@12  48..49  > > > > identifier    `n`\n",
        ]
        assert_ast_matches_ast_dump(result, expected_ast_dump)

        ast = result[0]
        self.assertEqual(ast.type, "CYPHER_AST_STATEMENT")
        query = ast.get_body()
        self.assertEqual(query.type, "CYPHER_AST_QUERY")
        start = query.get_clauses()[0]
        self.assertEqual(start.type, "CYPHER_AST_START")

        self.assertIsNone(start.get_predicate())

        self.assertEqual(len(start.get_points()), 1)
        lookup = start.get_points()[0]
        self.assertEqual(lookup.type, "CYPHER_AST_NODE_ID_LOOKUP")

        identifier = lookup.get_identifier()
        self.assertEqual(identifier.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(identifier.get_name(), "n")

        self.assertEqual(len(lookup.get_ids()), 4)
        id = lookup.get_ids()[0]
        self.assertEqual(id.type, "CYPHER_AST_INTEGER")
        self.assertEqual(id.get_valuestr(), "65")

        id = lookup.get_ids()[1]
        self.assertEqual(id.type, "CYPHER_AST_INTEGER")
        self.assertEqual(id.get_valuestr(), "78")

        id = lookup.get_ids()[2]
        self.assertEqual(id.type, "CYPHER_AST_INTEGER")
        self.assertEqual(id.get_valuestr(), "3")

        id = lookup.get_ids()[3]
        self.assertEqual(id.type, "CYPHER_AST_INTEGER")
        self.assertEqual(id.get_valuestr(), "0")


    def test_parse_all_nodes_scan(self):
        result = pycypher.parse_query("START n = node(*)\nRETURN /* all nodes */ n;")
        self.assertEqual(result[-1].end, 43)

        expected_ast_dump = [
            "@0   0..43  statement             body=@1\n",
            "@1   0..43  > query               clauses=[@2, @5]\n",
            "@2   0..18  > > START             points=[@3]\n",
            "@3   6..17  > > > all nodes scan  identifier=@4\n",
            "@4   6..7   > > > > identifier    `n`\n",
            "@5  18..42  > > RETURN            projections=[@7]\n",
            "@6  27..38  > > > block_comment   /* all nodes */\n",
            "@7  41..42  > > > projection      expression=@8\n",
            "@8  41..42  > > > > identifier    `n`\n",
        ]
        assert_ast_matches_ast_dump(result, expected_ast_dump)

        ast = result[0]
        self.assertEqual(ast.type, "CYPHER_AST_STATEMENT")
        query = ast.get_body()
        self.assertEqual(query.type, "CYPHER_AST_QUERY")
        start = query.get_clauses()[0]
        self.assertEqual(start.type, "CYPHER_AST_START")

        self.assertIsNone(start.get_predicate())

        self.assertEqual(len(start.get_points()), 1)
        scan = start.get_points()[0]
        self.assertEqual(scan.type, "CYPHER_AST_ALL_NODES_SCAN")

        identifier = scan.get_identifier()
        self.assertEqual(identifier.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(identifier.get_name(), "n")

    def test_parse_rel_index_lookup(self):
        result = pycypher.parse_query("START n=rel:index(foo = 'bar');")
        self.assertEqual(result[-1].end, 31)

        expected_ast_dump = [
            "@0   0..31  statement               body=@1\n",
            "@1   0..31  > query                 clauses=[@2]\n",
            "@2   0..30  > > START               points=[@3]\n",
            "@3   6..30  > > > rel index lookup  @4 = rel:@5(@6 = @7)\n",
            "@4   6..7   > > > > identifier      `n`\n",
            "@5  12..17  > > > > index name      `index`\n",
            "@6  18..21  > > > > prop name       `foo`\n",
            "@7  24..29  > > > > string          \"bar\"\n",
        ]
        assert_ast_matches_ast_dump(result, expected_ast_dump)

        ast = result[0]
        self.assertEqual(ast.type, "CYPHER_AST_STATEMENT")
        query = ast.get_body()
        self.assertEqual(query.type, "CYPHER_AST_QUERY")
        start = query.get_clauses()[0]
        self.assertEqual(start.type, "CYPHER_AST_START")

        self.assertIsNone(start.get_predicate())

        self.assertEqual(len(start.get_points()), 1)
        lookup = start.get_points()[0]
        self.assertEqual(lookup.type, "CYPHER_AST_REL_INDEX_LOOKUP")

        id = lookup.get_identifier()
        self.assertEqual(id.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(id.get_name(), "n")

        index_name = lookup.get_index_name()
        self.assertEqual(index_name.type, "CYPHER_AST_INDEX_NAME")
        self.assertEqual(index_name.get_value(), "index")

        prop_name = lookup.get_prop_name()
        self.assertEqual(prop_name.type, "CYPHER_AST_PROP_NAME")
        self.assertEqual(prop_name.get_value(), "foo")

        str = lookup.get_lookup()
        self.assertEqual(str.type, "CYPHER_AST_STRING")
        self.assertEqual(str.get_value(), "bar")

    def test_parse_rel_index_query(self):
        result = pycypher.parse_query("START n=rel:index('bar');")
        self.assertEqual(result[-1].end, 25)

        expected_ast_dump = [
            "@0   0..25  statement              body=@1\n",
            "@1   0..25  > query                clauses=[@2]\n",
            "@2   0..24  > > START              points=[@3]\n",
            "@3   6..24  > > > rel index query  @4 = rel:@5(@6)\n",
            "@4   6..7   > > > > identifier     `n`\n",
            "@5  12..17  > > > > index name     `index`\n",
            "@6  18..23  > > > > string         \"bar\"\n",
        ]
        assert_ast_matches_ast_dump(result, expected_ast_dump)

        ast = result[0]
        self.assertEqual(ast.type, "CYPHER_AST_STATEMENT")
        query = ast.get_body()
        self.assertEqual(query.type, "CYPHER_AST_QUERY")
        start = query.get_clauses()[0]
        self.assertEqual(start.type, "CYPHER_AST_START")

        self.assertIsNone(start.get_predicate())

        self.assertEqual(len(start.get_points()), 1)
        iquery = start.get_points()[0]
        self.assertEqual(iquery.type, "CYPHER_AST_REL_INDEX_QUERY")

        id = iquery.get_identifier()
        self.assertEqual(id.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(id.get_name(), "n")

        index_name = iquery.get_index_name()
        self.assertEqual(index_name.type, "CYPHER_AST_INDEX_NAME")
        self.assertEqual(index_name.get_value(), "index")

        str = iquery.get_query()
        self.assertEqual(str.type, "CYPHER_AST_STRING")
        self.assertEqual(str.get_value(), "bar")

    def test_parse_rel_id_lookup(self):
        result = pycypher.parse_query("START n=rel(65, 78, 3, 0) // find nodes\nRETURN n;")
        self.assertEqual(result[-1].end, 49)

        expected_ast_dump = [
            " @0   0..49  statement            body=@1\n",
            " @1   0..49  > query              clauses=[@2, @10]\n",
            " @2   0..40  > > START            points=[@3]\n",
            " @3   6..25  > > > rel id lookup  @4 = rel(@5, @6, @7, @8)\n",
            " @4   6..7   > > > > identifier   `n`\n",
            " @5  12..14  > > > > integer      65\n",
            " @6  16..18  > > > > integer      78\n",
            " @7  20..21  > > > > integer      3\n",
            " @8  23..24  > > > > integer      0\n",
            " @9  28..39  > > > line_comment   // find nodes\n",
            "@10  40..48  > > RETURN           projections=[@11]\n",
            "@11  47..48  > > > projection     expression=@12\n",
            "@12  47..48  > > > > identifier   `n`\n",
        ]
        assert_ast_matches_ast_dump(result, expected_ast_dump)

        ast = result[0]
        self.assertEqual(ast.type, "CYPHER_AST_STATEMENT")
        query = ast.get_body()
        self.assertEqual(query.type, "CYPHER_AST_QUERY")
        start = query.get_clauses()[0]
        self.assertEqual(start.type, "CYPHER_AST_START")

        self.assertIsNone(start.get_predicate())

        self.assertEqual(len(start.get_points()), 1)
        lookup = start.get_points()[0]
        self.assertEqual(lookup.type, "CYPHER_AST_REL_ID_LOOKUP")

        identifier = lookup.get_identifier()
        self.assertEqual(identifier.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(identifier.get_name(), "n")

        self.assertEqual(len(lookup.get_ids()), 4)
        id = lookup.get_ids()[0]
        self.assertEqual(id.type, "CYPHER_AST_INTEGER")
        self.assertEqual(id.get_valuestr(), "65")

        id = lookup.get_ids()[1]
        self.assertEqual(id.type, "CYPHER_AST_INTEGER")
        self.assertEqual(id.get_valuestr(), "78")

        id = lookup.get_ids()[2]
        self.assertEqual(id.type, "CYPHER_AST_INTEGER")
        self.assertEqual(id.get_valuestr(), "3")

        id = lookup.get_ids()[3]
        self.assertEqual(id.type, "CYPHER_AST_INTEGER")
        self.assertEqual(id.get_valuestr(), "0")


    def test_parse_all_rels_scan(self):
        result = pycypher.parse_query("START n = rel(*)\nRETURN /* all rels */ n;")
        self.assertEqual(result[-1].end, 41)

        expected_ast_dump = [
            "@0   0..41  statement            body=@1\n",
            "@1   0..41  > query              clauses=[@2, @5]\n",
            "@2   0..17  > > START            points=[@3]\n",
            "@3   6..16  > > > all rels scan  identifier=@4\n",
            "@4   6..7   > > > > identifier   `n`\n",
            "@5  17..40  > > RETURN           projections=[@7]\n",
            "@6  26..36  > > > block_comment  /* all rels */\n",
            "@7  39..40  > > > projection     expression=@8\n",
            "@8  39..40  > > > > identifier   `n`\n",
        ]
        assert_ast_matches_ast_dump(result, expected_ast_dump)

        ast = result[0]
        self.assertEqual(ast.type, "CYPHER_AST_STATEMENT")
        query = ast.get_body()
        self.assertEqual(query.type, "CYPHER_AST_QUERY")
        start = query.get_clauses()[0]
        self.assertEqual(start.type, "CYPHER_AST_START")

        self.assertIsNone(start.get_predicate())

        self.assertEqual(len(start.get_points()), 1)
        scan = start.get_points()[0]
        self.assertEqual(scan.type, "CYPHER_AST_ALL_RELS_SCAN")

        identifier = scan.get_identifier()
        self.assertEqual(identifier.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(identifier.get_name(), "n")

    def test_parse_start_with_predicate(self):
        result = pycypher.parse_query("START n = node(*) /* predicate */ WHERE n.foo > 1 RETURN n;")
        self.assertEqual(result[-1].end, 59)

        expected_ast_dump = [
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
        assert_ast_matches_ast_dump(result, expected_ast_dump)

        ast = result[0]
        self.assertEqual(ast.type, "CYPHER_AST_STATEMENT")
        query = ast.get_body()
        self.assertEqual(query.type, "CYPHER_AST_QUERY")
        start = query.get_clauses()[0]
        self.assertEqual(start.type, "CYPHER_AST_START")

        pred = start.get_predicate()
        self.assertTrue(pred.instanceof("CYPHER_AST_EXPRESSION"))
        self.assertEqual(pred.type, "CYPHER_AST_COMPARISON")

        self.assertEqual(len(pred.get_operators()), 1)

        o = pred.get_operators()[0]
        self.assertEqual(o, "CYPHER_OP_GT")

        l = pred.get_arguments()[0]
        self.assertEqual(l.type, "CYPHER_AST_PROPERTY_OPERATOR")

        r = pred.get_arguments()[1]
        self.assertEqual(r.type, "CYPHER_AST_INTEGER")
