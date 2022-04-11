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
"""This file contains a class for managing graphs."""


class GraphManager:
    """The graph manager."""

    _class_registry = {}

    @classmethod
    def get_graphs(cls):
        """Retrieves the registered graphs.

        Yields:
            tuple: containing:
                str: the uniquely identifying name of the graph
                type: the graph class.
        """
        for graph_name, graph_class in iter(cls._class_registry.items()):
            yield graph_name, graph_class

    @classmethod
    def get_graph(cls, graph_name):
        """Retrieves a class object of a specific graph.

        Args:
            graph_name (str): name of the graph to retrieve.

        Returns:
            Instance of Graph class object.

        Raises:
            KeyError: if the graph is not registered.
        """
        try:
            graph_class = cls._class_registry[graph_name.lower()]
        except KeyError:
            raise KeyError(f"No such graph type: {graph_name.lower()}")
        return graph_class

    @classmethod
    def register_graph(cls, graph_class):
        """Registers an graph class.

        The graph classes are identified by their lower case name.

        Args:
            graph_class (type): the graph class to register.

        Raises:
            KeyError: if class is already set for the corresponding name.
        """
        graph_name = graph_class.NAME.lower()
        if graph_name in cls._class_registry:
            raise KeyError(f"Class already set for name: {graph_class.NAME}.")
        cls._class_registry[graph_name] = graph_class

    @classmethod
    def clear_registration(cls):
        """Clears all graph registrations."""
        cls._class_registry = {}
