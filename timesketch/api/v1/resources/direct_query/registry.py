# Copyright 2026 Google Inc. All rights reserved.
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
"""Dialect singletons for direct queries.

Dialects are stateless, so each is instantiated once here and shared across
requests. Resources bind one of these to a class attribute, which is what pins
a language to its route.

They live in their own module rather than in `endpoints.py` so the dialect
modules and the resource shell can both import them without a cycle.
"""

from timesketch.api.v1.resources.direct_query.ppl import PplDialect
from timesketch.api.v1.resources.direct_query.sql import SqlDialect

PPL_DIALECT = PplDialect()
SQL_DIALECT = SqlDialect()
