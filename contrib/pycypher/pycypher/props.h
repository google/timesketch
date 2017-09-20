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
#ifndef PYCYPHER_PROPS_H
#define PYCYPHER_PROPS_H
#include <cypher-parser.h>

typedef unsigned int (*pycypher_length_getter_t)(const cypher_astnode_t*);

typedef enum cypher_rel_direction (*pycypher_direction_getter_t)(const cypher_astnode_t*);
typedef struct {
  cypher_astnode_type_t node_type;
  const char* name;
  pycypher_direction_getter_t getter;
}
pycypher_direction_prop_t;
extern pycypher_direction_prop_t* pycypher_direction_props;
extern size_t pycypher_direction_props_len;

typedef const cypher_operator_t* (*pycypher_operator_getter_t)(const cypher_astnode_t*);
typedef struct {
  cypher_astnode_type_t node_type;
  const char* name;
  pycypher_operator_getter_t getter;
}
pycypher_operator_prop_t;
extern pycypher_operator_prop_t* pycypher_operator_props;
extern size_t pycypher_operator_props_len;

typedef const cypher_operator_t* (*pycypher_operator_list_getter_t)(const cypher_astnode_t*, unsigned int);
typedef struct {
  cypher_astnode_type_t node_type;
  const char* name;
  pycypher_length_getter_t length_getter;
  pycypher_operator_list_getter_t list_getter;
}
pycypher_operator_list_prop_t;
extern pycypher_operator_list_prop_t* pycypher_operator_list_props;
extern size_t pycypher_operator_list_props_len;

typedef bool (*pycypher_bool_getter_t)(const cypher_astnode_t*);
typedef struct {
  cypher_astnode_type_t node_type;
  const char* name;
  pycypher_bool_getter_t getter;
}
pycypher_bool_prop_t;
extern pycypher_bool_prop_t* pycypher_bool_props;
extern size_t pycypher_bool_props_len;

typedef const char* (*pycypher_string_getter_t)(const cypher_astnode_t*);
typedef struct {
  cypher_astnode_type_t node_type;
  const char* name;
  pycypher_string_getter_t getter;
}
pycypher_string_prop_t;
extern pycypher_string_prop_t* pycypher_string_props;
extern size_t pycypher_string_props_len;

typedef const cypher_astnode_t* (*pycypher_ast_list_getter_t)(const cypher_astnode_t*, unsigned int);
typedef struct {
  cypher_astnode_type_t node_type;
  const char* name;
  const char* role;
  pycypher_length_getter_t length_getter;
  pycypher_ast_list_getter_t list_getter;
}
pycypher_ast_list_prop_t;
extern pycypher_ast_list_prop_t* pycypher_ast_list_props;
extern size_t pycypher_ast_list_props_len;

typedef const cypher_astnode_t* (*pycypher_ast_getter_t)(const cypher_astnode_t*);
typedef struct {
  cypher_astnode_type_t node_type;
  const char* name;
  pycypher_ast_getter_t getter;
}
pycypher_ast_prop_t;
extern pycypher_ast_prop_t* pycypher_ast_props;
extern size_t pycypher_ast_props_len;

void pycypher_init_props(void);

#endif
