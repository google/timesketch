# Copyright 2020 Google Inc. All rights reserved.
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
"""Information API for version 1 of the Timesketch API."""

from flask import jsonify
from flask import current_app
from flask_restful import Resource
from flask_login import login_required

from timesketch import version
from timesketch.api.v1 import resources
from timesketch.lib.definitions import HTTP_STATUS_CODE_OK


class VersionResource(resources.ResourceMixin, Resource):
    """Resource to get Timesketch API version information."""

    @login_required
    def get(self):
        """Handles GET request to the resource.

        Returns:
            JSON object including version info
        """
        schema = {
            "meta": {
                "version": version.get_version(),
                "plaso_version": current_app.config.get("PLASO_VERSION", "N/A"),
            },
            "objects": [],
        }
        response = jsonify(schema)
        response.status_code = HTTP_STATUS_CODE_OK
        return response
