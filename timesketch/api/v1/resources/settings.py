"""System settings."""

import logging
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
        # Settings from timesketch.conf to expose to the frontend clients
        result = {
            "DFIQ_ENABLED": current_app.config.get("DFIQ_ENABLED"),
            "SEARCH_PROCESSING_TIMELINES": current_app.config.get(
                "SEARCH_PROCESSING_TIMELINES", False
            ),
        }

        llm_configs = current_app.config.get("LLM_PROVIDER_CONFIGS", {})
        result["LLM_PROVIDER"] = bool(llm_configs)

        # Check default LLM provider
        default_provider_working = False
        if (
            "default" in llm_configs
            and isinstance(llm_configs["default"], dict)
            and len(llm_configs["default"]) == 1
        ):
            default_provider = next(iter(llm_configs["default"]))
            try:
                provider_class = llm_manager.LLMManager.get_provider(default_provider)
                provider_class(config=llm_configs["default"][default_provider])
                default_provider_working = True
            except Exception as e:  # pylint: disable=broad-except
                logger.debug(
                    "Default LLM provider '%s' failed to initialize: %s",
                    default_provider,
                    str(e),
                )

        # Initialize feature availability with default status
        llm_feature_availability = {"default": default_provider_working}

        # Check LLM feature-specific configurations
        for feature_name, feature_conf in llm_configs.items():
            if feature_name == "default":
                continue

            feature_provider_working = False
            if isinstance(feature_conf, dict) and len(feature_conf) == 1:
                feature_provider = next(iter(feature_conf))
                try:
                    provider_class = llm_manager.LLMManager.get_provider(
                        feature_provider
                    )
                    provider_class(config=feature_conf[feature_provider])
                    feature_provider_working = True
                except Exception as e:  # pylint: disable=broad-except
                    logger.debug(
                        "LLM provider '%s' for feature '%s' failed: %s",
                        feature_provider,
                        feature_name,
                        str(e),
                    )

            # Feature is available if either specific provider works
            # or default provider works
            llm_feature_availability[feature_name] = (
                feature_provider_working or default_provider_working
            )

        result["LLM_FEATURES_AVAILABLE"] = llm_feature_availability

        # TODO(mvd): Remove by 2025/06/01 once all users have updated their config.
        if current_app.config.get("LLM_PROVIDER") and "default" not in llm_configs:
            result["llm_config_warning"] = (
                "Your LLM configuration in timesketch.conf is outdated. "
                "Please update your LLM_PROVIDER_CONFIGS section to the new format."
            )
            logger.warning(result["llm_config_warning"])

        return jsonify(result)
