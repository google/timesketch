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
"""Ontology for attributes as well as related functions."""
import json

from timesketch.lib.analyzers import interface


def ontology():
    """Return a dict with the ontology definitions."""
    return interface.get_yaml_config("ontology.yaml")


class OntologyInterface:
    """Interface for the ontology class."""

    # Defines the type that this ontology class supports for encoding
    # and decoding.
    TYPE = ""

    @staticmethod
    def encode(data):
        """Returns an encoded string that can be stored in the database.

        Raises:
            ValueError: If the value is not of the correct value, as dictated
                by the ontology type.
        """
        raise NotImplementedError

    @staticmethod
    def decode(data):
        """Returns the proper data structure for this ontology."""
        raise NotImplementedError


class StringOntology(OntologyInterface):
    """Implements the string ontology."""

    TYPE = "str"

    @staticmethod
    def encode(data):
        """Returns the string or the original value back.

        Raises:
            ValueError: If the value is not a string.
        """
        if not isinstance(data, str):
            raise ValueError("Value needs to be a string.")
        return data

    @staticmethod
    def decode(data):
        """Returns back the string."""
        return data


class IntegerOntology(OntologyInterface):
    """Implements the ontology for an integer."""

    TYPE = "int"

    @staticmethod
    def encode(data):
        """Returns an encoded string that can be stored in the database.

        Raises:
            ValueError: If the value is not an integer.
        """
        if not isinstance(data, int):
            raise ValueError("Data is not an integer.")

        return str(data)

    @staticmethod
    def decode(data):
        """Returns back an ineger."""
        return int(data)


class FloatOntology(OntologyInterface):
    """Implements the ontology for floating numbers."""

    TYPE = "float"

    @staticmethod
    def encode(data):
        """Returns an encoded string that can be stored in the database.

        Raises:
            ValueError: If the value is not a float.
        """
        if not isinstance(data, float):
            raise ValueError("Data is not a float.")

        return str(data)

    @staticmethod
    def decode(data):
        """Returns back a float."""
        return float(data)


class BoolOntology(OntologyInterface):
    """Implements the ontology for boolean values."""

    TYPE = "bool"

    @staticmethod
    def encode(data):
        """Returns an encoded string that can be stored in the database."""
        if data:
            return "true"
        return "false"

    @staticmethod
    def decode(data):
        """Returns a bool value from the stored string."""
        return data == "true"


class DictOntology(OntologyInterface):
    """Implements the ontology for dict structures."""

    TYPE = "dict"

    @staticmethod
    def encode(data):
        """Returns an encoded string that can be stored in the database.

        Raises:
            ValueError: If the value is not a dict.
        """
        if not isinstance(data, dict):
            raise ValueError("Data needs to be a dictionary.")

        return json.dumps(data)

    @staticmethod
    def decode(data):
        """Returns a dict object from the stored string in the database."""
        dict_value = json.loads(data)
        if not isinstance(dict_value, dict):
            raise ValueError(
                "Unable to read in the data, it's not stored as a dictionary"
            )
        return dict_value


class OntologyManager:
    """Manager that handles various ontology types."""

    _types = {}

    @classmethod
    def register(cls, ontology_class):
        """Registers an ontology into the manager."""

        cls._types[ontology_class.TYPE] = ontology_class

    @classmethod
    def decode_value(cls, value, type_string):
        """Decodes a value from storage."""
        if type_string not in cls._types:
            raise NotImplementedError("Type [{0:s}] is not yet implemented as a type.")
        return cls._types[type_string].decode(value)

    @classmethod
    def encode_value(cls, value, type_string):
        """Encodes a value for storage."""
        if type_string not in cls._types:
            raise NotImplementedError("Type [{0:s}] is not yet implemented as a type.")
        return cls._types[type_string].encode(value)


ONTOLOGY = ontology()
OntologyManager.register(StringOntology)
OntologyManager.register(IntegerOntology)
OntologyManager.register(FloatOntology)
OntologyManager.register(BoolOntology)
OntologyManager.register(DictOntology)
