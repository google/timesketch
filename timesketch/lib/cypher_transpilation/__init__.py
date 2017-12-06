# Copyright 2017 Google Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Transpile cypher queries so that they are constrained only to access
subgraph specific to given sketch. Also insert some unwind clauses so that
accessing the edge.timestamp field is handled transparently even if edges have
only `timestamps` field containing the list of timestamps.
"""
from .transpile_query import transpile_query
from .invalid_query import InvalidQuery


__all__ = ['transpile_query', 'InvalidQuery']
