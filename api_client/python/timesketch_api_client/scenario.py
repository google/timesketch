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
from typing import Dict, List, Any, Optional

from . import error
from . import resource


logger = logging.getLogger("timesketch_api.scenario")


class Scenario(resource.BaseResource):
    """Timesketch scenario object.

    A Scenario represents an investigative playbook within a Timesketch sketch,
    often derived from a DFIQ template. It contains facets and questions to
    guide an investigation.

    Attributes:
        id: The ID of the scenario.
        uuid: The UUID of the scenario.
        sketch_id: The ID of the sketch this scenario belongs to.
        api: An instance of TimesketchApi object.
    """

    def __init__(self, sketch_id, scenario_id, uuid, api):
        """Initializes the Scenario object.

        Args:
            sketch_id: ID of a sketch.
            scenario_id: Primary key ID of the scenario.
            uuid: UUID of the scenario.
            api: An instance of the TimesketchApi object.
        """
        self.id = scenario_id
        self.uuid = uuid
        self.api = api
        self.sketch_id = sketch_id
        self._name = None
        self._display_name = None
        self._data = None
        super().__init__(
            api=api, resource_uri=f"sketches/{self.sketch_id}/scenarios/{self.id}/"
        )

    @property
    def name(self) -> str:
        """Property that returns the scenario name.

        Returns:
            Scenario name as string.
        """
        if self._name:
            return self._name
        scenario = self.lazyload_data()
        self._name = scenario["objects"][0].get("name", "")
        return self._name

    @property
    def display_name(self) -> str:
        """Property that returns the scenario display name.

        Returns:
            Scenario display name as string.
        """
        if self._display_name:
            return self._display_name
        scenario = self.lazyload_data()
        # Fallback to name if display_name is not present.
        self._display_name = scenario["objects"][0].get(
            "display_name", scenario["objects"][0].get("name", "")
        )
        return self._display_name

    def set_display_name(self, display_name: str) -> None:
        """Sets the display name of the scenario.

        This performs an API call to update the scenario on the server.

        Args:
            display_name: The new display name for the scenario.

        Raises:
            RuntimeError: If the API request fails to update the scenario.
        """
        resource_url = f"{self.api.api_root}/{self.resource_uri}"
        data = {"scenario_name": display_name}
        response = self.api.session.post(resource_url, json=data)

        try:
            response_json = error.get_response_json(response, logger)
            self._data = response_json
            updated_object = self._data["objects"][0]
            self._display_name = updated_object.get("display_name")
        except (RuntimeError, ValueError) as e:
            logger.error(f"Failed to set display name for scenario {self.id}: {e}")
            raise

    def list_facets(self) -> List[Dict[str, Any]]:
        """Lists all facets for the scenario.

        Returns:
            list[dict]: A list of dictionaries, each representing a facet.
        """
        resource_url = (
            f"{self.api.api_root}/sketches/{self.sketch_id}/"
            f"scenarios/{self.id}/facets/"
        )
        response = self.api.session.get(resource_url)
        response_json = error.get_response_json(response, logger)
        objects = response_json.get("objects", [])
        # Handle the case where the API returns a nested list
        if objects and isinstance(objects[0], list):
            return objects[0]
        return objects

    @property
    def dfiq_identifier(self) -> str:
        """Property that returns the dfiq identifier.

        Returns:
            dfiq identifier as string.
        """
        scenario = self.lazyload_data()
        return scenario["objects"][0].get("dfiq_identifier", "")

    @property
    def description(self) -> str:
        """Property that returns the scenario description.

        Returns:
            Description as string.
        """
        scenario = self.lazyload_data()
        return scenario["objects"][0].get("description", "")

    def to_dict(self) -> Dict[str, Any]:
        """Returns a dict representation of the scenario."""
        return self.lazyload_data()


