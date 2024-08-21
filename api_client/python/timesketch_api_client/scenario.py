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

    def __init__(self, sketch_id, scenario_id, api):
        """Initializes the Scenario object.

        Args:
            scenario_id: Primary key ID of the scenario.
            api: An instance of TiscmesketchApi object.
            sketch_id: ID of a sketch.
        """
        self.id = scenario_id
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
    def scenario_id(self):
        """Property that returns the scenario id.

        Returns:
            Scenario id as integer.
        """
        scenario = self.lazyload_data()
        return scenario["objects"][0]["id"]

    @property
    def dfiq_id(self):
        """Property that returns the dfiq id.

        Returns:
            dfiq id as string.
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


class ScenarioTemplateList(resource.BaseResource):
    """Timesketch scenario template list.

    Attributes:
        api: An instance of TimesketchApi object.
    """

    def __init__(self, api):
        """Initializes the ScenarioList object.

        Args:
            api: An instance of TimesketchApi object.
        """
        self.api = api
        super().__init__(api=api, resource_uri="scenarios/")

    def get(self):
        """
        Retrieves a list of scenario templates.

        Returns:
            list: A list of Scenario tempaltes.
        """
        resource_url = f"{self.api.api_root}/scenarios/"
        response = self.api.session.get(resource_url)
        response_json = error.get_response_json(response, logger)
        scenario_objects = response_json.get("objects", [])
        return scenario_objects


class Question(resource.BaseResource):
    """Timesketch question object.

    Attributes:
        id: The ID of the question.
        api: An instance of TimesketchApi object.
    """

    def __init__(self, sketch_id, question_id, api):
        """Initializes the question object.

        Args:
            question_id: Primary key ID of the scenario.
            api: An instance of TiscmesketchApi object.
            sketch_id: ID of a sketch.
        """
        self.id = question_id
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
    def question_id(self):
        """Property that returns the question id.

        Returns:
            Question id as integer.
        """
        question = self.lazyload_data()
        return question["objects"][0]["id"]

    @property
    def dfiq_id(self):
        """Property that returns the question template id.

        Returns:
            Question ID as string.
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


class QuestionTemplateList(resource.BaseResource):
    """Timesketch question template list.

    Attributes:
        api: An instance of TimesketchApi object.
    """

    def __init__(self, api):
        """Initializes the QuestionList object.

        Args:
            api: An instance of TimesketchApi object.
        """
        self.api = api
        super().__init__(api=api, resource_uri="questions/")

    def get(self):
        """
        Retrieves a list of question templates.

        Returns:
            list: A list of question tempaltes.
        """
        resource_url = f"{self.api.api_root}/questions/"
        response = self.api.session.get(resource_url)
        response_json = error.get_response_json(response, logger)
        scenario_objects = response_json.get("objects", [])
        return scenario_objects
