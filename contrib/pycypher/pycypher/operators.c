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
#include "operators.h"
#include "table_utils.h"

pycypher_operator_t* pycypher_operators;
size_t pycypher_operators_len;

void pycypher_init_operators(void) {
  INIT_TABLE(pycypher_operator_t, pycypher_operators, TABLE({
    {"CYPHER_OP_OR", CYPHER_OP_OR},
    {"CYPHER_OP_XOR", CYPHER_OP_XOR},
    {"CYPHER_OP_AND", CYPHER_OP_AND},
    {"CYPHER_OP_NOT", CYPHER_OP_NOT},
    {"CYPHER_OP_EQUAL", CYPHER_OP_EQUAL},
    {"CYPHER_OP_NEQUAL", CYPHER_OP_NEQUAL},
    {"CYPHER_OP_LT", CYPHER_OP_LT},
    {"CYPHER_OP_GT", CYPHER_OP_GT},
    {"CYPHER_OP_LTE", CYPHER_OP_LTE},
    {"CYPHER_OP_GTE", CYPHER_OP_GTE},
    {"CYPHER_OP_PLUS", CYPHER_OP_PLUS},
    {"CYPHER_OP_MINUS", CYPHER_OP_MINUS},
    {"CYPHER_OP_MULT", CYPHER_OP_MULT},
    {"CYPHER_OP_DIV", CYPHER_OP_DIV},
    {"CYPHER_OP_MOD", CYPHER_OP_MOD},
    {"CYPHER_OP_POW", CYPHER_OP_POW},
    {"CYPHER_OP_UNARY_PLUS", CYPHER_OP_UNARY_PLUS},
    {"CYPHER_OP_UNARY_MINUS", CYPHER_OP_UNARY_MINUS},
    {"CYPHER_OP_SUBSCRIPT", CYPHER_OP_SUBSCRIPT},
    {"CYPHER_OP_MAP_PROJECTION", CYPHER_OP_MAP_PROJECTION},
    {"CYPHER_OP_REGEX", CYPHER_OP_REGEX},
    {"CYPHER_OP_IN", CYPHER_OP_IN},
    {"CYPHER_OP_STARTS_WITH", CYPHER_OP_STARTS_WITH},
    {"CYPHER_OP_ENDS_WITH", CYPHER_OP_ENDS_WITH},
    {"CYPHER_OP_CONTAINS", CYPHER_OP_CONTAINS},
    {"CYPHER_OP_IS_NULL", CYPHER_OP_IS_NULL},
    {"CYPHER_OP_IS_NOT_NULL", CYPHER_OP_IS_NOT_NULL},
    {"CYPHER_OP_PROPERTY", CYPHER_OP_PROPERTY},
    {"CYPHER_OP_LABEL", CYPHER_OP_LABEL},
  }))
}
