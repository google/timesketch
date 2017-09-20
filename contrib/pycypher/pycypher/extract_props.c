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
#include "extract_props.h"

PyObject* pycypher_operator_to_python_string(const cypher_operator_t* op) {
  int i;
  for(i=0; i<pycypher_operators_len; ++i)
    if(op == pycypher_operators[i].operator)
      return Py_BuildValue("s", pycypher_operators[i].name);
  return Py_BuildValue("s", "CYPHER_OP_UNKNOWN");
}

PyObject* pycypher_astnode_to_python_dict(const cypher_astnode_t* src_ast, const char* role) {
  PyObject* result = PyDict_New();
  PyDict_SetItemString(result, "id", Py_BuildValue("i", src_ast));
  PyDict_SetItemString(result, "role", Py_BuildValue("s", role));
  return result;
}

PyObject* pycypher_extract_direction_prop(const cypher_astnode_t* src_ast, pycypher_direction_prop_t* prop) {
  enum cypher_rel_direction src_prop = prop->getter(src_ast);
  if(src_prop == CYPHER_REL_INBOUND)
    return Py_BuildValue("s", "CYPHER_REL_INBOUND");
  if(src_prop == CYPHER_REL_OUTBOUND)
    return Py_BuildValue("s", "CYPHER_REL_OUTBOUND");
  if(src_prop == CYPHER_REL_BIDIRECTIONAL)
    return Py_BuildValue("s", "CYPHER_REL_BIDIRECTIONAL");
  return Py_BuildValue("s", "CYPHER_REL_UNKNOWN");
}

PyObject* pycypher_extract_operator_prop(const cypher_astnode_t* src_ast, pycypher_operator_prop_t* prop) {
  const cypher_operator_t* src_prop = prop->getter(src_ast);
  return pycypher_operator_to_python_string(src_prop);
}

PyObject* pycypher_extract_operator_list_prop(const cypher_astnode_t* src_ast, pycypher_operator_list_prop_t* prop) {
  int n = prop->length_getter(src_ast);
  PyObject* result = PyList_New(n);
  int i;
  for(i=0; i<n; ++i)
    // PyList_SetItem consumes a reference so no need to call Py_DECREF
    PyList_SetItem(result, i, pycypher_operator_to_python_string(
      prop->list_getter(src_ast, i)
    ));
  return result;
}

PyObject* pycypher_extract_bool_prop(const cypher_astnode_t* src_ast, pycypher_bool_prop_t* prop) {
  bool src_prop = prop->getter(src_ast);
  if(src_prop)
    Py_RETURN_TRUE;
  else
    Py_RETURN_FALSE;
}

PyObject* pycypher_extract_string_prop(const cypher_astnode_t* src_ast, pycypher_string_prop_t* prop) {
  const char* src_prop = prop->getter(src_ast);
  return Py_BuildValue("s", src_prop);
}

PyObject* pycypher_extract_ast_list_prop(const cypher_astnode_t* src_ast, pycypher_ast_list_prop_t* prop) {
  int n = prop->length_getter(src_ast);
  PyObject* result = PyList_New(n);
  int i;
  for(i=0; i<n; ++i)
    // PyList_SetItem consumes a reference so no need to call Py_DECREF
    PyList_SetItem(result, i, pycypher_astnode_to_python_dict(
      prop->list_getter(src_ast, i), prop->role
    ));
  return result;
}

PyObject* pycypher_extract_ast_prop(const cypher_astnode_t* src_ast, pycypher_ast_prop_t* prop) {
  const cypher_astnode_t* src_prop = prop->getter(src_ast);
  if(!src_prop)
    Py_RETURN_NONE;
  return pycypher_astnode_to_python_dict(src_prop, prop->name);
}

PyObject* pycypher_extract_props(const cypher_astnode_t* src_ast) {
  PyObject* result = PyDict_New();
  PyObject* extracted_prop;
  int i;
  for(i=0; i<pycypher_direction_props_len; ++i)
    if(cypher_astnode_instanceof(src_ast, pycypher_direction_props[i].node_type)) {
      extracted_prop = pycypher_extract_direction_prop(
        src_ast, &pycypher_direction_props[i]
      );
      if(extracted_prop != Py_None)
        PyDict_SetItemString(
          result, pycypher_direction_props[i].name, extracted_prop
        );
      Py_DECREF(extracted_prop);
    }
  for(i=0; i<pycypher_operator_props_len; ++i)
    if(cypher_astnode_instanceof(src_ast, pycypher_operator_props[i].node_type)) {
      extracted_prop = pycypher_extract_operator_prop(
        src_ast, &pycypher_operator_props[i]
      );
      if(extracted_prop != Py_None)
        PyDict_SetItemString(
          result, pycypher_operator_props[i].name, extracted_prop
        );
      Py_DECREF(extracted_prop);
    }
  for(i=0; i<pycypher_operator_list_props_len; ++i)
    if(cypher_astnode_instanceof(src_ast, pycypher_operator_list_props[i].node_type)) {
      extracted_prop = pycypher_extract_operator_list_prop(
        src_ast, &pycypher_operator_list_props[i]
      );
      if(extracted_prop != Py_None)
        PyDict_SetItemString(
          result, pycypher_operator_list_props[i].name, extracted_prop
        );
      Py_DECREF(extracted_prop);
    }
  for(i=0; i<pycypher_bool_props_len; ++i)
    if(cypher_astnode_instanceof(src_ast, pycypher_bool_props[i].node_type)) {
      extracted_prop = pycypher_extract_bool_prop(
        src_ast, &pycypher_bool_props[i]
      );
      if(extracted_prop != Py_None)
        PyDict_SetItemString(
          result, pycypher_bool_props[i].name, extracted_prop
        );
      Py_DECREF(extracted_prop);
    }
  for(i=0; i<pycypher_string_props_len; ++i)
    if(cypher_astnode_instanceof(src_ast, pycypher_string_props[i].node_type)) {
      extracted_prop = pycypher_extract_string_prop(
        src_ast, &pycypher_string_props[i]
      );
      if(extracted_prop != Py_None)
        PyDict_SetItemString(
          result, pycypher_string_props[i].name, extracted_prop
        );
      Py_DECREF(extracted_prop);
    }
  for(i=0; i<pycypher_ast_list_props_len; ++i)
    if(cypher_astnode_instanceof(src_ast, pycypher_ast_list_props[i].node_type)) {
      extracted_prop = pycypher_extract_ast_list_prop(
        src_ast, &pycypher_ast_list_props[i]
      );
      if(extracted_prop != Py_None)
        PyDict_SetItemString(
          result, pycypher_ast_list_props[i].name, extracted_prop
        );
      Py_DECREF(extracted_prop);
    }
  for(i=0; i<pycypher_ast_props_len; ++i)
    if(cypher_astnode_instanceof(src_ast, pycypher_ast_props[i].node_type)) {
      extracted_prop = pycypher_extract_ast_prop(
        src_ast, &pycypher_ast_props[i]
      );
      if(extracted_prop != Py_None)
        PyDict_SetItemString(
          result, pycypher_ast_props[i].name, extracted_prop
        );
      Py_DECREF(extracted_prop);
    }
  return result;
}
