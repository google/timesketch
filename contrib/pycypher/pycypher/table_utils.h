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
#ifndef PYCYPHER_TABLE_UTILS_H
#define PYCYPHER_TABLE_UTILS_H
#include <stdlib.h>

static void* move_to_heap(void* src, size_t len) {
  void* dest = malloc(len);
  memcpy(dest, src, len);
  return dest;
}

#define INIT_TABLE(type, name, content) \
  type name##_tmp[] = content; \
  name = move_to_heap(name##_tmp, sizeof(name##_tmp)); \
  name##_len = sizeof(name##_tmp) / sizeof(type);

#define TABLE(...) __VA_ARGS__

#endif
