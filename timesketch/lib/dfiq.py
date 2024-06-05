# Copyright 2023 Google Inc. All rights reserved.
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
"""DFIQ support library."""

import os
import json
import yaml

import networkx as nx


class Component(object):
    """Base class for all DFIQ components.

    Attributes:
        id: The DFIQ ID of the component.
        name: The name of the component.
        description: The description of the component.
        tags: The tags of the component.
        parent_ids: The parent IDs of the component.
        child_ids: The child IDs of the component.
    """

    def __init__(self, dfiq_id, name, description=None, tags=None, parent_ids=None):
        self.id = dfiq_id
        self.name = name
        self.description = description
        self.tags = tags
        self.parent_ids = parent_ids
        self.child_ids = None
        if not self.tags:
            self.tags = ()
        if not self.parent_ids:
            self.parent_ids = ()
        if name:
            self.name = name.rstrip()
        if description:
            if isinstance(description, str):
                self.description = description.rstrip()

    def set_children(self, child_ids):
        self.child_ids = child_ids

    def to_json(self):
        return json.dumps(
            self, default=lambda o: o.__dict__, sort_keys=False, allow_nan=False
        )


class Approach(Component):
    """Class that represents an approach.

    Attributes:
        templates: The templates of the approach.
    """

    def __init__(self, dfiq_id, name, description, tags, view):
        """Initializes the approach."""
        self._parent_ids = [dfiq_id.split(".")[0]]
        self._view = view
        super().__init__(dfiq_id, name, description, tags, self._parent_ids)

    def _get_timesketch_analyses(self):
        """Returns the Timesketch analysis provider of the approach.

        An approach can have multiple processors, each with a Timesketch analysis
        section. This function returns all Timesketch analysis sections regardless of
        the processor.

        Returns:
            A list of Timesketch analysis approaches.
        """
        timesketch_analyses = []
        for processor in self._view.get("processors", []):
            if "timesketch" in processor.get("analysis", {}):
                provider = processor["analysis"]["timesketch"]
                for analysis in provider:
                    timesketch_analyses.append(analysis)
        return timesketch_analyses

    @property
    def search_templates(self):
        """Returns the search templates of the approach.

        Returns:
            A list of Timesketch search templates.
        """
        return [
            analysis
            for analysis in self._get_timesketch_analyses()
            if analysis["type"] == "searchtemplate"
        ]


class Question(Component):
    """Class that represents a question."""

    def __init__(self, dfiq_id, name, description, tags, parent_ids):
        """Initializes the question."""
        super().__init__(dfiq_id, name, description, tags, parent_ids)

    @property
    def approaches(self):
        """Returns the approaches of the question.

        Returns:
            A list of IDs of approaches linked to this question.
        """
        return self.child_ids


class Facet(Component):
    """Class that represents a facet."""

    def __init__(self, dfiq_id, name, description, tags, parent_ids):
        """Initializes the facet."""
        super().__init__(dfiq_id, name, description, tags, parent_ids)

    @property
    def questions(self):
        """Returns the questions of the facet.

        Returns:
            A list of IDs of questions linked to this facet.
        """
        return self.child_ids


class Scenario(Component):
    """Class that represents a scenario."""

    def __init__(self, dfiq_id, name, description, tags):
        """Initializes the scenario."""
        super().__init__(dfiq_id, name, description, tags)

    @property
    def facets(self):
        """Returns the facets of the scenario.

        Returns:
            A list of IDs of facets linked to this scenario.
        """
        return self.child_ids


