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
"""Timesketch API client library for working with scenarios."""


import logging

from . import error
from . import resource


logger = logging.getLogger("timesketch_api.scenario")


class Scenario(resource.BaseResource):
    """Timesketch scenario object.

    Attributes:
        id: The ID of the scenario.
        api: An instance of TimesketchApi object.
    """

    def __init__(self, sketch_id, scenario_id, uuid, api):
        """Initializes the Scenario object.

        Args:
            scenario_id: Primary key ID of the scenario.
            api: An instance of TiscmesketchApi object.
            uuid: UUID of the scenario.
            sketch_id: ID of a sketch.
        """
        self.id = scenario_id
        self.uuid = uuid
        self.api = api
        self.sketch_id = sketch_id
        self._name = None
        self._display_name = None
        super().__init__(
            api=api, resource_uri=f"sketches/{self.sketch_id}/scenarios/{self.id}/"
        )

    @property
    def name(self):
        """Property that returns the scenario name.

        Returns:
            Scenario name as string.
        """
        if self._name:
            return self._name
        scenario = self.lazyload_data()
        self._name = scenario["objects"][0]["name"]
        return self._name

    @property
    def display_name(self):
        """Property that returns the scenario display name."""
        if self._display_name:
            return self._display_name
        scenario = self.lazyload_data()
        self._display_name = scenario["objects"][0]["display_name"]
        return self._display_name

    @display_name.setter
    def display_name(self, value):
        """Sets the display name of the scenario."""
        resource_url = f"{self.api.api_root}/{self.resource_uri}"
        data = {"scenario_name": value}
        response = self.api.session.post(resource_url, json=data)
        self._data = error.get_response_json(response, logger)
        updated_object = self._data["objects"][0]
        self._display_name = updated_object["display_name"]
        self._name = updated_object["name"]

    def set_status(self, status):
        """Sets the status of the scenario.

        Args:
            status (str): The new status for the scenario.

        Returns:
            bool: True if the status was set successfully.
        """
        resource_url = (
            f"{self.api.api_root}/sketches/{self.sketch_id}/"
            f"scenarios/{self.id}/status/"
        )
        data = {"status": status}
        response = self.api.session.post(resource_url, json=data)
        status = error.check_return_status(response, logger)
        self.lazyload_data(refresh_cache=True)
        return status

    def list_facets(self):
        """Lists all facets for the scenario.

        Returns:
            A list of dictionaries, each representing a facet.
        """
        resource_url = (
            f"{self.api.api_root}/sketches/{self.sketch_id}/"
            f"scenarios/{self.id}/facets/"
        )
        response = self.api.session.get(resource_url)
        response_json = error.get_response_json(response, logger)
        objects = response_json.get("objects", [])
        if objects and isinstance(objects[0], list):
            return objects[0]
        return objects

    @property
    def dfiq_identifier(self):
        """Property that returns the dfiq identifier.

        Returns:
            dfiq identifier as string.
        """
        scenario = self.lazyload_data()
        return scenario["objects"][0]["dfiq_identifier"]

    @property
    def description(self):
        """Property that returns the scenario description.

        Returns:
            Description as string.
        """
        scenario = self.lazyload_data()
        return scenario["objects"][0]["description"]

    def to_dict(self):
        """Returns a dict representation of the scenario."""
        return self.lazyload_data()


