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
#ifndef PYCYPHER_NODE_TYPES_H
#define PYCYPHER_NODE_TYPES_H
#include <cypher-parser.h>

typedef struct {
  const char* name;
  const cypher_astnode_type_t node_type;
}
pycypher_node_type_t;
extern pycypher_node_type_t* pycypher_node_types;
extern size_t pycypher_node_types_len;

void pycypher_init_node_types(void);

#endif