class DFIQ:
    """Class that represents DFIQ.

    Atributes:
        yaml_data_path: The path to the DFIQ YAML files.
        plural_map: A map of DFIQ types to their plural form.
        components: A dict of DFIQ components.
        graph: A graph of DFIQ components.
    """

    def __init__(self, yaml_data_path):
        """Initializes DFIQ.

        Parameters:
            yaml_data_path: The path to the DFIQ YAML files.
        """
        self.yaml_data_path = yaml_data_path
        self.plural_map = {
            "Scenario": "scenarios",
            "Facet": "facets",
            "Question": "questions",
            "Approach": "approaches",
        }
        self.components = self._load_dfiq_items_from_yaml()
        self.graph = self._build_graph(self.components)

    @property
    def scenarios(self):
        """Returns the scenarios of DFIQ.

        Returns:
            A list of Scenario objects.
        """
        return sorted(
            [c for c in self.components.values() if isinstance(c, Scenario)],
            key=lambda x: x.id,
        )

    @property
    def facets(self):
        """Returns the facets of DFIQ.

        Returns:
            A list of Facet objects.
        """
        return sorted(
            [c for c in self.components.values() if isinstance(c, Facet)],
            key=lambda x: x.id,
        )

    @property
    def questions(self):
        """Returns the questions of DFIQ.

        Returns:
            A list of Question objects.
        """
        return sorted(
            [c for c in self.components.values() if isinstance(c, Question)],
            key=lambda x: x.id,
        )

    @property
    def approaches(self):
        """Returns the approaches of DFIQ.

        Returns:
            A list of Approach objects.
        """
        return sorted(
            [c for c in self.components.values() if isinstance(c, Approach)],
            key=lambda x: x.id,
        )

    @staticmethod
    def _convert_yaml_object_to_dfiq_component(yaml_object):
        """Converts a YAML object to a DFIQ component.

        Returns:
            A DFIQ component if the YAML object is valid, otherwise None.
        """
        if yaml_object["type"] == "scenario":
            return Scenario(
                yaml_object["id"],
                yaml_object["display_name"],
                yaml_object.get("description"),
                yaml_object.get("tags"),
            )
        if yaml_object["type"] == "facet":
            return Facet(
                yaml_object["id"],
                yaml_object["display_name"],
                yaml_object.get("description"),
                yaml_object.get("tags"),
                yaml_object.get("parent_ids"),
            )
        if yaml_object["type"] == "question":
            return Question(
                yaml_object["id"],
                yaml_object["display_name"],
                yaml_object.get("description"),
                yaml_object.get("tags"),
                yaml_object.get("parent_ids"),
            )
        if yaml_object["type"] == "approach":
            return Approach(
                yaml_object["id"],
                yaml_object["display_name"],
                yaml_object.get("description"),
                yaml_object.get("tags"),
                yaml_object.get("view"),
            )
        return None

    def _load_yaml_files_by_type(self, dfiq_type, yaml_data_path=None):
        """Loads YAML files by type.

        Parameters:
            dfiq_type: The type of DFIQ component.
            yaml_data_path: The path to the DFIQ YAML files.

        Returns:
            A dict of DFIQ components.
        """
        if not yaml_data_path:
            yaml_data_path = self.yaml_data_path
        component_dict = {}
        try:
            dfiq_files = os.listdir(
                os.path.join(yaml_data_path, self.plural_map.get(dfiq_type))
            )
        except FileNotFoundError:
            return component_dict
        for dfiq_file in dfiq_files:
            if dfiq_file.endswith("-template.yaml"):
                continue
            with open(
                os.path.join(yaml_data_path, self.plural_map.get(dfiq_type), dfiq_file),
                mode="r",
            ) as file:
                component_from_yaml = yaml.safe_load(file)
                component_dict[component_from_yaml["id"]] = (
                    self._convert_yaml_object_to_dfiq_component(component_from_yaml)
                )
        return component_dict

    def _load_dfiq_items_from_yaml(self):
        """Loads DFIQ items from YAML files.

        Returns:
            A dict of DFIQ components.
        """
        components = {}
        components.update(
            self._load_yaml_files_by_type("Scenario", self.yaml_data_path)
        )
        components.update(self._load_yaml_files_by_type("Facet", self.yaml_data_path))
        components.update(
            self._load_yaml_files_by_type("Question", self.yaml_data_path)
        )
        components.update(
            self._load_yaml_files_by_type("Approach", self.yaml_data_path)
        )
        return components

    def _build_graph(self, components):
        """Builds a graph of DFIQ components.

        Parameters:
            components: A dict of DFIQ components.

        Returns:
            A graph of DFIQ components.
        """
        graph = nx.DiGraph()
        for dfiq_id, content in components.items():
            graph.add_node(dfiq_id)
        for dfiq_id, content in components.items():
            if content.parent_ids:
                for parent_id in content.parent_ids:
                    graph.add_edge(parent_id, dfiq_id)

        for dfiq_id in components.keys():
            children = sorted(list(nx.DiGraph.successors(graph, dfiq_id)))
            components[dfiq_id].set_children(children)

        return graph