class Question(resource.BaseResource):
    """Timesketch question object.

    Attributes:
        id: The ID of the question.
        api: An instance of TimesketchApi object.
    """

    def __init__(self, sketch_id, question_id, uuid, api):
        """Initializes the question object.

        Args:
            question_id: Primary key ID of the scenario.
            api: An instance of TiscmesketchApi object.
            sketch_id: ID of a sketch.
        """
        self.id = question_id
        self.uuid = uuid
        self.api = api
        self.sketch_id = sketch_id
        self._name = None
        self._display_name = None
        self._description = None
        super().__init__(
            api=api, resource_uri=f"sketches/{self.sketch_id}/questions/{self.id}/"
        )

    def _update(self, data):
        """Internal helper to update the question."""
        resource_url = f"{self.api.api_root}/{self.resource_uri}"
        response = self.api.session.post(resource_url, json=data)
        self._data = error.get_response_json(response, logger)
        updated_object = self._data["objects"][0]
        self._name = updated_object["name"]
        self._display_name = updated_object["display_name"]
        self._description = updated_object["description"]

    @property
    def name(self):
        """Property that returns the question name.

        Returns:
            Question name as string.
        """
        if self._name:
            return self._name
        question = self.lazyload_data()
        self._name = question["objects"][0]["name"]
        return self._name

    @name.setter
    def name(self, value):
        """Sets the name of the question."""
        self._update({"name": value})

    @property
    def display_name(self):
        """Property that returns the question display name."""
        if self._display_name:
            return self._display_name
        question = self.lazyload_data()
        self._display_name = question["objects"][0]["display_name"]
        return self._display_name

    @display_name.setter
    def display_name(self, value):
        """Sets the display name of the question."""
        self._update({"display_name": value})

    def set_status(self, status):
        """Sets the status of the question."""
        self._update({"status": status})

    def set_priority(self, priority):
        """Sets the priority of the question."""
        self._update({"priority": priority})

    def list_conclusions(self):
        """Lists all conclusions for the question.

        Returns:
            A list of dictionaries, each representing a conclusion.
        """
        resource_url = (
            f"{self.api.api_root}/sketches/{self.sketch_id}/"
            f"questions/{self.id}/conclusions/"
        )
        response = self.api.session.get(resource_url)
        response_json = error.get_response_json(response, logger)
        objects = response_json.get("objects", [])
        if objects and isinstance(objects[0], list):
            return objects[0]
        return objects

    def add_conclusion(self, conclusion_text):
        """Adds a conclusion to the question for the current user.

        Args:
            conclusion_text (str): The text of the conclusion.

        Returns:
            A dictionary with the API response.
        """
        resource_url = (
            f"{self.api.api_root}/sketches/{self.sketch_id}/"
            f"questions/{self.id}/conclusions/"
        )
        data = {"conclusionText": conclusion_text}
        response = self.api.session.post(resource_url, json=data)
        return error.get_response_json(response, logger)

    @property
    def dfiq_identifier(self):
        """Property that returns the question template id.

        Returns:
            Question DFIQ identifier as string.
        """
        question = self.lazyload_data()
        return question["objects"][0]["dfiq_identifier"]

    @property
    def description(self):
        """Property that returns the question description.

        Returns:
            Question description as string.
        """
        if self._description:
            return self._description
        question = self.lazyload_data()
        self._description = question["objects"][0]["description"]
        return self._description

    @description.setter
    def description(self, value):
        """Sets the description of the question."""
        self._update({"description": value})

    @property
    def approaches(self):
        """Property that returns the question approaches.

        Returns:
            Question approaches as list of dict.
        """
        question = self.lazyload_data()
        return question["objects"][0]["approaches"]

    def to_dict(self):
        """Returns a dict representation of the question."""
        return self.lazyload_data()


def getScenarioTemplateList(api):
    """Retrieves a list of scenario templates.

    Args:
        api: An instance of TimesketchApi object.

    Returns:
        list: A list of Scenario templates.
    """
    resource_url = f"{api.api_root}/scenarios/"
    response = api.session.get(resource_url)
    response_json = error.get_response_json(response, logger)
    scenario_objects = response_json.get("objects", [])
    return scenario_objects


def getQuestionTemplateList(api):
    """Retrieves a list of question templates.

    Args:
        api: An instance of TimesketchApi object.

    Returns:
        list: A list of Question templates.
    """
    resource_url = f"{api.api_root}/questions/"
    response = api.session.get(resource_url)
    response_json = error.get_response_json(response, logger)
    question_objects = response_json.get("objects", [])
    return question_objects
