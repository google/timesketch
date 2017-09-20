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
#ifndef PYCYPHER_EXTRACT_PROPS_H
#define PYCYPHER_EXTRACT_PROPS_H
#include <Python.h>
#include <cypher-parser.h>
#include "props.h"
#include "operators.h"

/* Return a dict where keys are names of props (as defined in props.c) and
values are:
 - python strings for string properties
 - True of False for boolean properties
 - python lists for list properties
 - strings 'CYPHER_REL_INBOUND', 'CYPHER_REL_OUTBOUND' or 'CYPHER_REL_BIDIRECTIONAL' for direction properties
 - strings 'CYPHER_OP_OR','CYPHER_OP_MAP_PROJECTION', etc. for operator properties
 - dictionaries {"id": id, "role": role} where
   id is an integer identifying an AST node and role is a singular
   form of the prop name, for example:
   {..., "clauses": [{"id": 3, "role": "clause"}, {"id": 5, "role": "clause"}], ...}
   {..., "where": {"id": 4, "role": "where"}, ...}
*/
PyObject* pycypher_extract_props(const cypher_astnode_t*);

#endif