class Question(resource.BaseResource):
    """Timesketch question object.

    A Question represents a single investigative question within a sketch,
    which can be part of a Scenario, Facet or standalone.

    Attributes:
        id: The ID of the question.
        uuid: The UUID of the question.
        sketch_id: The ID of the sketch this question belongs to.
        api: An instance of TimesketchApi object.
    """

    def __init__(self, sketch_id, question_id, uuid, api):
        """Initializes the Question object.

        Args:
            sketch_id: ID of a sketch.
            question_id: Primary key ID of the question.
            uuid: UUID of the question.
            api: An instance of the TimesketchApi object.
        """
        self.id = question_id
        self.uuid = uuid
        self.api = api
        self.sketch_id = sketch_id
        self._name = None
        self._display_name = None
        self._description = None
        self._data = None
        super().__init__(
            api=api, resource_uri=f"sketches/{self.sketch_id}/questions/{self.id}/"
        )

    def _update(self, data: Dict[str, Any]) -> None:
        """Internal helper to send updates to the Question API endpoint.

        On success, this method updates the local cache (_data, _name, etc.)
        with the response from the server.

        Args:
            data: A dictionary with the fields to update.

        Raises:
            RuntimeError: If the API request fails.
        """
        resource_url = f"{self.api.api_root}/{self.resource_uri}"
        response = self.api.session.post(resource_url, json=data)

        try:
            response_json = error.get_response_json(response, logger)
            self._data = response_json
            updated_object = self._data["objects"][0]
            self._name = updated_object.get("name", self._name)
            self._display_name = updated_object.get("display_name", self._display_name)
            self._description = updated_object.get("description", self._description)
        except (RuntimeError, ValueError) as e:
            logger.error(f"Failed to update question {self.id}: {e}")
            raise

    def add_attribute(
        self,
        name: str,
        value: str,
        ontology: Optional[str] = None,
        description: Optional[str] = None,
    ) -> None:
        """Adds a single attribute to the question.

        Args:
            name: The name of the attribute.
            value: The value of the attribute.
            ontology: Optional ontology for the attribute (e.g., 'text').
            description: Optional description for the attribute.
        """
        attribute = {
            "name": name,
            "value": value,
            "ontology": ontology,
            "description": description,
        }
        self._update({"attributes": [attribute]})

    @property
    def name(self) -> str:
        """Property that returns the question name.

        Returns:
            Question name as string.
        """
        if self._name:
            return self._name
        question = self.lazyload_data()
        self._name = question["objects"][0].get("name", "")
        return self._name

    def set_name(self, name: str) -> None:
        """Sets the name of the question.

        Args:
            name: The new name for the question.

        Raises:
            RuntimeError: If the API request fails.
        """
        self._update({"name": name})

    @property
    def display_name(self) -> str:
        """Property that returns the question display name."""
        if self._display_name:
            return self._display_name
        question = self.lazyload_data()
        self._display_name = question["objects"][0].get("display_name", "")
        return self._display_name

    def set_display_name(self, display_name: str) -> None:
        """Sets the display name of the question.

        Args:
            display_name: The new display name for the question.

        Raises:
            RuntimeError: If the API request fails.
        """
        self._update({"display_name": display_name})

    def set_status(self, status: str) -> None:
        """Sets the status of the question.

        Args:
            status: The new status (e.g., 'new', 'verified').

        Raises:
            RuntimeError: If the API request fails.
        """
        self._update({"status": status})

    def set_priority(self, priority: str) -> None:
        """Sets the priority of the question.

        Args:
            priority: The new priority (e.g., '__ts_priority_high').

        Raises:
            RuntimeError: If the API request fails.
        """
        self._update({"priority": priority})

    def list_conclusions(self) -> List[Dict[str, Any]]:
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
        # Handle the case where the API returns a nested list
        if objects and isinstance(objects[0], list):
            return objects[0]
        return objects

    def add_conclusion(
        self, conclusion_text: str, automated: bool = False
    ) -> Dict[str, Any]:
        """Adds a conclusion to the question.

        If `automated` is False (default), it adds or updates the conclusion
        for the current user. If `automated` is True, it adds a new conclusion
        not associated with a user.

        Args:
            conclusion_text: The text of the conclusion.
            automated: Whether the conclusion is automated.

        Returns:
            A dictionary with the API response.
        """
        resource_url = (
            f"{self.api.api_root}/sketches/{self.sketch_id}/"
            f"questions/{self.id}/conclusions/"
        )
        data = {"conclusionText": conclusion_text, "automated": automated}
        response = self.api.session.post(resource_url, json=data)
        return error.get_response_json(response, logger)

    @property
    def dfiq_identifier(self) -> str:
        """Property that returns the question template id.

        Returns:
            Question DFIQ identifier as string.
        """
        question = self.lazyload_data()
        return question["objects"][0].get("dfiq_identifier", "")

    @property
    def description(self) -> str:
        """Property that returns the question description.

        Returns:
            Question description as string.
        """
        if self._description:
            return self._description
        question = self.lazyload_data()
        self._description = question["objects"][0].get("description", "")
        return self._description

    def set_description(self, description: str) -> None:
        """Sets the description of the question.

        Args:
            description: The new description for the question.

        Raises:
            RuntimeError: If the API request fails.
        """
        self._update({"description": description})

    @property
    def approaches(self) -> List[Dict[str, Any]]:
        """Property that returns the question approaches.

        Returns:
            Question approaches as list of dict.
        """
        question = self.lazyload_data()
        return question["objects"][0].get("approaches", [])

    def to_dict(self) -> Dict[str, Any]:
        """Returns a dict representation of the question."""
        return self.lazyload_data()


def getScenarioTemplateList(api) -> List[Dict[str, Any]]:
    """Retrieves a list of all available scenario templates.

    Args:
        api: An instance of the TimesketchApi object.

    Returns:
        A list of dictionaries, where each represents a Scenario template.
    """
    resource_url = f"{api.api_root}/scenarios/"
    response = api.session.get(resource_url)
    response_json = error.get_response_json(response, logger)
    scenario_objects = response_json.get("objects", [])
    return scenario_objects


def getQuestionTemplateList(api) -> List[Dict[str, Any]]:
    """Retrieves a list of all available question templates.

    Args:
        api: An instance of the TimesketchApi object.

    Returns:
        A list of dictionaries, where each represents a Question template.
    """
    resource_url = f"{api.api_root}/questions/"
    response = api.session.get(resource_url)
    response_json = error.get_response_json(response, logger)
    question_objects = response_json.get("objects", [])
    return question_objects
