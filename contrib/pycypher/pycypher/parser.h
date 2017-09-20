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
#ifndef PYCYPHER_PARSER_H
#define PYCYPHER_PARSER_H
#include <stdio.h>
#include <Python.h>
#include <methodobject.h>
#include <cypher-parser.h>
#include "node_types.h"
#include "extract_props.h"

PyObject* pycypher_parse_query(PyObject*, PyObject*);
PyObject* pycypher_build_ast(PyObject*, const cypher_astnode_t*);
PyObject* pycypher_build_ast_list(
  PyObject* cls, const cypher_parse_result_t* parse_result
);

#endif
