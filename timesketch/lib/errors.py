# Copyright 2015 Google Inc. All rights reserved.
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
"""Error classes."""

from flask import jsonify


class ApiHTTPError(Exception):
    """Error class for API HTTP errors."""

    def __init__(self, message, status_code):
        """Initialize the class with a custom error message.

        Args:
            message: Description of the error.
            status_code: HTTP status code.
        """
        Exception.__init__(self)
        self.message = message
        self.status_code = status_code

    def build_response(self):
        """Create a response object.

        Returns:
            Response object (instance of flask.wrappers.Response)
        """
        response = jsonify({
            u'message': self.message,
            u'status': self.status_code
        })
        response.status_code = self.status_code
        return response
