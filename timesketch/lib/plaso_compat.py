# Copyright 2026 Google Inc. All rights reserved.
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
"""Compatibility helpers for event attributes renamed by Plaso.

Plaso 20260720 renamed several event attributes, e.g. "body" to "message_body"
and "computer_name" to "hostname". Timesketch requires Plaso >= 20260720 for
new imports, but existing timelines created with older Plaso versions still
contain the legacy field names.

Code that reads or queries these fields should use the current field name
together with the helpers in this module, which transparently fall back to
the legacy field names. The helpers are bidirectional, so a lookup of a legacy
name (e.g. from an outdated user config) also falls back to the current name.

Once timelines created with Plaso < 20260720 are no longer supported, remove
the corresponding entries from PLASO_FIELD_ALIASES.
"""

from typing import Any, Dict, Iterable, List, Tuple

# Maps the current Plaso field name to its legacy field name(s).
PLASO_FIELD_ALIASES: Dict[str, Tuple[str, ...]] = {
    # log2timeline/plaso#5130: syslog, systemd journal and other text logs.
    "message_body": ("body",),
    # log2timeline/plaso#5136: Windows EventLog (EVT/EVTX) records and others.
    "hostname": ("computer_name",),
}


def _build_field_name_lookup(
    aliases: Dict[str, Tuple[str, ...]],
) -> Dict[str, Tuple[str, ...]]:
    """Builds a bidirectional lookup of field names and their aliases.

    Args:
        aliases (dict[str, tuple[str]]): current field names mapped to their
            legacy field names.

    Returns:
        dict[str, tuple[str]]: every known field name mapped to all equivalent
            field names, starting with the field name itself followed by the
            current name and then the legacy names.
    """
    lookup = {}
    for current_name, legacy_names in aliases.items():
        group = (current_name, *legacy_names)
        for field_name in group:
            lookup[field_name] = (field_name,) + tuple(
                name for name in group if name != field_name
            )
    return lookup


_FIELD_NAME_LOOKUP = _build_field_name_lookup(PLASO_FIELD_ALIASES)


def get_field_names(field_name: str) -> Tuple[str, ...]:
    """Returns a field name and its aliases in order of preference.

    Args:
        field_name (str): name of the field, e.g. "message_body".

    Returns:
        tuple[str]: the field name followed by its aliases, e.g.
            ("message_body", "body"). Field names without aliases are returned
            as a tuple containing only the field name.
    """
    return _FIELD_NAME_LOOKUP.get(field_name, (field_name,))


def expand_field_names(field_names: Iterable[str]) -> List[str]:
    """Expands a list of field names with their aliases.

    Useful to build the list of fields to return from a search.

    Args:
        field_names (Iterable[str]): names of fields.

    Returns:
        list[str]: unique field names including aliases, in order of first
            occurrence.
    """
    expanded_field_names = []
    for field_name in field_names:
        for name in get_field_names(field_name):
            if name not in expanded_field_names:
                expanded_field_names.append(name)
    return expanded_field_names


def get_field_value(source: Dict, field_name: str, default: Any = None) -> Any:
    """Returns the value of a field, falling back to its aliases.

    Args:
        source (dict): event source, e.g. the "_source" of an OpenSearch hit.
        field_name (str): name of the field, e.g. "hostname".
        default (Any): value to return if neither the field nor any of its
            aliases are set.

    Returns:
        Any: the value of the first field that is set, where None and empty
            strings, lists, tuples or dicts are considered not set, or the
            default value.
    """
    for name in get_field_names(field_name):
        value = source.get(name)
        if value is None:
            continue
        if isinstance(value, (str, list, tuple, dict)) and not value:
            continue
        return value
    return default


def build_field_query(field_name: str, value: str) -> str:
    """Builds a query string clause that matches a field or its aliases.

    Args:
        field_name (str): name of the field, e.g. "message_body".
        value (str): query string value, e.g. "*Accepted*".

    Returns:
        str: query string clause, e.g.
            "(message_body:*Accepted* OR body:*Accepted*)", or
            "field_name:value" if the field has no aliases.
    """
    field_names = get_field_names(field_name)
    if len(field_names) == 1:
        return f"{field_name}:{value}"
    clauses = " OR ".join(f"{name}:{value}" for name in field_names)
    return f"({clauses})"
