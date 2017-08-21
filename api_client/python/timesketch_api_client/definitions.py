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
"""Timesketch API client definitions."""


# HTTP status codes
HTTP_STATUS_CODE_OK = 200
HTTP_STATUS_CODE_CREATED = 201
HTTP_STATUS_CODE_REDIRECT = 302
HTTP_STATUS_CODE_BAD_REQUEST = 400
HTTP_STATUS_CODE_UNAUTHORIZED = 401
HTTP_STATUS_CODE_FORBIDDEN = 403
HTTP_STATUS_CODE_NOT_FOUND = 404
HTTP_STATUS_CODE_CONFLICT = 409

# Convenient buckets of return code families
HTTP_STATUS_CODE_20X = [HTTP_STATUS_CODE_OK, HTTP_STATUS_CODE_CREATED]
