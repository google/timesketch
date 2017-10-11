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
"""Graph entities."""

# TODO: Add tests.


class BaseEntity(object):
    """Base class for graph entities."""

    def __init__(self, entity):
        """Initialize. Attributes will be filled out from the node or edge
        edge dictionaty.

        Args:
            entity: Neo4j Node or edge dictionary.

        Attributes:
            id: Neo4j node or edge ID.
            type: Neo4j node label or edge type.
        """
        self.id = entity[u'id']
        try:
            self.type = entity[u'labels'][0]
        except KeyError:
            self.type = entity[u'type']
            self.startNode = entity[u'startNode']
            self.endNode = entity[u'endNode']

        properties = entity[u'properties']
        for key in properties:
            setattr(self, key, properties[key])

    @property
    def human_readable(self):
        """Format human readable string for the entity.

        Returns:
            Human readable string.
        """
        return NotImplemented

    def to_dict(self):
        """Create dictionary from the objects attributes.

        Returns:
            Dictionary with object attributes.
        """
        attributes = self.__dict__
        attributes[u'human_readable'] = self.human_readable
        return attributes


class GenericEntity(BaseEntity):
    """Generic entity."""

    def __init__(self, entity):
        super(GenericEntity, self).__init__(entity)

    @property
    def human_readable(self):
        return self.type


class MachineNode(BaseEntity):
    """Machine node entity."""

    NEO4J_TYPE = u'Machine'

    def __init__(self, node):
        super(MachineNode, self).__init__(node)

    @property
    def human_readable(self):
        return self.hostname


class UserNode(BaseEntity):
    """User node entity."""

    NEO4J_TYPE = u'User'

    def __init__(self, node):
        super(UserNode, self).__init__(node)

    @property
    def human_readable(self):
        return self.username


class WindowsServiceNode(BaseEntity):
    """Windows service node entity."""

    NEO4J_TYPE = u'Service'

    def __init__(self, node):
        super(WindowsServiceNode, self).__init__(node)

    @property
    def human_readable(self):
        return self.service_name


class WindowsServiceImagePathNode(BaseEntity):
    """Windows image path node entity."""

    NEO4J_TYPE = u'ServiceImagePath'

    def __init__(self, node):
        super(WindowsServiceImagePathNode, self).__init__(node)

    @property
    def human_readable(self):
        return self.image_path


class AccessEdge(BaseEntity):
    """ACCESS edge entity."""

    NEO4J_TYPE = u'ACCESS'

    def __init__(self, edge):
        super(AccessEdge, self).__init__(edge)

    @property
    def human_readable(self):
        return self.method


class WindowsServiceStartEdge(BaseEntity):
    """Windows service start edge entity."""

    NEO4J_TYPE = u'START'

    def __init__(self, edge):
        super(WindowsServiceStartEdge, self).__init__(edge)

    @property
    def human_readable(self):
        return self.start_type
