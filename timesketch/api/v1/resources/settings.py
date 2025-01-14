# Copyright 2024 Google Inc. All rights reserved.
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
"""System settings."""

from flask import current_app
from flask import jsonify
from flask_restful import Resource
from flask_login import login_required


class SystemSettingsResource(Resource):
    """Resource to get system settings."""

    @login_required
    def get(self):
        """GET system settings.

        Returns:
            JSON object with system settings.
        """
        # Settings from timesketch.conf to expose to the frontend clients.
        settings_to_return = ["LLM_PROVIDER", "DFIQ_ENABLED"]
        result = {}

        for setting in settings_to_return:
            result[setting] = current_app.config.get(setting)

        return jsonify(result)
