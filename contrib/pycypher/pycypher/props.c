/* Copyright 2017, Google Inc. All rights reserved.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
#include "props.h"
#include "table_utils.h"

pycypher_direction_prop_t* pycypher_direction_props;
size_t pycypher_direction_props_len;
pycypher_operator_prop_t* pycypher_operator_props;
size_t pycypher_operator_props_len;
pycypher_operator_list_prop_t* pycypher_operator_list_props;
size_t pycypher_operator_list_props_len;
pycypher_bool_prop_t* pycypher_bool_props;
size_t pycypher_bool_props_len;
pycypher_string_prop_t* pycypher_string_props;
size_t pycypher_string_props_len;
pycypher_ast_list_prop_t* pycypher_ast_list_props;
size_t pycypher_ast_list_props_len;
pycypher_ast_prop_t* pycypher_ast_props;
size_t pycypher_ast_props_len;

static unsigned int cypher_ast_comparison_get_length_plus_one(const cypher_astnode_t *node) {
  return cypher_ast_comparison_get_length(node) + 1;
}

void pycypher_init_props(void) {

  INIT_TABLE(pycypher_direction_prop_t, pycypher_direction_props, TABLE({
    {CYPHER_AST_REL_PATTERN, "direction", cypher_ast_rel_pattern_get_direction},
  }))

  INIT_TABLE(pycypher_operator_prop_t, pycypher_operator_props, TABLE({
    {CYPHER_AST_UNARY_OPERATOR, "operator", cypher_ast_unary_operator_get_operator},
    {CYPHER_AST_BINARY_OPERATOR, "operator", cypher_ast_binary_operator_get_operator},
  }))

  INIT_TABLE(pycypher_operator_list_prop_t, pycypher_operator_list_props, TABLE({
    {CYPHER_AST_COMPARISON, "operators", cypher_ast_comparison_get_length, cypher_ast_comparison_get_operator},
  }))

  INIT_TABLE(pycypher_bool_prop_t, pycypher_bool_props, TABLE({
    {CYPHER_AST_APPLY_OPERATOR, "distinct", cypher_ast_apply_operator_get_distinct},
    {CYPHER_AST_APPLY_ALL_OPERATOR, "distinct", cypher_ast_apply_all_operator_get_distinct},
    {CYPHER_AST_WITH, "distinct", cypher_ast_with_is_distinct},
    {CYPHER_AST_RETURN, "distinct", cypher_ast_return_is_distinct},
    {CYPHER_AST_MATCH, "optional", cypher_ast_match_is_optional},
    {CYPHER_AST_CREATE, "unique", cypher_ast_create_is_unique},
    {CYPHER_AST_CREATE_NODE_PROP_CONSTRAINT, "unique", cypher_ast_create_node_prop_constraint_is_unique},
    {CYPHER_AST_DROP_NODE_PROP_CONSTRAINT, "unique", cypher_ast_drop_node_prop_constraint_is_unique},
    {CYPHER_AST_CREATE_REL_PROP_CONSTRAINT, "unique", cypher_ast_create_rel_prop_constraint_is_unique},
    {CYPHER_AST_DROP_REL_PROP_CONSTRAINT, "unique", cypher_ast_drop_rel_prop_constraint_is_unique},
    {CYPHER_AST_SORT_ITEM, "ascending", cypher_ast_sort_item_is_ascending},
    {CYPHER_AST_SHORTEST_PATH, "single", cypher_ast_shortest_path_is_single},
    {CYPHER_AST_DELETE, "detach", cypher_ast_delete_has_detach},
    {CYPHER_AST_WITH, "include_existing", cypher_ast_with_has_include_existing},
    {CYPHER_AST_RETURN, "include_existing", cypher_ast_return_has_include_existing},
    {CYPHER_AST_UNION, "all", cypher_ast_union_has_all},
    {CYPHER_AST_LOAD_CSV, "with_headers", cypher_ast_load_csv_has_with_headers},
  }))

  INIT_TABLE(pycypher_string_prop_t, pycypher_string_props, TABLE({
    {CYPHER_AST_IDENTIFIER, "name", cypher_ast_identifier_get_name},
    {CYPHER_AST_PARAMETER, "name", cypher_ast_parameter_get_name},
    {CYPHER_AST_STRING, "value", cypher_ast_string_get_value},
    {CYPHER_AST_INTEGER, "valuestr", cypher_ast_integer_get_valuestr},
    {CYPHER_AST_FLOAT, "valuestr", cypher_ast_float_get_valuestr},
    {CYPHER_AST_LABEL, "name", cypher_ast_label_get_name},
    {CYPHER_AST_RELTYPE, "name", cypher_ast_reltype_get_name},
    {CYPHER_AST_PROP_NAME, "value", cypher_ast_prop_name_get_value},
    {CYPHER_AST_FUNCTION_NAME, "value", cypher_ast_function_name_get_value},
    {CYPHER_AST_INDEX_NAME, "value", cypher_ast_index_name_get_value},
    {CYPHER_AST_PROC_NAME, "value", cypher_ast_proc_name_get_value},
    {CYPHER_AST_LINE_COMMENT, "value", cypher_ast_line_comment_get_value},
    {CYPHER_AST_BLOCK_COMMENT, "value", cypher_ast_block_comment_get_value},
    {CYPHER_AST_ERROR, "value", cypher_ast_error_get_value},
  }))

  INIT_TABLE(pycypher_ast_list_prop_t, pycypher_ast_list_props, TABLE({
    {CYPHER_AST_STATEMENT, "options", "option", cypher_ast_statement_noptions, cypher_ast_statement_get_option},
    {CYPHER_AST_CYPHER_OPTION, "params", "param", cypher_ast_cypher_option_nparams, cypher_ast_cypher_option_get_param},
    {CYPHER_AST_QUERY, "options", "option", cypher_ast_query_noptions, cypher_ast_query_get_option},
    {CYPHER_AST_QUERY, "clauses", "clause", cypher_ast_query_nclauses, cypher_ast_query_get_clause},
    {CYPHER_AST_START, "points", "point", cypher_ast_start_npoints, cypher_ast_start_get_point},
    {CYPHER_AST_NODE_ID_LOOKUP, "ids", "id", cypher_ast_node_id_lookup_nids, cypher_ast_node_id_lookup_get_id},
    {CYPHER_AST_REL_ID_LOOKUP, "ids", "id", cypher_ast_rel_id_lookup_nids, cypher_ast_rel_id_lookup_get_id},
    {CYPHER_AST_MATCH, "hints", "hint", cypher_ast_match_nhints, cypher_ast_match_get_hint},
    {CYPHER_AST_USING_JOIN, "identifiers", "identifier", cypher_ast_using_join_nidentifiers, cypher_ast_using_join_get_identifier},
    {CYPHER_AST_MERGE, "actions", "action", cypher_ast_merge_nactions, cypher_ast_merge_get_action},
    {CYPHER_AST_ON_MATCH, "items", "item", cypher_ast_on_match_nitems, cypher_ast_on_match_get_item},
    {CYPHER_AST_ON_CREATE, "items", "item", cypher_ast_on_create_nitems, cypher_ast_on_create_get_item},
    {CYPHER_AST_SET, "items", "item", cypher_ast_set_nitems, cypher_ast_set_get_item},
    {CYPHER_AST_SET_LABELS, "labels", "label", cypher_ast_set_labels_nlabels, cypher_ast_set_labels_get_label},
    {CYPHER_AST_DELETE, "expressions", "expression", cypher_ast_delete_nexpressions, cypher_ast_delete_get_expression},
    {CYPHER_AST_REMOVE, "items", "item", cypher_ast_remove_nitems, cypher_ast_remove_get_item},
    {CYPHER_AST_REMOVE_LABELS, "labels", "label", cypher_ast_remove_labels_nlabels, cypher_ast_remove_labels_get_label},
    {CYPHER_AST_FOREACH, "clauses", "clause", cypher_ast_foreach_nclauses, cypher_ast_foreach_get_clause},
    {CYPHER_AST_WITH, "projections", "projection", cypher_ast_with_nprojections, cypher_ast_with_get_projection},
    {CYPHER_AST_CALL, "arguments", "argument", cypher_ast_call_narguments, cypher_ast_call_get_argument},
    {CYPHER_AST_CALL, "projections", "projection", cypher_ast_call_nprojections, cypher_ast_call_get_projection},
    {CYPHER_AST_RETURN, "projections", "projection", cypher_ast_return_nprojections, cypher_ast_return_get_projection},
    {CYPHER_AST_ORDER_BY, "items", "item", cypher_ast_order_by_nitems, cypher_ast_order_by_get_item},
    {CYPHER_AST_APPLY_OPERATOR, "arguments", "argument", cypher_ast_apply_operator_narguments, cypher_ast_apply_operator_get_argument},
    {CYPHER_AST_MAP_PROJECTION, "selectors", "selector", cypher_ast_map_projection_nselectors, cypher_ast_map_projection_get_selector},
    {CYPHER_AST_LABELS_OPERATOR, "labels", "label", cypher_ast_labels_operator_nlabels, cypher_ast_labels_operator_get_label},
    {CYPHER_AST_CASE, "predicates", "predicate", cypher_ast_case_nalternatives, cypher_ast_case_get_predicate},
    {CYPHER_AST_CASE, "values", "value", cypher_ast_case_nalternatives, cypher_ast_case_get_value},
    {CYPHER_AST_MAP, "keys", "key", cypher_ast_map_nentries, cypher_ast_map_get_key},
    {CYPHER_AST_MAP, "values", "value", cypher_ast_map_nentries, cypher_ast_map_get_value},
    {CYPHER_AST_PATTERN, "paths", "path", cypher_ast_pattern_npaths, cypher_ast_pattern_get_path},
    {CYPHER_AST_PATTERN_PATH, "elements", "element", cypher_ast_pattern_path_nelements, cypher_ast_pattern_path_get_element},
    {CYPHER_AST_NODE_PATTERN, "labels", "label", cypher_ast_node_pattern_nlabels, cypher_ast_node_pattern_get_label},
    {CYPHER_AST_REL_PATTERN, "reltypes", "reltype", cypher_ast_rel_pattern_nreltypes, cypher_ast_rel_pattern_get_reltype},
    {CYPHER_AST_COMMAND, "arguments", "argument", cypher_ast_command_narguments, cypher_ast_command_get_argument},
    {CYPHER_AST_COMPARISON, "arguments", "argument", cypher_ast_comparison_get_length_plus_one, cypher_ast_comparison_get_argument},
  }))

  INIT_TABLE(pycypher_ast_prop_t, pycypher_ast_props, TABLE({
    {CYPHER_AST_STATEMENT, "body", cypher_ast_statement_get_body},
    {CYPHER_AST_CYPHER_OPTION, "version", cypher_ast_cypher_option_get_version},
    {CYPHER_AST_CYPHER_OPTION_PARAM, "name", cypher_ast_cypher_option_param_get_name},
    {CYPHER_AST_CYPHER_OPTION_PARAM, "value", cypher_ast_cypher_option_param_get_value},
    {CYPHER_AST_CREATE_NODE_PROP_INDEX, "label", cypher_ast_create_node_prop_index_get_label},
    {CYPHER_AST_CREATE_NODE_PROP_INDEX, "prop_name", cypher_ast_create_node_prop_index_get_prop_name},
    {CYPHER_AST_DROP_NODE_PROP_INDEX, "label", cypher_ast_drop_node_prop_index_get_label},
    {CYPHER_AST_DROP_NODE_PROP_INDEX, "prop_name", cypher_ast_drop_node_prop_index_get_prop_name},
    {CYPHER_AST_CREATE_NODE_PROP_CONSTRAINT, "identifier", cypher_ast_create_node_prop_constraint_get_identifier},
    {CYPHER_AST_CREATE_NODE_PROP_CONSTRAINT, "label", cypher_ast_create_node_prop_constraint_get_label},
    {CYPHER_AST_CREATE_NODE_PROP_CONSTRAINT, "expression", cypher_ast_create_node_prop_constraint_get_expression},
    {CYPHER_AST_DROP_NODE_PROP_CONSTRAINT, "identifier", cypher_ast_drop_node_prop_constraint_get_identifier},
    {CYPHER_AST_DROP_NODE_PROP_CONSTRAINT, "label", cypher_ast_drop_node_prop_constraint_get_label},
    {CYPHER_AST_DROP_NODE_PROP_CONSTRAINT, "expression", cypher_ast_drop_node_prop_constraint_get_expression},
    {CYPHER_AST_CREATE_REL_PROP_CONSTRAINT, "identifier", cypher_ast_create_rel_prop_constraint_get_identifier},
    {CYPHER_AST_CREATE_REL_PROP_CONSTRAINT, "reltype", cypher_ast_create_rel_prop_constraint_get_reltype},
    {CYPHER_AST_CREATE_REL_PROP_CONSTRAINT, "expression", cypher_ast_create_rel_prop_constraint_get_expression},
    {CYPHER_AST_DROP_REL_PROP_CONSTRAINT, "identifier", cypher_ast_drop_rel_prop_constraint_get_identifier},
    {CYPHER_AST_DROP_REL_PROP_CONSTRAINT, "reltype", cypher_ast_drop_rel_prop_constraint_get_reltype},
    {CYPHER_AST_DROP_REL_PROP_CONSTRAINT, "expression", cypher_ast_drop_rel_prop_constraint_get_expression},
    {CYPHER_AST_USING_PERIODIC_COMMIT, "limit", cypher_ast_using_periodic_commit_get_limit},
    {CYPHER_AST_LOAD_CSV, "url", cypher_ast_load_csv_get_url},
    {CYPHER_AST_LOAD_CSV, "identifier", cypher_ast_load_csv_get_identifier},
    {CYPHER_AST_LOAD_CSV, "field_terminator", cypher_ast_load_csv_get_field_terminator},
    {CYPHER_AST_START, "predicate", cypher_ast_start_get_predicate},
    {CYPHER_AST_NODE_INDEX_LOOKUP, "identifier", cypher_ast_node_index_lookup_get_identifier},
    {CYPHER_AST_NODE_INDEX_LOOKUP, "index_name", cypher_ast_node_index_lookup_get_index_name},
    {CYPHER_AST_NODE_INDEX_LOOKUP, "prop_name", cypher_ast_node_index_lookup_get_prop_name},
    {CYPHER_AST_NODE_INDEX_LOOKUP, "lookup", cypher_ast_node_index_lookup_get_lookup},
    {CYPHER_AST_NODE_INDEX_QUERY, "identifier", cypher_ast_node_index_query_get_identifier},
    {CYPHER_AST_NODE_INDEX_QUERY, "index_name", cypher_ast_node_index_query_get_index_name},
    {CYPHER_AST_NODE_INDEX_QUERY, "query", cypher_ast_node_index_query_get_query},
    {CYPHER_AST_NODE_ID_LOOKUP, "identifier", cypher_ast_node_id_lookup_get_identifier},
    {CYPHER_AST_ALL_NODES_SCAN, "identifier", cypher_ast_all_nodes_scan_get_identifier},
    {CYPHER_AST_REL_INDEX_LOOKUP, "identifier", cypher_ast_rel_index_lookup_get_identifier},
    {CYPHER_AST_REL_INDEX_LOOKUP, "index_name", cypher_ast_rel_index_lookup_get_index_name},
    {CYPHER_AST_REL_INDEX_LOOKUP, "prop_name", cypher_ast_rel_index_lookup_get_prop_name},
    {CYPHER_AST_REL_INDEX_LOOKUP, "lookup", cypher_ast_rel_index_lookup_get_lookup},
    {CYPHER_AST_REL_INDEX_QUERY, "identifier", cypher_ast_rel_index_query_get_identifier},
    {CYPHER_AST_REL_INDEX_QUERY, "index_name", cypher_ast_rel_index_query_get_index_name},
    {CYPHER_AST_REL_INDEX_QUERY, "query", cypher_ast_rel_index_query_get_query},
    {CYPHER_AST_REL_ID_LOOKUP, "identifier", cypher_ast_rel_id_lookup_get_identifier},
    {CYPHER_AST_ALL_RELS_SCAN, "identifier", cypher_ast_all_rels_scan_get_identifier},
    {CYPHER_AST_MATCH, "pattern", cypher_ast_match_get_pattern},
    {CYPHER_AST_MATCH, "predicate", cypher_ast_match_get_predicate},
    {CYPHER_AST_USING_INDEX, "identifier", cypher_ast_using_index_get_identifier},
    {CYPHER_AST_USING_INDEX, "label", cypher_ast_using_index_get_label},
    {CYPHER_AST_USING_INDEX, "prop_name", cypher_ast_using_index_get_prop_name},
    {CYPHER_AST_USING_SCAN, "identifier", cypher_ast_using_scan_get_identifier},
    {CYPHER_AST_USING_SCAN, "label", cypher_ast_using_scan_get_label},
    {CYPHER_AST_MERGE, "pattern_path", cypher_ast_merge_get_pattern_path},
    {CYPHER_AST_CREATE, "pattern", cypher_ast_create_get_pattern},
    {CYPHER_AST_SET_PROPERTY, "property", cypher_ast_set_property_get_property},
    {CYPHER_AST_SET_PROPERTY, "expression", cypher_ast_set_property_get_expression},
    {CYPHER_AST_SET_ALL_PROPERTIES, "identifier", cypher_ast_set_all_properties_get_identifier},
    {CYPHER_AST_SET_ALL_PROPERTIES, "expression", cypher_ast_set_all_properties_get_expression},
    {CYPHER_AST_MERGE_PROPERTIES, "identifier", cypher_ast_merge_properties_get_identifier},
    {CYPHER_AST_MERGE_PROPERTIES, "expression", cypher_ast_merge_properties_get_expression},
    {CYPHER_AST_SET_LABELS, "identifier", cypher_ast_set_labels_get_identifier},
    {CYPHER_AST_REMOVE_LABELS, "identifier", cypher_ast_remove_labels_get_identifier},
    {CYPHER_AST_REMOVE_PROPERTY, "property", cypher_ast_remove_property_get_property},
    {CYPHER_AST_FOREACH, "identifier", cypher_ast_foreach_get_identifier},
    {CYPHER_AST_FOREACH, "expression", cypher_ast_foreach_get_expression},
    {CYPHER_AST_WITH, "order_by", cypher_ast_with_get_order_by},
    {CYPHER_AST_WITH, "skip", cypher_ast_with_get_skip},
    {CYPHER_AST_WITH, "limit", cypher_ast_with_get_limit},
    {CYPHER_AST_WITH, "predicate", cypher_ast_with_get_predicate},
    {CYPHER_AST_UNWIND, "expression", cypher_ast_unwind_get_expression},
    {CYPHER_AST_UNWIND, "alias", cypher_ast_unwind_get_alias},
    {CYPHER_AST_CALL, "proc_name", cypher_ast_call_get_proc_name},
    {CYPHER_AST_RETURN, "order_by", cypher_ast_return_get_order_by},
    {CYPHER_AST_RETURN, "skip", cypher_ast_return_get_skip},
    {CYPHER_AST_RETURN, "limit", cypher_ast_return_get_limit},
    {CYPHER_AST_PROJECTION, "expression", cypher_ast_projection_get_expression},
    {CYPHER_AST_PROJECTION, "alias", cypher_ast_projection_get_alias},
    {CYPHER_AST_SORT_ITEM, "expression", cypher_ast_sort_item_get_expression},
    {CYPHER_AST_UNARY_OPERATOR, "argument", cypher_ast_unary_operator_get_argument},
    {CYPHER_AST_BINARY_OPERATOR, "argument1", cypher_ast_binary_operator_get_argument1},
    {CYPHER_AST_BINARY_OPERATOR, "argument2", cypher_ast_binary_operator_get_argument2},
    {CYPHER_AST_APPLY_OPERATOR, "func_name", cypher_ast_apply_operator_get_func_name},
    {CYPHER_AST_APPLY_ALL_OPERATOR, "func_name", cypher_ast_apply_all_operator_get_func_name},
    {CYPHER_AST_PROPERTY_OPERATOR, "expression", cypher_ast_property_operator_get_expression},
    {CYPHER_AST_PROPERTY_OPERATOR, "prop_name", cypher_ast_property_operator_get_prop_name},
    {CYPHER_AST_SUBSCRIPT_OPERATOR, "expression", cypher_ast_subscript_operator_get_expression},
    {CYPHER_AST_SUBSCRIPT_OPERATOR, "subscript", cypher_ast_subscript_operator_get_subscript},
    {CYPHER_AST_SLICE_OPERATOR, "expression", cypher_ast_slice_operator_get_expression},
    {CYPHER_AST_SLICE_OPERATOR, "start", cypher_ast_slice_operator_get_start},
    {CYPHER_AST_SLICE_OPERATOR, "end", cypher_ast_slice_operator_get_end},
    {CYPHER_AST_MAP_PROJECTION, "expression", cypher_ast_map_projection_get_expression},
    {CYPHER_AST_MAP_PROJECTION_LITERAL, "prop_name", cypher_ast_map_projection_literal_get_prop_name},
    {CYPHER_AST_MAP_PROJECTION_LITERAL, "expression", cypher_ast_map_projection_literal_get_expression},
    {CYPHER_AST_MAP_PROJECTION_PROPERTY, "prop_name", cypher_ast_map_projection_property_get_prop_name},
    {CYPHER_AST_MAP_PROJECTION_IDENTIFIER, "identifier", cypher_ast_map_projection_identifier_get_identifier},
    {CYPHER_AST_LABELS_OPERATOR, "expression", cypher_ast_labels_operator_get_expression},
    {CYPHER_AST_LIST_COMPREHENSION, "identifier", cypher_ast_list_comprehension_get_identifier},
    {CYPHER_AST_LIST_COMPREHENSION, "expression", cypher_ast_list_comprehension_get_expression},
    {CYPHER_AST_LIST_COMPREHENSION, "predicate", cypher_ast_list_comprehension_get_predicate},
    {CYPHER_AST_LIST_COMPREHENSION, "eval", cypher_ast_list_comprehension_get_eval},
    {CYPHER_AST_PATTERN_COMPREHENSION, "identifier", cypher_ast_pattern_comprehension_get_identifier},
    {CYPHER_AST_PATTERN_COMPREHENSION, "pattern", cypher_ast_pattern_comprehension_get_pattern},
    {CYPHER_AST_PATTERN_COMPREHENSION, "predicate", cypher_ast_pattern_comprehension_get_predicate},
    {CYPHER_AST_PATTERN_COMPREHENSION, "eval", cypher_ast_pattern_comprehension_get_eval},
    {CYPHER_AST_REDUCE, "accumulator", cypher_ast_reduce_get_accumulator},
    {CYPHER_AST_REDUCE, "init", cypher_ast_reduce_get_init},
    {CYPHER_AST_REDUCE, "identifier", cypher_ast_reduce_get_identifier},
    {CYPHER_AST_REDUCE, "expression", cypher_ast_reduce_get_expression},
    {CYPHER_AST_REDUCE, "eval", cypher_ast_reduce_get_eval},
    {CYPHER_AST_CASE, "expression", cypher_ast_case_get_expression},
    {CYPHER_AST_CASE, "default", cypher_ast_case_get_default},
    {CYPHER_AST_NAMED_PATH, "identifier", cypher_ast_named_path_get_identifier},
    {CYPHER_AST_NAMED_PATH, "path", cypher_ast_named_path_get_path},
    {CYPHER_AST_SHORTEST_PATH, "path", cypher_ast_shortest_path_get_path},
    {CYPHER_AST_NODE_PATTERN, "identifier", cypher_ast_node_pattern_get_identifier},
    {CYPHER_AST_NODE_PATTERN, "properties", cypher_ast_node_pattern_get_properties},
    {CYPHER_AST_REL_PATTERN, "identifier", cypher_ast_rel_pattern_get_identifier},
    {CYPHER_AST_REL_PATTERN, "varlength", cypher_ast_rel_pattern_get_varlength},
    {CYPHER_AST_REL_PATTERN, "properties", cypher_ast_rel_pattern_get_properties},
    {CYPHER_AST_RANGE, "start", cypher_ast_range_get_start},
    {CYPHER_AST_RANGE, "end", cypher_ast_range_get_end},
    {CYPHER_AST_COMMAND, "name", cypher_ast_command_get_name},
  }))
}
