# Copyright 2017, Google Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from pycypher.getters import GettersMixin


class CypherAstNode(GettersMixin):
    def __init__(self, id, type, instanceof, children, props, start, end):
        self._id = id
        self._type = type
        self._instanceof = instanceof
        self._children = children
        self._props = props
        self._indirect_props = []
        self._start = start
        self._end = end
        self._role = None
        self._init_props()

    def _init_props(self):
        for k, v in list(self._props.items()):
            if isinstance(v, dict):
                self._add_child_role(**v)
                del self._props[k]
            elif isinstance(v, list) and v and isinstance(v[0], dict):
                for i in v:
                    self._add_child_role(**i)
                del self._props[k]
            elif isinstance(v, list) and not v:
                del self._props[k]

    def _add_child_role(self, id, role):
        for child in self._children:
            if child.id == id:
                child._role = role
                return
        for d in self._all_descendants():
            if d.id == id:
                d._role = role
                self._indirect_props.append(role)
                return
        raise ValueError('Child with id %d not found.' % id)

    def _all_descendants(self):
        for child in self._children:
            yield child
            for d in child._all_descendants():
                yield d

    @property
    def id(self):
        return self._id

    @property
    def type(self):
        return self._type

    def instanceof(self, type):
        return type in self._instanceof

    @property
    def children(self):
        return self._children

    @property
    def props(self):
        return self._props

    @property
    def start(self):
        return self._start

    @property
    def end(self):
        return self._end

    @property
    def role(self):
        return self._role

    def find_nodes(
        self, type=None, role=None, instanceof=None, start=None, end=None
    ):
        """Return an iterable of nodes from subtree of this node (including it)
        matching the criteria given as keyword arguments. Return all nodes from
        the subtree if called without any arguments.
        """
        def pred(node):
            result = True
            if type is not None:
                result = result and node.type == type
            if role is not None:
                result = result and node.role == role
            if instanceof is not None:
                result = result and node.instanceof(instanceof)
            if start is not None:
                result = result and node.start >= start
            if end is not None:
                result = result and node.end <= end
            return result

        if pred(self):
            yield self

        for d in self._all_descendants():
            if pred(d):
                yield d

    def __repr__(self):
        return "<CypherAstNode.%s>" % self.type

    def to_json(self):
        """Return a json-serializable representation made from built-in
        python data types.
        """
        children = [child.to_json() for child in self._children]
        return {
            "type": self._type,
            "instanceof": self._instanceof,
            "children": children,
            "props": self._props,
            "start": self._start,
            "end": self._end,
            "role": self._role,
        }
