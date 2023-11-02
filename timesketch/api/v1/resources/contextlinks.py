# Copyright 2022 Google Inc. All rights reserved.
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
"""Context link API for version 1 of the Timesketch API."""

from copy import deepcopy
from flask import jsonify
from flask_restful import Resource
from flask_login import login_required

from timesketch.api.v1 import resources
from timesketch.api.v1.utils import load_yaml_config


class ContextLinkConfigResource(resources.ResourceMixin, Resource):
    """Resource to get context link information."""

    @login_required
    def get(self):
        """Handles GET request to the resource.

        HINT:
            In case of errors with loading the context links, use the
            tsctl tool to validate your config file!
            Example: tsctl validate-context-links-conf ./data/context_links.yaml

        Returns:
            JSON object including version info
        """
        # HINT: In case of errors with loading the context links, use the
        # tsctl tool to validate your config file!
        # Example: tsctl validate-context-links-conf ./data/context_links.yaml

        context_link_yaml = load_yaml_config("CONTEXT_LINKS_CONFIG_PATH")

        response = {}
        if not context_link_yaml:
            return jsonify(response)

        # Support for earlier version format of context links without hardcoded modules:
        if "linked_services" not in context_link_yaml.keys():
            context_link_yaml = {
                "linked_services": context_link_yaml,
            }

        if context_link_yaml.get("hardcoded_modules"):
            for entry in context_link_yaml.get("hardcoded_modules", []):
                context_link_config = {
                    "type": "hardcoded_modules",
                    "short_name": context_link_yaml["hardcoded_modules"][entry][
                        "short_name"
                    ],
                    "module": entry,
                }
                if context_link_yaml["hardcoded_modules"][entry].get(
                    "validation_regex"
                ):
                    context_link_config["validation_regex"] = context_link_yaml[
                        "hardcoded_modules"
                    ][entry]["validation_regex"]
                for field in context_link_yaml["hardcoded_modules"][entry][
                    "match_fields"
                ]:
                    response.setdefault(field.lower(), []).append(context_link_config)

        if context_link_yaml.get("linked_services"):
            for entry in context_link_yaml.get("linked_services", []):
                context_link_config = deepcopy(
                    context_link_yaml["linked_services"][entry]
                )
                context_link_config["type"] = "linked_services"
                del context_link_config["match_fields"]
                for field in context_link_yaml["linked_services"][entry][
                    "match_fields"
                ]:
                    response.setdefault(field.lower(), []).append(context_link_config)

        return jsonify(response)
