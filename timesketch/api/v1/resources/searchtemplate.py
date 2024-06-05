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
"""SearchTemplate resources for version 1 of the Timesketch API."""
import json

from flask import abort
from flask import request
from flask import jsonify
from flask_restful import Resource
from flask_login import current_user
from flask_login import login_required

import jinja2

from timesketch.api.v1 import resources
from timesketch.api.v1 import utils
from timesketch.lib.definitions import HTTP_STATUS_CODE_BAD_REQUEST
from timesketch.lib.definitions import HTTP_STATUS_CODE_FORBIDDEN
from timesketch.lib.definitions import HTTP_STATUS_CODE_NOT_FOUND
from timesketch.lib.definitions import HTTP_STATUS_CODE_OK

from timesketch.models import db_session
from timesketch.models.sketch import SearchTemplate
from timesketch.models.sketch import Sketch
from timesketch.models.sketch import View


class SearchTemplateResource(resources.ResourceMixin, Resource):
    """Resource to get a search template."""

    @login_required
    def get(self, searchtemplate_id):
        """Handles GET request to the resource.

        Args:
            searchtemplate_id: Primary key for a search template database model

        Returns:
            Search template in JSON (instance of flask.wrappers.Response)
        """
        searchtemplate = SearchTemplate.get_by_id(searchtemplate_id)

        if not searchtemplate:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "Search template was not found")

        return self.to_json(searchtemplate)

    @login_required
    def delete(self, searchtemplate_id):
        """Handles DELETE request to the resource.

        Args:
            searchtemplate_id: Primary key for a search template database model

        Returns:
            HTTP status 200 if successful, otherwise error messages.
        """
        searchtemplate = SearchTemplate.get_by_id(searchtemplate_id)
        if not searchtemplate:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "Search template was not found")

        saved_searches = View.query.filter_by(searchtemplate=searchtemplate)
        for saved_search in saved_searches:
            saved_search.searchtemplate = None

        db_session.delete(searchtemplate)
        db_session.commit()

        return HTTP_STATUS_CODE_OK


class SearchTemplateParseResource(resources.ResourceMixin, Resource):
    """Resource to parse a search template query string using Jinja2 template."""

    @login_required
    def post(self, searchtemplate_id):
        """Parse the query string template with Jinja2.

        This resource take a form with parameters to be parsed with the Jinja2
        parsing engine in order to format the final query string template. Example:
        {
            "username": "user",
            "hostname"" "hostname"
        }

        Args:
            searchtemplate_id: Primary key for a search template database model

        Returns:
            Parsed and sanitized search query string.
        """
        form = request.json or {}
        searchtemplate = SearchTemplate.get_by_id(searchtemplate_id)
        if not searchtemplate:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "Search template was not found")

        try:
            template = jinja2.Template(searchtemplate.query_string)
            query_string = template.render(form)
        except jinja2.exceptions.TemplateSyntaxError as e:
            abort(HTTP_STATUS_CODE_BAD_REQUEST, f"Search template syntax error: {e}")

        escaped_query_string = utils.escape_query_string(query_string)
        return jsonify(
            {"objects": [{"query_string": escaped_query_string}], "meta": {}}
        )


class SearchTemplateListResource(resources.ResourceMixin, Resource):
    """Resource to create a search template."""

    @login_required
    def get(self):
        """Handles GET request to the resource.

        Returns:
            View in JSON (instance of flask.wrappers.Response)
        """
        templates = SearchTemplate.query.all()
        meta = {"collection": []}
        for template in templates:
            saved_searches = View.query.filter_by(searchtemplate=template)
            for saved_search in saved_searches:
                data = {
                    "search_id": saved_search.id,
                    "template_id": template.id,
                    "sketch_id": saved_search.sketch.id,
                }
                meta["collection"].append(data)

        return self.to_json(templates, meta=meta)

    @login_required
    def post(self):
        """Handles POST request to the resource.

        Returns:
            View in JSON (instance of flask.wrappers.Response)
        """
        # Disable adding search templates from the API. This is not supported yet and
        # can only be done by the server admin using the YAML format.
        # TODO: Remove this when support is added for template reviews and tooling.
        abort(
            HTTP_STATUS_CODE_BAD_REQUEST,
            "Unable to save template. Please contact server admin to add using YAML",
        )

        form = request.json
        if not form:
            form = request.data

        search_id = form.get("search_id")
        if not search_id:
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                "Unable to save the searchtemplate, the saved search ID is " "missing.",
            )

        search_obj = View.get_by_id(search_id)
        if not search_obj:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No search found with this ID.")

        templates = SearchTemplate.query.filter_by(
            name=search_obj.name, description=search_obj.description
        ).all()

        if templates:
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                "This search has already been saved as a template.",
            )

        sketch = Sketch.get_with_acl(search_obj.sketch.id)
        if not sketch:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No sketch found with this ID.")

        if not sketch.has_permission(current_user, "read"):
            abort(
                HTTP_STATUS_CODE_FORBIDDEN,
                "User does not have read access controls on sketch.",
            )

        if sketch.get_status.status == "archived":
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST, "Unable to query on an archived sketch."
            )

        # Remove date filter chips from the saved search.
        query_filter_dict = json.loads(search_obj.query_filter)
        chips = []
        for chip in query_filter_dict.get("chips", []):
            chip_type = chip.get("type", "")
            if not chip_type.startswith("datetime"):
                chips.append(chip)

        query_filter_dict["chips"] = chips
        query_filter = json.dumps(query_filter_dict, ensure_ascii=False)

        searchtemplate = SearchTemplate(
            name=search_obj.name,
            description=search_obj.description,
            user=current_user,
            query_string=search_obj.query_string,
            query_filter=query_filter,
            query_dsl=search_obj.query_dsl,
        )

        db_session.add(searchtemplate)
        db_session.commit()

        search_obj.searchtemplate = searchtemplate
        db_session.add(search_obj)
        db_session.commit()

        return self.to_json(searchtemplate)
