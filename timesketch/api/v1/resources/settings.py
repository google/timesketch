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

import logging
from flask import current_app, jsonify
from flask_restful import Resource
from flask_login import login_required

logger = logging.getLogger("timesketch.system_settings")


class SystemSettingsResource(Resource):
    """Resource to get system settings."""

    @login_required
    def get(self):
        """GET system settings.

        Returns:
            JSON object with system settings.
        """
        # Settings from timesketch.conf to expose to the frontend clients.
        settings_to_return = ["DFIQ_ENABLED"]
        result = {}

        for setting in settings_to_return:
            result[setting] = current_app.config.get(setting)

        # Derive the default LLM provider from the new configuration.
        # Expecting the "default" config to be a dict with exactly one key:
        # the provider name.
        llm_configs = current_app.config.get("LLM_PROVIDER_CONFIGS", {})
        default_provider = None
        default_conf = llm_configs.get("default")
        if default_conf and isinstance(default_conf, dict) and len(default_conf) == 1:
            default_provider = next(iter(default_conf))
        result["LLM_PROVIDER"] = default_provider

        # TODO(mvd): Remove by 2025/06/01 once all users have updated their config.
        old_llm_provider = current_app.config.get("LLM_PROVIDER")
        if (
            old_llm_provider and "default" not in llm_configs
        ):  # Basic check for old config
            warning_message = (
                "Your LLM configuration in timesketch.conf is outdated and may cause "
                "issues with LLM features. "
                "Please update your LLM_PROVIDER_CONFIGS section to the new format. "
                "Refer to the documentation for the updated configuration structure."
            )
            result["llm_config_warning"] = warning_message
            logger.warning(warning_message)

        return jsonify(result)
