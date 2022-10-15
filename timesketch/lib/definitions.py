# Copyright 2014 Google Inc. All rights reserved.
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
"""Definitions for Timesketch."""

from __future__ import unicode_literals

# HTTP status codes
HTTP_STATUS_CODE_OK = 200
HTTP_STATUS_CODE_CREATED = 201
HTTP_STATUS_CODE_REDIRECT = 302
HTTP_STATUS_CODE_BAD_REQUEST = 400
HTTP_STATUS_CODE_UNAUTHORIZED = 401
HTTP_STATUS_CODE_FORBIDDEN = 403
HTTP_STATUS_CODE_NOT_FOUND = 404
HTTP_STATUS_CODE_CONFLICT = 409
HTTP_STATUS_CODE_INTERNAL_SERVER_ERROR = 500

# Time and date
MICROSECONDS_PER_SECOND = 1000000

# _source fields for search and export functions
DEFAULT_FIELDS = [
    "datetime",
    "timestamp",
    "timestamp_desc",
    "_index",
    "__ts_timeline_id",
    "message",
    "comment",
]
DEFAULT_SOURCE_FIELDS = DEFAULT_FIELDS + [
    "timesketch_label",
    "tag",
    "similarity_score",
    "human_readable",
    "__ts_emojis",
]

# Prometheus metrics
METRICS_NAMESPACE = "timesketch"
