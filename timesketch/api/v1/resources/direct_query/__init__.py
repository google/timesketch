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
"""Direct PPL / SQL query resources for the Timesketch API.

Proxies the OpenSearch `_plugins/_ppl` and `_plugins/_sql` endpoints, enforces
sketch-level ACLs, and injects a `source=`/`FROM` clause that restricts every
query to the sketch's own indices.

PPL and SQL are separated into dedicated dialect modules (`ppl.py`, `sql.py`)
behind a common interface, following the same shape as the query-string /
wildcard split in `explore.py`: a thin per-language entry point over one shared
execution shell. The REST resources are re-exported here because they are the
package's public surface; everything else is imported from its own module.
"""

from timesketch.api.v1.resources.direct_query.endpoints import (
    PplQueryExplainResource,
    PplQueryExportResource,
    PplQueryResource,
    SqlQueryExplainResource,
    SqlQueryExportResource,
    SqlQueryResource,
)

__all__ = [
    "PplQueryExplainResource",
    "PplQueryExportResource",
    "PplQueryResource",
    "SqlQueryExplainResource",
    "SqlQueryExportResource",
    "SqlQueryResource",
]
