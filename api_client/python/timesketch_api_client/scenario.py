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
        super().__init__(
            api=api, resource_uri=f"sketches/{self.sketch_id}/scenarios/{self.id}/"
        )

    @property
    def name(self):
        """Property that returns the scenario name.

        Returns:
            Scenario name as string.
        """
        scenario = self.lazyload_data()
        return scenario["objects"][0]["name"]

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
        super().__init__(
            api=api, resource_uri=f"sketches/{self.sketch_id}/questions/{self.id}/"
        )

    @property
    def name(self):
        """Property that returns the question name.

        Returns:
            Question name as string.
        """
        question = self.lazyload_data()
        return question["objects"][0]["name"]

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
        question = self.lazyload_data()
        return question["objects"][0]["description"]

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
        list: A list of Scenario tempaltes.
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
        list: A list of Question tempaltes.
    """
    resource_url = f"{api.api_root}/questions/"
    response = api.session.get(resource_url)
    response_json = error.get_response_json(response, logger)
    question_objects = response_json.get("objects", [])
    return question_objects
