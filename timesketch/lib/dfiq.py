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
import logging

import yaml
import networkx as nx
from packaging.version import Version

logger = logging.getLogger("timesketch.lib.dfiq")


class Component:
    """Base class for all DFIQ components.

    Attributes:
        id: The DFIQ ID of the component.
        name: The name of the component.
        description: The description of the component.
        tags: The tags of the component.
        parent_ids: The parent IDs of the component.
        child_ids: The child IDs of the component.
    """

    def __init__(
        self,
        component_uuid,
        name,
        dfiq_id=None,
        description=None,
        tags=None,
        parent_ids=None,
    ):
        """Initializes the component.

        Args:
            component_uuid (str): The UUID of the component.
            name (str): The name of the component.
            dfiq_id (str): The DFIQ ID of the component.
            description (str): The description of the component.
            tags (list): The tags of the component.
            parent_ids (list): The parent IDs of the component.
        """
        self.id = dfiq_id
        self.uuid = component_uuid
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
        """Sets the children of the component.

        Args:
            child_ids (list): The child IDs of the component.
        """
        self.child_ids = child_ids

    def to_json(self):
        """Returns the component as a JSON string.

        Returns:
            str: The component as a JSON string.
        """
        return json.dumps(
            self, default=lambda o: o.__dict__, sort_keys=False, allow_nan=False
        )


class ApproachTemplate:
    """Class that represents an approach.

    Attributes:
        search_templates: The search templates of the approach.
    """

    def __init__(self, approach):
        """Initializes the approach.

        Args:
            approach (dict): A dictionary representing the approach.
        """
        self.name = approach["name"]
        self.description = approach.get("description")
        self.notes = approach.get("notes")
        self.references = approach.get("references")
        self.steps = approach.get("steps")
        self.tags = approach.get("tags")

    def _get_timesketch_analyses(self):
        """Returns the Timesketch analysis provider of the approach.

        An approach can have multiple processors, each with a Timesketch analysis
        section. This function returns all Timesketch analysis sections regardless of
        the processor.

        Returns:
            A list of Timesketch analysis approaches.
        """
        analysis_types = ["timesketch-searchtemplate", "opensearch-query"]
        return [
            step
            for step in self.steps
            if step["stage"] == "analysis" and step["type"] in analysis_types
        ]

    def to_json(self):
        """Returns the approach as a JSON string.

        Returns:
            str: The approach as a JSON string.
        """
        return json.dumps(
            self, default=lambda o: o.__dict__, sort_keys=False, allow_nan=False
        )

    @property
    def search_templates(self):
        """Returns the search templates of the approach.

        Returns:
            A list of Timesketch search templates.
        """
        return [
            analysis
            for analysis in self._get_timesketch_analyses()
            if analysis["type"] == "timesketch-searchtemplate"
        ]


class QuestionTemplate(Component):
    """Class that represents a question."""

    def __init__(
        self,
        component_uuid,
        name,
        dfiq_id=None,
        description=None,
        tags=None,
        parent_ids=None,
        approaches=None,
    ):
        """Initializes the question.

        Args:
            component_uuid (str): The UUID of the component.
            name (str): The name of the question.
            dfiq_id (str): The DFIQ ID of the question.
            description (str): The description of the question.
            tags (list): The tags of the question.
            parent_ids (list): The parent IDs of the question.
            approaches (list): A list of approaches for the question.
        """
        self.approaches = []
        if approaches:
            self.approaches = [ApproachTemplate(approach) for approach in approaches]
        super().__init__(
            component_uuid=component_uuid,
            name=name,
            dfiq_id=dfiq_id,
            description=description,
            tags=tags,
            parent_ids=parent_ids,
        )


class FacetTemplate(Component):
    """Class that represents a facet."""

    def __init__(
        self,
        component_uuid,
        name,
        dfiq_id=None,
        description=None,
        tags=None,
        parent_ids=None,
    ):
        """Initializes the facet.

        Args:
            component_uuid (str): The UUID of the component.
            name (str): The name of the facet.
            dfiq_id (str): The DFIQ ID of the facet.
            description (str): The description of the facet.
            tags (list): The tags of the facet.
            parent_ids (list): The parent IDs of the facet.
        """
        super().__init__(
            component_uuid=component_uuid,
            name=name,
            dfiq_id=dfiq_id,
            description=description,
            tags=tags,
            parent_ids=parent_ids,
        )
        self.questions = []


class ScenarioTemplate(Component):
    """Class that represents a scenario."""

    def __init__(self, component_uuid, name, dfiq_id=None, description=None, tags=None):
        """Initializes the scenario.

        Args:
            component_uuid (str): The UUID of the component.
            name (str): The name of the scenario.
            dfiq_id (str): The DFIQ ID of the scenario.
            description (str): The description of the scenario.
            tags (list): The tags of the scenario.
        """
        # A scenario is a root node, so it never has parents.
        # We explicitly pass parent_ids=None.
        super().__init__(
            component_uuid=component_uuid,
            name=name,
            dfiq_id=dfiq_id,
            description=description,
            tags=tags,
            parent_ids=None,
        )
        self.facets = []
        self.questions = []


