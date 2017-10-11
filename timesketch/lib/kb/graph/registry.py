# Copyright 2017 Google Inc. All rights reserved.
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
"""Graph entity registry."""

import inspect
from timesketch.lib.kb.graph import entities


class GraphEntityRegistry(object):
    """Registry for graph entities.

    Attributes:
        registry: Dictionary with Neo4j types as keys and entity class as value.
    """

    def __init__(self):
        """Initialize."""
        self.registry = self._create_registry()

    @staticmethod
    def _create_registry():
        """Generate list of graph entity classes.

        Returns:
            Dictionary with Neo4j types as keys and entity class as value.
        """
        registry = {}
        for member in inspect.getmembers(entities, inspect.isclass):
            klass = member[1]
            if klass.__module__ == entities.__name__:
                try:
                    registry[klass.NEO4J_TYPE] = klass
                except AttributeError:
                    pass
        return registry

    def get_entity(self, entity):
        """Get entity class for neo4j entity.

        Args:
            entity: Neo4j node or edge as dictionary.

        Returns:
            Instance of graph entity class.
        """
        try:
            _type = entity[u'labels'][0]
        except KeyError:
            _type = entity[u'type']

        entity_class = self.registry.get(_type, entities.GenericEntity)
        entity_instance = entity_class(entity)
        return entity_instance
