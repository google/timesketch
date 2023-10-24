# Copyright 2023 Google Inc. All rights reserved.
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
"""Unfurl API for version 1 of the Timesketch API."""

import logging
import unfurl

from flask import jsonify
from flask import request
from flask import abort
from flask_restful import Resource
from flask_login import login_required

from timesketch.lib.definitions import HTTP_STATUS_CODE_BAD_REQUEST
from timesketch.lib.definitions import HTTP_STATUS_CODE_INTERNAL_SERVER_ERROR

logger = logging.getLogger("timesketch.api_unfurl")


class UnfurlResource(Resource):
    """Resource to get unfurl information."""

    @login_required
    def post(self):
        """Handles POST request to the resource.

        Returns:
            JSON object including version info
        """
        form = request.json
        if not form:
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                "No JSON data provided",
            )

        if "url" not in form:
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                "url parameter is required",
            )

        url = form.get("url")

        try:
            unfurl_result = unfurl.run(url)
        except Exception as e:  # pylint: disable=broad-except
            logger.error("Error unfurling URL: {}".format(e))
            abort(
                HTTP_STATUS_CODE_INTERNAL_SERVER_ERROR,
                e,
            )

        return jsonify(unfurl_result)