class DFIQCatalog:
    """Class that represents DFIQ.

    Attributes:
        yaml_data_path: The path to the DFIQ YAML files.
        plural_map: A map of DFIQ types to their plural form.
        components: A dict of DFIQ components keyed by UUID.
        id_to_uuid_map: A mapping from DFIQ ID (e.g., "S1001") to UUID.
        graph: A graph of DFIQ components.
    """

    def __init__(self, yaml_data_path=None):
        """Initializes DFIQ.

        Args:
            yaml_data_path (str): The path to the DFIQ YAML files.
        """
        self.min_supported_DFIQ_version = "1.1.0"
        self.yaml_data_path = yaml_data_path
        self.plural_map = {
            "Scenario": "scenarios",
            "Facet": "facets",
            "Question": "questions",
        }
        self.components = {}
        self.id_to_uuid_map = {}
        self.graph = None

        if self.yaml_data_path:
            yaml_strings = self._read_dfiq_from_yaml_files()
            components, id_to_uuid_map = self._parse_yaml_content(yaml_strings)
            self._populate(components, id_to_uuid_map)

    def _populate(self, components, id_to_uuid_map):
        """Populates the instance from parsed YAML components."""
        self.components = components
        self.id_to_uuid_map = id_to_uuid_map
        if self.components:
            self.graph = self._build_graph()

    @property
    def scenarios(self):
        """Returns the scenarios of DFIQ.

        Returns:
            A list of Scenario objects.
        """
        return sorted(
            [c for c in self.components.values() if isinstance(c, ScenarioTemplate)],
            key=lambda x: x.uuid,
        )

    @property
    def facets(self):
        """Returns the facets of DFIQ.

        Returns:
            A list of Facet objects.
        """
        return sorted(
            [c for c in self.components.values() if isinstance(c, FacetTemplate)],
            key=lambda x: x.uuid,
        )

    @property
    def questions(self):
        """Returns the questions of DFIQ.

        Returns:
            A list of Question objects.
        """
        return sorted(
            [c for c in self.components.values() if isinstance(c, QuestionTemplate)],
            key=lambda x: x.uuid,
        )

    def get_by_id(self, dfiq_id: str):
        """Returns a DFIQ component by its human-readable ID.

        Returns:
            The DFIQCatalog component or None if not found.
        """
        component_uuid = self.id_to_uuid_map.get(dfiq_id)
        if component_uuid:
            return self.components.get(component_uuid)
        return None

    def get_by_uuid(self, uuid_str: str):
        """Returns a DFIQ component by its UUID.

        Returns:
            The DFIQCatalog component or None if not found.
        """
        return self.components.get(uuid_str)

    @classmethod
    def from_yaml_list(cls, yaml_strings: list):
        """Creates a DFIQ instance from a list of in-memory YAML strings.

        This is used for loading DFIQ data from sources other than the
        filesystem, such as a remote API.

        Args:
            yaml_strings (list[str]): A list of strings, where each string is
                the content of a DFIQ YAML file.

        Returns:
            DFIQ: An instance of the DFIQ class populated with the parsed
                components.
        """
        dfiq_instance = cls()
        components, id_to_uuid_map = dfiq_instance._parse_yaml_content(yaml_strings)
        dfiq_instance._populate(components, id_to_uuid_map)
        return dfiq_instance

    @staticmethod
    def _convert_yaml_object_to_dfiq_component(yaml_object):
        """Converts a YAML object to a DFIQ component.

        If the YAML object is missing a UUID, an error is logged and the object
        is skipped.

        Args:
            yaml_object (dict): A dictionary parsed from a DFIQ YAML file.

        Returns:
            An instance of a Component subclass (ScenarioTemplate,
            FacetTemplate, or QuestionTemplate), or None if the object type is
            unknown or a schema error occurs.
        """
        component_uuid = yaml_object.get("uuid")
        if not component_uuid:
            logger.error(
                "DFIQ object '%s' ('%s') is missing a UUID. "
                "Skipping import. Please add a permanent UUID to the source file.",
                yaml_object.get("id", "N/A"),
                yaml_object.get("name", "N/A"),
            )
            return None

        try:
            if yaml_object["type"] == "scenario":
                return ScenarioTemplate(
                    dfiq_id=yaml_object.get("id"),
                    component_uuid=component_uuid,
                    name=yaml_object["name"],
                    description=yaml_object.get("description"),
                    tags=yaml_object.get("tags"),
                )
            if yaml_object["type"] == "facet":
                return FacetTemplate(
                    dfiq_id=yaml_object.get("id"),
                    component_uuid=component_uuid,
                    name=yaml_object["name"],
                    description=yaml_object.get("description"),
                    tags=yaml_object.get("tags"),
                    parent_ids=yaml_object.get("parent_ids"),
                )
            if yaml_object["type"] == "question":
                return QuestionTemplate(
                    dfiq_id=yaml_object.get("id"),
                    component_uuid=component_uuid,
                    name=yaml_object["name"],
                    description=yaml_object.get("description"),
                    tags=yaml_object.get("tags"),
                    parent_ids=yaml_object.get("parent_ids"),
                    approaches=yaml_object.get("approaches"),
                )
        except KeyError as e:
            logger.error(
                "DFIQ: Loaded YAML object has a schema error! KeyError: %s", str(e)
            )
            return None
        return None

    def _parse_yaml_content(self, yaml_content_list):
        """Parses a list of YAML file contents into DFIQ components.

        It validates the DFIQ version and handles YAML parsing errors.

        Args:
            yaml_content_list (list[str]): A list of strings, where each string
                is the content of a DFIQ YAML file.

        Returns:
            tuple[dict, dict]: A tuple containing:
                - A dictionary of DFIQ components keyed by their UUID.
                - A dictionary mapping DFIQ IDs to UUIDs.
        """
        component_dict = {}
        id_to_uuid_map = {}
        for yaml_content in yaml_content_list:
            try:
                component_from_yaml = yaml.safe_load(yaml_content)
                if not isinstance(component_from_yaml, dict):
                    continue
            except yaml.YAMLError as e:
                logger.error("Failed to parse DFIQ YAML content: %s", str(e))
                continue

            try:
                if Version(str(component_from_yaml.get("dfiq_version"))) < Version(
                    self.min_supported_DFIQ_version
                ):
                    continue
            except (KeyError, TypeError):
                continue

            dfiq_object = self._convert_yaml_object_to_dfiq_component(
                component_from_yaml
            )
            if dfiq_object:
                component_dict[dfiq_object.uuid] = dfiq_object
                # Only add to the map if an ID exists.
                if dfiq_object.id:
                    id_to_uuid_map[dfiq_object.id] = dfiq_object.uuid

        return component_dict, id_to_uuid_map

    def _read_dfiq_from_yaml_files(self):
        """Reads DFIQ items from YAML files located in the configured path.

        It reads all .yaml files from subdirectories corresponding to DFIQ
        types (scenarios, facets, questions).

        Returns:
            A list of strings, where each string is the content of a DFIQ YAML file.
        """
        if not self.yaml_data_path:
            return []

        yaml_content_list = []
        for dfiq_type in self.plural_map.values():
            try:
                type_path = os.path.join(self.yaml_data_path, dfiq_type)
                if not os.path.isdir(type_path):
                    continue
                for dfiq_file in os.listdir(type_path):
                    if not dfiq_file.endswith(".yaml"):
                        continue
                    with open(
                        os.path.join(type_path, dfiq_file), "r", encoding="utf-8"
                    ) as file:
                        yaml_content_list.append(file.read())
            except FileNotFoundError:
                continue

        return yaml_content_list

    def _build_graph(self):
        """Builds a directed graph of DFIQ components and populates children.

        This method uses the parent_ids of each component to construct the
        relationship graph. It then traverses the graph to populate the
        `child_ids`, `facets`, and `questions` attributes for each relevant
        component.

        Returns:
            networkx.DiGraph: A directed graph representing the DFIQ structure.
        """
        graph = nx.DiGraph()

        for component_uuid in self.components:
            graph.add_node(component_uuid)

        for component_uuid, component in self.components.items():
            if component.parent_ids:
                for parent_id in component.parent_ids:
                    parent_uuid = self.id_to_uuid_map.get(parent_id)
                    if parent_uuid:
                        graph.add_edge(parent_uuid, component_uuid)
                    else:
                        logger.debug(
                            "Could not find parent UUID for DFIQ ID '%s' "
                            "referenced by '%s' ('%s'). Skipping edge.",
                            parent_id,
                            component.id,
                            component.name,
                        )

        for component_uuid, content in self.components.items():
            children_uuids = sorted(list(nx.DiGraph.successors(graph, component_uuid)))
            content.set_children(children_uuids)  # Keep the raw list of child UUIDs

            # Now, populate the specific typed lists (facets, questions)
            if isinstance(content, ScenarioTemplate):
                for child_uuid in children_uuids:
                    child_obj = self.get_by_uuid(child_uuid)
                    if isinstance(child_obj, FacetTemplate):
                        content.facets.append(child_uuid)
                    elif isinstance(child_obj, QuestionTemplate):
                        content.questions.append(child_uuid)
                    else:
                        logger.warning(
                            "DFIQ validation error: Scenario '%s' has an invalid "
                            "child of type '%s' ('%s'). Scenarios can only have "
                            "Facets or Questions as children.",
                            content.name,
                            type(child_obj).__name__,
                            child_obj.name,
                        )

            elif isinstance(content, FacetTemplate):
                for child_uuid in children_uuids:
                    child_obj = self.get_by_uuid(child_uuid)
                    if isinstance(child_obj, QuestionTemplate):
                        content.questions.append(child_uuid)
                    else:
                        logger.warning(
                            "DFIQ validation error: Facet '%s' has an invalid "
                            "child of type '%s' ('%s'). Facets can only have "
                            "Questions as children.",
                            content.name,
                            type(child_obj).__name__,
                            child_obj.name,
                        )

        return graph
