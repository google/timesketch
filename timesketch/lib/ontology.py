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

import yaml

from timesketch.lib.analyzers import interface


def ontology():
    """Return a dict with the ontology definitions."""
    return interface.get_yaml_config('ontology.yaml')


def cast_variable(value, cast_as_str):
    """Cast a variable and return it.

    Args:
      value (str): Value as a string.
      cast_as_str (str): The type to cast it as.

    Returns:
      The value cast as cast_as_str defines.
    """
    if cast_as_str == 'str':
        return value

    if cast_as_str == 'int':
        return int(value)

    if cast_as_str == 'float':
        return float(value)

    if cast_as_str == 'bool':
        return bool(value == 'True')

    # TODO: Support more casting.
    return value


ONTOLOGY = ontology()
