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

from flask import abort
from flask_restful import Resource
from flask_login import login_required

from timesketch.api.v1 import resources
from timesketch.lib.definitions import HTTP_STATUS_CODE_NOT_FOUND
from timesketch.models.sketch import SearchTemplate


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
        searchtemplate = SearchTemplate.query.get(searchtemplate_id)
        if not searchtemplate:
            abort(HTTP_STATUS_CODE_NOT_FOUND, 'Search template was not found')
        return self.to_json(searchtemplate)


class SearchTemplateListResource(resources.ResourceMixin, Resource):
    """Resource to create a search template."""

    @login_required
    def get(self):
        """Handles GET request to the resource.

        Returns:
            View in JSON (instance of flask.wrappers.Response)
        """
        return self.to_json(SearchTemplate.query.all())
