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
#include "parser.h"
#include "node_types.h"
#include "operators.h"
#include "props.h"

PyObject *pycypher_error;

static PyMethodDef methods[] = {
    {
      "parse_query", pycypher_parse_query, METH_VARARGS,
      "Return a list of CypherAst instances corresponding to parsed query."
    },
    {NULL, NULL, 0, NULL}
};

PyMODINIT_FUNC initbindings(void) {
  PyObject *m = Py_InitModule("pycypher.bindings", methods);
  if (m == NULL)
    return;
  pycypher_error = PyErr_NewException("pycypher.bindings.Error", NULL, NULL);
  Py_INCREF(pycypher_error);
  PyModule_AddObject(m, "Error", pycypher_error);
  pycypher_init_node_types();
  pycypher_init_operators();
  pycypher_init_props();
}
