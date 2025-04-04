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
from typing import Any

from flask import current_app, jsonify
from flask_restful import Resource
from flask_login import login_required
from timesketch.lib.llms.providers import manager as llm_manager

logger = logging.getLogger("timesketch.system_settings")


class SystemSettingsResource(Resource):
    """Resource to get system settings."""

    @login_required
    def get(self):
        """GET system settings.

        Returns:
            JSON object with system settings.
        """
        result = {
            "DFIQ_ENABLED": current_app.config.get("DFIQ_ENABLED", False),
            "SEARCH_PROCESSING_TIMELINES": current_app.config.get(
                "SEARCH_PROCESSING_TIMELINES", False
            ),
            "LLM_FEATURES_AVAILABLE": self._get_llm_features_availability(
                current_app.config.get("LLM_PROVIDER_CONFIGS", {})
            ),
        }

        return jsonify(result)

    def _get_llm_features_availability(
        self, llm_configs: dict[str, Any]
    ) -> dict[str, bool]:
        """Get availability status for all LLM features.

        Args:
            llm_configs: LLM provider configuration dictionary

        Returns:
            dict mapping feature names to availability status (bool)
        """
        default_provider_working = False

        if not isinstance(llm_configs, dict):
            logger.debug(
                "LLM_PROVIDER_CONFIGS is not a dictionary: %s",
                type(llm_configs).__name__,
            )
            return {"default": default_provider_working}

        if (
            "default" in llm_configs
            and isinstance(llm_configs["default"], dict)
            and len(llm_configs["default"]) == 1
        ):
            default_provider = next(iter(llm_configs["default"]))
            default_provider_config = llm_configs["default"][default_provider]
            default_provider_working = self._check_provider_working(
                default_provider, default_provider_config
            )

        llm_feature_availability = {"default": default_provider_working}

        for feature_name, feature_conf in llm_configs.items():
            if feature_name == "default":
                continue

            feature_provider_working = False
            if isinstance(feature_conf, dict) and len(feature_conf) == 1:
                feature_provider = next(iter(feature_conf))
                feature_provider_config = feature_conf[feature_provider]
                feature_provider_working = self._check_provider_working(
                    feature_provider, feature_provider_config
                )

            # Feature is available if either specific provider works
            # or default provider works
            llm_feature_availability[feature_name] = (
                feature_provider_working or default_provider_working
            )

        return llm_feature_availability

    def _check_provider_working(self, provider_name: str, config: dict) -> bool:
        """Check if a specific LLM provider works with given configuration.

        Args:
            provider_name: Name of the provider to check
            config: Configuration dict for the provider

        Returns:
            bool: Whether the provider is working
        """
        try:
            provider_class = llm_manager.LLMManager.get_provider(provider_name)
            provider_class(config=config)
            return True
        except Exception as e:  # pylint: disable=broad-except
            logger.debug(
                "LLM provider '%s' failed to initialize: %s",
                provider_name,
                str(e),
            )
            return False
