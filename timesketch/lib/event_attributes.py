# Copyright 2022 Google Inc. All rights reserved.
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
"""Timesketch Event Attribute."""

import logging
from numbers import Complex
from timesketch.lib.analyzers import interface

logger = logging.getLogger("timesketch.lib.attributes")

BASE_TYPES = {
    'string': str,
    'float': float
}

ONTOLOGY_DESCRIPTION = interface.get_yaml_config('event_attribute_ontology.yaml')
ONTOLOGY_DESCRIPTION.update(BASE_TYPES)


class Attribute:

    def __init__(self, value=None):
        self.value = value

    def serialize(self):
        members = ONTOLOGY_DESCRIPTION[self.type]
        serialized = {}

        # For simple types (e.g. strings or floats)
        # we want to return a dict encoding the type and the value.
        if isinstance(members, str) and members in BASE_TYPES:
            _type = BASE_TYPES[members]
            return {
                '__' + self.type: {
                    'type': self.type,
                    'value': _type(self.value)
                },
            }

        # For compound types, cycle through all members defined
        if isinstance(members, dict):
            for attribute, attr_type in members.items():
                value = getattr(self, attribute)
                if attr_type in BASE_TYPES:
                    serialized[attribute] = value
                else:
                    serialized[attribute] = value.serialize()

            serialized['type'] = self.type
            return {
                "__" + self.type : serialized,
            }

    @classmethod
    def load(cls, _json):

        prefix = "__" + cls.type
        if not prefix in _json:
            raise ValueError(f'The JSON object passed is not representing a {cls.type}: {_json}')

        obj = cls()
        contents = _json[prefix]
        for attribute, value in contents.items():
            if isinstance(value, dict):  # we're dealing with a complex type
                object_type = list(value.values())[0]['type']
                value = ONTOLOGY_CLASSES[object_type].load(value)
            setattr(obj, attribute, value)
        return obj


# Compound attributes

class GeoIP(Attribute):
    type = 'geoip'
    def __init__(self, ip_address_latitude=None, ip_address_longitude=None):
        self.ip_address_latitude = ip_address_latitude
        self.ip_address_longitude = ip_address_longitude

class BrowserSearch(Attribute):
    type = 'browser_search'
    def __init__(self, search_string=None, search_engine=None):
        self.search_string = search_string
        self.search_engine = search_engine


# Leaf attributes

class Hostname(Attribute):
    type = 'hostname'

class IPAddress(Attribute):
    type = 'ip_address'

class URL(Attribute):
    type = 'url'

class Email(Attribute):
    type = 'email'


ONTOLOGY_CLASSES = {
    cls.type: cls for cls in [
        GeoIP,
        BrowserSearch,
        Hostname,
        IPAddress,
        URL,
        Email
    ]
}
