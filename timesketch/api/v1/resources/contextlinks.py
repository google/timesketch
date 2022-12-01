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
import logging
import re
import copy

from flask import jsonify
from flask_restful import Resource
from flask_login import login_required

from timesketch.api.v1 import resources
from timesketch.api.v1.utils import load_yaml_config

# Set up logging
logger = logging.getLogger("timesketch.contextlinks_api")


class ContextLinkConfigResource(resources.ResourceMixin, Resource):
    """Resource to get context link information."""

    @login_required
    def get(self):
        """Handles GET request to the resource.
        Returns:
            JSON object including version info
        """
        context_link_config = load_yaml_config("CONTEXT_LINKS_CONFIG_PATH")

        response = {}

        if not context_link_config:
            return jsonify(response)

        verification_results = []

        # Check mandatory fields are correctly defined.
        for item in context_link_config:
            item_dict = context_link_config[item]

            verification = {
                "check_short_name": False,
                "check_match_fields": False,
                "check_validation_regex": False,
                "check_context_link": False,
                "check_redirect_warning": False
            }

            # Verify that short_name is defined and type string
            if isinstance(item_dict.get("short_name"), str):
                verification["check_short_name"] = True

            # Verify that match_fields is defined, has entries and is type list
            if isinstance(item_dict.get("match_fields"), list):
                if len(item_dict.get("match_fields")) > 0:
                    verification["check_match_fields"] = True

            # Verify that validation_regex is a valid regeular expression
            if isinstance(item_dict.get("validation_regex"), str):
                try:
                    re.compile(item_dict.get("validation_regex"))
                    verification["check_validation_regex"] = True
                except re.error:
                    pass
            else:
                if not "validation_regex" in item_dict.keys():
                    item_dict["validation_regex"] = ""
                    verification["check_validation_regex"] = True

            # Verify that context_link is defined and a type string
            # Verify that context_link contains the replacment keyword for the value
            if isinstance(item_dict.get("context_link"), str):
                if "<ATTR_VALUE>" in item_dict.get("context_link"):
                    verification["check_context_link"] = True

            # Verify that redirect_warning is defined and type bool
            if isinstance(item_dict.get("redirect_warning"), bool):
                verification["check_redirect_warning"] = True

            verification_result = f"ContextLink '{item.upper()}':"
            for check in verification:
                if verification[check]:
                    verification_result += f" {check} = ok;"
                else:
                    verification_result += f" {check} = FAILED;"

            if "FAILED;" in verification_result:
                verification_results.append(verification_result)
                continue

            # All checks clear. Restructure the output and append to the response.
            context_link_conf = copy.deepcopy(item_dict)
            del context_link_conf["match_fields"]
            for field in item_dict.get("match_fields"):
                response.setdefault(field.lower(), []).append(context_link_conf)

        if len(verification_results) > 0:
            logger.warning(str(verification_results))

        return jsonify(response)
