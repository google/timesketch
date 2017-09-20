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


class TestPattern(unittest.TestCase):
    def test_parse_single_node(self):
        result = pycypher.parse_query("MATCH (n) RETURN n;")
        self.assertEqual(result[-1].end, 19)

        expected_ast_dump = [
            "@0   0..19  statement               body=@1\n",
            "@1   0..19  > query                 clauses=[@2, @7]\n",
            "@2   0..10  > > MATCH               pattern=@3\n",
            "@3   6..9   > > > pattern           paths=[@4]\n",
            "@4   6..9   > > > > pattern path    (@5)\n",
            "@5   6..9   > > > > > node pattern  (@6)\n",
            "@6   7..8   > > > > > > identifier  `n`\n",
            "@7  10..18  > > RETURN              projections=[@8]\n",
            "@8  17..18  > > > projection        expression=@9\n",
            "@9  17..18  > > > > identifier      `n`\n",
        ]
        assert_ast_matches_ast_dump(result, expected_ast_dump)

        ast = result[0]
        query = ast.get_body()
        match = query.get_clauses()[0]

        pattern = match.get_pattern()
        self.assertEqual(pattern.type, "CYPHER_AST_PATTERN")

        self.assertEqual(len(pattern.get_paths()), 1)
        path = pattern.get_paths()[0]
        self.assertEqual(path.type, "CYPHER_AST_PATTERN_PATH")

        self.assertEqual(len(path.get_elements()), 1)
        node = path.get_elements()[0]
        self.assertEqual(node.type, "CYPHER_AST_NODE_PATTERN")

        id = node.get_identifier()
        self.assertEqual(id.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(id.get_name(), "n")

        self.assertEqual(len(node.get_labels()), 0)
        self.assertIsNone(node.get_properties())

    def test_parse_labeled_node(self):
        result = pycypher.parse_query("MATCH (n:Foo) RETURN n;")
        self.assertEqual(result[-1].end, 23)

        expected_ast_dump = [
            " @0   0..23  statement               body=@1\n",
            " @1   0..23  > query                 clauses=[@2, @8]\n",
            " @2   0..14  > > MATCH               pattern=@3\n",
            " @3   6..13  > > > pattern           paths=[@4]\n",
            " @4   6..13  > > > > pattern path    (@5)\n",
            " @5   6..13  > > > > > node pattern  (@6:@7)\n",
            " @6   7..8   > > > > > > identifier  `n`\n",
            " @7   8..12  > > > > > > label       :`Foo`\n",
            " @8  14..22  > > RETURN              projections=[@9]\n",
            " @9  21..22  > > > projection        expression=@10\n",
            "@10  21..22  > > > > identifier      `n`\n",
        ]
        assert_ast_matches_ast_dump(result, expected_ast_dump)

        ast = result[0]
        query = ast.get_body()
        match = query.get_clauses()[0]

        pattern = match.get_pattern()
        self.assertEqual(pattern.type, "CYPHER_AST_PATTERN")

        self.assertEqual(len(pattern.get_paths()), 1)
        path = pattern.get_paths()[0]
        self.assertEqual(path.type, "CYPHER_AST_PATTERN_PATH")

        self.assertEqual(len(path.get_elements()), 1)
        node = path.get_elements()[0]
        self.assertEqual(node.type, "CYPHER_AST_NODE_PATTERN")

        id = node.get_identifier()
        self.assertEqual(id.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(id.get_name(), "n")

        self.assertEqual(len(node.get_labels()), 1)
        label = node.get_labels()[0]
        self.assertEqual(label.type, "CYPHER_AST_LABEL")
        self.assertEqual(label.get_name(), "Foo")

        self.assertIsNone(node.get_properties())

    def test_parse_multiple_labeled_node(self):
        result = pycypher.parse_query("MATCH (n:Foo:Bar) RETURN n;")
        self.assertEqual(result[-1].end, 27)

        expected_ast_dump = [
            " @0   0..27  statement               body=@1\n",
            " @1   0..27  > query                 clauses=[@2, @9]\n",
            " @2   0..18  > > MATCH               pattern=@3\n",
            " @3   6..17  > > > pattern           paths=[@4]\n",
            " @4   6..17  > > > > pattern path    (@5)\n",
            " @5   6..17  > > > > > node pattern  (@6:@7:@8)\n",
            " @6   7..8   > > > > > > identifier  `n`\n",
            " @7   8..12  > > > > > > label       :`Foo`\n",
            " @8  12..16  > > > > > > label       :`Bar`\n",
            " @9  18..26  > > RETURN              projections=[@10]\n",
            "@10  25..26  > > > projection        expression=@11\n",
            "@11  25..26  > > > > identifier      `n`\n",
        ]
        assert_ast_matches_ast_dump(result, expected_ast_dump)

        ast = result[0]
        query = ast.get_body()
        match = query.get_clauses()[0]

        pattern = match.get_pattern()
        self.assertEqual(pattern.type, "CYPHER_AST_PATTERN")

        self.assertEqual(len(pattern.get_paths()), 1)
        path = pattern.get_paths()[0]
        self.assertEqual(path.type, "CYPHER_AST_PATTERN_PATH")

        self.assertEqual(len(path.get_elements()), 1)
        node = path.get_elements()[0]
        self.assertEqual(node.type, "CYPHER_AST_NODE_PATTERN")

        id = node.get_identifier()
        self.assertEqual(id.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(id.get_name(), "n")

        self.assertEqual(len(node.get_labels()), 2)
        label = node.get_labels()[0]
        self.assertEqual(label.type, "CYPHER_AST_LABEL")
        self.assertEqual(label.get_name(), "Foo")
        label = node.get_labels()[1]
        self.assertEqual(label.type, "CYPHER_AST_LABEL")
        self.assertEqual(label.get_name(), "Bar")

        self.assertIsNone(node.get_properties())

    def test_parse_node_with_map_props(self):
        result = pycypher.parse_query("MATCH (n:Person {name: 'Hunter'}) RETURN n;")
        self.assertEqual(result[-1].end, 43)

        expected_ast_dump = [
            " @0   0..43  statement                body=@1\n",
            " @1   0..43  > query                  clauses=[@2, @11]\n",
            " @2   0..34  > > MATCH                pattern=@3\n",
            " @3   6..33  > > > pattern            paths=[@4]\n",
            " @4   6..33  > > > > pattern path     (@5)\n",
            " @5   6..33  > > > > > node pattern   (@6:@7 {@8})\n",
            " @6   7..8   > > > > > > identifier   `n`\n",
            " @7   8..15  > > > > > > label        :`Person`\n",
            " @8  16..32  > > > > > > map          {@9:@10}\n",
            " @9  17..21  > > > > > > > prop name  `name`\n",
            "@10  23..31  > > > > > > > string     \"Hunter\"\n",
            "@11  34..42  > > RETURN               projections=[@12]\n",
            "@12  41..42  > > > projection         expression=@13\n",
            "@13  41..42  > > > > identifier       `n`\n",
        ]
        assert_ast_matches_ast_dump(result, expected_ast_dump)

        ast = result[0]
        query = ast.get_body()
        match = query.get_clauses()[0]

        pattern = match.get_pattern()
        self.assertEqual(pattern.type, "CYPHER_AST_PATTERN")

        self.assertEqual(len(pattern.get_paths()), 1)
        path = pattern.get_paths()[0]
        self.assertEqual(path.type, "CYPHER_AST_PATTERN_PATH")

        self.assertEqual(len(path.get_elements()), 1)
        node = path.get_elements()[0]
        self.assertEqual(node.type, "CYPHER_AST_NODE_PATTERN")

        id = node.get_identifier()
        self.assertEqual(id.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(id.get_name(), "n")

        self.assertEqual(len(node.get_labels()), 1)
        label = node.get_labels()[0]
        self.assertEqual(label.type, "CYPHER_AST_LABEL")
        self.assertEqual(label.get_name(), "Person")

        props = node.get_properties()
        self.assertEqual(props.type, "CYPHER_AST_MAP")

        self.assertEqual(len(props.get_keys()), 1)
        key = props.get_keys()[0]
        self.assertEqual(key.type, "CYPHER_AST_PROP_NAME")
        self.assertEqual(key.get_value(), "name")
        value = props.get_values()[0]
        self.assertEqual(value.type, "CYPHER_AST_STRING")
        self.assertEqual(value.get_value(), "Hunter")

    def test_parse_node_with_param_props(self):
        result = pycypher.parse_query("MATCH (n:Person {param}) RETURN n;")
        self.assertEqual(result[-1].end, 34)

        expected_ast_dump = [
            " @0   0..34  statement               body=@1\n",
            " @1   0..34  > query                 clauses=[@2, @9]\n",
            " @2   0..25  > > MATCH               pattern=@3\n",
            " @3   6..24  > > > pattern           paths=[@4]\n",
            " @4   6..24  > > > > pattern path    (@5)\n",
            " @5   6..24  > > > > > node pattern  (@6:@7 {@8})\n",
            " @6   7..8   > > > > > > identifier  `n`\n",
            " @7   8..15  > > > > > > label       :`Person`\n",
            " @8  16..23  > > > > > > parameter   $`param`\n",
            " @9  25..33  > > RETURN              projections=[@10]\n",
            "@10  32..33  > > > projection        expression=@11\n",
            "@11  32..33  > > > > identifier      `n`\n",
        ]
        assert_ast_matches_ast_dump(result, expected_ast_dump)

        ast = result[0]
        query = ast.get_body()
        match = query.get_clauses()[0]

        pattern = match.get_pattern()
        self.assertEqual(pattern.type, "CYPHER_AST_PATTERN")

        self.assertEqual(len(pattern.get_paths()), 1)
        path = pattern.get_paths()[0]
        self.assertEqual(path.type, "CYPHER_AST_PATTERN_PATH")

        self.assertEqual(len(path.get_elements()), 1)
        node = path.get_elements()[0]
        self.assertEqual(node.type, "CYPHER_AST_NODE_PATTERN")

        id = node.get_identifier()
        self.assertEqual(id.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(id.get_name(), "n")

        self.assertEqual(len(node.get_labels()), 1)
        label = node.get_labels()[0]
        self.assertEqual(label.type, "CYPHER_AST_LABEL")
        self.assertEqual(label.get_name(), "Person")

        props = node.get_properties()
        self.assertEqual(props.type, "CYPHER_AST_PARAMETER")
        self.assertEqual(props.get_name(), "param")

    def test_parse_single_rel(self):
        result = pycypher.parse_query("MATCH (n)-[:Foo]->(m) RETURN n;")
        self.assertEqual(result[-1].end, 31)

        expected_ast_dump = [
            " @0   0..31  statement               body=@1\n",
            " @1   0..31  > query                 clauses=[@2, @11]\n",
            " @2   0..22  > > MATCH               pattern=@3\n",
            " @3   6..21  > > > pattern           paths=[@4]\n",
            " @4   6..21  > > > > pattern path    (@5)-[@7]-(@9)\n",
            " @5   6..9   > > > > > node pattern  (@6)\n",
            " @6   7..8   > > > > > > identifier  `n`\n",
            " @7   9..18  > > > > > rel pattern   -[:@8]->\n",
            " @8  11..15  > > > > > > rel type    :`Foo`\n",
            " @9  18..21  > > > > > node pattern  (@10)\n",
            "@10  19..20  > > > > > > identifier  `m`\n",
            "@11  22..30  > > RETURN              projections=[@12]\n",
            "@12  29..30  > > > projection        expression=@13\n",
            "@13  29..30  > > > > identifier      `n`\n",
        ]
        assert_ast_matches_ast_dump(result, expected_ast_dump)

        ast = result[0]
        query = ast.get_body()
        match = query.get_clauses()[0]

        pattern = match.get_pattern()
        self.assertEqual(pattern.type, "CYPHER_AST_PATTERN")

        self.assertEqual(len(pattern.get_paths()), 1)
        path = pattern.get_paths()[0]
        self.assertEqual(path.type, "CYPHER_AST_PATTERN_PATH")

        self.assertEqual(len(path.get_elements()), 3)
        node = path.get_elements()[0]
        self.assertEqual(node.type, "CYPHER_AST_NODE_PATTERN")

        id = node.get_identifier()
        self.assertEqual(id.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(id.get_name(), "n")

        self.assertEqual(len(node.get_labels()), 0)
        self.assertIsNone(node.get_properties())

        rel = path.get_elements()[1]
        self.assertEqual(rel.type, "CYPHER_AST_REL_PATTERN")

        self.assertEqual(rel.get_direction(), "CYPHER_REL_OUTBOUND")

        self.assertIsNone(rel.get_identifier())

        self.assertEqual(len(rel.get_reltypes()), 1)
        reltype = rel.get_reltypes()[0]
        self.assertEqual(reltype.type, "CYPHER_AST_RELTYPE")
        self.assertEqual(reltype.get_name(), "Foo")

        self.assertIsNone(rel.get_varlength())

        node = path.get_elements()[2]
        self.assertEqual(node.type, "CYPHER_AST_NODE_PATTERN")

    def test_parse_varlength_rel(self):
        result = pycypher.parse_query("MATCH (n)-[r:Foo*]-(m) RETURN n;")
        self.assertEqual(result[-1].end, 32)

        expected_ast_dump = [
            " @0   0..32  statement               body=@1\n",
            " @1   0..32  > query                 clauses=[@2, @13]\n",
            " @2   0..23  > > MATCH               pattern=@3\n",
            " @3   6..22  > > > pattern           paths=[@4]\n",
            " @4   6..22  > > > > pattern path    (@5)-[@7]-(@11)\n",
            " @5   6..9   > > > > > node pattern  (@6)\n",
            " @6   7..8   > > > > > > identifier  `n`\n",
            " @7   9..19  > > > > > rel pattern   -[@8:@9*@10]-\n",
            " @8  11..12  > > > > > > identifier  `r`\n",
            " @9  12..16  > > > > > > rel type    :`Foo`\n",
            "@10  17..17  > > > > > > range       *\n",
            "@11  19..22  > > > > > node pattern  (@12)\n",
            "@12  20..21  > > > > > > identifier  `m`\n",
            "@13  23..31  > > RETURN              projections=[@14]\n",
            "@14  30..31  > > > projection        expression=@15\n",
            "@15  30..31  > > > > identifier      `n`\n",
        ]
        assert_ast_matches_ast_dump(result, expected_ast_dump)

        ast = result[0]
        query = ast.get_body()
        match = query.get_clauses()[0]

        pattern = match.get_pattern()
        self.assertEqual(pattern.type, "CYPHER_AST_PATTERN")

        self.assertEqual(len(pattern.get_paths()), 1)
        path = pattern.get_paths()[0]
        self.assertEqual(path.type, "CYPHER_AST_PATTERN_PATH")

        self.assertEqual(len(path.get_elements()), 3)
        node = path.get_elements()[0]
        self.assertEqual(node.type, "CYPHER_AST_NODE_PATTERN")

        id = node.get_identifier()
        self.assertEqual(id.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(id.get_name(), "n")

        self.assertEqual(len(node.get_labels()), 0)
        self.assertIsNone(node.get_properties())

        rel = path.get_elements()[1]
        self.assertEqual(rel.type, "CYPHER_AST_REL_PATTERN")

        self.assertEqual(rel.get_direction(), "CYPHER_REL_BIDIRECTIONAL")

        id = rel.get_identifier()
        self.assertEqual(id.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(id.get_name(), "r")

        self.assertEqual(len(rel.get_reltypes()), 1)
        reltype = rel.get_reltypes()[0]
        self.assertEqual(reltype.type, "CYPHER_AST_RELTYPE")
        self.assertEqual(reltype.get_name(), "Foo")

        range = rel.get_varlength()
        self.assertEqual(range.type, "CYPHER_AST_RANGE")
        self.assertIsNone(range.get_start())
        self.assertIsNone(range.get_end())

        node = path.get_elements()[2]
        self.assertEqual(node.type, "CYPHER_AST_NODE_PATTERN")

    def test_parse_varlength_rel_with_bounded_start(self):
        result = pycypher.parse_query("MATCH (n)<-[r:Foo*5..]-(m) RETURN n;")
        self.assertEqual(result[-1].end, 36)

        expected_ast_dump = [
            " @0   0..36  statement               body=@1\n",
            " @1   0..36  > query                 clauses=[@2, @14]\n",
            " @2   0..27  > > MATCH               pattern=@3\n",
            " @3   6..26  > > > pattern           paths=[@4]\n",
            " @4   6..26  > > > > pattern path    (@5)-[@7]-(@12)\n",
            " @5   6..9   > > > > > node pattern  (@6)\n",
            " @6   7..8   > > > > > > identifier  `n`\n",
            " @7   9..23  > > > > > rel pattern   <-[@8:@9*@10]-\n",
            " @8  12..13  > > > > > > identifier  `r`\n",
            " @9  13..17  > > > > > > rel type    :`Foo`\n",
            "@10  17..21  > > > > > > range       *@11..\n",
            "@11  18..19  > > > > > > > integer   5\n",
            "@12  23..26  > > > > > node pattern  (@13)\n",
            "@13  24..25  > > > > > > identifier  `m`\n",
            "@14  27..35  > > RETURN              projections=[@15]\n",
            "@15  34..35  > > > projection        expression=@16\n",
            "@16  34..35  > > > > identifier      `n`\n",
        ]
        assert_ast_matches_ast_dump(result, expected_ast_dump)

        ast = result[0]
        query = ast.get_body()
        match = query.get_clauses()[0]

        pattern = match.get_pattern()
        self.assertEqual(pattern.type, "CYPHER_AST_PATTERN")

        self.assertEqual(len(pattern.get_paths()), 1)
        path = pattern.get_paths()[0]
        self.assertEqual(path.type, "CYPHER_AST_PATTERN_PATH")

        self.assertEqual(len(path.get_elements()), 3)
        node = path.get_elements()[0]
        self.assertEqual(node.type, "CYPHER_AST_NODE_PATTERN")

        id = node.get_identifier()
        self.assertEqual(id.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(id.get_name(), "n")

        self.assertEqual(len(node.get_labels()), 0)
        self.assertIsNone(node.get_properties())

        rel = path.get_elements()[1]
        self.assertEqual(rel.type, "CYPHER_AST_REL_PATTERN")

        self.assertEqual(rel.get_direction(), "CYPHER_REL_INBOUND")

        id = rel.get_identifier()
        self.assertEqual(id.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(id.get_name(), "r")

        self.assertEqual(len(rel.get_reltypes()), 1)
        reltype = rel.get_reltypes()[0]
        self.assertEqual(reltype.type, "CYPHER_AST_RELTYPE")
        self.assertEqual(reltype.get_name(), "Foo")

        range = rel.get_varlength()
        self.assertEqual(range.type, "CYPHER_AST_RANGE")
        start = range.get_start()
        self.assertEqual(start.type, "CYPHER_AST_INTEGER")
        self.assertEqual(start.get_valuestr(), "5")
        self.assertIsNone(range.get_end())

        node = path.get_elements()[2]
        self.assertEqual(node.type, "CYPHER_AST_NODE_PATTERN")

    def test_parse_varlength_rel_with_bounded_end(self):
        result = pycypher.parse_query("MATCH (n)<-[r:Foo*..9]->(m) RETURN n;")
        self.assertEqual(result[-1].end, 37)

        expected_ast_dump = [
            " @0   0..37  statement               body=@1\n",
            " @1   0..37  > query                 clauses=[@2, @14]\n",
            " @2   0..28  > > MATCH               pattern=@3\n",
            " @3   6..27  > > > pattern           paths=[@4]\n",
            " @4   6..27  > > > > pattern path    (@5)-[@7]-(@12)\n",
            " @5   6..9   > > > > > node pattern  (@6)\n",
            " @6   7..8   > > > > > > identifier  `n`\n",
            " @7   9..24  > > > > > rel pattern   -[@8:@9*@10]-\n",
            " @8  12..13  > > > > > > identifier  `r`\n",
            " @9  13..17  > > > > > > rel type    :`Foo`\n",
            "@10  17..21  > > > > > > range       *..@11\n",
            "@11  20..21  > > > > > > > integer   9\n",
            "@12  24..27  > > > > > node pattern  (@13)\n",
            "@13  25..26  > > > > > > identifier  `m`\n",
            "@14  28..36  > > RETURN              projections=[@15]\n",
            "@15  35..36  > > > projection        expression=@16\n",
            "@16  35..36  > > > > identifier      `n`\n",
        ]
        assert_ast_matches_ast_dump(result, expected_ast_dump)

        ast = result[0]
        query = ast.get_body()
        match = query.get_clauses()[0]

        pattern = match.get_pattern()
        self.assertEqual(pattern.type, "CYPHER_AST_PATTERN")

        self.assertEqual(len(pattern.get_paths()), 1)
        path = pattern.get_paths()[0]
        self.assertEqual(path.type, "CYPHER_AST_PATTERN_PATH")

        self.assertEqual(len(path.get_elements()), 3)
        node = path.get_elements()[0]
        self.assertEqual(node.type, "CYPHER_AST_NODE_PATTERN")

        id = node.get_identifier()
        self.assertEqual(id.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(id.get_name(), "n")

        self.assertEqual(len(node.get_labels()), 0)
        self.assertIsNone(node.get_properties())

        rel = path.get_elements()[1]
        self.assertEqual(rel.type, "CYPHER_AST_REL_PATTERN")

        self.assertEqual(rel.get_direction(), "CYPHER_REL_BIDIRECTIONAL")

        id = rel.get_identifier()
        self.assertEqual(id.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(id.get_name(), "r")

        self.assertEqual(len(rel.get_reltypes()), 1)
        reltype = rel.get_reltypes()[0]
        self.assertEqual(reltype.type, "CYPHER_AST_RELTYPE")
        self.assertEqual(reltype.get_name(), "Foo")

        range = rel.get_varlength()
        self.assertIsNone(range.get_start())
        self.assertEqual(range.type, "CYPHER_AST_RANGE")
        end = range.get_end()
        self.assertEqual(end.type, "CYPHER_AST_INTEGER")
        self.assertEqual(end.get_valuestr(), "9")

        node = path.get_elements()[2]
        self.assertEqual(node.type, "CYPHER_AST_NODE_PATTERN")

    def test_parse_varlength_rel_with_fixed_range(self):
        result = pycypher.parse_query("MATCH (n)<-[r:Foo*7]->(m) RETURN n;")
        self.assertEqual(result[-1].end, 35)

        expected_ast_dump = [
            " @0   0..35  statement               body=@1\n",
            " @1   0..35  > query                 clauses=[@2, @14]\n",
            " @2   0..26  > > MATCH               pattern=@3\n",
            " @3   6..25  > > > pattern           paths=[@4]\n",
            " @4   6..25  > > > > pattern path    (@5)-[@7]-(@12)\n",
            " @5   6..9   > > > > > node pattern  (@6)\n",
            " @6   7..8   > > > > > > identifier  `n`\n",
            " @7   9..22  > > > > > rel pattern   -[@8:@9*@10]-\n",
            " @8  12..13  > > > > > > identifier  `r`\n",
            " @9  13..17  > > > > > > rel type    :`Foo`\n",
            "@10  18..19  > > > > > > range       *@11..@11\n",
            "@11  18..19  > > > > > > > integer   7\n",
            "@12  22..25  > > > > > node pattern  (@13)\n",
            "@13  23..24  > > > > > > identifier  `m`\n",
            "@14  26..34  > > RETURN              projections=[@15]\n",
            "@15  33..34  > > > projection        expression=@16\n",
            "@16  33..34  > > > > identifier      `n`\n",
        ]
        assert_ast_matches_ast_dump(result, expected_ast_dump)

        ast = result[0]
        query = ast.get_body()
        match = query.get_clauses()[0]

        pattern = match.get_pattern()
        self.assertEqual(pattern.type, "CYPHER_AST_PATTERN")

        self.assertEqual(len(pattern.get_paths()), 1)
        path = pattern.get_paths()[0]
        self.assertEqual(path.type, "CYPHER_AST_PATTERN_PATH")

        self.assertEqual(len(path.get_elements()), 3)
        node = path.get_elements()[0]
        self.assertEqual(node.type, "CYPHER_AST_NODE_PATTERN")

        id = node.get_identifier()
        self.assertEqual(id.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(id.get_name(), "n")

        self.assertEqual(len(node.get_labels()), 0)
        self.assertIsNone(node.get_properties())

        rel = path.get_elements()[1]
        self.assertEqual(rel.type, "CYPHER_AST_REL_PATTERN")

        self.assertEqual(rel.get_direction(), "CYPHER_REL_BIDIRECTIONAL")

        id = rel.get_identifier()
        self.assertEqual(id.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(id.get_name(), "r")

        self.assertEqual(len(rel.get_reltypes()), 1)
        reltype = rel.get_reltypes()[0]
        self.assertEqual(reltype.type, "CYPHER_AST_RELTYPE")
        self.assertEqual(reltype.get_name(), "Foo")

        range = rel.get_varlength()
        self.assertEqual(range.type, "CYPHER_AST_RANGE")
        start = range.get_end()
        end = range.get_end()
        self.assertEqual(start.type, "CYPHER_AST_INTEGER")
        self.assertEqual(start.get_valuestr(), "7")
        self.assertIs(start, end)

        node = path.get_elements()[2]
        self.assertEqual(node.type, "CYPHER_AST_NODE_PATTERN")

    def test_parse_rel_with_map_props(self):
        result = pycypher.parse_query("RETURN (n)-[:Foo {start:1999, end:2000}]->(m) AS p;")
        self.assertEqual(result[-1].end, 51)

        expected_ast_dump = [
            " @0   0..51  statement                body=@1\n",
            " @1   0..51  > query                  clauses=[@2]\n",
            " @2   0..50  > > RETURN               projections=[@3]\n",
            " @3   7..50  > > > projection         expression=@4, alias=@16\n",
            " @4   7..45  > > > > pattern path     (@5)-[@7]-(@14)\n",
            " @5   7..10  > > > > > node pattern   (@6)\n",
            " @6   8..9   > > > > > > identifier   `n`\n",
            " @7  10..42  > > > > > rel pattern    -[:@8 {@9}]->\n",
            " @8  12..16  > > > > > > rel type     :`Foo`\n",
            " @9  17..39  > > > > > > map          {@10:@11, @12:@13}\n",
            "@10  18..23  > > > > > > > prop name  `start`\n",
            "@11  24..28  > > > > > > > integer    1999\n",
            "@12  30..33  > > > > > > > prop name  `end`\n",
            "@13  34..38  > > > > > > > integer    2000\n",
            "@14  42..45  > > > > > node pattern   (@15)\n",
            "@15  43..44  > > > > > > identifier   `m`\n",
            "@16  49..50  > > > > identifier       `p`\n",
        ]
        assert_ast_matches_ast_dump(result, expected_ast_dump)

        ast = result[0]
        query = ast.get_body()
        clause = query.get_clauses()[0]
        self.assertEqual(clause.type, "CYPHER_AST_RETURN")

        projection = clause.get_projections()[0]
        self.assertEqual(projection.type, "CYPHER_AST_PROJECTION")
        ppath = projection.get_expression()
        self.assertEqual(ppath.type, "CYPHER_AST_PATTERN_PATH")

        self.assertEqual(len(ppath.get_elements()), 3)
        node = ppath.get_elements()[0]
        self.assertEqual(node.type, "CYPHER_AST_NODE_PATTERN")

        id = node.get_identifier()
        self.assertEqual(id.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(id.get_name(), "n")

        self.assertEqual(len(node.get_labels()), 0)
        self.assertIsNone(node.get_properties())

        rel = ppath.get_elements()[1]
        self.assertEqual(rel.type, "CYPHER_AST_REL_PATTERN")

        self.assertEqual(rel.get_direction(), "CYPHER_REL_OUTBOUND")

        self.assertIsNone(rel.get_identifier())

        self.assertEqual(len(rel.get_reltypes()), 1)
        reltype = rel.get_reltypes()[0]
        self.assertEqual(reltype.type, "CYPHER_AST_RELTYPE")
        self.assertEqual(reltype.get_name(), "Foo")

        self.assertIsNone(rel.get_varlength())

        props = rel.get_properties()
        self.assertEqual(props.type, "CYPHER_AST_MAP")

        self.assertEqual(len(props.get_keys()), 2)

        key = props.get_keys()[0]
        self.assertEqual(key.type, "CYPHER_AST_PROP_NAME")
        self.assertEqual(key.get_value(), "start")
        value = props.get_values()[0]
        self.assertEqual(value.type, "CYPHER_AST_INTEGER")
        self.assertEqual(value.get_valuestr(), "1999")

        key = props.get_keys()[1]
        self.assertEqual(key.type, "CYPHER_AST_PROP_NAME")
        self.assertEqual(key.get_value(), "end")
        value = props.get_values()[1]
        self.assertEqual(value.type, "CYPHER_AST_INTEGER")
        self.assertEqual(value.get_valuestr(), "2000")

        node = ppath.get_elements()[2]
        self.assertEqual(node.type, "CYPHER_AST_NODE_PATTERN")

    def test_parse_rel_with_param_props(self):
        result = pycypher.parse_query("RETURN (n)-[:Foo {param}]->(m) AS p;")
        self.assertEqual(result[-1].end, 36)

        expected_ast_dump = [
            " @0   0..36  statement               body=@1\n",
            " @1   0..36  > query                 clauses=[@2]\n",
            " @2   0..35  > > RETURN              projections=[@3]\n",
            " @3   7..35  > > > projection        expression=@4, alias=@12\n",
            " @4   7..30  > > > > pattern path    (@5)-[@7]-(@10)\n",
            " @5   7..10  > > > > > node pattern  (@6)\n",
            " @6   8..9   > > > > > > identifier  `n`\n",
            " @7  10..27  > > > > > rel pattern   -[:@8 {@9}]->\n",
            " @8  12..16  > > > > > > rel type    :`Foo`\n",
            " @9  17..24  > > > > > > parameter   $`param`\n",
            "@10  27..30  > > > > > node pattern  (@11)\n",
            "@11  28..29  > > > > > > identifier  `m`\n",
            "@12  34..35  > > > > identifier      `p`\n",
        ]
        assert_ast_matches_ast_dump(result, expected_ast_dump)

        ast = result[0]
        query = ast.get_body()
        clause = query.get_clauses()[0]
        self.assertEqual(clause.type, "CYPHER_AST_RETURN")

        projection = clause.get_projections()[0]
        self.assertEqual(projection.type, "CYPHER_AST_PROJECTION")
        ppath = projection.get_expression()
        self.assertEqual(ppath.type, "CYPHER_AST_PATTERN_PATH")

        self.assertEqual(len(ppath.get_elements()), 3)
        node = ppath.get_elements()[0]
        self.assertEqual(node.type, "CYPHER_AST_NODE_PATTERN")

        id = node.get_identifier()
        self.assertEqual(id.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(id.get_name(), "n")

        self.assertEqual(len(node.get_labels()), 0)
        self.assertIsNone(node.get_properties())

        rel = ppath.get_elements()[1]
        self.assertEqual(rel.type, "CYPHER_AST_REL_PATTERN")

        self.assertEqual(rel.get_direction(), "CYPHER_REL_OUTBOUND")

        self.assertIsNone(rel.get_identifier())

        self.assertEqual(len(rel.get_reltypes()), 1)
        reltype = rel.get_reltypes()[0]
        self.assertEqual(reltype.type, "CYPHER_AST_RELTYPE")
        self.assertEqual(reltype.get_name(), "Foo")

        self.assertIsNone(rel.get_varlength())

        param = rel.get_properties()
        self.assertEqual(param.type, "CYPHER_AST_PARAMETER")
        self.assertEqual(param.get_name(), "param")

        node = ppath.get_elements()[2]
        self.assertEqual(node.type, "CYPHER_AST_NODE_PATTERN")

    def test_parse_named_path(self):
        result = pycypher.parse_query("MATCH p = (n)-[:Foo]->(m) RETURN p;")
        self.assertEqual(result[-1].end, 35)

        expected_ast_dump = [
            " @0   0..35  statement                 body=@1\n",
            " @1   0..35  > query                   clauses=[@2, @13]\n",
            " @2   0..26  > > MATCH                 pattern=@3\n",
            " @3   6..25  > > > pattern             paths=[@4]\n",
            " @4   6..25  > > > > named path        @5 = @6\n",
            " @5   6..7   > > > > > identifier      `p`\n",
            " @6  10..25  > > > > > pattern path    (@7)-[@9]-(@11)\n",
            " @7  10..13  > > > > > > node pattern  (@8)\n",
            " @8  11..12  > > > > > > > identifier  `n`\n",
            " @9  13..22  > > > > > > rel pattern   -[:@10]->\n",
            "@10  15..19  > > > > > > > rel type    :`Foo`\n",
            "@11  22..25  > > > > > > node pattern  (@12)\n",
            "@12  23..24  > > > > > > > identifier  `m`\n",
            "@13  26..34  > > RETURN                projections=[@14]\n",
            "@14  33..34  > > > projection          expression=@15\n",
            "@15  33..34  > > > > identifier        `p`\n",
        ]
        assert_ast_matches_ast_dump(result, expected_ast_dump)

        ast = result[0]
        query = ast.get_body()
        match = query.get_clauses()[0]

        pattern = match.get_pattern()
        self.assertEqual(pattern.type, "CYPHER_AST_PATTERN")

        self.assertEqual(len(pattern.get_paths()), 1)
        path = pattern.get_paths()[0]
        self.assertEqual(path.type, "CYPHER_AST_NAMED_PATH")

        id = path.get_identifier()
        self.assertEqual(id.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(id.get_name(), "p")

        self.assertEqual(len(path.get_elements()), 3)
        node = path.get_elements()[0]
        self.assertEqual(node.type, "CYPHER_AST_NODE_PATTERN")

        unnamed_path = path.get_path()
        self.assertEqual(unnamed_path.type, "CYPHER_AST_PATTERN_PATH")
        self.assertEqual(len(unnamed_path.get_elements()), 3)
        self.assertIs(unnamed_path.get_elements()[0], node)

        id = node.get_identifier()
        self.assertEqual(id.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(id.get_name(), "n")

        self.assertEqual(len(node.get_labels()), 0)
        self.assertIsNone(node.get_properties())

        rel = path.get_elements()[1]
        self.assertEqual(rel.type, "CYPHER_AST_REL_PATTERN")

        self.assertEqual(rel.get_direction(), "CYPHER_REL_OUTBOUND")

        self.assertIsNone(rel.get_identifier())

        self.assertEqual(len(rel.get_reltypes()), 1)
        reltype = rel.get_reltypes()[0]
        self.assertEqual(reltype.type, "CYPHER_AST_RELTYPE")
        self.assertEqual(reltype.get_name(), "Foo")

        self.assertIsNone(rel.get_varlength())

        node = path.get_elements()[2]
        self.assertEqual(node.type, "CYPHER_AST_NODE_PATTERN")

    def test_parse_shortest_path(self):
        result = pycypher.parse_query("MATCH p = shortestPath((n)-[:Foo]->(m)) RETURN n;")
        self.assertEqual(result[-1].end, 49)

        expected_ast_dump = [
            " @0   0..49  statement                   body=@1\n",
            " @1   0..49  > query                     clauses=[@2, @14]\n",
            " @2   0..40  > > MATCH                   pattern=@3\n",
            " @3   6..39  > > > pattern               paths=[@4]\n",
            " @4   6..39  > > > > named path          @5 = @6\n",
            " @5   6..7   > > > > > identifier        `p`\n",
            " @6  10..39  > > > > > shortestPath      single=true, path=@7\n",
            " @7  23..38  > > > > > > pattern path    (@8)-[@10]-(@12)\n",
            " @8  23..26  > > > > > > > node pattern  (@9)\n",
            " @9  24..25  > > > > > > > > identifier  `n`\n",
            "@10  26..35  > > > > > > > rel pattern   -[:@11]->\n",
            "@11  28..32  > > > > > > > > rel type    :`Foo`\n",
            "@12  35..38  > > > > > > > node pattern  (@13)\n",
            "@13  36..37  > > > > > > > > identifier  `m`\n",
            "@14  40..48  > > RETURN                  projections=[@15]\n",
            "@15  47..48  > > > projection            expression=@16\n",
            "@16  47..48  > > > > identifier          `n`\n",
        ]
        assert_ast_matches_ast_dump(result, expected_ast_dump)

        ast = result[0]
        query = ast.get_body()
        match = query.get_clauses()[0]

        pattern = match.get_pattern()
        self.assertEqual(pattern.type, "CYPHER_AST_PATTERN")

        self.assertEqual(len(pattern.get_paths()), 1)
        npath = pattern.get_paths()[0]
        self.assertEqual(npath.type, "CYPHER_AST_NAMED_PATH")

        id = npath.get_identifier()
        self.assertEqual(id.type, "CYPHER_AST_IDENTIFIER")
        self.assertEqual(id.get_name(), "p")

        self.assertEqual(len(npath.get_elements()), 3)
        node = npath.get_elements()[0]
        self.assertEqual(node.type, "CYPHER_AST_NODE_PATTERN")

        spath = npath.get_path()
        self.assertEqual(spath.type, "CYPHER_AST_SHORTEST_PATH")
        self.assertEqual(len(spath.get_elements()), 3)
        self.assertIs(spath.get_elements()[0], node)

        self.assertTrue(spath.is_single())

        unnamed_path = spath.get_path()
        self.assertEqual(unnamed_path.type, "CYPHER_AST_PATTERN_PATH")
        self.assertEqual(len(unnamed_path.get_elements()), 3)
        self.assertIs(unnamed_path.get_elements()[0], node)

    def test_parse_all_shortest_paths(self):
        result = pycypher.parse_query("RETURN allShortestPaths((n)-[:Foo]->(m)) AS p;")
        self.assertEqual(result[-1].end, 46)

        expected_ast_dump = [
            " @0   0..46  statement                 body=@1\n",
            " @1   0..46  > query                   clauses=[@2]\n",
            " @2   0..45  > > RETURN                projections=[@3]\n",
            " @3   7..45  > > > projection          expression=@4, alias=@12\n",
            " @4   7..40  > > > > shortestPath      single=false, path=@5\n",
            " @5  24..39  > > > > > pattern path    (@6)-[@8]-(@10)\n",
            " @6  24..27  > > > > > > node pattern  (@7)\n",
            " @7  25..26  > > > > > > > identifier  `n`\n",
            " @8  27..36  > > > > > > rel pattern   -[:@9]->\n",
            " @9  29..33  > > > > > > > rel type    :`Foo`\n",
            "@10  36..39  > > > > > > node pattern  (@11)\n",
            "@11  37..38  > > > > > > > identifier  `m`\n",
            "@12  44..45  > > > > identifier        `p`\n",
        ]
        assert_ast_matches_ast_dump(result, expected_ast_dump)

        ast = result[0]
        query = ast.get_body()
        clause = query.get_clauses()[0]
        self.assertEqual(clause.type, "CYPHER_AST_RETURN")

        projection = clause.get_projections()[0]
        self.assertEqual(projection.type, "CYPHER_AST_PROJECTION")
        spath = projection.get_expression()
        self.assertEqual(spath.type, "CYPHER_AST_SHORTEST_PATH")

        self.assertEqual(len(spath.get_elements()), 3)
        node = spath.get_elements()[0]
        self.assertEqual(node.type, "CYPHER_AST_NODE_PATTERN")

        self.assertFalse(spath.is_single())

        unnamed_path = spath.get_path()
        self.assertEqual(unnamed_path.type, "CYPHER_AST_PATTERN_PATH")
        self.assertEqual(len(unnamed_path.get_elements()), 3)
        self.assertIs(unnamed_path.get_elements()[0], node)
