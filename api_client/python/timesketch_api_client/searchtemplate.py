# Copyright 2021 Google Inc. All rights reserved.
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
"""Timesketch API search template object."""

import logging

from . import error
from . import resource
from . import search


logger = logging.getLogger("timesketch_api.searchtemplate")


class SearchTemplate(resource.BaseResource):
    """Search template object. TEST e2e"""

    def __init__(self, api):
        """Initialize the search template object."""
        super().__init__(api, "searchtemplates/")
        self._description = ""
        self._name = ""
        self._resource_id = None
        self._search_id = None
        self._sketch_id = None

    @property
    def description(self):
        """Property that returns the template description."""
        if self._description:
            return self._description

        if not self._resource_id:
            logger.error("No resource ID, have you loaded the template yet?")
            raise ValueError("Unable to get a name, not loaded yet.")

        data = self.lazyload_data()
        objects = data.get("objects")
        if not objects:
            return "No description"

        self._description = objects[0].get("description", "N/A")
        return self._description

    def delete(self):
        """Deletes the saved graph from the store."""
        if not self._resource_id:
            raise ValueError(
                "Unable to delete the search template, since the template "
                "does not seem to be saved, which is required."
            )

        resource_url = f"{self.api.api_root}/searchtemplates/{self._resource_id}/"
        response = self.api.session.delete(resource_url)
        return error.check_return_status(response, logger)

    def from_saved(self, template_id, sketch_id=0):
        """Initialize the search template from a saved template, by ID value.

        Args:
            template_id: integer value for the saved search template.
            sketch_id: optional integer value for a sketch ID. If not
                provided, an attempt is made to figure it out.

        Raises:
            ValueError: If issues came up during processing.
        """
        self._resource_id = template_id
        self.resource_uri = f"searchtemplates/{self._resource_id}/"

        if sketch_id:
            self._sketch_id = sketch_id
        else:
            data = self.lazyload_data(refresh_cache=True)
            meta = data.get("meta", {})
            sketch_ids = meta.get("sketch_ids", [])
            if len(sketch_ids) > 1:
                sketch_string = ", ".join(sketch_ids)
                raise ValueError(
                    "Search template has too many attached saved searches, "
                    "please pick one from: {0:s}".format(sketch_string)
                )
            self._sketch_id = sketch_ids[0]

    def from_search_object(self, search_obj):
        """Initialize template from a search object.

        Args:
            search_obj (search.Search): a search object.
        """
        self._search_id = search_obj.id
        self._sketch_id = search_obj.sketch.id

        response = self.api.fetch_resource_data("searchtemplates/")
        meta = response.get("meta", {})
        template_id = 0
        for data in meta.get("collection", []):
            if data.get("search_id") == self._search_id:
                template_id = data.get("template_id", 0)

        if not template_id:
            return

        self._resource_id = template_id
        self.resource_uri = f"searchtemplates/{self._resource_id}/"

    @property
    def id(self):
        """Property that returns back the search template ID."""
        return self._resource_id

    @property
    def name(self):
        """Property that returns the template name."""
        if self._name:
            return self._name

        if not self._resource_id:
            logger.error("No resource ID, have you loaded the template yet?")
            raise ValueError("Unable to get a name, not loaded yet.")

        data = self.lazyload_data()
        objects = data.get("objects")
        if not objects:
            return "No name"

        self._name = objects[0].get("name", "N/A")
        return self._name

    def set_sketch(self, sketch=None, sketch_id=None):
        """Set the sketch for the search template.

        Args:
            sketch (sketch.Sketch): an optional sketch object to use as the
                sketch object for the search template.
            sketch_id (int): an optional sketch ID to use as the sketch ID
                for the search template.

        Raises:
            ValueError: If neither a sketch nor a sketch ID is set.
        """
        if not sketch and not sketch_id:
            raise ValueError("Either sketch or sketch ID needs to be set.")

        if sketch:
            self._sketch_id = sketch
        elif isinstance(sketch_id, int):
            self._sketch_id = sketch_id
        else:
            raise ValueError(
                "Sketch needs to be set, or an integer value for a sketch ID."
            )

    def save(self):
        """Save the search template."""
        if self._resource_id:
            raise ValueError(
                "The template has already been saved, ATM updates to an "
                "existing template are not yet supported."
            )

        if not self._search_id:
            raise ValueError(
                "Unable to save the search template since the identification "
                "value of the saved search is not known. The object needs "
                "to be initialized from a previously saved search."
            )

        data = {
            "search_id": self._search_id,
        }
        resource_url = f"{self.api.api_root}/searchtemplates/"
        response = self.api.session.post(resource_url, json=data)

        status = error.check_return_status(response, logger)
        if not status:
            error.error_message(
                response, "Unable to save search as a template", error=RuntimeError
            )

        response_json = error.get_response_json(response, logger)
        template_dict = response_json.get("objects", [{}])[0]

        self._resource_id = template_dict.get("id", 0)
        self.resource_uri = f"searchtemplates/{self._resource_id}/"
        return f"Saved search as a template to ID: {self.id}"

    def to_search(self):
        """Returns a search object from a template."""
        if not self._resource_id:
            raise ValueError(
                "Unable to get a search object unless it is tied to a template."
            )

        if not self._sketch_id:
            raise ValueError(
                "Unable to get a search object unless it is tied to a sketch."
            )

        data = self.lazyload_data(refresh_cache=True)
        objects = data.get("objects")
        if not objects:
            raise ValueError(
                "Unable to get search object, issue with retrieving template data."
            )

        template_dict = objects[0]
        sketch = self.api.get_sketch(self._sketch_id)

        search_obj = search.Search(sketch=sketch)
        search_obj.from_manual(
            query_string=template_dict.get("query_string"),
            query_dsl=template_dict.get("query_dsl"),
            query_filter=template_dict.get("query_filter"),
        )
        search_obj.name = template_dict.get("name", "No Name")
        search_obj.description = template_dict.get("description", "No Description")
        return search_obj
